"""Validated, benchmarked FA-FR-006 orchestration."""

from __future__ import annotations

import time
import uuid
from collections import Counter
from dataclasses import replace
from typing import Any

import psutil
from sqlalchemy.ext.asyncio import AsyncSession

from backend.correlation.production_engine import CorrelationConfig, ProductionCorrelationEngine
from backend.correlation.production_repository import ProductionCorrelationRepository
from backend.correlation.schemas import AnalyzeCorrelationRequest


class CorrelationValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Correlation input validation failed")


class ProductionCorrelationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionCorrelationRepository(session)

    async def execute(
        self,
        request: AnalyzeCorrelationRequest,
        *,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        analysis_id = execution_id or str(uuid.uuid4())
        config = CorrelationConfig.load()
        updates: dict[str, Any] = {}
        if request.coefficient_threshold is not None:
            updates["coefficient_threshold"] = request.coefficient_threshold
        if request.confidence_threshold is not None:
            updates["min_confidence"] = request.confidence_threshold
        if request.significance_level is not None:
            updates["significance_level"] = request.significance_level
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
                details={"incremental": request.incremental, "requirement": "FA-FR-006"},
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
                historical_window=request.historical_window,
            )
            load_ms = (time.perf_counter() - load_started) * 1000
            issues, warnings = validate_correlation_source(source)
            warnings.extend(source["warnings"])
            if issues:
                raise CorrelationValidationError(issues)
            compute_started = time.perf_counter()
            result = ProductionCorrelationEngine(config).analyze(
                observations=source["observations"],
                source_record_counts=source["source_record_counts"],
                recurrences=source["recurrences"],
                failure_rates=source["failure_rates"],
                analysis_id=analysis_id,
                current_execution_id=source["detection"].analysis_id,
            )
            compute_ms = (time.perf_counter() - compute_started) * 1000
            processing_ms = round((time.perf_counter() - started) * 1000, 3)
            benchmarks = correlation_benchmarks(
                result["correlations"],
                request.expected_correlated_pairs,
                request.expected_uncorrelated_pairs,
            )
            memory_current = process.memory_info().rss
            benchmarks.update(
                {
                    "detection_latency_ms": processing_ms,
                    "throughput_records_per_second": round(
                        len(source["observations"]) / max(processing_ms / 1000, 0.000001), 3
                    ),
                    "cpu_time_ms": round((time.process_time() - cpu_started) * 1000, 3),
                    "process_memory_mb": round(memory_current / (1024 * 1024), 3),
                    "memory_delta_mb": round((memory_current - memory_started) / (1024 * 1024), 3),
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
                algorithm=config.algorithm,
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
                "correlation_count": len(persisted),
                "processing_ms": processing_ms,
                "correlations": [serialize_correlation(row) for row in persisted],
                "matrix": result["matrix"],
                "relationship_graph": result["relationship_graph"],
                "benchmark_metrics": benchmarks,
                "warnings": warnings,
            }
        except Exception as exc:
            await self.session.rollback()
            persisted_audit = await self.repo.get_audit(analysis_id)
            if persisted_audit is not None:
                message = str(exc.issues) if isinstance(exc, CorrelationValidationError) else str(exc)
                await self.repo.mark_failed(persisted_audit, message)
                await self.session.commit()
            raise


def validate_correlation_source(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    observations = source["observations"]
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []
    keys = [
        (str(row.get("execution_id", "")), str(row.get("detected_pattern_id", "")), str(row.get("source_record_id", "")))
        for row in observations
    ]
    duplicates = [key for key, count in Counter(keys).items() if count > 1]
    if duplicates:
        issues.append({"code": "DUPLICATE_RECORDS", "message": "Duplicate traceable pattern occurrences", "records": duplicates[:50]})
    missing_pattern = [str(row.get("occurrence_id", "")) for row in observations if not str(row.get("pattern_id", "")).strip()]
    if missing_pattern:
        issues.append({"code": "MISSING_PATTERN_ID", "message": "Every occurrence requires a Pattern ID", "occurrence_ids": missing_pattern[:50]})
    missing_fault = [str(row.get("occurrence_id", "")) for row in observations if not str(row.get("fault_type", "")).strip()]
    if missing_fault:
        issues.append({"code": "MISSING_FAULT_TYPE", "message": "Every occurrence requires an FA-FR-004 Fault Type", "occurrence_ids": missing_fault[:50]})
    if len(source["source_record_counts"]) < 2:
        issues.append({"code": "MISSING_HISTORICAL_DATASETS", "message": "At least two compatible historical executions are required"})
    recurrence_pairs = {(row["pattern_id"], row["fault_type"]) for row in source["recurrences"]}
    current_execution = source["detection"].analysis_id
    current_pairs = {
        (row["pattern_id"], row["fault_type"])
        for row in observations
        if row["execution_id"] == current_execution
    }
    uncovered = sorted(current_pairs - recurrence_pairs)
    if uncovered:
        warnings.append(f"{len(uncovered)} current pattern/fault pairs are not recurring and were excluded")
    if not recurrence_pairs:
        issues.append({"code": "MISSING_RECURRENCE_RESULTS", "message": "FA-FR-005 produced no eligible recurrence pairs"})
    return issues, warnings


def correlation_benchmarks(
    correlations: list[dict[str, Any]],
    expected_pairs: list[str],
    expected_negative_pairs: list[str] | None = None,
) -> dict[str, Any]:
    detected = {f"{row['pattern_id']}|{row['fault_type']}" for row in correlations}
    expected = {item.strip() for item in expected_pairs if item.strip()}
    negatives = {item.strip() for item in (expected_negative_pairs or []) if item.strip()}
    if not expected:
        return {
            "ground_truth_available": False,
            "correlation_accuracy": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "false_positive_rate": None,
            "false_negative_rate": None,
        }
    tp = len(detected & expected)
    fp = len(detected & negatives) if negatives else len(detected - expected)
    fn = len(expected - detected)
    tn = len(negatives - detected)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    return {
        "ground_truth_available": True,
        "correlation_accuracy": round((tp + tn) / max(1, tp + tn + fp + fn), 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(2 * precision * recall / max(precision + recall, 0.000001), 6),
        "false_positive_rate": round(fp / max(1, fp + tn), 6) if negatives else None,
        "false_negative_rate": round(fn / max(1, tp + fn), 6),
    }


def serialize_correlation(row: Any) -> dict[str, Any]:
    return {
        "correlation_id": row.correlation_id,
        "analysis_id": row.analysis_id,
        "pattern_id": row.pattern_id,
        "fault_type": row.fault_type,
        "correlated_failures": row.correlated_failures,
        "correlation_coefficient": row.correlation_coefficient,
        "correlation_strength": row.correlation_strength,
        "confidence_score": row.confidence_score,
        "p_value": row.p_value,
        "sample_size": row.sample_size,
        "severity": row.severity,
        "trend_status": row.trend_status,
        "hotspot_location": row.hotspot_location,
        "engineering_recommendation": row.engineering_recommendation,
        "correlation_timestamp": row.correlation_timestamp.isoformat() if row.correlation_timestamp else None,
    }
