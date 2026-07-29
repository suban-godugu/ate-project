"""Validated, auditable FA-FR-005 orchestration service."""

from __future__ import annotations

import time
import uuid
from collections import Counter
from dataclasses import replace
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
import psutil

from backend.recurring.production_engine import (
    ProductionRecurrenceEngine,
    RecurrenceComputationError,
    RecurrenceConfig,
)
from backend.recurring.production_repository import ProductionRecurrenceRepository
from backend.recurring.schemas import AnalyzeRecurrenceRequest


class RecurrenceValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Recurrence input validation failed")


class ProductionRecurrenceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionRecurrenceRepository(session)

    async def execute(
        self,
        request: AnalyzeRecurrenceRequest,
        *,
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        analysis_id = execution_id or str(uuid.uuid4())
        config = RecurrenceConfig.load()
        if request.similarity_threshold is not None:
            config = replace(config, similarity_threshold=request.similarity_threshold)
        audit = await self.repo.get_audit(analysis_id)
        if audit is None:
            audit = await self.repo.create_audit(
                analysis_id=analysis_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                detection_execution_id=request.detection_execution_id,
                computation_id=request.computation_id,
                status="processing",
                config_version=config.version,
                actor=request.actor,
                details={
                    "incremental": request.incremental,
                    "requirement": "FA-FR-005",
                },
            )
        else:
            audit.status = "processing"
            audit.config_version = config.version
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
                historical_window=request.historical_window,
                compatible_formula_prefix=config.compatible_formula_prefix,
                require_same_tenant=config.require_same_tenant,
                require_product_overlap=config.require_product_overlap,
                require_test_stage_overlap=config.require_test_stage_overlap,
            )
            load_ms = (time.perf_counter() - load_started) * 1000
            issues, warnings = validate_recurrence_source(
                observations=source["observations"],
                current_execution_id=source["detection"].analysis_id,
                current_source_count=source["source_record_counts"].get(
                    source["detection"].analysis_id, 0
                ),
                detection_source_count=int(source["detection"].source_record_count),
                computation_source_count=int(source["current"].source_record_count),
            )
            warnings.extend(source["warnings"])
            if issues:
                raise RecurrenceValidationError(issues)

            compute_started = time.perf_counter()
            result = ProductionRecurrenceEngine(config).analyze(
                observations=source["observations"],
                current_execution_id=source["detection"].analysis_id,
                source_record_counts=source["source_record_counts"],
                failure_rates=source["failure_rates"],
                incremental=request.incremental,
            )
            computation_ms = (time.perf_counter() - compute_started) * 1000
            processing_ms = round((time.perf_counter() - started) * 1000, 3)
            memory_current = process.memory_info().rss
            benchmark = recurrence_benchmarks(
                result["recurrences"],
                request.expected_recurring_pattern_ids,
                request.expected_non_recurring_pattern_ids,
            )
            benchmark.update(
                {
                    "detection_latency_ms": processing_ms,
                    "throughput_records_per_second": round(
                        len(source["observations"]) / max(processing_ms / 1000, 0.000001),
                        3,
                    ),
                    "cpu_time_ms": round(
                        (time.process_time() - cpu_started) * 1000, 3
                    ),
                    "process_memory_mb": round(memory_current / (1024 * 1024), 3),
                    "memory_delta_mb": round(
                        (memory_current - memory_started) / (1024 * 1024), 3
                    ),
                    "database_load_ms": round(load_ms, 3),
                    "computation_ms": round(computation_ms, 3),
                    "api_sla_met": processing_ms < 2000,
                }
            )
            persist_started = time.perf_counter()
            persisted = await self.repo.persist(
                analysis_id=analysis_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                detection_execution_id=source["detection"].analysis_id,
                computation_id=source["current"].computation_id,
                classification_execution_id=source[
                    "classification_execution_ids"
                ][0],
                config_version=config.version,
                incremental=request.incremental,
                result=result,
                audit=audit,
                source_record_count=sum(source["source_record_counts"].values()),
                processing_ms=processing_ms,
                benchmark_metrics=benchmark,
                warnings=warnings,
            )
            benchmark["database_persist_ms"] = round(
                (time.perf_counter() - persist_started) * 1000, 3
            )
            audit.benchmark_metrics = benchmark
            await self.session.commit()
            return {
                "execution_id": analysis_id,
                "dataset_id": request.dataset_id,
                "upload_id": request.upload_id,
                "detection_execution_id": source["detection"].analysis_id,
                "computation_id": source["current"].computation_id,
                "classification_execution_id": source[
                    "classification_execution_ids"
                ][0],
                "status": "completed",
                "config_version": config.version,
                "source_record_count": sum(source["source_record_counts"].values()),
                "pattern_count": len(
                    {row.pattern_id for row in persisted}
                ),
                "recurrence_count": len(persisted),
                "hotspot_count": len(result["hotspots"]),
                "processing_ms": processing_ms,
                "recurrences": [serialize_recurrence(row) for row in persisted],
                "benchmark_metrics": benchmark,
                "warnings": warnings,
            }
        except Exception as exc:
            await self.session.rollback()
            persisted_audit = await self.repo.get_audit(analysis_id)
            if persisted_audit is not None:
                message = (
                    str(exc.issues)
                    if isinstance(exc, RecurrenceValidationError)
                    else str(exc)
                )
                await self.repo.mark_failed(persisted_audit, message)
                await self.session.commit()
            raise


