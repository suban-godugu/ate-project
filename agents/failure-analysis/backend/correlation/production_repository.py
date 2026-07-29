"""Versioned FA-FR-006 handoff, persistence, and query repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    CorrelationAuditLog,
    CorrelationHistory,
    CorrelationStatistic,
    CorrelationTrend,
    EngineeringRecommendation,
    FailurePatternCorrelation,
    RecurrenceAuditLog,
    RecurringFailure,
)
from backend.recurring.production_repository import ProductionRecurrenceRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductionCorrelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def load_analysis_source(
        self,
        *,
        dataset_id: str | None,
        upload_id: str | None,
        detection_execution_id: str | None,
        computation_id: str | None,
        recurrence_analysis_id: str | None,
        historical_window: int,
    ) -> dict[str, Any]:
        source = await ProductionRecurrenceRepository(self.session).load_analysis_source(
            dataset_id=dataset_id,
            upload_id=upload_id,
            detection_execution_id=detection_execution_id,
            computation_id=computation_id,
            historical_window=historical_window,
            compatible_formula_prefix="failure-rate-v1",
            require_same_tenant=True,
            require_product_overlap=True,
            require_test_stage_overlap=True,
        )
        stmt = select(RecurrenceAuditLog).where(
            RecurrenceAuditLog.status == "completed",
            RecurrenceAuditLog.detection_execution_id == source["detection"].analysis_id,
            RecurrenceAuditLog.computation_id == source["current"].computation_id,
        )
        if dataset_id:
            stmt = stmt.where(RecurrenceAuditLog.dataset_id == dataset_id)
        else:
            stmt = stmt.where(RecurrenceAuditLog.upload_id == upload_id)
        if recurrence_analysis_id:
            stmt = stmt.where(RecurrenceAuditLog.analysis_id == recurrence_analysis_id)
        audit = (
            await self.session.execute(stmt.order_by(RecurrenceAuditLog.completed_at.desc()).limit(1))
        ).scalar_one_or_none()
        if audit is None:
            raise ValueError("A completed FA-FR-005 recurrence analysis for this exact upstream lineage is required")
        recurrences = list(
            (
                await self.session.execute(
                    select(RecurringFailure).where(RecurringFailure.analysis_id == audit.analysis_id)
                )
            ).scalars().all()
        )
        if not recurrences:
            raise ValueError("FA-FR-005 completed without traceable recurring failures")
        return {
            **source,
            "recurrence_audit": audit,
            "recurrences": [
                {
                    "recurrence_id": row.recurrence_id,
                    "analysis_id": row.analysis_id,
                    "pattern_id": row.pattern_id,
                    "fault_type": row.fault_type,
                    "recurrence_count": row.recurrence_count,
                    "recurrence_frequency": row.recurrence_frequency,
                    "confidence_score": row.confidence_score,
                    "severity": row.severity,
                    "trend_status": row.trend_direction,
                    "hotspot_location": row.hotspot_location,
                }
                for row in recurrences
            ],
        }

    async def get_audit(self, analysis_id: str) -> CorrelationAuditLog | None:
        return (
            await self.session.execute(
                select(CorrelationAuditLog)
                .where(CorrelationAuditLog.analysis_id == analysis_id)
                .order_by(CorrelationAuditLog.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def create_audit(
        self,
        *,
        analysis_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        config_version: str,
        status: str,
        actor: str | None,
        details: dict[str, Any],
    ) -> CorrelationAuditLog:
        row = CorrelationAuditLog(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            upload_id=upload_id,
            status=status,
            config_version=config_version,
            actor=actor,
            details=details,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def persist(
        self,
        *,
        analysis_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        source: dict[str, Any],
        result: dict[str, Any],
        audit: CorrelationAuditLog,
        processing_ms: float,
        benchmarks: dict[str, Any],
        warnings: list[str],
        config_version: str,
        algorithm: str,
    ) -> list[FailurePatternCorrelation]:
        persisted: list[FailurePatternCorrelation] = []
        classification_id = source["classification_execution_ids"][0]
        recurrence_analysis_id = source["recurrence_audit"].analysis_id
        for item in result["correlations"]:
            row = FailurePatternCorrelation(
                correlation_id=item["correlation_id"],
                analysis_id=analysis_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                detection_execution_id=source["detection"].analysis_id,
                computation_id=source["current"].computation_id,
                classification_execution_id=classification_id,
                recurrence_analysis_id=recurrence_analysis_id,
                recurrence_id=item["recurrence_id"],
                pattern_id=item["pattern_id"],
                fault_type=item["fault_type"],
                canonical_correlation_key=item["canonical_correlation_key"],
                correlated_failures=item["correlated_failures"],
                correlation_coefficient=item["correlation_coefficient"],
                correlation_strength=item["correlation_strength"],
                confidence_score=item["confidence_score"],
                p_value=item["p_value"],
                sample_size=item["sample_size"],
                severity=item["severity"],
                trend_status=item["trend_status"],
                hotspot_location=item["hotspot_location"],
                engineering_recommendation=item["engineering_recommendation"],
                algorithm=algorithm,
                config_version=config_version,
                metadata_json={
                    "support": item["support"],
                    "impact_score": item["impact_score"],
                    "contingency": item["contingency"],
                    "source_execution_ids": item["source_execution_ids"],
                    "scope_breakdown": item["scope_breakdown"],
                },
            )
            self.session.add(row)
            persisted.append(row)
            self.session.add(
                CorrelationHistory(
                    correlation_id=row.correlation_id,
                    analysis_id=analysis_id,
                    pattern_id=row.pattern_id,
                    fault_type=row.fault_type,
                    coefficient=row.correlation_coefficient,
                    confidence_score=row.confidence_score,
                    source_execution_ids=item["source_execution_ids"],
                    details={"p_value": row.p_value, "sample_size": row.sample_size, "contingency": item["contingency"]},
                )
            )
            self.session.add(
                CorrelationTrend(
                    correlation_id=row.correlation_id,
                    analysis_id=analysis_id,
                    pattern_id=row.pattern_id,
                    fault_type=row.fault_type,
                    trend_status=row.trend_status,
                    current_coefficient=item["current_coefficient"],
                    historical_coefficient=item["historical_coefficient"],
                    absolute_change=item["current_coefficient"] - item["historical_coefficient"],
                    time_series=item["time_series"],
                )
            )
            for recommendation in item["recommendations"]:
                self.session.add(
                    EngineeringRecommendation(
                        recommendation_id=recommendation["recommendation_id"],
                        recurrence_id=None,
                        correlation_id=row.correlation_id,
                        source_module="FA-FR-006",
                        analysis_id=analysis_id,
                        pattern_id=row.pattern_id,
                        fault_type=row.fault_type,
                        recommendation_code=recommendation["recommendation_code"],
                        priority=recommendation["priority"],
                        action=recommendation["action"],
                        rationale=recommendation["rationale"],
                        evidence=recommendation["evidence"],
                        config_version=config_version,
                    )
                )
        statistics = result["statistics"]
        self.session.add(
            CorrelationStatistic(
                analysis_id=analysis_id,
                scope_type="analysis",
                scope_key=analysis_id,
                correlation_count=statistics["correlation_count"],
                strong_count=statistics["strong_count"],
                mean_coefficient=statistics["mean_coefficient"],
                mean_confidence=statistics["mean_confidence"],
                details={**statistics, "matrix": result["matrix"], "relationship_graph": result["relationship_graph"]},
            )
        )
        scoped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for item in result["correlations"]:
            for dimension, values in item["scope_breakdown"].items():
                if dimension == "failure_code":
                    continue
                for value in values:
                    scoped.setdefault((dimension.removesuffix("_id"), value), []).append(item)
        for (scope_type, scope_key), items in scoped.items():
            self.session.add(
                CorrelationStatistic(
                    analysis_id=analysis_id,
                    scope_type=scope_type,
                    scope_key=scope_key,
                    correlation_count=len(items),
                    strong_count=sum(
                        item["correlation_strength"] in {"strong", "very_strong"}
                        for item in items
                    ),
                    mean_coefficient=sum(
                        abs(item["correlation_coefficient"]) for item in items
                    )
                    / len(items),
                    mean_confidence=sum(item["confidence_score"] for item in items)
                    / len(items),
                    details={
                        "correlation_ids": [
                            item["correlation_id"] for item in items
                        ]
                    },
                )
            )
        audit.status = "completed"
        audit.source_record_count = sum(source["source_record_counts"].values())
        audit.pattern_count = len({row.pattern_id for row in persisted})
        audit.correlation_count = len(persisted)
        audit.processing_ms = processing_ms
        audit.benchmark_metrics = benchmarks
        audit.upstream_execution_ids = {
            "detection_execution_id": source["detection"].analysis_id,
            "computation_id": source["current"].computation_id,
            "classification_execution_ids": source["classification_execution_ids"],
            "recurrence_analysis_id": recurrence_analysis_id,
        }
        audit.warnings = warnings
        audit.details = {**dict(audit.details or {}), "matrix": result["matrix"], "relationship_graph": result["relationship_graph"]}
        audit.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, audit: CorrelationAuditLog, message: str) -> None:
        audit.status = "failed"
        audit.errors = [message[:2000]]
        audit.completed_at = _now()
        await self.session.flush()

    async def list_correlations(
        self,
        *,
        limit: int,
        offset: int,
        pattern_id: str | None = None,
        fault_type: str | None = None,
        strength: str | None = None,
        severity: str | None = None,
        trend: str | None = None,
        analysis_id: str | None = None,
    ) -> list[FailurePatternCorrelation]:
        stmt = select(FailurePatternCorrelation)
        for column, value in (
            (FailurePatternCorrelation.pattern_id, pattern_id),
            (FailurePatternCorrelation.fault_type, fault_type),
            (FailurePatternCorrelation.correlation_strength, strength),
            (FailurePatternCorrelation.severity, severity),
            (FailurePatternCorrelation.trend_status, trend),
            (FailurePatternCorrelation.analysis_id, analysis_id),
        ):
            if value:
                stmt = stmt.where(column == value)
        stmt = stmt.order_by(
            FailurePatternCorrelation.confidence_score.desc(),
            FailurePatternCorrelation.correlation_timestamp.desc(),
        ).offset(offset).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_correlation(self, correlation_id: str) -> FailurePatternCorrelation | None:
        return (
            await self.session.execute(
                select(FailurePatternCorrelation).where(
                    FailurePatternCorrelation.correlation_id == correlation_id
                )
            )
        ).scalar_one_or_none()

    async def history(self, limit: int) -> list[CorrelationAuditLog]:
        return list(
            (
                await self.session.execute(
                    select(CorrelationAuditLog).order_by(CorrelationAuditLog.created_at.desc()).limit(limit)
                )
            ).scalars().all()
        )

    async def trends(self, limit: int, correlation_id: str | None = None) -> list[CorrelationTrend]:
        stmt = select(CorrelationTrend)
        if correlation_id:
            stmt = stmt.where(CorrelationTrend.correlation_id == correlation_id)
        return list(
            (await self.session.execute(stmt.order_by(CorrelationTrend.created_at.desc()).limit(limit)))
            .scalars().all()
        )

    async def recommendations(self, correlation_id: str) -> list[EngineeringRecommendation]:
        return list(
            (
                await self.session.execute(
                    select(EngineeringRecommendation).where(
                        EngineeringRecommendation.correlation_id == correlation_id
                    )
                )
            ).scalars().all()
        )

    async def latest_statistics(self) -> dict[str, Any]:
        audit = (
            await self.session.execute(
                select(CorrelationAuditLog)
                .where(CorrelationAuditLog.status == "completed")
                .order_by(CorrelationAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if audit is None:
            return {"correlation_count": 0, "strong_count": 0, "mean_coefficient": 0.0, "mean_confidence": 0.0}
        statistic = (
            await self.session.execute(
                select(CorrelationStatistic)
                .where(
                    CorrelationStatistic.analysis_id == audit.analysis_id,
                    CorrelationStatistic.scope_type == "analysis",
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        return {
            "execution_id": audit.analysis_id,
            "correlation_count": audit.correlation_count,
            "strong_count": statistic.strong_count if statistic else 0,
            "mean_coefficient": statistic.mean_coefficient if statistic else 0.0,
            "mean_confidence": statistic.mean_confidence if statistic else 0.0,
            "benchmark_metrics": audit.benchmark_metrics,
            "matrix": (statistic.details or {}).get("matrix", {}) if statistic else {},
            "relationship_graph": (statistic.details or {}).get("relationship_graph", {}) if statistic else {},
        }
