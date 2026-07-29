"""Validated, benchmarked FA-FR-007 orchestration."""

from __future__ import annotations

import time
import uuid
from collections import Counter
from dataclasses import replace
from typing import Any

import psutil
from sqlalchemy.ext.asyncio import AsyncSession

from backend.die_analysis.production_engine import (
    DieAnalysisConfig,
    ProductionDieAnalysisEngine,
)
from backend.die_analysis.production_repository import ProductionDieAnalysisRepository
from backend.die_analysis.schemas import AnalyzeDieRequest


class DieValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Die analysis input validation failed")


class ProductionDieAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionDieAnalysisRepository(session)

    async def execute(
        self,
        request: AnalyzeDieRequest,
        *,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        analysis_id = execution_id or str(uuid.uuid4())
        config = DieAnalysisConfig.load()
        updates: dict[str, Any] = {}
        if request.hotspot_density_threshold is not None:
            updates["hotspot_density"] = request.hotspot_density_threshold
        if request.cluster_eps is not None:
            updates["cluster_eps"] = request.cluster_eps
        if request.confidence_threshold is not None:
            updates["min_confidence"] = request.confidence_threshold
        if updates:
            config = replace(config, **updates)
        audit = await self.repo.get_audit(analysis_id)
        if audit is None:
            audit = await self.repo.create_audit(
                analysis_id=analysis_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                config_version=config.version,
                status="processing",
                actor=request.actor,
                details={"incremental": request.incremental, "requirement": "FA-FR-007"},
            )
        else:
            audit.status = "processing"
        await self.session.commit()

        started = time.perf_counter()
        cpu_started = time.process_time()
        process = psutil.Process()
        memory_started = process.memory_info().rss
        try:
            load_started = time.perf_counter()
            source = await self.repo.load_analysis_source(
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                detection_execution_id=request.detection_execution_id,
                computation_id=request.computation_id,
                recurrence_analysis_id=request.recurrence_analysis_id,
                correlation_analysis_id=request.correlation_analysis_id,
                historical_window=request.historical_window,
                compatible_formula_prefix=config.compatible_formula_prefix,
                require_same_tenant=config.require_same_tenant,
                require_product_overlap=config.require_product_overlap,
                require_test_stage_overlap=config.require_test_stage_overlap,
            )
            load_ms = (time.perf_counter() - load_started) * 1000
            issues, warnings = validate_die_source(source)
            warnings.extend(source["warnings"])
            if issues:
                raise DieValidationError(issues)
            compute_started = time.perf_counter()
            result = ProductionDieAnalysisEngine(config).analyze(
                observations=source["observations"],
                source_record_counts=source["source_record_counts"],
                correlations=source["correlations"],
                recurrences=source["recurrences"],
                failure_rates=source["failure_rates"],
                analysis_id=analysis_id,
                current_execution_id=source["detection"].analysis_id,
            )
            compute_ms = (time.perf_counter() - compute_started) * 1000
            processing_ms = round((time.perf_counter() - started) * 1000, 3)
            benchmarks = die_benchmarks(
                result["dies"],
                request.expected_failing_die_ids,
                request.expected_passing_die_ids,
            )
            memory_current = process.memory_info().rss
            benchmarks.update(
                {
                    "detection_latency_ms": processing_ms,
                    "throughput_records_per_second": round(
                        len(source["observations"])
                        / max(processing_ms / 1000, 0.000001),
                        3,
                    ),
                    "cpu_time_ms": round((time.process_time() - cpu_started) * 1000, 3),
                    "process_memory_mb": round(memory_current / (1024 * 1024), 3),
                    "memory_delta_mb": round(
                        (memory_current - memory_started) / (1024 * 1024), 3
                    ),
                    "database_load_ms": round(load_ms, 3),
                    "computation_ms": round(compute_ms, 3),
                    "api_sla_met": processing_ms < 2000,
                }
            )
            persist_started = time.perf_counter()
            persisted = await self.repo.persist(
                analysis_id=analysis_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                source=source,
                result=result,
                audit=audit,
                processing_ms=processing_ms,
                benchmarks=benchmarks,
                warnings=warnings,
                config_version=config.version,
            )
            benchmarks["database_persist_ms"] = round(
                (time.perf_counter() - persist_started) * 1000, 3
            )
            audit.benchmark_metrics = benchmarks
            await self.session.commit()
            upstream = dict(audit.upstream_execution_ids or {})
            return {
                "execution_id": analysis_id,
                "dataset_id": request.dataset_id,
                "upload_id": request.upload_id,
                "status": "completed",
                "config_version": config.version,
                "upstream_execution_ids": upstream,
                "source_record_count": sum(source["source_record_counts"].values()),
                "die_count": len(persisted),
                "failing_die_count": sum(1 for row in persisted if row.is_failing),
                "hotspot_count": len(result["hotspots"]),
                "cluster_count": len(result["clusters"]),
                "processing_ms": processing_ms,
                "dies": [serialize_die(row) for row in persisted],
                "hotspots": result["hotspots"],
                "clusters": result["clusters"],
                "statistics": result["statistics"],
                "benchmark_metrics": benchmarks,
                "warnings": warnings,
            }
        except Exception as exc:
            await self.session.rollback()
            persisted_audit = await self.repo.get_audit(analysis_id)
            if persisted_audit is not None:
                message = (
                    str(exc.issues)
                    if isinstance(exc, DieValidationError)
                    else str(exc)
                )
                await self.repo.mark_failed(persisted_audit, message)
                await self.session.commit()
            raise


def validate_die_source(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    observations = source["observations"]
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []
    keys = [
        (
            str(row.get("execution_id", "")),
            str(row.get("detected_pattern_id", "")),
            str(row.get("source_record_id", "")),
        )
        for row in observations
    ]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        issues.append(
            {
                "code": "DUPLICATE_RECORDS",
                "message": "Duplicate traceable pattern occurrences",
                "records": duplicates[:50],
            }
        )
    current_execution = source["detection"].analysis_id
    current = [
        row for row in observations if row.get("execution_id") == current_execution
    ]
    missing_identity = [
        str(row.get("occurrence_id", ""))
        for row in current
        if not all(
            str(row.get(field, "")).strip() for field in ("lot_id", "wafer_id", "die_id")
        )
    ]
    if missing_identity:
        issues.append(
            {
                "code": "MISSING_DIE_IDENTITY",
                "message": "Every current occurrence requires lot_id, wafer_id, and die_id",
                "occurrence_ids": missing_identity[:50],
            }
        )
    coordinate_conflicts: dict[tuple[str, str, str], set[tuple[Any, Any]]] = {}
    for row in current:
        identity = (
            str(row.get("lot_id", "")),
            str(row.get("wafer_id", "")),
            str(row.get("die_id", "")),
        )
        if row.get("x") is None or row.get("y") is None:
            continue
        coordinate_conflicts.setdefault(identity, set()).add(
            (float(row["x"]), float(row["y"]))
        )
    conflicting = [
        key for key, coords in coordinate_conflicts.items() if len(coords) > 1
    ]
    if conflicting:
        issues.append(
            {
                "code": "COORDINATE_CONFLICT",
                "message": "A die identity cannot map to multiple distinct coordinates",
                "dies": [
                    {"lot_id": lot, "wafer_id": wafer, "die_id": die}
                    for lot, wafer, die in conflicting[:50]
                ],
            }
        )
    if not source["correlations"]:
        issues.append(
            {
                "code": "MISSING_CORRELATION_RESULTS",
                "message": "FA-FR-006 produced no eligible correlations",
            }
        )
    missing_coordinates = sum(
        1 for row in current if row.get("x") is None or row.get("y") is None
    )
    if missing_coordinates:
        warnings.append(
            f"{missing_coordinates} current occurrences lack coordinates; "
            "they remain eligible for die aggregation but not spatial clustering"
        )
    return issues, warnings


def die_benchmarks(
    dies: list[dict[str, Any]],
    expected_failing: list[str],
    expected_passing: list[str] | None = None,
) -> dict[str, Any]:
    detected_failing = {str(row["die_id"]) for row in dies if row.get("is_failing")}
    expected = {item.strip() for item in expected_failing if item.strip()}
    negatives = {item.strip() for item in (expected_passing or []) if item.strip()}
    if not expected:
        return {
            "ground_truth_available": False,
            "die_detection_accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "false_positive_rate": None,
            "false_negative_rate": None,
        }
    tp = len(detected_failing & expected)
    fp = (
        len(detected_failing & negatives)
        if negatives
        else len(detected_failing - expected)
    )
    fn = len(expected - detected_failing)
    tn = len(negatives - detected_failing)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "ground_truth_available": True,
        "die_detection_accuracy": round((tp + tn) / max(1, tp + tn + fp + fn), 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(
            2 * precision * recall / max(precision + recall, 0.000001), 6
        ),
        "false_positive_rate": round(fp / max(1, fp + tn), 6) if negatives else None,
        "false_negative_rate": round(fn / max(1, tp + fn), 6),
    }


def serialize_die(row: Any) -> dict[str, Any]:
    return {
        "die_result_id": row.die_result_id,
        "analysis_id": row.analysis_id,
        "lot_id": row.lot_id,
        "wafer_id": row.wafer_id,
        "die_id": row.die_id,
        "x": row.x,
        "y": row.y,
        "failure_count": row.failure_count,
        "total_tests": row.total_tests,
        "failure_density": row.failure_density,
        "neighbor_failure_count": row.neighbor_failure_count,
        "is_isolated": row.is_isolated,
        "is_failing": row.is_failing,
        "health_score": row.health_score,
        "severity": row.severity,
        "confidence_score": row.confidence_score,
        "trend_status": row.trend_status,
        "dominant_fault_type": row.dominant_fault_type,
        "dominant_pattern_id": row.dominant_pattern_id,
        "hotspot_id": row.hotspot_id,
        "cluster_id": row.cluster_id,
        "engineering_recommendation": row.engineering_recommendation,
        "analyzed_at": row.analyzed_at.isoformat() if row.analyzed_at else None,
    }
