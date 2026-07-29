"""Versioned FA-FR-008 handoff, persistence, and query repository."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.die_analysis.production_repository import ProductionDieAnalysisRepository
from backend.models import (
    DieAnalysis,
    DieAuditLog,
    DieHotspot,
    EngineeringRecommendation,
    WaferAnalysis,
    WaferAnalysisHistory,
    WaferAuditLog,
    WaferHealthScore,
    WaferHotspot,
    WaferStatistic,
    WaferYieldMetric,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductionWaferAnalysisRepository:
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
        die_analysis_id: str | None,
        historical_window: int,
        compatible_formula_prefix: str,
        require_same_tenant: bool,
        require_product_overlap: bool,
        require_test_stage_overlap: bool,
    ) -> dict[str, Any]:
        die_repo = ProductionDieAnalysisRepository(self.session)
        source = await die_repo.load_analysis_source(
            dataset_id=dataset_id,
            upload_id=upload_id,
            detection_execution_id=detection_execution_id,
            computation_id=computation_id,
            recurrence_analysis_id=recurrence_analysis_id,
            correlation_analysis_id=correlation_analysis_id,
            historical_window=historical_window,
            compatible_formula_prefix=compatible_formula_prefix,
            require_same_tenant=require_same_tenant,
            require_product_overlap=require_product_overlap,
            require_test_stage_overlap=require_test_stage_overlap,
        )
        expected_detection = source["detection"].analysis_id
        expected_computation = source["current"].computation_id
        expected_recurrence = source["recurrence_audit"].analysis_id
        expected_correlation = source["correlation_audit"].analysis_id

        audit_stmt = select(DieAuditLog).where(DieAuditLog.status == "completed")
        if dataset_id:
            audit_stmt = audit_stmt.where(DieAuditLog.dataset_id == dataset_id)
        else:
            audit_stmt = audit_stmt.where(DieAuditLog.upload_id == upload_id)
        if die_analysis_id:
            audit_stmt = audit_stmt.where(DieAuditLog.analysis_id == die_analysis_id)
        candidates = list(
            (
                await self.session.execute(
                    audit_stmt.order_by(DieAuditLog.completed_at.desc())
                )
            )
            .scalars()
            .all()
        )
        die_audit = None
        for candidate in candidates:
            upstream = dict(candidate.upstream_execution_ids or {})
            if (
                upstream.get("detection_execution_id") == expected_detection
                and upstream.get("computation_id") == expected_computation
                and upstream.get("recurrence_analysis_id") == expected_recurrence
                and upstream.get("correlation_analysis_id") == expected_correlation
            ):
                die_audit = candidate
                break
        if die_audit is None:
            raise ValueError(
                "A completed FA-FR-007 die analysis for this exact upstream lineage is required"
            )

        die_rows = list(
            (
                await self.session.execute(
                    select(DieAnalysis).where(
                        DieAnalysis.analysis_id == die_audit.analysis_id
                    )
                )
            )
            .scalars()
            .all()
        )
        if not die_rows:
            raise ValueError("FA-FR-007 completed without traceable die results")

        die_hotspots = list(
            (
                await self.session.execute(
                    select(DieHotspot).where(
                        DieHotspot.analysis_id == die_audit.analysis_id
                    )
                )
            )
            .scalars()
            .all()
        )

        historical_yields = await self._historical_wafer_yields(
            dataset_id=dataset_id,
            upload_id=upload_id,
            exclude_analysis_id=die_audit.analysis_id,
            historical_window=historical_window,
        )

        return {
            **source,
            "die_audit": die_audit,
            "dies": [_serialize_die(row) for row in die_rows],
            "die_hotspots": [
                {
                    "hotspot_id": row.hotspot_id,
                    "lot_id": row.lot_id,
                    "wafer_id": row.wafer_id,
                    "center_x": row.center_x,
                    "center_y": row.center_y,
                    "radius": row.radius,
                    "die_count": row.die_count,
                    "failure_count": row.failure_count,
                    "density": row.density,
                    "severity": row.severity,
                    "confidence_score": row.confidence_score,
                    "member_die_ids": row.member_die_ids,
                }
                for row in die_hotspots
            ],
            "historical_wafer_yields": historical_yields,
            "compatible_formula_prefix": compatible_formula_prefix,
            "cohort_flags": {
                "require_same_tenant": require_same_tenant,
                "require_product_overlap": require_product_overlap,
                "require_test_stage_overlap": require_test_stage_overlap,
            },
        }

    async def _historical_wafer_yields(
        self,
        *,
        dataset_id: str | None,
        upload_id: str | None,
        exclude_analysis_id: str,
        historical_window: int,
    ) -> dict[str, float]:
        stmt = select(DieAuditLog).where(
            DieAuditLog.status == "completed",
            DieAuditLog.analysis_id != exclude_analysis_id,
        )
        if dataset_id:
            stmt = stmt.where(DieAuditLog.dataset_id == dataset_id)
        else:
            stmt = stmt.where(DieAuditLog.upload_id == upload_id)
        audits = list(
            (
                await self.session.execute(
                    stmt.order_by(DieAuditLog.completed_at.desc()).limit(historical_window)
                )
            )
            .scalars()
            .all()
        )
        yields: dict[str, list[float]] = {}
        for audit in audits:
            rows = list(
                (
                    await self.session.execute(
                        select(DieAnalysis).where(
                            DieAnalysis.analysis_id == audit.analysis_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            buckets: dict[str, dict[str, int]] = {}
            for row in rows:
                key = hashlib.sha256(
                    f"{row.lot_id.lower()}|{row.wafer_id.lower()}".encode()
                ).hexdigest()
                bucket = buckets.setdefault(key, {"total": 0, "failing": 0})
                bucket["total"] += 1
                if row.is_failing:
                    bucket["failing"] += 1
            for key, bucket in buckets.items():
                yield_pct = (1.0 - bucket["failing"] / max(1, bucket["total"])) * 100.0
                yields.setdefault(key, []).append(yield_pct)
        return {
            key: round(sum(values) / len(values), 4)
            for key, values in yields.items()
            if values
        }

    async def get_audit(self, analysis_id: str) -> WaferAuditLog | None:
        return (
            await self.session.execute(
                select(WaferAuditLog)
                .where(WaferAuditLog.analysis_id == analysis_id)
                .order_by(WaferAuditLog.created_at.desc())
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
    ) -> WaferAuditLog:
        row = WaferAuditLog(
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
        audit: WaferAuditLog,
        processing_ms: float,
        benchmarks: dict[str, Any],
        warnings: list[str],
        config_version: str,
    ) -> list[WaferAnalysis]:
        persisted: list[WaferAnalysis] = []
        die_audit = source["die_audit"]
        upstream = dict(die_audit.upstream_execution_ids or {})
        classification_ids = upstream.get("classification_execution_ids", [])
        classification_id = classification_ids[0] if classification_ids else ""
        dependents: list[Any] = []

        for item in result["wafers"]:
            row = WaferAnalysis(
                wafer_result_id=item["wafer_result_id"],
                analysis_id=analysis_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                detection_execution_id=upstream.get("detection_execution_id", ""),
                computation_id=upstream.get("computation_id", ""),
                classification_execution_id=classification_id,
                recurrence_analysis_id=upstream.get("recurrence_analysis_id", ""),
                correlation_analysis_id=upstream.get("correlation_analysis_id", ""),
                die_analysis_id=die_audit.analysis_id,
                lot_id=item["lot_id"],
                wafer_id=item["wafer_id"],
                canonical_wafer_key=item["canonical_wafer_key"],
                total_dies=item["total_dies"],
                failing_dies=item["failing_dies"],
                yield_pct=item["yield_pct"],
                failure_density=item["failure_density"],
                edge_failure_rate=item["edge_failure_rate"],
                center_failure_rate=item["center_failure_rate"],
                health_score=item["health_score"],
                severity=item["severity"],
                confidence_score=item["confidence_score"],
                trend_status=item["trend_status"],
                radial_distribution=item["radial_distribution"],
                lot_comparison=item["lot_comparison"],
                engineering_recommendation=item["engineering_recommendation"],
                config_version=config_version,
                metadata_json={
                    "spatial": item.get("spatial", {}),
                    "historical_yield_pct": item.get("historical_yield_pct"),
                    "yield_delta": item.get("yield_delta"),
                    "die_count": len(item.get("dies", [])),
                },
            )
            self.session.add(row)
            persisted.append(row)
            dependents.append(
                WaferHealthScore(
                    wafer_result_id=row.wafer_result_id,
                    analysis_id=analysis_id,
                    lot_id=row.lot_id,
                    wafer_id=row.wafer_id,
                    health_score=row.health_score,
                    severity=row.severity,
                    confidence_score=row.confidence_score,
                    contributing_factors={
                        "failure_density": row.failure_density,
                        "edge_failure_rate": row.edge_failure_rate,
                        "center_failure_rate": row.center_failure_rate,
                        "trend_status": row.trend_status,
                    },
                )
            )
            dependents.append(
                WaferAnalysisHistory(
                    wafer_result_id=row.wafer_result_id,
                    analysis_id=analysis_id,
                    lot_id=row.lot_id,
                    wafer_id=row.wafer_id,
                    yield_pct=row.yield_pct,
                    failure_density=row.failure_density,
                    health_score=row.health_score,
                    confidence_score=row.confidence_score,
                    source_execution_ids=[
                        upstream.get("detection_execution_id", ""),
                        upstream.get("computation_id", ""),
                        classification_id,
                        upstream.get("recurrence_analysis_id", ""),
                        upstream.get("correlation_analysis_id", ""),
                        die_audit.analysis_id,
                    ],
                    details={
                        "severity": row.severity,
                        "trend_status": row.trend_status,
                        "canonical_wafer_key": row.canonical_wafer_key,
                    },
                )
            )
            for recommendation in item["recommendations"]:
                dependents.append(
                    EngineeringRecommendation(
                        recommendation_id=recommendation["recommendation_id"],
                        recurrence_id=None,
                        correlation_id=None,
                        source_module="FA-FR-008",
                        analysis_id=analysis_id,
                        pattern_id=row.wafer_id,
                        fault_type="wafer_yield",
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
                WaferHotspot(
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
                    density_grid=hotspot["density_grid"],
                    details=hotspot["details"],
                )
            )
        for metric in result["yield_metrics"]:
            dependents.append(
                WaferYieldMetric(
                    analysis_id=analysis_id,
                    wafer_result_id=metric["wafer_result_id"],
                    lot_id=metric["lot_id"],
                    wafer_id=metric["wafer_id"],
                    yield_pct=metric["yield_pct"],
                    historical_yield_pct=metric.get("historical_yield_pct"),
                    yield_delta=metric.get("yield_delta"),
                    trend_status=metric["trend_status"],
                    lot_yield_pct=metric.get("lot_yield_pct"),
                    details=metric.get("details", {}),
                )
            )
        for item in result["scoped_statistics"]:
            dependents.append(
                WaferStatistic(
                    analysis_id=analysis_id,
                    scope_type=item["scope_type"],
                    scope_key=item["scope_key"],
                    total_wafers=item.get("total_wafers", 0),
                    failing_wafers=item.get("failing_wafers", 0),
                    total_dies=item.get("total_dies", 0),
                    failing_dies=item.get("failing_dies", 0),
                    mean_yield_pct=item.get("mean_yield_pct", item.get("overall_yield_pct", 100.0)),
                    mean_failure_density=item.get("mean_failure_density", 0.0),
                    mean_health_score=item.get("mean_health_score", 1.0),
                    mean_confidence=item.get("mean_confidence", 0.0),
                    hotspot_count=item.get("hotspot_count", 0),
                    details=item.get("details", item),
                )
            )
        self.session.add_all(dependents)
        statistics = result["statistics"]
        audit.status = "completed"
        audit.source_die_count = len(source["dies"])
        audit.wafer_count = statistics["total_wafers"]
        audit.failing_wafer_count = statistics["failing_wafers"]
        audit.hotspot_count = statistics["hotspot_count"]
        audit.processing_ms = processing_ms
        audit.benchmark_metrics = benchmarks
        audit.upstream_execution_ids = {
            "detection_execution_id": upstream.get("detection_execution_id"),
            "computation_id": upstream.get("computation_id"),
            "classification_execution_ids": classification_ids,
            "recurrence_analysis_id": upstream.get("recurrence_analysis_id"),
            "correlation_analysis_id": upstream.get("correlation_analysis_id"),
            "die_analysis_id": die_audit.analysis_id,
        }
        audit.warnings = warnings
        audit.details = {
            **dict(audit.details or {}),
            "statistics": statistics,
            "requirement": "FA-FR-008",
        }
        audit.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, audit: WaferAuditLog, message: str) -> None:
        audit.status = "failed"
        audit.errors = [message[:2000]]
        audit.completed_at = _now()
        await self.session.flush()

    async def list_wafers(
        self,
        *,
        limit: int,
        offset: int,
        lot_id: str | None = None,
        wafer_id: str | None = None,
        severity: str | None = None,
        analysis_id: str | None = None,
    ) -> list[WaferAnalysis]:
        stmt = select(WaferAnalysis)
        for column, value in (
            (WaferAnalysis.lot_id, lot_id),
            (WaferAnalysis.wafer_id, wafer_id),
            (WaferAnalysis.severity, severity),
            (WaferAnalysis.analysis_id, analysis_id),
        ):
            if value:
                stmt = stmt.where(column == value)
        stmt = (
            stmt.order_by(
                WaferAnalysis.health_score.asc(),
                WaferAnalysis.analyzed_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_wafer(self, wafer_result_id: str) -> WaferAnalysis | None:
        return (
            await self.session.execute(
                select(WaferAnalysis).where(
                    WaferAnalysis.wafer_result_id == wafer_result_id
                )
            )
        ).scalar_one_or_none()

    async def hotspots(
        self, *, limit: int, analysis_id: str | None = None
    ) -> list[WaferHotspot]:
        stmt = select(WaferHotspot)
        if analysis_id:
            stmt = stmt.where(WaferHotspot.analysis_id == analysis_id)
        return list(
            (
                await self.session.execute(
                    stmt.order_by(
                        WaferHotspot.density.desc(), WaferHotspot.created_at.desc()
                    ).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def yield_metrics(
        self, *, limit: int, analysis_id: str | None = None
    ) -> list[WaferYieldMetric]:
        stmt = select(WaferYieldMetric)
        if analysis_id:
            stmt = stmt.where(WaferYieldMetric.analysis_id == analysis_id)
        return list(
            (
                await self.session.execute(
                    stmt.order_by(
                        WaferYieldMetric.yield_pct.asc(),
                        WaferYieldMetric.created_at.desc(),
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
                        EngineeringRecommendation.source_module == "FA-FR-008",
                    )
                )
            )
            .scalars()
            .all()
        )

    async def latest_statistics(self) -> dict[str, Any]:
        audit = (
            await self.session.execute(
                select(WaferAuditLog)
                .where(WaferAuditLog.status == "completed")
                .order_by(WaferAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if audit is None:
            return {
                "total_wafers": 0,
                "failing_wafers": 0,
                "total_dies": 0,
                "failing_dies": 0,
                "overall_yield_pct": 100.0,
                "hotspot_count": 0,
                "mean_failure_density": 0.0,
                "mean_health_score": 1.0,
                "mean_confidence": 0.0,
            }
        statistic = (
            await self.session.execute(
                select(WaferStatistic).where(
                    WaferStatistic.analysis_id == audit.analysis_id,
                    WaferStatistic.scope_type == "analysis",
                )
            )
        ).scalar_one_or_none()
        return {
            "execution_id": audit.analysis_id,
            "total_wafers": audit.wafer_count,
            "failing_wafers": audit.failing_wafer_count,
            "total_dies": statistic.total_dies if statistic else 0,
            "failing_dies": statistic.failing_dies if statistic else 0,
            "overall_yield_pct": statistic.mean_yield_pct if statistic else 100.0,
            "hotspot_count": audit.hotspot_count,
            "mean_failure_density": statistic.mean_failure_density if statistic else 0.0,
            "mean_health_score": statistic.mean_health_score if statistic else 1.0,
            "mean_confidence": statistic.mean_confidence if statistic else 0.0,
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
            "statistics": (audit.details or {}).get("statistics", {}),
        }


def _serialize_die(row: DieAnalysis) -> dict[str, Any]:
    return {
        "die_result_id": row.die_result_id,
        "lot_id": row.lot_id,
        "wafer_id": row.wafer_id,
        "die_id": row.die_id,
        "canonical_die_key": row.canonical_die_key,
        "x": row.x,
        "y": row.y,
        "failure_count": row.failure_count,
        "failure_density": row.failure_density,
        "is_failing": row.is_failing,
        "health_score": row.health_score,
        "severity": row.severity,
        "confidence_score": row.confidence_score,
        "hotspot_id": row.hotspot_id,
        "cluster_id": row.cluster_id,
    }