def validate_recurrence_source(
    *,
    observations: list[dict[str, Any]],
    current_execution_id: str,
    current_source_count: int,
    detection_source_count: int,
    computation_source_count: int,
) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not observations:
        return [{"code": "EMPTY_SOURCE", "message": "No pattern observations"}], warnings
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
                "code": "DUPLICATE_OCCURRENCES",
                "message": "Duplicate pattern occurrences are not allowed",
                "occurrences": duplicates[:50],
            }
        )
    if any(not str(row.get("pattern_id", "")).strip() for row in observations):
        issues.append(
            {"code": "MISSING_PATTERN_ID", "message": "Pattern ID is mandatory"}
        )
    invalid_timestamps = [
        str(row.get("occurrence_id"))
        for row in observations
        if not _valid_timestamp(row.get("timestamp"))
    ]
    if invalid_timestamps:
        issues.append(
            {
                "code": "INVALID_TIMESTAMPS",
                "message": "Every occurrence requires a valid timestamp",
                "occurrence_ids": invalid_timestamps[:50],
            }
        )
    current = [
        row for row in observations if str(row.get("execution_id")) == current_execution_id
    ]
    if not current:
        issues.append(
            {
                "code": "CURRENT_EXECUTION_EMPTY",
                "message": "Current FA-FR-002 execution has no traceable occurrences",
            }
        )
    missing_fault_types = [
        str(row.get("occurrence_id"))
        for row in current
        if not str(row.get("fault_type", "")).strip()
    ]
    if missing_fault_types:
        issues.append(
            {
                "code": "MISSING_FAULT_TYPE",
                "message": (
                    "Every current occurrence must match a completed FA-FR-004 "
                    "classified fault"
                ),
                "occurrence_ids": missing_fault_types[:50],
            }
        )
    if current_source_count <= 0:
        issues.append(
            {"code": "INVALID_TEST_COUNT", "message": "Source record count must be positive"}
        )
    if detection_source_count and current_source_count != detection_source_count:
        issues.append(
            {
                "code": "DETECTION_SOURCE_DRIFT",
                "message": (
                    f"FA-FR-002 used {detection_source_count} records but "
                    f"{current_source_count} are currently available"
                ),
            }
        )
    if computation_source_count and current_source_count != computation_source_count:
        warnings.append(
            f"FA-FR-003 used {computation_source_count} PASS/FAIL records while "
            f"FA-FR-001 contains {current_source_count} total normalized records"
        )
    missing_coordinates = sum(
        1 for row in current if row.get("x") is None or row.get("y") is None
    )
    if missing_coordinates:
        warnings.append(
            f"{missing_coordinates} current occurrences have no coordinates; "
            "they remain eligible for recurrence but not hotspot analysis"
        )
    return issues, warnings


def recurrence_benchmarks(
    recurrences: list[dict[str, Any]],
    expected_pattern_ids: list[str],
    expected_non_recurring_pattern_ids: list[str] | None = None,
) -> dict[str, Any]:
    detected = {str(row["pattern_id"]) for row in recurrences}
    expected = {str(item) for item in expected_pattern_ids if str(item)}
    expected_negative = {
        str(item)
        for item in (expected_non_recurring_pattern_ids or [])
        if str(item)
    }
    if not expected:
        return {
            "ground_truth_available": False,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "false_positive_rate": None,
            "false_discovery_rate": None,
            "false_negative_rate": None,
        }
    true_positive = len(detected & expected)
    false_positive = (
        len(detected & expected_negative)
        if expected_negative
        else len(detected - expected)
    )
    false_negative = len(expected - detected)
    true_negative = len(expected_negative - detected)
    precision = true_positive / max(1, true_positive + false_positive)
    recall = true_positive / max(1, true_positive + false_negative)
    f1 = 2 * precision * recall / max(precision + recall, 0.000001)
    return {
        "ground_truth_available": True,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(f1, 6),
        "false_positive_rate": round(
            false_positive / max(1, false_positive + true_negative), 6
        )
        if expected_negative
        else None,
        "false_discovery_rate": round(
            len(detected - expected) / max(1, len(detected)), 6
        ),
        "false_negative_rate": round(
            false_negative / max(1, len(expected)), 6
        ),
    }


def serialize_recurrence(row: Any) -> dict[str, Any]:
    return {
        "recurrence_id": row.recurrence_id,
        "analysis_id": row.analysis_id,
        "pattern_id": row.pattern_id,
        "pattern_name": row.pattern_name,
        "fault_type": row.fault_type,
        "recurrence_count": row.recurrence_count,
        "recurrence_frequency": row.recurrence_frequency,
        "recurrence_percentage": row.recurrence_percentage,
        "confidence_score": row.confidence_score,
        "severity": row.severity,
        "trend_direction": row.trend_direction,
        "first_occurrence": row.first_occurrence.isoformat(),
        "latest_occurrence": row.latest_occurrence.isoformat(),
        "historical_frequency": row.historical_frequency,
        "hotspot_location": row.hotspot_location,
        "engineering_recommendation": row.engineering_recommendation,
        "similarity_group": row.similarity_group,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _valid_timestamp(value: Any) -> bool:
    if isinstance(value, datetime):
        return True
    text = str(value or "").strip()
    if not text:
        return False
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False
