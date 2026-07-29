"""Validated, benchmarked FA-FR-008 orchestration."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections import Counter
from dataclasses import replace
from typing import Any

import psutil
from sqlalchemy.ext.asyncio import AsyncSession

from backend.wafer_analysis.production_engine import (
    ProductionWaferAnalysisEngine,
    WaferAnalysisConfig,
)
from backend.wafer_analysis.production_repository import ProductionWaferAnalysisRepository
from backend.wafer_analysis.schemas import AnalyzeWaferRequest


class WaferValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Wafer analysis input validation failed")


class ProductionWaferAnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionWaferAnalysisRepository(session)

    async def execute(
        self,
        request: AnalyzeWaferRequest,
        *,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        analysis_id = execution_id or str(uuid.uuid4())
        config = WaferAnalysisConfig.load()
        updates: dict[str, Any] = {}
        if request.hotspot_density_threshold is not None:
            updates["hotspot_density"] = request.hotspot_density_threshold
        if request.edge_radius_fraction is not None:
            updates["edge_radius_fraction"] = request.edge_radius_fraction
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
                details={"incremental": request.incremental, "requirement": "FA-FR-008"},
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
                die_analysis_id=request.die_analysis_id,
                historical_window=request.historical_window,
                compatible_formula_prefix=config.compatible_formula_prefix,
                require_same_tenant=config.require_same_tenant,
                require_product_overlap=config.require_product_overlap,
                require_test_stage_overlap=config.require_test_stage_overlap,
            )
            load_ms = (time.perf_counter() - load_started) * 1000
            issues, warnings = validate_wafer_source(source)
            warnings.extend(source.get("warnings", []))
            if issues:
                raise WaferValidationError(issues)
            compute_started = time.perf_counter()
            result = ProductionWaferAnalysisEngine(config).analyze(
                dies=source["dies"],
                die_hotspots=source["die_hotspots"],
                historical_wafer_yields=source["historical_wafer_yields"],
                analysis_id=analysis_id,
                die_analysis_id=source["die_audit"].analysis_id,
            )
            compute_ms = (time.perf_counter() - compute_started) * 1000
            processing_ms = round((time.perf_counter() - started) * 1000, 3)
            benchmarks = wafer_benchmarks(
                result["wafers"],
                request.expected_failing_wafer_ids,
                request.expected_passing_wafer_ids,
            )
            memory_current = process.memory_info().rss
            benchmarks.update(
                {
                    "detection_latency_ms": processing_ms,
                    "throughput_dies_per_second": round(
                        len(source["dies"]) / max(processing_ms / 1000, 0.000001),
                        3,
                    ),
                    "cpu_time_ms": round((time.process_time() - cpu_started) * 1000, 3),
                    "process_memory_mb": round(memory_current / (1024 * 1024), 3),
                    "memory_delta_mb": round(
                        (memory_current - memory_started) / (1024 * 1024), 3
                    ),
                    "database_load_ms": round(load_ms, 3),
                    "computation_ms": round(compute_ms, 3),
                    "api_sla_met": processing_ms < 3000,
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
                "source_die_count": len(source["dies"]),
                "wafer_count": len(persisted),
                "failing_wafer_count": sum(
                    1 for row in persisted if row.failing_dies > 0
                ),
                "hotspot_count": len(result["hotspots"]),
                "processing_ms": processing_ms,
                "wafers": [serialize_wafer(row) for row in persisted],
                "hotspots": result["hotspots"],
                "yield_metrics": result["yield_metrics"],
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
                    if isinstance(exc, WaferValidationError)
                    else str(exc)
                )
                await self.repo.mark_failed(persisted_audit, message)
                await self.session.commit()
            raise


def validate_wafer_source(
    source: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    dies = source["dies"]
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []

    die_result_ids = [str(row.get("die_result_id", "")) for row in dies]
    duplicates = [key for key, count in Counter(die_result_ids).items() if count > 1]
    if duplicates:
        issues.append(
            {
                "code": "DUPLICATE_RECORDS",
                "message": "Duplicate die result identities in FA-FR-007 handoff",
                "records": duplicates[:50],
            }
        )

    missing_wafer = [
        str(row.get("die_result_id", ""))
        for row in dies
        if not str(row.get("wafer_id", "")).strip()
    ]
    if missing_wafer:
        issues.append(
            {
                "code": "MISSING_WAFER_ID",
                "message": "Every die result requires wafer_id",
                "die_result_ids": missing_wafer[:50],
            }
        )

    missing_lot = [
        str(row.get("die_result_id", ""))
        for row in dies
        if not str(row.get("lot_id", "")).strip()
    ]
    if missing_lot:
        issues.append(
            {
                "code": "MISSING_LOT_ID",
                "message": "Every die result requires lot_id",
                "die_result_ids": missing_lot[:50],
            }
        )

    coordinate_conflicts: dict[tuple[str, str, str], set[tuple[Any, Any]]] = {}
    invalid_coordinates: list[str] = []
    for row in dies:
        identity = (
            str(row.get("lot_id", "")),
            str(row.get("wafer_id", "")),
            str(row.get("die_id", "")),
        )
        x, y = row.get("x"), row.get("y")
        if x is None or y is None:
            continue
        try:
            coords = (round(float(x), 6), round(float(y), 6))
        except (TypeError, ValueError):
            invalid_coordinates.append(str(row.get("die_result_id", "")))
            continue
        if not math_is_finite(coords[0]) or not math_is_finite(coords[1]):
            invalid_coordinates.append(str(row.get("die_result_id", "")))
            continue
        coordinate_conflicts.setdefault(identity, set()).add(coords)

    if invalid_coordinates:
        issues.append(
            {
                "code": "INVALID_COORDINATES",
                "message": "Die coordinates must be finite numeric values",
                "die_result_ids": invalid_coordinates[:50],
            }
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

    wafer_keys = [
        hashlib.sha256(
            f"{str(row.get('lot_id', '')).lower()}|{str(row.get('wafer_id', '')).lower()}".encode()
        ).hexdigest()
        for row in dies
        if str(row.get("wafer_id", "")).strip()
    ]
    if not wafer_keys:
        issues.append(
            {
                "code": "MISSING_WAFER_RESULTS",
                "message": "FA-FR-007 produced no eligible wafer identities",
            }
        )

    missing_coordinates = sum(
        1 for row in dies if row.get("x") is None or row.get("y") is None
    )
    if missing_coordinates:
        warnings.append(
            f"{missing_coordinates} die results lack coordinates; "
            "radial and edge/center metrics use available spatial dies only"
        )
    return issues, warnings


def math_is_finite(value: float) -> bool:
    return value == value and abs(value) != float("inf")


def wafer_benchmarks(
    wafers: list[dict[str, Any]],
    expected_failing: list[str],
    expected_passing: list[str] | None = None,
) -> dict[str, Any]:
    detected_failing = {
        str(row["wafer_id"]) for row in wafers if row.get("failing_dies", 0) > 0
    }
    expected = {item.strip() for item in expected_failing if item.strip()}
    negatives = {item.strip() for item in (expected_passing or []) if item.strip()}
    if not expected:
        return {
            "ground_truth_available": False,
            "wafer_detection_accuracy": None,
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
        "wafer_detection_accuracy": round((tp + tn) / max(1, tp + tn + fp + fn), 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(
            2 * precision * recall / max(precision + recall, 0.000001), 6
        ),
        "false_positive_rate": round(fp / max(1, fp + tn), 6) if negatives else None,
        "false_negative_rate": round(fn / max(1, tp + fn), 6),
    }


def serialize_wafer(row: Any) -> dict[str, Any]:
    return {
        "wafer_result_id": row.wafer_result_id,
        "analysis_id": row.analysis_id,
        "lot_id": row.lot_id,
        "wafer_id": row.wafer_id,
        "total_dies": row.total_dies,
        "failing_dies": row.failing_dies,
        "yield_pct": row.yield_pct,
        "failure_density": row.failure_density,
        "edge_failure_rate": row.edge_failure_rate,
        "center_failure_rate": row.center_failure_rate,
        "health_score": row.health_score,
        "severity": row.severity,
        "confidence_score": row.confidence_score,
        "trend_status": row.trend_status,
        "engineering_recommendation": row.engineering_recommendation,
        "analyzed_at": row.analyzed_at.isoformat() if row.analyzed_at else None,
    }
