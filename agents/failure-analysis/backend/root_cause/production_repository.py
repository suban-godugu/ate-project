"""Versioned FA-FR-009 handoff, persistence, and query repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import (
    FaultPrediction,
    PredictionAuditLog,
    PredictionFeedback,
    PredictionHistory,
    PredictionModel,
    PredictionStatistic,
    RecurringFailure,
    WaferAnalysis,
    WaferAuditLog,
    WaferHotspot,
)
from backend.wafer_analysis.production_repository import ProductionWaferAnalysisRepository


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductionFaultPredictionRepository:
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
        wafer_analysis_id: str | None,
        historical_window: int,
        compatible_formula_prefix: str,
        require_same_tenant: bool,
        require_product_overlap: bool,
        require_test_stage_overlap: bool,
    ) -> dict[str, Any]:
        wafer_repo = ProductionWaferAnalysisRepository(self.session)
        source = await wafer_repo.load_analysis_source(
            dataset_id=dataset_id,
            upload_id=upload_id,
            detection_execution_id=detection_execution_id,
            computation_id=computation_id,
            recurrence_analysis_id=recurrence_analysis_id,
            correlation_analysis_id=correlation_analysis_id,
            die_analysis_id=die_analysis_id,
            historical_window=historical_window,
            compatible_formula_prefix=compatible_formula_prefix,
            require_same_tenant=require_same_tenant,
            require_product_overlap=require_product_overlap,
            require_test_stage_overlap=require_test_stage_overlap,
        )
        die_audit = source["die_audit"]
        upstream = dict(die_audit.upstream_execution_ids or {})
        expected_detection = upstream.get("detection_execution_id")
        expected_computation = upstream.get("computation_id")
        expected_recurrence = upstream.get("recurrence_analysis_id")
        expected_correlation = upstream.get("correlation_analysis_id")
        expected_die = die_audit.analysis_id

        audit_stmt = select(WaferAuditLog).where(WaferAuditLog.status == "completed")
        if dataset_id:
            audit_stmt = audit_stmt.where(WaferAuditLog.dataset_id == dataset_id)
        else:
            audit_stmt = audit_stmt.where(WaferAuditLog.upload_id == upload_id)
        if wafer_analysis_id:
            audit_stmt = audit_stmt.where(WaferAuditLog.analysis_id == wafer_analysis_id)
        candidates = list(
            (
                await self.session.execute(
                    audit_stmt.order_by(WaferAuditLog.completed_at.desc())
                )
            )
            .scalars()
            .all()
        )
        wafer_audit = None
        for candidate in candidates:
            candidate_upstream = dict(candidate.upstream_execution_ids or {})
            if (
                candidate_upstream.get("detection_execution_id") == expected_detection
                and candidate_upstream.get("computation_id") == expected_computation
                and candidate_upstream.get("recurrence_analysis_id") == expected_recurrence
                and candidate_upstream.get("correlation_analysis_id")
                == expected_correlation
                and candidate_upstream.get("die_analysis_id") == expected_die
            ):
                wafer_audit = candidate
                break
        if wafer_audit is None:
            raise ValueError(
                "A completed FA-FR-008 wafer analysis for this exact upstream lineage is required"
            )

        wafer_rows = list(
            (
                await self.session.execute(
                    select(WaferAnalysis).where(
                        WaferAnalysis.analysis_id == wafer_audit.analysis_id
                    )
                )
            )
            .scalars()
            .all()
        )
        if not wafer_rows:
            raise ValueError("FA-FR-008 completed without traceable wafer results")

        wafer_hotspots = list(
            (
                await self.session.execute(
                    select(WaferHotspot).where(
                        WaferHotspot.analysis_id == wafer_audit.analysis_id
                    )
                )
            )
            .scalars()
            .all()
        )

        recurrence_audit = source.get("recurrence_audit")
        recurrences: list[dict[str, Any]] = []
        if recurrence_audit is not None:
            recurrence_rows = list(
                (
                    await self.session.execute(
                        select(RecurringFailure).where(
                            RecurringFailure.analysis_id == recurrence_audit.analysis_id
                        )
                    )
                )
                .scalars()
                .all()
            )
            recurrences = [
                {
                    "recurrence_id": row.recurrence_id,
                    "pattern_id": row.pattern_id,
                    "fault_type": row.fault_type,
                    "recurrence_count": row.recurrence_count,
                    "recurrence_percentage": row.recurrence_percentage,
                    "confidence_score": row.confidence_score,
                    "severity": row.severity,
                }
                for row in recurrence_rows
            ]

        patterns = _unique_patterns(
            source.get("correlations", []),
            recurrences,
            source.get("classifications", []),
        )
        classifications = list(source.get("classifications", []))
        if not classifications:
            classifications = _classifications_from_observations(
                source.get("observations", [])
            )

        feedback_rows = list(
            (
                await self.session.execute(
                    select(PredictionFeedback).order_by(
                        PredictionFeedback.created_at.desc()
                    )
                )
            )
            .scalars()
            .all()
        )
        feedback_signals = [
            {
                "pattern_id": row.pattern_id,
                "validated_fault_type": row.validated_fault_type,
                "learning_weight": row.learning_weight,
            }
            for row in feedback_rows
            if not pattern_ids or row.pattern_id in pattern_ids
        ] if (pattern_ids := {item["pattern_id"] for item in patterns}) else []

        return {
            **source,
            "wafer_audit": wafer_audit,
            "wafers": [_serialize_wafer(row) for row in wafer_rows],
            "wafer_hotspots": [
                {
                    "hotspot_id": row.hotspot_id,
                    "lot_id": row.lot_id,
                    "wafer_id": row.wafer_id,
                    "density": row.density,
                    "severity": row.severity,
                }
                for row in wafer_hotspots
            ],
            "recurrences": recurrences,
            "patterns": patterns,
            "classifications": classifications,
            "feedback_signals": feedback_signals,
            "compatible_formula_prefix": compatible_formula_prefix,
            "cohort_flags": {
                "require_same_tenant": require_same_tenant,
                "require_product_overlap": require_product_overlap,
                "require_test_stage_overlap": require_test_stage_overlap,
            },
        }

    async def ensure_model(self, *, model_version: str, config_version: str) -> PredictionModel:
        existing = (
            await self.session.execute(
                select(PredictionModel).where(
                    PredictionModel.model_version == model_version
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        row = PredictionModel(
            model_id=str(uuid.uuid4()),
            model_version=model_version,
            model_type="rule_based",
            status="active",
            config_version=config_version,
            parameters={"algorithm": "rule_based_explainable_scoring"},
            metrics={},
            activated_at=_now(),
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_audit(self, execution_id: str) -> PredictionAuditLog | None:
        return (
            await self.session.execute(
                select(PredictionAuditLog)
                .where(PredictionAuditLog.execution_id == execution_id)
                .order_by(PredictionAuditLog.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    async def create_audit(
        self,
        *,
        execution_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        config_version: str,
        model_version: str,
        status: str,
        actor: str | None,
        details: dict[str, Any],
    ) -> PredictionAuditLog:
        row = PredictionAuditLog(
            execution_id=execution_id,
            dataset_id=dataset_id,
            upload_id=upload_id,
            status=status,
            config_version=config_version,
            model_version=model_version,
            actor=actor,
            details=details,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def persist(
        self,
        *,
        execution_id: str,
        dataset_id: str | None,
        upload_id: str | None,
        source: dict[str, Any],
        result: dict[str, Any],
        audit: PredictionAuditLog,
        processing_ms: float,
        benchmarks: dict[str, Any],
        warnings: list[str],
        config_version: str,
        model_version: str,
    ) -> list[FaultPrediction]:
        wafer_audit = source["wafer_audit"]
        die_audit = source["die_audit"]
        upstream = dict(wafer_audit.upstream_execution_ids or {})
        classification_ids = upstream.get("classification_execution_ids", [])
        classification_id = classification_ids[0] if classification_ids else ""
        persisted: list[FaultPrediction] = []
        dependents: list[Any] = []

        for item in result["predictions"]:
            row = FaultPrediction(
                prediction_id=item["prediction_id"],
                execution_id=execution_id,
                dataset_id=dataset_id,
                upload_id=upload_id,
                detection_execution_id=upstream.get("detection_execution_id", ""),
                computation_id=upstream.get("computation_id", ""),
                classification_execution_id=classification_id,
                recurrence_analysis_id=upstream.get("recurrence_analysis_id", ""),
                correlation_analysis_id=upstream.get("correlation_analysis_id", ""),
                die_analysis_id=die_audit.analysis_id,
                wafer_analysis_id=wafer_audit.analysis_id,
                pattern_id=item["pattern_id"],
                canonical_prediction_key=item["canonical_prediction_key"],
                predicted_fault_type=item["predicted_fault_type"],
                alternative_fault_types=item["alternative_fault_types"],
                confidence_score=item["confidence_score"],
                prediction_probability=item["prediction_probability"],
                supporting_evidence=item["supporting_evidence"],
                engineering_explanation=item["engineering_explanation"],
                investigation_steps=item["investigation_steps"],
                model_version=model_version,
                config_version=config_version,
                metadata_json=item.get("metadata_json", {}),
            )
            self.session.add(row)
            persisted.append(row)
            dependents.append(
                PredictionHistory(
                    prediction_id=item["prediction_id"],
                    execution_id=execution_id,
                    pattern_id=item["pattern_id"],
                    predicted_fault_type=item["predicted_fault_type"],
                    confidence_score=item["confidence_score"],
                    prediction_probability=item["prediction_probability"],
                    source_execution_ids=[
                        upstream.get("detection_execution_id", ""),
                        upstream.get("computation_id", ""),
                        classification_id,
                        upstream.get("recurrence_analysis_id", ""),
                        upstream.get("correlation_analysis_id", ""),
                        die_audit.analysis_id,
                        wafer_audit.analysis_id,
                    ],
                    details={
                        "alternative_fault_types": item["alternative_fault_types"],
                        "investigation_steps": item["investigation_steps"],
                    },
                )
            )

        for scoped in result["scoped_statistics"]:
            dependents.append(
                PredictionStatistic(
                    execution_id=execution_id,
                    scope_type=scoped["scope_type"],
                    scope_key=scoped["scope_key"],
                    total_predictions=scoped.get("total_predictions", 0),
                    high_confidence_count=scoped.get("high_confidence_count", 0),
                    mean_confidence=scoped.get("mean_confidence", 0.0),
                    mean_probability=scoped.get("mean_probability", 0.0),
                    top_fault_type=scoped.get("top_fault_type", ""),
                    top1_accuracy=benchmarks.get("top1_accuracy"),
                    top3_accuracy=benchmarks.get("top3_accuracy"),
                    details=scoped.get("details", scoped),
                )
            )

        self.session.add_all(dependents)
        statistics = result["statistics"]
        audit.status = "completed"
        audit.source_pattern_count = len(source["patterns"])
        audit.prediction_count = statistics["total_predictions"]
        audit.high_confidence_count = statistics["high_confidence_count"]
        audit.processing_ms = processing_ms
        audit.benchmark_metrics = benchmarks
        audit.upstream_execution_ids = {
            "detection_execution_id": upstream.get("detection_execution_id"),
            "computation_id": upstream.get("computation_id"),
            "classification_execution_ids": classification_ids,
            "recurrence_analysis_id": upstream.get("recurrence_analysis_id"),
            "correlation_analysis_id": upstream.get("correlation_analysis_id"),
            "die_analysis_id": die_audit.analysis_id,
            "wafer_analysis_id": wafer_audit.analysis_id,
        }
        audit.warnings = warnings
        audit.details = {
            **dict(audit.details or {}),
            "statistics": statistics,
            "requirement": "FA-FR-009",
            "model": result.get("model", {}),
        }
        audit.completed_at = _now()
        await self.session.flush()
        return persisted

    async def mark_failed(self, audit: PredictionAuditLog, message: str) -> None:
        audit.status = "failed"
        audit.errors = [message[:2000]]
        audit.completed_at = _now()
        await self.session.flush()

    async def list_predictions(
        self,
        *,
        limit: int,
        offset: int,
        pattern_id: str | None = None,
        execution_id: str | None = None,
        predicted_fault_type: str | None = None,
    ) -> list[FaultPrediction]:
        stmt = select(FaultPrediction)
        for column, value in (
            (FaultPrediction.pattern_id, pattern_id),
            (FaultPrediction.execution_id, execution_id),
            (FaultPrediction.predicted_fault_type, predicted_fault_type),
        ):
            if value:
                stmt = stmt.where(column == value)
        stmt = (
            stmt.order_by(
                FaultPrediction.confidence_score.desc(),
                FaultPrediction.predicted_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_prediction(self, prediction_id: str) -> FaultPrediction | None:
        return (
            await self.session.execute(
                select(FaultPrediction).where(
                    FaultPrediction.prediction_id == prediction_id
                )
            )
        ).scalar_one_or_none()

    async def history(
        self, *, limit: int, execution_id: str | None = None
    ) -> list[PredictionHistory]:
        stmt = select(PredictionHistory)
        if execution_id:
            stmt = stmt.where(PredictionHistory.execution_id == execution_id)
        return list(
            (
                await self.session.execute(
                    stmt.order_by(PredictionHistory.recorded_at.desc()).limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def latest_statistics(self) -> dict[str, Any]:
        audit = (
            await self.session.execute(
                select(PredictionAuditLog)
                .where(PredictionAuditLog.status == "completed")
                .order_by(PredictionAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if audit is None:
            return {
                "total_predictions": 0,
                "high_confidence_count": 0,
                "mean_confidence": 0.0,
                "mean_probability": 0.0,
                "top_fault_type": "",
            }
        statistic = (
            await self.session.execute(
                select(PredictionStatistic).where(
                    PredictionStatistic.execution_id == audit.execution_id,
                    PredictionStatistic.scope_type == "execution",
                )
            )
        ).scalar_one_or_none()
        return {
            "execution_id": audit.execution_id,
            "total_predictions": audit.prediction_count,
            "high_confidence_count": audit.high_confidence_count,
            "mean_confidence": statistic.mean_confidence if statistic else 0.0,
            "mean_probability": statistic.mean_probability if statistic else 0.0,
            "top_fault_type": statistic.top_fault_type if statistic else "",
            "model_version": audit.model_version,
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
            "statistics": (audit.details or {}).get("statistics", {}),
        }

    async def save_feedback(
        self,
        *,
        feedback_id: str,
        prediction_id: str,
        execution_id: str,
        pattern_id: str,
        validated_fault_type: str,
        feedback_status: str,
        engineer_notes: str,
        learning_weight: float,
        actor: str | None,
        details: dict[str, Any],
    ) -> PredictionFeedback:
        row = PredictionFeedback(
            feedback_id=feedback_id,
            prediction_id=prediction_id,
            execution_id=execution_id,
            pattern_id=pattern_id,
            validated_fault_type=validated_fault_type,
            feedback_status=feedback_status,
            engineer_notes=engineer_notes,
            learning_weight=learning_weight,
            actor=actor,
            details=details,
        )
        self.session.add(row)
        await self.session.flush()
        return row


def _unique_patterns(
    correlations: list[dict[str, Any]],
    recurrences: list[dict[str, Any]],
    classifications: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    patterns: dict[str, dict[str, Any]] = {}
    for rows in (correlations, recurrences, classifications):
        for row in rows:
            pattern_id = str(row.get("pattern_id", "")).strip()
            if not pattern_id:
                continue
            bucket = patterns.setdefault(pattern_id, {"pattern_id": pattern_id})
            if row.get("fault_type"):
                bucket["fault_type"] = row["fault_type"]
    return sorted(patterns.values(), key=lambda item: item["pattern_id"])


def _classifications_from_observations(
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for obs in observations:
        pattern_id = str(obs.get("pattern_id", "")).strip()
        if not pattern_id:
            continue
        rows.append(
            {
                "pattern_id": pattern_id,
                "fault_type": obs.get("fault_type", obs.get("predicted_fault_type", "UNKNOWN")),
                "confidence": obs.get("confidence", obs.get("confidence_score", 0.5)),
            }
        )
    return rows


def _serialize_wafer(row: WaferAnalysis) -> dict[str, Any]:
    return {
        "wafer_result_id": row.wafer_result_id,
        "lot_id": row.lot_id,
        "wafer_id": row.wafer_id,
        "total_dies": row.total_dies,
        "failing_dies": row.failing_dies,
        "yield_pct": row.yield_pct,
        "failure_density": row.failure_density,
        "health_score": row.health_score,
        "severity": row.severity,
        "confidence_score": row.confidence_score,
        "trend_status": row.trend_status,
        "edge_failure_rate": row.edge_failure_rate,
        "center_failure_rate": row.center_failure_rate,
    }
