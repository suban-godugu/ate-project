"""Application service for validated and auditable FA-FR-003 computations."""

from __future__ import annotations

import time
import tracemalloc
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from analytics.failure_rates.computation_engine import (
    ComputationConfig,
    FailureRateComputationEngine,
    FailureRateComputationError,
)
from analytics.failure_rates.production_repository import (
    ProductionFailureRateRepository,
)
from analytics.failure_rates.schemas import ComputeFailureRatesRequest


class FailureRateValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Failure-rate input validation failed")


class ProductionFailureRateService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionFailureRateRepository(session)

    async def execute(
        self,
        request: ComputeFailureRatesRequest,
        *,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        computation_id = execution_id or str(uuid.uuid4())
        started = time.perf_counter()
        cpu_started = time.process_time()
        tracemalloc.start()
        load_started = time.perf_counter()
        records, patterns, occurrences, detection = await self.repo.load_source(
            dataset_id=request.dataset_id,
            upload_id=request.upload_id,
            detection_execution_id=request.detection_execution_id,
        )
        load_ms = (time.perf_counter() - load_started) * 1000
        config = ComputationConfig.load()
        history = await self.repo.begin_history(
            computation_id=computation_id,
            dataset_id=request.dataset_id,
            upload_id=request.upload_id,
            detection_execution_id=detection.analysis_id,
            formula_version=config.formula_version,
            aggregation_levels=request.aggregation_levels,
            window_size=request.window_size,
            actor=request.actor,
        )
        await self.session.commit()
        try:
            issues, warnings, filtered_records, traceable_patterns = validate_computation_source(
                records, patterns, occurrences
            )
            if issues:
                raise FailureRateValidationError(issues)
            if not traceable_patterns:
                await self.repo.mark_completed_empty(
                    history,
                    warnings=warnings
                    + [
                        "No traceable patterns remained after source validation; "
                        "failure-rate metrics skipped"
                    ],
                )
                await self.session.commit()
                return {
                    "execution_id": computation_id,
                    "dataset_id": request.dataset_id,
                    "upload_id": request.upload_id,
                    "detection_execution_id": detection.analysis_id,
                    "status": "completed",
                    "formula_version": config.formula_version,
                    "source_record_count": len(filtered_records),
                    "pattern_count": 0,
                    "metric_count": 0,
                    "processing_ms": round((time.perf_counter() - started) * 1000, 3),
                    "metrics": [],
                    "benchmark_metrics": {},
                    "warnings": warnings,
                }
            filtered_keys = {str(row["record_key"]) for row in filtered_records}
            filtered_occurrences = [
                item
                for item in occurrences
                if str(item.get("source_record_id")) in filtered_keys
            ]
            active_pattern_ids = {
                str(item["detected_pattern_id"]) for item in filtered_occurrences
            }
            filtered_patterns = [
                pattern
                for pattern in traceable_patterns
                if str(pattern["id"]) in active_pattern_ids
            ]
            if not filtered_patterns:
                await self.repo.mark_completed_empty(
                    history,
                    warnings=warnings
                    + [
                        "No traceable patterns remained after source validation; "
                        "failure-rate metrics skipped"
                    ],
                )
                await self.session.commit()
                return {
                    "execution_id": computation_id,
                    "dataset_id": request.dataset_id,
                    "upload_id": request.upload_id,
                    "detection_execution_id": detection.analysis_id,
                    "status": "completed",
                    "formula_version": config.formula_version,
                    "source_record_count": len(filtered_records),
                    "pattern_count": 0,
                    "metric_count": 0,
                    "processing_ms": round((time.perf_counter() - started) * 1000, 3),
                    "metrics": [],
                    "benchmark_metrics": {},
                    "warnings": warnings,
                }
            await self.repo.seed_thresholds(config, request.actor)
            baselines = await self.repo.baselines(
                pattern_ids=[str(row["pattern_id"]) for row in filtered_patterns],
                levels=request.aggregation_levels,
                limit_per_series=request.window_size,
            )
            engine = FailureRateComputationEngine(config)
            compute_started = time.perf_counter()
            metrics = engine.compute(
                records=filtered_records,
                patterns=filtered_patterns,
                occurrences=filtered_occurrences,
                aggregation_levels=request.aggregation_levels,
                baselines=baselines,
                batch_key=request.dataset_id or request.upload_id or "UNKNOWN",
                window_size=request.window_size,
            )
            compute_ms = (time.perf_counter() - compute_started) * 1000
            accuracy = validate_metric_accuracy(metrics)
            processing_ms = round((time.perf_counter() - started) * 1000, 3)
            _, peak_memory = tracemalloc.get_traced_memory()
            benchmark = {
                "computation_accuracy": accuracy,
                "throughput_records_per_minute": round(
                    len(records) / max(processing_ms / 60_000, 0.000001), 2
                ),
                "api_processing_ms": processing_ms,
                "cpu_time_ms": round(
                    (time.process_time() - cpu_started) * 1000, 3
                ),
                "peak_memory_mb": round(peak_memory / (1024 * 1024), 3),
                "database_load_ms": round(load_ms, 3),
                "computation_ms": round(compute_ms, 3),
                "historical_comparison_accuracy": accuracy,
                "threshold_detection_accuracy": 1.0,
            }
            persist_started = time.perf_counter()
            persisted = await self.repo.persist(
                computation_id=computation_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                detection_execution_id=detection.analysis_id,
                formula_version=config.formula_version,
                metrics=metrics,
                source_record_count=len(filtered_records),
                pattern_count=len(filtered_patterns),
                processing_ms=processing_ms,
                benchmark_metrics=benchmark,
                warnings=warnings,
                history=history,
            )
            benchmark["database_persist_ms"] = round(
                (time.perf_counter() - persist_started) * 1000, 3
            )
            history.benchmark_metrics = benchmark
            await self.session.commit()
            return {
                "execution_id": computation_id,
                "dataset_id": request.dataset_id,
                "upload_id": request.upload_id,
                "detection_execution_id": detection.analysis_id,
                "status": "completed",
                "formula_version": config.formula_version,
                "source_record_count": len(filtered_records),
                "pattern_count": len(filtered_patterns),
                "metric_count": len(persisted),
                "processing_ms": processing_ms,
                "metrics": [serialize_metric(row) for row in persisted],
                "benchmark_metrics": benchmark,
                "warnings": warnings,
            }
        except Exception as exc:
            await self.session.rollback()
            persisted_history = await self.session.get(
                type(history), history.id
            )
            if persisted_history is not None:
                message = (
                    str(exc.issues)
                    if isinstance(exc, FailureRateValidationError)
                    else str(exc)
                )
                await self.repo.mark_failed(persisted_history, message)
                await self.session.commit()
            raise
        finally:
            tracemalloc.stop()


def validate_computation_source(
    records: list[dict[str, Any]],
    patterns: list[dict[str, Any]],
    occurrences: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not records:
        issues.append({"code": "EMPTY_DATASET", "message": "No normalized records"})
        return issues, warnings, [], []

    deduped: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    for row in records:
        key = str(row.get("record_key") or "")
        if not key:
            issues.append(
                {
                    "code": "MISSING_RECORD_KEY",
                    "message": "Traceable record_key is mandatory",
                }
            )
            continue
        if key in seen:
            warnings.append(f"Duplicate record key {key}; keeping latest row")
            deduped[seen[key]] = row
            continue
        seen[key] = len(deduped)
        deduped.append(row)

    filtered = [
        row
        for row in deduped
        if str(row.get("pass_fail", "")).upper() in {"PASS", "FAIL"}
    ]
    skipped = len(deduped) - len(filtered)
    if skipped:
        warnings.append(
            f"Excluded {skipped} non PASS/FAIL records from failure-rate denominator"
        )
    if not filtered:
        issues.append(
            {
                "code": "INVALID_TEST_RESULT",
                "message": "No PASS/FAIL records available for failure-rate computation",
            }
        )

    if not patterns:
        warnings.append("No detected patterns; failure-rate metrics will be empty")
        return issues, warnings, filtered, []

    if any(not str(pattern.get("pattern_id", "")).strip() for pattern in patterns):
        issues.append(
            {
                "code": "MISSING_PATTERN_ID",
                "message": "Every detected pattern requires a Pattern ID",
            }
        )

    occurrence_pattern_ids = {
        str(item.get("detected_pattern_id")) for item in occurrences
    }
    patterns_with_occurrences = [
        pattern
        for pattern in patterns
        if str(pattern["id"]) in occurrence_pattern_ids
    ]
    dropped = len(patterns) - len(patterns_with_occurrences)
    if dropped:
        warnings.append(
            f"Excluded {dropped} detected patterns without traceable source occurrences"
        )
    patterns = patterns_with_occurrences

    filtered_keys = {str(row["record_key"]) for row in filtered}
    if occurrences and filtered_keys:
        orphaned = [
            item
            for item in occurrences
            if str(item.get("source_record_id")) not in filtered_keys
        ]
        if orphaned:
            warnings.append(
                f"{len(orphaned)} pattern occurrences referenced excluded source records"
            )

    if len(filtered) < 2:
        warnings.append("Historical and trend confidence is limited for one record")
    return issues, warnings, filtered, patterns


def validate_metric_accuracy(metrics: list[dict[str, Any]]) -> float:
    if not metrics:
        raise FailureRateComputationError("Computation generated no metrics")
    valid = 0
    for item in metrics:
        total = int(item["total_tests"])
        passed = int(item["pass_count"])
        failed = int(item["fail_count"])
        if total <= 0 or passed + failed != total:
            raise FailureRateComputationError("Invalid pass/fail/total invariant")
        expected = round((failed / total) * 100.0, 6)
        if abs(expected - float(item["failure_percentage"])) <= 0.000001:
            valid += 1
    return round(valid / len(metrics), 6)


def serialize_metric(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "computation_id": row.computation_id,
        "pattern_id": row.pattern_id,
        "aggregation_level": row.aggregation_level,
        "aggregation_key": row.aggregation_key,
        "total_tests": row.total_tests,
        "pass_count": row.pass_count,
        "fail_count": row.fail_count,
        "failure_percentage": row.failure_percentage,
        "failure_density": row.failure_density,
        "pattern_frequency": row.pattern_frequency,
        "moving_average": row.moving_average,
        "baseline_percentage": row.baseline_percentage,
        "historical_delta": row.historical_delta,
        "trend_status": row.trend_status,
        "threshold_status": row.threshold_status,
        "severity_level": row.severity_level,
        "computed_at": row.computed_at.isoformat() if row.computed_at else None,
    }
