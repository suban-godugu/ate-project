"""PostgreSQL repository for versioned FA-FR-003 computations."""

from __future__ import annotations

import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from analytics.failure_rates.computation_engine import ComputationConfig
from backend.ingestion.models_ingestion import IngestionDataset, NormalizedRecord
from backend.models import (
    ComputationHistory,
    DetectedPattern,
    DetectionHistory,
    FailureRateMetric,
    FailureStatistic,
    FailureTrendAnalysis,
    HistoricalFailureRate,
    PatternOccurrence,
    ThresholdConfiguration,
    Upload,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductionFailureRateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_source(
        self,
        *,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str | None,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        DetectionHistory,
    ]:
        if dataset_id:
            source = await self.session.get(IngestionDataset, dataset_id)
            if source is None:
                raise LookupError("Dataset not found")
            if source.status != "completed":
                raise ValueError(f"FA-FR-001 dataset status is {source.status}")
            record_stmt = select(NormalizedRecord).where(
                NormalizedRecord.dataset_id == dataset_id
            )
        else:
            source = await self.session.get(Upload, upload_id)
            if source is None:
                raise LookupError("Upload not found")
            if source.status != "completed":
                raise ValueError(f"FA-FR-001 upload status is {source.status}")
            record_stmt = select(NormalizedRecord).where(
                NormalizedRecord.upload_id == upload_id
            )

        detection_stmt = select(DetectionHistory).where(
            DetectionHistory.execution_status == "completed"
        )
        if detection_execution_id:
            detection_stmt = detection_stmt.where(
                DetectionHistory.analysis_id == detection_execution_id
            )
        elif dataset_id:
            detection_stmt = detection_stmt.where(
                DetectionHistory.dataset_id == dataset_id
            )
        else:
            detection_stmt = detection_stmt.where(
                DetectionHistory.upload_id == upload_id
            )
        detection_stmt = detection_stmt.order_by(DetectionHistory.created_at.desc())
        detection = (await self.session.execute(detection_stmt)).scalars().first()
        if detection is None:
            raise ValueError("A completed FA-FR-002 detection execution is required")
        if dataset_id and detection.dataset_id != dataset_id:
            raise ValueError("Detection execution does not belong to this dataset")
        if upload_id and detection.upload_id != upload_id:
            raise ValueError("Detection execution does not belong to this upload")

        normalized = list(
            (await self.session.execute(record_stmt.order_by(NormalizedRecord.id)))
            .scalars()
            .all()
        )
        records: list[dict[str, Any]] = []
        for row in normalized:
            payload = dict(row.payload or {})
            records.append(
                {
                    **payload,
                    "id": row.id,
                    "upload_id": row.upload_id,
                    "dataset_id": row.dataset_id,
                    "record_key": row.record_key,
                    "lot_id": row.lot_id,
                    "wafer_id": row.wafer_id,
                    "die_id": row.die_id,
                    "device_id": payload.get("product_id") or row.tester_id,
                    "test_program": payload.get("test_program") or row.test_stage,
                    "pass_fail": row.pass_fail,
                }
            )

        patterns = list(
            (
                await self.session.execute(
                    select(DetectedPattern)
                    .where(DetectedPattern.analysis_id == detection.analysis_id)
                    .order_by(DetectedPattern.id)
                )
            )
            .scalars()
            .all()
        )
        pattern_payload = [
            {
                "id": row.id,
                "pattern_id": row.pattern_id,
                "category": row.pattern_category,
                "confidence": row.confidence,
            }
            for row in patterns
        ]
        detected_ids = [row.id for row in patterns]
        occurrences: list[PatternOccurrence] = []
        if detected_ids:
            occurrences = list(
                (
                    await self.session.execute(
                        select(PatternOccurrence).where(
                            PatternOccurrence.detected_pattern_id.in_(detected_ids)
                        )
                    )
                )
                .scalars()
                .all()
            )
        occurrence_payload = [
            {
                "id": row.id,
                "detected_pattern_id": row.detected_pattern_id,
                "source_record_id": row.source_record_id,
            }
            for row in occurrences
        ]
        return records, pattern_payload, occurrence_payload, detection

    async def baselines(
        self,
        *,
        pattern_ids: list[str],
        levels: list[str],
        limit_per_series: int,
    ) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
        if not pattern_ids:
            return {}
        stmt = (
            select(FailureRateMetric)
            .where(
                FailureRateMetric.pattern_id.in_(pattern_ids),
                FailureRateMetric.aggregation_level.in_(levels),
            )
            .order_by(FailureRateMetric.computed_at.desc())
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            key = (row.pattern_id, row.aggregation_level, row.aggregation_key)
            if len(grouped[key]) >= limit_per_series:
                continue
            grouped[key].append(
                {
                    "computation_id": row.computation_id,
                    "failure_percentage": row.failure_percentage,
                }
            )
        return dict(grouped)

    async def begin_history(
        self,
        *,
        computation_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str,
        formula_version: str,
        aggregation_levels: list[str],
        window_size: int,
        actor: str | None,
    ) -> ComputationHistory:
        history = ComputationHistory(
            computation_id=computation_id,
            dataset_id=dataset_id,
            upload_id=upload_id,
            detection_execution_id=detection_execution_id,
            status="processing",
            formula_version=formula_version,
            aggregation_levels=aggregation_levels,
            window_size=window_size,
            actor=actor,
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def seed_thresholds(
        self, config: ComputationConfig, actor: str | None
    ) -> None:
        for threshold in config.thresholds:
            stmt = select(ThresholdConfiguration).where(
                ThresholdConfiguration.configuration_key == threshold.key,
                ThresholdConfiguration.version == threshold.version,
            )
            if (await self.session.execute(stmt)).scalar_one_or_none():
                continue
            self.session.add(
                ThresholdConfiguration(
                    configuration_key=threshold.key,
                    version=threshold.version,
                    pattern_id=threshold.pattern_id,
                    aggregation_level=threshold.aggregation_level,
                    warning_percentage=threshold.warning,
                    critical_percentage=threshold.critical,
                    abnormal_delta_percentage=threshold.abnormal_delta,
                    created_by=actor,
                    metadata_json={"source": "failure_rate_computation.yaml"},
                )
            )

    async def persist(
        self,
        *,
        computation_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str,
        formula_version: str,
        metrics: list[dict[str, Any]],
        source_record_count: int,
        pattern_count: int,
        processing_ms: float,
        benchmark_metrics: dict[str, Any],
        warnings: list[str],
        history: ComputationHistory,
    ) -> list[FailureRateMetric]:
        persisted: list[FailureRateMetric] = []
        by_level: dict[str, list[FailureRateMetric]] = defaultdict(list)
        for item in metrics:
            row = FailureRateMetric(
                computation_id=computation_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                detection_execution_id=detection_execution_id,
                detected_pattern_id=item["detected_pattern_id"],
                pattern_id=item["pattern_id"],
                aggregation_level=item["aggregation_level"],
                aggregation_key=item["aggregation_key"],
                formula_version=formula_version,
                total_tests=item["total_tests"],
                pass_count=item["pass_count"],
                fail_count=item["fail_count"],
                failure_percentage=item["failure_percentage"],
                failure_density=item["failure_density"],
                pattern_frequency=item["pattern_frequency"],
                moving_average=item["moving_average"],
                baseline_percentage=item["baseline_percentage"],
                historical_delta=item["historical_delta"],
                trend_status=item["trend_status"],
                threshold_status=item["threshold_status"],
                threshold_value=item["threshold_value"],
                severity_level=item["severity_level"],
                metadata_json={
                    "threshold_key": item["threshold_key"],
                    "history_ids": item["history_ids"],
                },
            )
            self.session.add(row)
            await self.session.flush()
            persisted.append(row)
            by_level[row.aggregation_level].append(row)
            self.session.add(
                HistoricalFailureRate(
                    failure_rate_id=row.id,
                    computation_id=computation_id,
                    pattern_id=row.pattern_id,
                    aggregation_level=row.aggregation_level,
                    aggregation_key=row.aggregation_key,
                    failure_percentage=row.failure_percentage,
                    baseline_percentage=row.baseline_percentage,
                    source_computation_ids=item["history_ids"],
                )
            )
            relative = (
                (row.historical_delta / row.baseline_percentage) * 100
                if row.baseline_percentage not in (None, 0)
                and row.historical_delta is not None
                else None
            )
            self.session.add(
                FailureTrendAnalysis(
                    computation_id=computation_id,
                    failure_rate_id=row.id,
                    pattern_id=row.pattern_id,
                    aggregation_level=row.aggregation_level,
                    aggregation_key=row.aggregation_key,
                    trend_direction=row.trend_status,
                    current_percentage=row.failure_percentage,
                    moving_average=row.moving_average,
                    baseline_percentage=row.baseline_percentage,
                    absolute_change=row.historical_delta,
                    relative_change=relative,
                    abnormal_increase=row.trend_status == "worsening",
                    details={"threshold_status": row.threshold_status},
                )
            )

        for level, rows in by_level.items():
            rates = [row.failure_percentage for row in rows]
            self.session.add(
                FailureStatistic(
                    computation_id=computation_id,
                    aggregation_level=level,
                    metric_count=len(rows),
                    mean_failure_percentage=statistics.mean(rates),
                    median_failure_percentage=statistics.median(rates),
                    std_dev=statistics.pstdev(rates) if len(rates) > 1 else 0.0,
                    minimum=min(rates),
                    maximum=max(rates),
                    total_tests=sum(row.total_tests for row in rows),
                    total_failures=sum(row.fail_count for row in rows),
                    details={},
                )
            )
        history.status = "completed"
        history.source_record_count = source_record_count
        history.pattern_count = pattern_count
        history.metric_count = len(persisted)
        history.processing_ms = processing_ms
        history.benchmark_metrics = benchmark_metrics
        history.warnings = warnings
        history.details = {
            "formula": "(Fail Count / Total Test Count) × 100",
            "metric_count": len(persisted),
        }
        history.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, history: ComputationHistory, message: str) -> None:
        history.status = "failed"
        history.errors = [message]
        history.completed_at = _now()
        await self.session.flush()

    async def mark_completed_empty(
        self,
        history: ComputationHistory,
        *,
        warnings: list[str] | None = None,
    ) -> None:
        history.status = "completed"
        history.source_record_count = 0
        history.pattern_count = 0
        history.metric_count = 0
        history.warnings = warnings or []
        history.completed_at = _now()
        await self.session.flush()

    async def list_metrics(
        self,
        *,
        limit: int,
        offset: int,
        pattern_id: str | None,
        level: str | None,
        computation_id: str | None,
    ) -> list[FailureRateMetric]:
        stmt = select(FailureRateMetric).order_by(
            FailureRateMetric.computed_at.desc(),
            FailureRateMetric.failure_percentage.desc(),
        )
        if pattern_id:
            stmt = stmt.where(FailureRateMetric.pattern_id == pattern_id)
        if level:
            stmt = stmt.where(FailureRateMetric.aggregation_level == level)
        if computation_id:
            stmt = stmt.where(FailureRateMetric.computation_id == computation_id)
        return list(
            (
                await self.session.execute(stmt.offset(offset).limit(limit))
            ).scalars().all()
        )

    async def get_pattern_metrics(self, pattern_id: str) -> list[FailureRateMetric]:
        return await self.list_metrics(
            limit=1000,
            offset=0,
            pattern_id=pattern_id,
            level=None,
            computation_id=None,
        )

    async def trends(self, limit: int) -> list[FailureTrendAnalysis]:
        stmt = (
            select(FailureTrendAnalysis)
            .order_by(FailureTrendAnalysis.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def statistics(self) -> dict[str, Any]:
        total = await self.session.scalar(select(func.count(FailureRateMetric.id))) or 0
        avg = (
            await self.session.scalar(
                select(func.avg(FailureRateMetric.failure_percentage))
            )
            or 0.0
        )
        violations = (
            await self.session.scalar(
                select(func.count(FailureRateMetric.id)).where(
                    FailureRateMetric.threshold_status != "within_limit"
                )
            )
            or 0
        )
        latest = (
            await self.session.execute(
                select(ComputationHistory)
                .where(ComputationHistory.status == "completed")
                .order_by(ComputationHistory.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        levels = (
            await self.session.execute(
                select(
                    FailureRateMetric.aggregation_level,
                    func.count(FailureRateMetric.id),
                    func.avg(FailureRateMetric.failure_percentage),
                ).group_by(FailureRateMetric.aggregation_level)
            )
        ).all()
        return {
            "total_metrics": total,
            "average_failure_percentage": round(float(avg), 6),
            "threshold_violations": violations,
            "latest_computation_id": latest.computation_id if latest else None,
            "latest_benchmark_metrics": latest.benchmark_metrics if latest else {},
            "by_level": [
                {
                    "aggregation_level": level,
                    "metric_count": count,
                    "average_failure_percentage": round(float(level_avg or 0), 6),
                }
                for level, count, level_avg in levels
            ],
        }

    async def histories(self, limit: int) -> list[ComputationHistory]:
        stmt = (
            select(ComputationHistory)
            .order_by(ComputationHistory.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())
