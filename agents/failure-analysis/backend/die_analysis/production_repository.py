"""Versioned FA-FR-007 handoff, persistence, and query repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.correlation.production_repository import ProductionCorrelationRepository
from backend.models import (
    CorrelationAuditLog,
    DieAnalysis,
    DieAnalysisHistory,
    DieAuditLog,
    DieCluster,
    DieFailureStatistic,
    DieHealthScore,
    DieHotspot,
    EngineeringRecommendation,
    FailurePatternCorrelation,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductionDieAnalysisRepository:
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
        correlation_analysis_id: str | None,
        historical_window: int,
        compatible_formula_prefix: str,
        require_same_tenant: bool,
        require_product_overlap: bool,
        require_test_stage_overlap: bool,
    ) -> dict[str, Any]:
        source = await ProductionCorrelationRepository(self.session).load_analysis_source(
            dataset_id=dataset_id,
            upload_id=upload_id,
            detection_execution_id=detection_execution_id,
            computation_id=computation_id,
            recurrence_analysis_id=recurrence_analysis_id,
            historical_window=historical_window,
        )
        # Prefer exact upstream lineage checks over dialect-specific JSON operators.
        audit_stmt = select(CorrelationAuditLog).where(
            CorrelationAuditLog.status == "completed",
        )
        if dataset_id:
            audit_stmt = audit_stmt.where(CorrelationAuditLog.dataset_id == dataset_id)
        else:
            audit_stmt = audit_stmt.where(CorrelationAuditLog.upload_id == upload_id)
        if correlation_analysis_id:
            audit_stmt = audit_stmt.where(
                CorrelationAuditLog.analysis_id == correlation_analysis_id
            )
        candidates = list(
            (
                await self.session.execute(
                    audit_stmt.order_by(CorrelationAuditLog.completed_at.desc())
                )
            )
            .scalars()
            .all()
        )
        correlation_audit = None
        expected_detection = source["detection"].analysis_id
        expected_computation = source["current"].computation_id
        expected_recurrence = source["recurrence_audit"].analysis_id
        for candidate in candidates:
            upstream = dict(candidate.upstream_execution_ids or {})
            if (
                upstream.get("detection_execution_id") == expected_detection
                and upstream.get("computation_id") == expected_computation
                and upstream.get("recurrence_analysis_id") == expected_recurrence
            ):
                correlation_audit = candidate
                break
        if correlation_audit is None:
            raise ValueError(
                "A completed FA-FR-006 correlation analysis for this exact upstream lineage is required"
            )
        correlations = list(
            (
                await self.session.execute(
                    select(FailurePatternCorrelation).where(
                        FailurePatternCorrelation.analysis_id
                        == correlation_audit.analysis_id
                    )
                )
            )
            .scalars()
            .all()
        )
        if not correlations:
            raise ValueError("FA-FR-006 completed without traceable correlations")
        return {
            **source,
            "correlation_audit": correlation_audit,
            "correlations": [
                {
                    "correlation_id": row.correlation_id,
                    "analysis_id": row.analysis_id,
                    "pattern_id": row.pattern_id,
                    "fault_type": row.fault_type,
                    "correlation_coefficient": row.correlation_coefficient,
                    "correlation_strength": row.correlation_strength,
                    "confidence_score": row.confidence_score,
                    "severity": row.severity,
                    "trend_status": row.trend_status,
                    "hotspot_location": row.hotspot_location,
                }
                for row in correlations
            ],
            "compatible_formula_prefix": compatible_formula_prefix,
            "cohort_flags": {
                "require_same_tenant": require_same_tenant,
                "require_product_overlap": require_product_overlap,
                "require_test_stage_overlap": require_test_stage_overlap,
            },
        }

    async def get_audit(self, analysis_id: str) -> DieAuditLog | None:
        return (
            await self.session.execute(
                select(DieAuditLog)
                .where(DieAuditLog.analysis_id == analysis_id)
                .order_by(DieAuditLog.created_at.desc())
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
    ) -> DieAuditLog:
        row = DieAuditLog(
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
        audit: DieAuditLog,
        processing_ms: float,
        benchmarks: dict[str, Any],
        warnings: list[str],
        config_version: str,
    ) -> list[DieAnalysis]:
        persisted: list[DieAnalysis] = []
        classification_id = source["classification_execution_ids"][0]
        recurrence_analysis_id = source["recurrence_audit"].analysis_id
        correlation_analysis_id = source["correlation_audit"].analysis_id
        dependents: list[Any] = []
        for item in result["dies"]:
            row = DieAnalysis(
                die_result_id=item["die_result_id"],
                analysis_id=analysis_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                detection_execution_id=source["detection"].analysis_id,
                computation_id=source["current"].computation_id,
                classification_execution_id=classification_id,
                recurrence_analysis_id=recurrence_analysis_id,
                correlation_analysis_id=correlation_analysis_id,
                lot_id=item["lot_id"],
                wafer_id=item["wafer_id"],
                die_id=item["die_id"],
                canonical_die_key=item["canonical_die_key"],
                x=item["x"],
                y=item["y"],
                failure_count=item["failure_count"],
                total_tests=item["total_tests"],
                failure_density=item["failure_density"],
                neighbor_failure_count=item["neighbor_failure_count"],
                is_isolated=item["is_isolated"],
                is_failing=item["is_failing"],
                health_score=item["health_score"],
                severity=item["severity"],
                confidence_score=item["confidence_score"],
                trend_status=item["trend_status"],
                dominant_fault_type=item["dominant_fault_type"],
                dominant_pattern_id=item["dominant_pattern_id"],
                hotspot_id=item["hotspot_id"],
                cluster_id=item["cluster_id"],
                engineering_recommendation=item["engineering_recommendation"],
                lot_comparison=item["lot_comparison"],
                wafer_comparison=item["wafer_comparison"],
                config_version=config_version,
                metadata_json={
                    "pattern_breakdown": item["pattern_breakdown"],
                    "fault_breakdown": item["fault_breakdown"],
                    "occurrence_ids": item["occurrence_ids"],
                    "source_record_ids": item["source_record_ids"],
                    "historical_density": item["historical_density"],
                    "upstream_correlation_id": item.get("upstream_correlation_id"),
                    "upstream_recurrence_id": item.get("upstream_recurrence_id"),
                    "failure_rate_pct": item.get("failure_rate_pct"),
                },
            )
            self.session.add(row)
            persisted.append(row)
            dependents.append(
                DieHealthScore(
                    die_result_id=row.die_result_id,
                    analysis_id=analysis_id,
                    lot_id=row.lot_id,
                    wafer_id=row.wafer_id,
                    die_id=row.die_id,
                    health_score=row.health_score,
                    severity=row.severity,
                    confidence_score=row.confidence_score,
                    contributing_factors={
                        "failure_density": row.failure_density,
                        "neighbor_failure_count": row.neighbor_failure_count,
                        "is_isolated": row.is_isolated,
                        "trend_status": row.trend_status,
                    },
                )
            )
            dependents.append(
                DieAnalysisHistory(
                    die_result_id=row.die_result_id,
                    analysis_id=analysis_id,
                    lot_id=row.lot_id,
                    wafer_id=row.wafer_id,
                    die_id=row.die_id,
                    failure_count=row.failure_count,
                    failure_density=row.failure_density,
                    health_score=row.health_score,
                    confidence_score=row.confidence_score,
                    source_execution_ids=[
                        source["detection"].analysis_id,
                        source["current"].computation_id,
                        classification_id,
                        recurrence_analysis_id,
                        correlation_analysis_id,
                    ],
                    details={
                        "severity": row.severity,
                        "trend_status": row.trend_status,
                        "canonical_die_key": row.canonical_die_key,
                    },
                )
            )
            for recommendation in item["recommendations"]:
                dependents.append(
                    EngineeringRecommendation(
                        recommendation_id=recommendation["recommendation_id"],
                        recurrence_id=None,
                        correlation_id=None,
                        source_module="FA-FR-007",
                        analysis_id=analysis_id,
                        pattern_id=row.dominant_pattern_id or row.die_id,
                        fault_type=row.dominant_fault_type or "die_failure",
                        recommendation_code=recommendation["recommendation_code"],
                        priority=recommendation["priority"],
                        action=recommendation["action"],
                        rationale=recommendation["rationale"],
                        evidence=recommendation["evidence"],
                        config_version=config_version,
                    )
                )
        await self.session.flush()
        for hotspot in result["hotspots"]:
            dependents.append(
                DieHotspot(
                    hotspot_id=hotspot["hotspot_id"],
                    analysis_id=analysis_id,
                    lot_id=hotspot["lot_id"],
                    wafer_id=hotspot["wafer_id"],
                    center_x=hotspot["center_x"],
                    center_y=hotspot["center_y"],
                    radius=hotspot["radius"],
                    die_count=hotspot["die_count"],
                    failure_count=hotspot["failure_count"],
                    density=hotspot["density"],
                    severity=hotspot["severity"],
                    confidence_score=hotspot["confidence_score"],
                    member_die_ids=hotspot["member_die_ids"],
                    coordinates=hotspot["coordinates"],
                    details=hotspot["details"],
                )
            )
        for cluster in result["clusters"]:
            dependents.append(
                DieCluster(
                    cluster_id=cluster["cluster_id"],
                    analysis_id=analysis_id,
                    lot_id=cluster["lot_id"],
                    wafer_id=cluster["wafer_id"],
                    algorithm=cluster["algorithm"],
                    die_count=cluster["die_count"],
                    failure_count=cluster["failure_count"],
                    density=cluster["density"],
                    centroid_x=cluster["centroid_x"],
                    centroid_y=cluster["centroid_y"],
                    severity=cluster["severity"],
                    member_die_ids=cluster["member_die_ids"],
                    coordinates=cluster["coordinates"],
                    details=cluster["details"],
                )
            )
        for item in result["scoped_statistics"]:
            dependents.append(
                DieFailureStatistic(
                    analysis_id=analysis_id,
                    scope_type=item["scope_type"],
                    scope_key=item["scope_key"],
                    total_dies=item["total_dies"],
                    failing_dies=item["failing_dies"],
                    isolated_failures=item["isolated_failures"],
                    mean_failure_density=item["mean_failure_density"],
                    mean_health_score=item["mean_health_score"],
                    mean_confidence=item["mean_confidence"],
                    hotspot_count=item["hotspot_count"],
                    cluster_count=item["cluster_count"],
                    details=item["details"],
                )
            )
        self.session.add_all(dependents)
        statistics = result["statistics"]
        audit.status = "completed"
        audit.source_record_count = sum(source["source_record_counts"].values())
        audit.die_count = statistics["total_dies"]
        audit.failing_die_count = statistics["failing_dies"]
        audit.hotspot_count = statistics["hotspot_count"]
        audit.cluster_count = statistics["cluster_count"]
        audit.processing_ms = processing_ms
        audit.benchmark_metrics = benchmarks
        audit.upstream_execution_ids = {
            "detection_execution_id": source["detection"].analysis_id,
            "computation_id": source["current"].computation_id,
            "classification_execution_ids": source["classification_execution_ids"],
            "recurrence_analysis_id": recurrence_analysis_id,
            "correlation_analysis_id": correlation_analysis_id,
        }
        audit.warnings = warnings
        audit.details = {
            **dict(audit.details or {}),
            "statistics": statistics,
            "requirement": "FA-FR-007",
        }
        audit.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, audit: DieAuditLog, message: str) -> None:
        audit.status = "failed"
        audit.errors = [message[:2000]]
        audit.completed_at = _now()
        await self.session.flush()

    async def list_dies(
        self,
        *,
        limit: int,
        offset: int,
        lot_id: str | None = None,
        wafer_id: str | None = None,
        die_id: str | None = None,
        severity: str | None = None,
        is_failing: bool | None = None,
        analysis_id: str | None = None,
    ) -> list[DieAnalysis]:
        stmt = select(DieAnalysis)
        for column, value in (
            (DieAnalysis.lot_id, lot_id),
            (DieAnalysis.wafer_id, wafer_id),
            (DieAnalysis.die_id, die_id),
            (DieAnalysis.severity, severity),
            (DieAnalysis.analysis_id, analysis_id),
        ):
            if value:
                stmt = stmt.where(column == value)
        if is_failing is not None:
            stmt = stmt.where(DieAnalysis.is_failing.is_(is_failing))
        stmt = (
            stmt.order_by(
                DieAnalysis.health_score.asc(),
                DieAnalysis.analyzed_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_die(self, die_result_id: str) -> DieAnalysis | None:
        return (
            await self.session.execute(
                select(DieAnalysis).where(DieAnalysis.die_result_id == die_result_id)
            )
        ).scalar_one_or_none()

    async def hotspots(
        self, *, limit: int, analysis_id: str | None = None
    ) -> list[DieHotspot]:
        stmt = select(DieHotspot)
        if analysis_id:
            stmt = stmt.where(DieHotspot.analysis_id == analysis_id)
        return list(
            (
                await self.session.execute(
                    stmt.order_by(
                        DieHotspot.density.desc(), DieHotspot.created_at.desc()
                    ).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def clusters(
        self, *, limit: int, analysis_id: str | None = None
    ) -> list[DieCluster]:
        stmt = select(DieCluster)
        if analysis_id:
            stmt = stmt.where(DieCluster.analysis_id == analysis_id)
        return list(
            (
                await self.session.execute(
                    stmt.order_by(
                        DieCluster.density.desc(), DieCluster.created_at.desc()
                    ).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def recommendations(self, analysis_id: str) -> list[EngineeringRecommendation]:
        return list(
            (
                await self.session.execute(
                    select(EngineeringRecommendation).where(
                        EngineeringRecommendation.analysis_id == analysis_id,
                        EngineeringRecommendation.source_module == "FA-FR-007",
                    )
                )
            )
            .scalars()
            .all()
        )

    async def history(self, limit: int) -> list[DieAuditLog]:
        return list(
            (
                await self.session.execute(
                    select(DieAuditLog)
                    .order_by(DieAuditLog.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_statistics(self) -> dict[str, Any]:
        audit = (
            await self.session.execute(
                select(DieAuditLog)
                .where(DieAuditLog.status == "completed")
                .order_by(DieAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if audit is None:
            return {
                "total_dies": 0,
                "failing_dies": 0,
                "isolated_failures": 0,
                "hotspot_count": 0,
                "cluster_count": 0,
                "mean_failure_density": 0.0,
                "mean_health_score": 0.0,
                "mean_confidence": 0.0,
            }
        statistic = (
            await self.session.execute(
                select(DieFailureStatistic).where(
                    DieFailureStatistic.analysis_id == audit.analysis_id,
                    DieFailureStatistic.scope_type == "analysis",
                )
            )
        ).scalar_one_or_none()
        return {
            "execution_id": audit.analysis_id,
            "total_dies": audit.die_count,
            "failing_dies": audit.failing_die_count,
            "isolated_failures": statistic.isolated_failures if statistic else 0,
            "hotspot_count": audit.hotspot_count,
            "cluster_count": audit.cluster_count,
            "mean_failure_density": statistic.mean_failure_density if statistic else 0.0,
            "mean_health_score": statistic.mean_health_score if statistic else 0.0,
            "mean_confidence": statistic.mean_confidence if statistic else 0.0,
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
            "statistics": (audit.details or {}).get("statistics", {}),
        }
