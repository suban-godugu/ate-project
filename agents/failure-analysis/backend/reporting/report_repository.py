"""Persistence for FA-FR-010 engineering reports."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import (
    ClassificationRun,
    CorrelationAuditLog,
    CorrelationAnalysisRun,
    DieAnalysis,
    DieAnalysisRun,
    DieAuditLog,
    EngineeringReportRun,
    FailurePatternCorrelation,
    FailureRateRun,
    FaultPrediction,
    PredictionAuditLog,
    RecurringAnalysisRun,
    RecurrenceAuditLog,
    RecurringFailure,
    RootCausePredictionRun,
    TestRecordRow,
    Upload,
    WaferAnalysis,
    WaferAnalysisRun,
    WaferAuditLog,
)


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_upload(self, upload_id: str) -> Upload | None:
        return await self._session.get(Upload, upload_id)

    async def load_test_records(self, upload_id: str) -> list[TestRecord]:
        stmt = select(TestRecordRow).where(TestRecordRow.upload_id == upload_id)
        result = await self._session.execute(stmt)
        records: list[TestRecord] = []
        for row in result.scalars().all():
            payload = dict(row.payload)
            payload.setdefault("lot_id", row.lot_id)
            payload.setdefault("wafer_id", row.wafer_id)
            payload.setdefault("die_id", row.die_id)
            records.append(TestRecord.from_dict(payload))
        return records

    async def load_module_outputs(self, upload_id: str) -> dict[str, Any]:
        """Load latest analysis run outputs from each enterprise module."""
        outputs: dict[str, Any] = {}

        failure_rate = await self._latest(FailureRateRun, upload_id)
        if failure_rate:
            outputs["failure_rates"] = failure_rate.report_json

        classification = await self._latest(ClassificationRun, upload_id)
        if classification:
            outputs["classification"] = classification.report_json

        recurring = await self._latest(RecurringAnalysisRun, upload_id)
        if recurring:
            outputs["recurring"] = recurring.report_json

        production_recurring = await self._latest_production_recurrence(upload_id)
        if production_recurring:
            outputs["recurring_production"] = production_recurring
            outputs.setdefault("recurring", production_recurring)

        correlation = await self._latest(CorrelationAnalysisRun, upload_id)
        if correlation:
            outputs["correlation"] = correlation.report_json
        production_correlation = await self._latest_production_correlation(upload_id)
        if production_correlation:
            outputs["correlation_production"] = production_correlation
            outputs["correlation"] = production_correlation

        die = await self._latest(DieAnalysisRun, upload_id)
        if die:
            outputs["die_analysis"] = die.report_json
        production_die = await self._latest_production_die_analysis(upload_id)
        if production_die:
            outputs["die_analysis_production"] = production_die
            outputs["die_analysis"] = production_die

        wafer = await self._latest(WaferAnalysisRun, upload_id)
        if wafer:
            outputs["wafer_analysis"] = wafer.report_json
        production_wafer = await self._latest_production_wafer_analysis(upload_id)
        if production_wafer:
            outputs["wafer_analysis_production"] = production_wafer
            outputs["wafer_analysis"] = production_wafer

        root_cause = await self._latest(RootCausePredictionRun, upload_id)
        if root_cause:
            outputs["root_cause"] = root_cause.report_json
        production_fault = await self._latest_production_fault_prediction(upload_id)
        if production_fault:
            outputs["root_cause_production"] = production_fault
            outputs["root_cause"] = production_fault

        return outputs

    async def _latest_production_recurrence(
        self, upload_id: str
    ) -> dict[str, Any] | None:
        audit = (
            await self._session.execute(
                select(RecurrenceAuditLog)
                .where(
                    RecurrenceAuditLog.upload_id == upload_id,
                    RecurrenceAuditLog.status == "completed",
                )
                .order_by(RecurrenceAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalars().first()
        if audit is None:
            return None
        rows = list(
            (
                await self._session.execute(
                    select(RecurringFailure)
                    .where(RecurringFailure.analysis_id == audit.analysis_id)
                    .order_by(RecurringFailure.confidence_score.desc())
                )
            )
            .scalars()
            .all()
        )
        recurring = [
            {
                "recurrence_id": row.recurrence_id,
                "signature_type": "pattern_fault",
                "entity_key": row.canonical_recurrence_key,
                "pattern_id": row.pattern_id,
                "fault_type": row.fault_type,
                "failure_count": row.recurrence_count,
                "recurrence_percentage": row.recurrence_percentage,
                "confidence": row.confidence_score,
                "severity": row.severity,
                "trend_status": row.trend_direction,
                "recommendation": row.engineering_recommendation,
            }
            for row in rows
        ]
        return {
            "requirement": "FA-FR-005",
            "analysis_id": audit.analysis_id,
            "upload_id": upload_id,
            "recurring_failure_list": recurring,
            "recurrence_events": recurring,
            "classification_summary": {
                "total_recurring_signatures": len(recurring),
                "alert_count": sum(
                    1 for row in rows if row.severity in {"critical", "high"}
                ),
            },
        }

    async def _latest_production_correlation(
        self, upload_id: str
    ) -> dict[str, Any] | None:
        audit = (
            await self._session.execute(
                select(CorrelationAuditLog)
                .where(
                    CorrelationAuditLog.upload_id == upload_id,
                    CorrelationAuditLog.status == "completed",
                )
                .order_by(CorrelationAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalars().first()
        if audit is None:
            return None
        rows = list(
            (
                await self._session.execute(
                    select(FailurePatternCorrelation)
                    .where(FailurePatternCorrelation.analysis_id == audit.analysis_id)
                    .order_by(FailurePatternCorrelation.confidence_score.desc())
                )
            ).scalars().all()
        )
        relationships = [
            {
                "correlation_id": row.correlation_id,
                "pattern_id": row.pattern_id,
                "fault_type": row.fault_type,
                "correlation_coefficient": row.correlation_coefficient,
                "correlation_strength": row.correlation_strength,
                "confidence": row.confidence_score,
                "severity": row.severity,
                "trend_status": row.trend_status,
                "hotspot_location": row.hotspot_location,
                "recommendation": row.engineering_recommendation,
            }
            for row in rows
        ]
        return {
            "requirement": "FA-FR-006",
            "analysis_id": audit.analysis_id,
            "upload_id": upload_id,
            "correlation_report": relationships,
            "top_failing_patterns": relationships[:20],
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
        }

    async def _latest_production_die_analysis(
        self, upload_id: str
    ) -> dict[str, Any] | None:
        audit = (
            await self._session.execute(
                select(DieAuditLog)
                .where(
                    DieAuditLog.upload_id == upload_id,
                    DieAuditLog.status == "completed",
                )
                .order_by(DieAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalars().first()
        if audit is None:
            return None
        rows = list(
            (
                await self._session.execute(
                    select(DieAnalysis)
                    .where(DieAnalysis.analysis_id == audit.analysis_id)
                    .order_by(DieAnalysis.health_score.asc())
                )
            )
            .scalars()
            .all()
        )
        die_profiles = [
            {
                "die_result_id": row.die_result_id,
                "lot_id": row.lot_id,
                "wafer_id": row.wafer_id,
                "die_id": row.die_id,
                "x": row.x,
                "y": row.y,
                "failure_count": row.failure_count,
                "failure_density": row.failure_density,
                "neighbor_failure_count": row.neighbor_failure_count,
                "is_isolated": row.is_isolated,
                "is_failing": row.is_failing,
                "health_score": row.health_score,
                "severity": row.severity,
                "confidence": row.confidence_score,
                "trend_status": row.trend_status,
                "hotspot_id": row.hotspot_id,
                "cluster_id": row.cluster_id,
                "recommendation": row.engineering_recommendation,
            }
            for row in rows
        ]
        total = int(audit.die_count or 0)
        failing = int(audit.failing_die_count or 0)
        return {
            "requirement": "FA-FR-007",
            "analysis_id": audit.analysis_id,
            "upload_id": upload_id,
            "total_dies": total,
            "failing_dies": failing,
            "overall_yield_pct": round((1.0 - failing / total) * 100.0, 2) if total else 0.0,
            "hotspot_count": audit.hotspot_count,
            "cluster_count": audit.cluster_count,
            "die_profiles": die_profiles,
            "dashboard_feed": die_profiles,
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
        }

    async def _latest_production_wafer_analysis(
        self, upload_id: str
    ) -> dict[str, Any] | None:
        audit = (
            await self._session.execute(
                select(WaferAuditLog)
                .where(
                    WaferAuditLog.upload_id == upload_id,
                    WaferAuditLog.status == "completed",
                )
                .order_by(WaferAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalars().first()
        if audit is None:
            return None
        rows = list(
            (
                await self._session.execute(
                    select(WaferAnalysis)
                    .where(WaferAnalysis.analysis_id == audit.analysis_id)
                    .order_by(WaferAnalysis.health_score.asc())
                )
            )
            .scalars()
            .all()
        )
        wafer_profiles = [
            {
                "wafer_result_id": row.wafer_result_id,
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
                "confidence": row.confidence_score,
                "trend_status": row.trend_status,
                "recommendation": row.engineering_recommendation,
            }
            for row in rows
        ]
        total = int(audit.wafer_count or 0)
        failing = int(audit.failing_wafer_count or 0)
        total_dies = sum(row.total_dies for row in rows)
        failing_dies = sum(row.failing_dies for row in rows)
        return {
            "requirement": "FA-FR-008",
            "analysis_id": audit.analysis_id,
            "upload_id": upload_id,
            "total_wafers": total,
            "failing_wafers": failing,
            "total_dies": total_dies,
            "failing_dies": failing_dies,
            "overall_yield_pct": round(
                (1.0 - failing_dies / total_dies) * 100.0, 2
            )
            if total_dies
            else 100.0,
            "outlier_wafer_count": (audit.details or {})
            .get("statistics", {})
            .get("outlier_wafer_count", 0),
            "hotspot_count": audit.hotspot_count,
            "wafer_statistics": wafer_profiles,
            "dashboard_feed": wafer_profiles,
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
        }

    async def _latest_production_fault_prediction(
        self, upload_id: str
    ) -> dict[str, Any] | None:
        audit = (
            await self._session.execute(
                select(PredictionAuditLog)
                .where(
                    PredictionAuditLog.upload_id == upload_id,
                    PredictionAuditLog.status == "completed",
                )
                .order_by(PredictionAuditLog.completed_at.desc())
                .limit(1)
            )
        ).scalars().first()
        if audit is None:
            return None
        rows = list(
            (
                await self._session.execute(
                    select(FaultPrediction)
                    .where(FaultPrediction.execution_id == audit.execution_id)
                    .order_by(FaultPrediction.confidence_score.desc())
                )
            )
            .scalars()
            .all()
        )
        predictions = [
            {
                "prediction_id": row.prediction_id,
                "pattern_id": row.pattern_id,
                "predicted_fault_type": row.predicted_fault_type,
                "predicted_root_cause": row.predicted_fault_type,
                "confidence_score": row.confidence_score,
                "prediction_probability": row.prediction_probability,
                "alternative_fault_types": row.alternative_fault_types,
                "supporting_evidence": row.supporting_evidence,
                "engineering_explanation": row.engineering_explanation,
                "investigation_steps": row.investigation_steps,
            }
            for row in rows
        ]
        confidences = [row.confidence_score for row in rows]
        return {
            "requirement": "FA-FR-009",
            "execution_id": audit.execution_id,
            "upload_id": upload_id,
            "phase": "fault_type_prediction",
            "phase_description": "Probable fault-type predictions (not definitive root causes)",
            "total_predictions": audit.prediction_count,
            "average_confidence": round(
                sum(confidences) / len(confidences), 4
            )
            if confidences
            else 0.0,
            "high_confidence_count": audit.high_confidence_count,
            "predictions": predictions,
            "ranked_hypothesis_queue": predictions[:20],
            "benchmark_metrics": audit.benchmark_metrics,
            "upstream_execution_ids": audit.upstream_execution_ids,
            "disclaimer": (
                "Predictions are probable fault types only, not definitive root causes."
            ),
        }

    async def _latest(self, model: type, upload_id: str) -> Any | None:
        stmt = (
            select(model)
            .where(model.upload_id == upload_id)
            .order_by(model.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def save_run(self, report: dict[str, Any]) -> EngineeringReportRun:
        summaries = report.get("summaries", {})
        exec_sum = summaries.get("executive_summary", report.get("executive_report", {}))
        run = EngineeringReportRun(
            id=report.get("report_id"),
            upload_id=report.get("upload_id"),
            status="completed",
            processing_ms=float(report.get("processing_ms", 0.0)),
            pdf_ms=float(report.get("pdf_ms", 0.0)),
            excel_ms=float(report.get("excel_ms", 0.0)),
            total_dies=int(exec_sum.get("total_dies_tested", 0)),
            failing_dies=int(exec_sum.get("total_failing_dies", 0)),
            overall_yield_pct=float(exec_sum.get("overall_yield_pct") or 0.0),
            pdf_path=report.get("export_paths", {}).get("pdf"),
            excel_path=report.get("export_paths", {}).get("excel"),
            json_path=report.get("export_paths", {}).get("json"),
            report_json=report,
            dashboard_json=report.get("dashboard_dataset", {}),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, report_id: str) -> EngineeringReportRun | None:
        return await self._session.get(EngineeringReportRun, report_id)

    async def list_runs(self, *, limit: int = 50) -> list[EngineeringReportRun]:
        stmt = (
            select(EngineeringReportRun)
            .order_by(EngineeringReportRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
