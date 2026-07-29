"""PostgreSQL persistence and upstream handoff loading for FA-FR-010."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.ingestion.models_ingestion import IngestionDataset, NormalizedRecord
from backend.models import (
    BenchmarkResult,
    ClassificationRun,
    ComputationHistory,
    CorrelationAuditLog,
    DetectionHistory,
    DieAuditLog,
    EngineeringRecommendation,
    EngineeringReportRun,
    FailureRateRun,
    PatternAnalysisRun,
    PredictionAuditLog,
    RecurrenceAuditLog,
    Report,
    ReportAuditLog,
    ReportExport,
    ReportHistory,
    ReportTemplate,
    TestRecordRow,
    Upload,
    WaferAuditLog,
)
from backend.reporting.report_repository import ReportRepository
from backend.reporting.templates import BUILTIN_TEMPLATES


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProductionReportingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.legacy = ReportRepository(session)

    async def ensure_default_templates(self) -> list[ReportTemplate]:
        existing = list(
            (await self.session.execute(select(ReportTemplate))).scalars().all()
        )
        if existing:
            return existing
        created: list[ReportTemplate] = []
        now = _now()
        for spec in BUILTIN_TEMPLATES:
            template = ReportTemplate(
                id=str(uuid.uuid4()),
                template_key=spec["template_key"],
                name=spec["name"],
                version=spec["version"],
                description=spec.get("description", ""),
                sections_json=spec.get("sections_json", {}),
                is_default=bool(spec.get("is_default", False)),
                created_at=now,
                updated_at=now,
            )
            self.session.add(template)
            created.append(template)
        await self.session.flush()
        return created

    async def get_template(self, template_key: str | None) -> ReportTemplate:
        await self.ensure_default_templates()
        if template_key:
            stmt = select(ReportTemplate).where(ReportTemplate.template_key == template_key)
            template = (await self.session.execute(stmt)).scalars().first()
            if template is None:
                raise ValueError(f"Report template not found: {template_key}")
            return template
        stmt = (
            select(ReportTemplate)
            .where(ReportTemplate.is_default.is_(True))
            .order_by(ReportTemplate.created_at.asc())
        )
        template = (await self.session.execute(stmt)).scalars().first()
        if template is None:
            raise ValueError("No default report template configured")
        return template

    async def list_templates(self) -> list[ReportTemplate]:
        await self.ensure_default_templates()
        stmt = select(ReportTemplate).order_by(ReportTemplate.template_key.asc())
        return list((await self.session.execute(stmt)).scalars().all())

    async def load_upstream_handoff(
        self,
        *,
        dataset_id: str | None,
        upload_id: str | None,
    ) -> dict[str, Any]:
        ingestion: dict[str, Any] = {}
        if dataset_id:
            dataset = await self.session.get(IngestionDataset, dataset_id)
            if dataset is None:
                raise LookupError("Dataset not found")
            ingestion = {
                "source_id": dataset_id,
                "status": dataset.status,
                "records_accepted": dataset.records_accepted,
                "integrity_pct": dataset.integrity_pct,
            }
            upload_id = upload_id or dataset.upload_id
        elif upload_id:
            upload = await self.session.get(Upload, upload_id)
            if upload is None:
                raise LookupError("Upload not found")
            ingestion = {
                "source_id": upload_id,
                "status": upload.status,
                "records_accepted": upload.records_accepted,
                "integrity_pct": upload.integrity_pct,
                "original_filename": upload.original_filename,
            }
        else:
            raise ValueError("dataset_id or upload_id required")

        detection = await self._latest_detection(dataset_id, upload_id)
        computation = await self._latest_computation(dataset_id, upload_id, detection)
        classification = await self._latest_classification(dataset_id, upload_id)
        recurrence = await self._latest_audit(RecurrenceAuditLog, dataset_id, upload_id)
        correlation = await self._latest_audit(CorrelationAuditLog, dataset_id, upload_id)
        die_analysis = await self._latest_audit(DieAuditLog, dataset_id, upload_id)
        wafer_analysis = await self._latest_audit(WaferAuditLog, dataset_id, upload_id)
        fault_prediction = await self._latest_prediction_audit(dataset_id, upload_id)

        return {
            "ingestion": ingestion,
            "detection": self._serialize_detection(detection),
            "computation": self._serialize_computation(computation),
            "classification": self._serialize_classification(classification),
            "recurrence": self._serialize_recurrence(recurrence),
            "correlation": self._serialize_correlation(correlation),
            "die_analysis": self._serialize_die(die_analysis),
            "wafer_analysis": self._serialize_wafer(wafer_analysis),
            "fault_prediction": self._serialize_prediction(fault_prediction),
        }

    async def load_module_outputs(self, upload_id: str | None) -> dict[str, Any]:
        if not upload_id:
            return {}
        outputs = await self.legacy.load_module_outputs(upload_id)
        if "patterns" not in outputs:
            pattern = await self._latest_pattern_run(upload_id)
            if pattern is not None:
                outputs["patterns"] = pattern.report_json
        return outputs

    async def _latest_pattern_run(self, upload_id: str) -> PatternAnalysisRun | None:
        stmt = (
            select(PatternAnalysisRun)
            .where(
                PatternAnalysisRun.upload_id == upload_id,
                PatternAnalysisRun.status == "completed",
            )
            .order_by(PatternAnalysisRun.created_at.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def load_test_records(
        self, *, dataset_id: str | None, upload_id: str | None
    ) -> list[TestRecord]:
        if dataset_id:
            stmt = select(NormalizedRecord).where(NormalizedRecord.dataset_id == dataset_id)
            result = await self.session.execute(stmt)
            records: list[TestRecord] = []
            for row in result.scalars().all():
                payload = dict(row.payload or {})
                payload.setdefault("lot_id", row.lot_id)
                payload.setdefault("wafer_id", row.wafer_id)
                payload.setdefault("die_id", row.die_id)
                records.append(TestRecord.from_dict(payload))
            if records:
                return records
        if upload_id:
            return await self.legacy.load_test_records(upload_id)
        return []

    async def load_recommendations(
        self,
        *,
        report_id: str,
        upload_id: str | None,
        dataset_id: str | None,
        upstream: dict[str, Any],
    ) -> list[dict[str, Any]]:
        analysis_ids = [
            upstream.get("recurrence", {}).get("analysis_id"),
            upstream.get("correlation", {}).get("analysis_id"),
            upstream.get("die_analysis", {}).get("analysis_id"),
            upstream.get("wafer_analysis", {}).get("analysis_id"),
            upstream.get("fault_prediction", {}).get("execution_id"),
        ]
        analysis_ids = [item for item in analysis_ids if item]
        stmt = select(EngineeringRecommendation)
        if analysis_ids:
            stmt = stmt.where(EngineeringRecommendation.analysis_id.in_(analysis_ids))
        elif upload_id:
            stmt = stmt.where(EngineeringRecommendation.analysis_id == upload_id)
        else:
            return []
        rows = list(
            (
                await self.session.execute(
                    stmt.order_by(EngineeringRecommendation.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        recommendations: list[dict[str, Any]] = []
        for row in rows:
            row.report_id = report_id
            recommendations.append(
                {
                    "recommendation_id": row.recommendation_id,
                    "source_module": row.source_module,
                    "priority": row.priority,
                    "action": row.action,
                    "rationale": row.rationale,
                    "pattern_id": row.pattern_id,
                    "fault_type": row.fault_type,
                    "evidence": row.evidence,
                }
            )
        return recommendations

    async def create_audit(
        self,
        *,
        report_id: str | None,
        action: str,
        status: str,
        actor: str | None,
        dataset_id: str | None,
        upload_id: str | None,
        template_id: str | None = None,
        export_format: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> ReportAuditLog:
        audit = ReportAuditLog(
            id=str(uuid.uuid4()),
            report_id=report_id,
            action=action,
            status=status,
            actor=actor,
            dataset_id=dataset_id,
            upload_id=upload_id,
            template_id=template_id,
            export_format=export_format,
            details=details or {},
            created_at=_now(),
        )
        self.session.add(audit)
        await self.session.flush()
        return audit

    async def save_report(self, payload: dict[str, Any]) -> Report:
        report = Report(
            id=payload["report_id"],
            report_name=payload.get("report_name", "Enterprise Failure Analysis Report"),
            report_version=int(payload.get("report_version", 1)),
            template_id=payload.get("template_id"),
            dataset_id=payload.get("dataset_id"),
            upload_id=payload.get("upload_id"),
            status=payload.get("status", "completed"),
            completeness_score=float(payload.get("completeness_score", 0.0)),
            consistency_score=float(payload.get("consistency_score", 0.0)),
            traceability_json=payload.get("traceability", {}),
            upstream_execution_ids=payload.get("upstream_execution_ids", {}),
            report_json=payload,
            dashboard_json=payload.get("dashboard_dataset", {}),
            executive_summary=payload.get("executive_report", {}),
            engineering_summary=payload.get("engineering_report", {}),
            benchmark_summary=payload.get("benchmark_summary", {}),
            config_version=payload.get("config_version", ""),
            actor=payload.get("actor"),
            processing_ms=float(payload.get("processing_ms", 0.0)),
            pdf_ms=float(payload.get("pdf_ms", 0.0)),
            excel_ms=float(payload.get("excel_ms", 0.0)),
            export_ms=float(payload.get("export_ms", 0.0)),
            created_at=_now(),
            completed_at=_now() if payload.get("status") == "completed" else None,
        )
        self.session.add(report)
        await self.session.flush()
        await self.append_history(
            report_id=report.id,
            version=report.report_version,
            snapshot_json=payload,
            actor=payload.get("actor"),
            change_reason="initial_generation",
        )
        return report

    async def append_history(
        self,
        *,
        report_id: str,
        version: int,
        snapshot_json: dict[str, Any],
        actor: str | None,
        change_reason: str,
    ) -> ReportHistory:
        history = ReportHistory(
            id=str(uuid.uuid4()),
            report_id=report_id,
            version=version,
            snapshot_json=snapshot_json,
            change_reason=change_reason,
            actor=actor,
            created_at=_now(),
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def save_benchmarks(
        self, report_id: str, benchmark_summary: dict[str, Any], config: Any
    ) -> None:
        metrics = [
            (
                "completeness",
                "completeness_score",
                benchmark_summary.get("completeness_score", 0.0),
                config.min_completeness_score,
            ),
            (
                "consistency",
                "consistency_score",
                benchmark_summary.get("consistency_score", 0.0),
                config.min_consistency_score,
            ),
            (
                "performance",
                "processing_ms",
                benchmark_summary.get("processing_ms", 0.0),
                config.report_target_ms,
            ),
        ]
        for benchmark_type, metric_name, value, target in metrics:
            self.session.add(
                BenchmarkResult(
                    id=str(uuid.uuid4()),
                    report_id=report_id,
                    benchmark_type=benchmark_type,
                    metric_name=metric_name,
                    metric_value=float(value or 0.0),
                    target_value=float(target),
                    passed=(
                        float(value or 0.0) < float(target)
                        if benchmark_type == "performance"
                        else float(value or 0.0) >= float(target)
                    ),
                    details={},
                    created_at=_now(),
                )
            )

    async def save_export(self, payload: dict[str, Any]) -> ReportExport:
        export = ReportExport(
            id=str(uuid.uuid4()),
            export_id=payload["export_id"],
            report_id=payload["report_id"],
            format=payload["format"],
            file_path=payload.get("file_path", ""),
            file_size_bytes=int(payload.get("file_size_bytes", 0)),
            status=payload.get("status", "completed"),
            processing_ms=float(payload.get("processing_ms", 0.0)),
            actor=payload.get("actor"),
            metadata_json=payload.get("metadata_json", {}),
            created_at=_now(),
        )
        self.session.add(export)
        await self.session.flush()
        return export

    async def get_report(self, report_id: str) -> Report | None:
        return await self.session.get(Report, report_id)

    async def get_legacy_run(self, report_id: str) -> EngineeringReportRun | None:
        return await self.legacy.get_run(report_id)

    async def list_reports(self, *, limit: int = 50) -> list[Report]:
        stmt = select(Report).order_by(Report.created_at.desc()).limit(limit)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_history(
        self, *, report_id: str | None = None, limit: int = 100
    ) -> list[ReportHistory]:
        stmt = select(ReportHistory).order_by(ReportHistory.created_at.desc()).limit(limit)
        if report_id:
            stmt = stmt.where(ReportHistory.report_id == report_id)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_exports(self, report_id: str) -> list[ReportExport]:
        stmt = (
            select(ReportExport)
            .where(ReportExport.report_id == report_id)
            .order_by(ReportExport.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_export(self, export_id: str) -> ReportExport | None:
        stmt = select(ReportExport).where(ReportExport.export_id == export_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def _latest_detection(
        self, dataset_id: str | None, upload_id: str | None
    ) -> DetectionHistory | PatternAnalysisRun | None:
        stmt = select(DetectionHistory).where(
            DetectionHistory.execution_status == "completed"
        )
        if dataset_id:
            stmt = stmt.where(DetectionHistory.dataset_id == dataset_id)
        elif upload_id:
            stmt = stmt.where(DetectionHistory.upload_id == upload_id)
        detection = (
            await self.session.execute(
                stmt.order_by(DetectionHistory.completed_at.desc()).limit(1)
            )
        ).scalars().first()
        if detection:
            return detection
        legacy_stmt = select(PatternAnalysisRun).where(
            PatternAnalysisRun.status == "completed"
        )
        if upload_id:
            legacy_stmt = legacy_stmt.where(PatternAnalysisRun.upload_id == upload_id)
        return (await self.session.execute(legacy_stmt.order_by(PatternAnalysisRun.created_at.desc()).limit(1))).scalars().first()

    async def _latest_computation(
        self,
        dataset_id: str | None,
        upload_id: str | None,
        detection: Any,
    ) -> ComputationHistory | FailureRateRun | None:
        stmt = select(ComputationHistory).where(ComputationHistory.status == "completed")
        if dataset_id:
            stmt = stmt.where(ComputationHistory.dataset_id == dataset_id)
        elif upload_id:
            stmt = stmt.where(ComputationHistory.upload_id == upload_id)
        computation = (
            await self.session.execute(
                stmt.order_by(ComputationHistory.completed_at.desc()).limit(1)
            )
        ).scalars().first()
        if computation:
            return computation
        legacy_stmt = select(FailureRateRun)
        if upload_id:
            legacy_stmt = legacy_stmt.where(FailureRateRun.upload_id == upload_id)
        return (await self.session.execute(legacy_stmt.order_by(FailureRateRun.created_at.desc()).limit(1))).scalars().first()

    async def _latest_classification(
        self, dataset_id: str | None, upload_id: str | None
    ) -> ClassificationRun | None:
        stmt = select(ClassificationRun).where(ClassificationRun.status == "completed")
        if upload_id:
            stmt = stmt.where(ClassificationRun.upload_id == upload_id)
        return (await self.session.execute(stmt.order_by(ClassificationRun.created_at.desc()).limit(1))).scalars().first()

    async def _latest_audit(
        self,
        model: type,
        dataset_id: str | None,
        upload_id: str | None,
    ) -> Any | None:
        stmt = select(model).where(model.status == "completed")
        if dataset_id:
            stmt = stmt.where(model.dataset_id == dataset_id)
        elif upload_id:
            stmt = stmt.where(model.upload_id == upload_id)
        return (await self.session.execute(stmt.order_by(model.completed_at.desc()).limit(1))).scalars().first()

    async def _latest_prediction_audit(
        self, dataset_id: str | None, upload_id: str | None
    ) -> PredictionAuditLog | None:
        stmt = select(PredictionAuditLog).where(PredictionAuditLog.status == "completed")
        if dataset_id:
            stmt = stmt.where(PredictionAuditLog.dataset_id == dataset_id)
        elif upload_id:
            stmt = stmt.where(PredictionAuditLog.upload_id == upload_id)
        return (await self.session.execute(stmt.order_by(PredictionAuditLog.completed_at.desc()).limit(1))).scalars().first()

    def _serialize_detection(self, row: Any | None) -> dict[str, Any]:
        if row is None:
            return {}
        if isinstance(row, DetectionHistory):
            return {
                "analysis_id": row.analysis_id,
                "execution_status": row.execution_status,
                "pattern_count": row.pattern_count,
                "benchmark_metrics": row.benchmark_metrics,
            }
        return {
            "analysis_id": row.id,
            "execution_status": row.status,
            "pattern_count": row.unique_patterns,
            "benchmark_metrics": {},
        }

    def _serialize_computation(self, row: Any | None) -> dict[str, Any]:
        if row is None:
            return {}
        if isinstance(row, ComputationHistory):
            return {
                "computation_id": row.computation_id,
                "detection_execution_id": row.detection_execution_id,
                "status": row.status,
                "benchmark_metrics": row.benchmark_metrics,
            }
        return {
            "computation_id": row.id,
            "detection_execution_id": None,
            "status": row.status,
            "benchmark_metrics": {},
        }

    def _serialize_classification(self, row: ClassificationRun | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "execution_id": row.id,
            "status": row.status,
            "total_faults": row.total_faults,
        }

    def _serialize_recurrence(self, row: RecurrenceAuditLog | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "analysis_id": row.analysis_id,
            "detection_execution_id": row.detection_execution_id,
            "computation_id": row.computation_id,
            "status": row.status,
            "benchmark_metrics": row.benchmark_metrics,
        }

    def _serialize_correlation(self, row: CorrelationAuditLog | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "analysis_id": row.analysis_id,
            "detection_execution_id": row.detection_execution_id,
            "status": row.status,
            "benchmark_metrics": row.benchmark_metrics,
        }

    def _serialize_die(self, row: DieAuditLog | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "analysis_id": row.analysis_id,
            "detection_execution_id": row.detection_execution_id,
            "status": row.status,
            "benchmark_metrics": row.benchmark_metrics,
        }

    def _serialize_wafer(self, row: WaferAuditLog | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "analysis_id": row.analysis_id,
            "detection_execution_id": row.detection_execution_id,
            "status": row.status,
            "benchmark_metrics": row.benchmark_metrics,
        }

    def _serialize_prediction(self, row: PredictionAuditLog | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "execution_id": row.execution_id,
            "status": row.status,
            "upstream_execution_ids": row.upstream_execution_ids,
            "benchmark_metrics": row.benchmark_metrics,
        }
