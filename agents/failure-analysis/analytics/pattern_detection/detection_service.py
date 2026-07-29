"""Application service for validated, traceable FA-FR-002 execution."""

from __future__ import annotations

import os
import time
import uuid
from collections import Counter
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import SCHEMA_VERSION, TestRecord
from analytics.pattern_detection.detection_repository import DetectionRepository
from analytics.pattern_detection.rule_engine import EngineeringRuleEngine
from analytics.pattern_detection.schemas import DetectPatternsRequest


class DetectionValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Normalized source validation failed")


class DetectionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = DetectionRepository(session)
        self.session = session

    async def execute(
        self, request: DetectPatternsRequest, *, execution_id: str | None = None
    ) -> dict[str, Any]:
        started = time.perf_counter()
        analysis_id = execution_id or str(uuid.uuid4())
        engine = EngineeringRuleEngine()
        history = await self.repo.begin_history(
            analysis_id=analysis_id,
            dataset_id=request.dataset_id,
            upload_id=request.upload_id,
            rule_set_version=engine.rule_set.version,
            actor=request.actor,
        )
        await self.session.commit()
        try:
            records, source_rows = await self.repo.load_source(
                dataset_id=request.dataset_id, upload_id=request.upload_id
            )
            issues, warnings = validate_normalized_source(records, source_rows)
            if issues:
                raise DetectionValidationError(issues)
            if request.incremental:
                prior = await self.repo.prior_record_keys(
                    dataset_id=request.dataset_id, upload_id=request.upload_id
                )
                records = [
                    record
                    for record in records
                    if (record.record_key or record.build_record_key()) not in prior
                ]
                if prior:
                    warnings.append(
                        f"Incremental analysis skipped {len(prior)} previously analyzed record keys"
                    )
            if not records:
                raise DetectionValidationError(
                    [
                        {
                            "code": "NO_ELIGIBLE_RECORDS",
                            "message": "No new valid normalized records are available",
                        }
                    ]
                )

            await self.repo.upsert_config_rules(engine.rule_set.rules, request.actor)
            detections = engine.detect(records)
            threshold = (
                request.confidence_threshold
                if request.confidence_threshold is not None
                else engine.rule_set.confidence_threshold
            )
            detections = [d for d in detections if d["confidence"] >= threshold]
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            benchmark = benchmark_metrics(
                detections,
                expected_pattern_ids=request.expected_pattern_ids,
                processing_ms=elapsed_ms,
                source_count=len(records),
            )
            confidence_distribution = _confidence_distribution(detections)
            report = {
                "requirement": "FA-FR-002",
                "analysis_id": analysis_id,
                "dataset_id": request.dataset_id,
                "upload_id": request.upload_id,
                "rule_set_version": engine.rule_set.version,
                "source_record_count": len(records),
                "pattern_count": len(detections),
                "confidence_distribution": confidence_distribution,
                "benchmark_metrics": benchmark,
                "warnings": warnings,
            }
            patterns = await self.repo.persist_detection(
                analysis_id=analysis_id,
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
                detections=detections,
                total_records=len(records),
                threshold=threshold,
                processing_ms=elapsed_ms,
                report=report,
                history=history,
            )
            await self.session.commit()
            return {
                "execution_id": analysis_id,
                "dataset_id": request.dataset_id,
                "upload_id": request.upload_id,
                "status": "completed",
                "pattern_count": len(patterns),
                "source_record_count": len(records),
                "processing_ms": elapsed_ms,
                "rule_set_version": engine.rule_set.version,
                "patterns": [serialize_pattern(row) for row in patterns],
                "benchmark_metrics": benchmark,
                "warnings": warnings,
            }
        except Exception as exc:
            await self.session.rollback()
            persisted_history = await self.repo.session.get(type(history), history.id)
            if persisted_history is not None:
                message = (
                    str(exc.issues)
                    if isinstance(exc, DetectionValidationError)
                    else str(exc)
                )
                await self.repo.mark_failed(persisted_history, message)
                await self.session.commit()
            raise


def validate_normalized_source(
    records: list[TestRecord], source_rows: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[dict[str, Any]] = []
    warnings: list[str] = []
    if not records:
        return (
            [{"code": "EMPTY_DATASET", "message": "Normalized source is empty"}],
            warnings,
        )
    seen: set[str] = set()
    for index, (record, source) in enumerate(zip(records, source_rows, strict=True)):
        key = record.record_key or record.build_record_key()
        if key in seen:
            issues.append(
                {
                    "code": "DUPLICATE_RECORD",
                    "record": index,
                    "message": f"Duplicate normalized record key: {key}",
                }
            )
        seen.add(key)
        missing = record.missing_mandatory()
        if missing:
            issues.append(
                {
                    "code": "MISSING_METADATA",
                    "record": index,
                    "fields": missing,
                    "message": "Mandatory normalized metadata is missing",
                }
            )
        if record.x is not None and not -100_000 <= record.x <= 100_000:
            issues.append(
                {
                    "code": "INVALID_COORDINATE",
                    "record": index,
                    "field": "x",
                    "value": record.x,
                }
            )
        if record.y is not None and not -100_000 <= record.y <= 100_000:
            issues.append(
                {
                    "code": "INVALID_COORDINATE",
                    "record": index,
                    "field": "y",
                    "value": record.y,
                }
            )
        version = source["payload"].get("schema_version", SCHEMA_VERSION)
        if version != SCHEMA_VERSION:
            issues.append(
                {
                    "code": "UNSUPPORTED_SCHEMA",
                    "record": index,
                    "value": version,
                    "expected": SCHEMA_VERSION,
                }
            )
        if (
            record.pass_fail.upper() == "FAIL"
            and not record.failing_patterns
            and not record.failing_tests
        ):
            warnings.append(
                f"Record {key} has no Pattern ID; it will be evaluated as unknown"
            )
    return issues, warnings[:100]


def benchmark_metrics(
    detections: list[dict[str, Any]],
    *,
    expected_pattern_ids: list[str] | None,
    processing_ms: float,
    source_count: int,
) -> dict[str, Any]:
    throughput = (
        round(source_count / (processing_ms / 60_000), 2) if processing_ms > 0 else 0.0
    )
    metrics: dict[str, Any] = {
        "detection_latency_ms": processing_ms,
        "throughput_records_per_minute": throughput,
        "resource_pid": os.getpid(),
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1_score": None,
        "false_positive_rate": None,
        "false_negative_rate": None,
    }
    if expected_pattern_ids is None:
        return metrics
    expected = set(expected_pattern_ids)
    predicted = {str(d["pattern_id"]) for d in detections}
    tp = len(expected & predicted)
    fp = len(predicted - expected)
    fn = len(expected - predicted)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    metrics.update(
        {
            "accuracy": round(tp / max(len(expected | predicted), 1), 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fp / max(len(predicted), 1), 4),
            "false_negative_rate": round(fn / max(len(expected), 1), 4),
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
        }
    )
    return metrics


def _confidence_distribution(detections: list[dict[str, Any]]) -> dict[str, int]:
    buckets: Counter[str] = Counter()
    for item in detections:
        score = item["confidence"]
        bucket = "high" if score >= 0.85 else "medium" if score >= 0.65 else "low"
        buckets[bucket] += 1
    return dict(buckets)


def serialize_pattern(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "analysis_id": row.analysis_id,
        "dataset_id": row.dataset_id,
        "pattern_id": row.pattern_id,
        "pattern_name": row.pattern_name,
        "pattern_category": row.pattern_category,
        "pattern_frequency": row.pattern_frequency,
        "confidence": row.confidence,
        "detection_method": row.detection_method,
        "severity_level": row.severity_level,
        "failure_count": row.failure_count,
        "affected_device_count": len(row.affected_devices or []),
        "affected_die_count": len(row.affected_dies or []),
        "affected_wafer_count": len(row.affected_wafers or []),
        "affected_lot_count": len(row.affected_lots or []),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
