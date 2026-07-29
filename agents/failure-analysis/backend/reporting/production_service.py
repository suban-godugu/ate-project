"""Validated, benchmarked FA-FR-010 orchestration."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.bridge import test_records_to_die_logs
from backend.reporting.csv_exporter import export_csv_report
from backend.reporting.excel_generator import export_excel_report
from backend.reporting.html_exporter import export_html_report
from backend.reporting.json_export import export_json_report
from backend.reporting.pdf_generator import export_pdf_report
from backend.reporting.production_engine import (
    ReportHandoffGateError,
    ReportingConfig,
    build_benchmark_summary,
    build_traceability,
    score_completeness,
    score_consistency,
    validate_upstream_handoff,
)
from backend.reporting.production_repository import ProductionReportingRepository
from backend.reporting.report_engine import ReportEngine, _render_template
from backend.reporting.schemas import ExportReportRequest, GenerateReportRequest
from backend.reporting.templates import (
    apply_template_to_summaries,
    build_module_sections,
    merge_template_sections,
)


class ReportValidationError(ValueError):
    def __init__(self, issues: list[dict[str, Any]]) -> None:
        self.issues = issues
        super().__init__("Report generation validation failed")


class ProductionReportingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ProductionReportingRepository(session)

    async def execute(
        self,
        request: GenerateReportRequest,
        *,
        report_id: str | None = None,
    ) -> dict[str, Any]:
        config = ReportingConfig.load(request.config_path)
        report_id = report_id or str(uuid.uuid4())
        template = await self.repo.get_template(request.template_key)
        audit = await self.repo.create_audit(
            report_id=report_id,
            action="generate",
            status="processing",
            actor=request.actor,
            dataset_id=request.dataset_id,
            upload_id=request.upload_id,
            template_id=template.id,
            details={"incremental": request.incremental, "requirement": "FA-FR-010"},
        )
        await self.session.commit()
        started = time.perf_counter()
        try:
            upstream = await self.repo.load_upstream_handoff(
                dataset_id=request.dataset_id,
                upload_id=request.upload_id,
            )
            issues = validate_upstream_handoff(upstream)
            if issues:
                raise ReportHandoffGateError(issues)

            upload_id = request.upload_id or upstream.get("ingestion", {}).get("source_id")
            test_records = await self.repo.load_test_records(
                dataset_id=request.dataset_id,
                upload_id=upload_id,
            )
            if not test_records:
                raise ReportValidationError(
                    [
                        {
                            "code": "NO_SOURCE_RECORDS",
                            "message": "No normalized test records available for reporting",
                        }
                    ]
                )

            module_outputs = await self.repo.load_module_outputs(upload_id)

            die_logs = test_records_to_die_logs(test_records)
            upload_meta = {
                "upload_id": upload_id,
                "dataset_id": request.dataset_id,
                "original_filename": upstream.get("ingestion", {}).get(
                    "original_filename", ""
                ),
                "records_accepted": upstream.get("ingestion", {}).get(
                    "records_accepted", len(test_records)
                ),
                "integrity_pct": upstream.get("ingestion", {}).get("integrity_pct", 0.0),
                "status": upstream.get("ingestion", {}).get("status", "completed"),
            }

            enabled_sections = merge_template_sections(
                template.sections_json,
                config.sections,
            )
            engine = ReportEngine(config_path=request.config_path)
            base_report = engine.generate(
                die_logs=die_logs,
                test_records=test_records,
                upload_meta=upload_meta,
                module_outputs=module_outputs,
                upload_id=upload_id,
            )
            base_report["report_id"] = report_id

            module_sections = build_module_sections(
                module_outputs=module_outputs,
                upstream=upstream,
                enabled_sections=enabled_sections,
            )
            recommendations = await self.repo.load_recommendations(
                report_id=report_id,
                upload_id=upload_id,
                dataset_id=request.dataset_id,
                upstream=upstream,
            )
            if not recommendations:
                recommendations = base_report["summaries"].get(
                    "recommended_corrective_actions", []
                )

            completeness = score_completeness(
                module_outputs=module_outputs,
                module_sections=module_sections,
                recommendations=recommendations,
            )
            consistency = score_consistency(
                upstream=upstream,
                module_outputs=module_outputs,
            )
            upstream_benchmarks = {
                key: value.get("benchmark_metrics", {})
                for key, value in upstream.items()
                if isinstance(value, dict)
            }
            benchmark_summary = build_benchmark_summary(
                completeness_score=completeness,
                consistency_score=consistency,
                processing_ms=base_report.get("processing_ms", 0.0),
                pdf_ms=base_report.get("pdf_ms", 0.0),
                excel_ms=base_report.get("excel_ms", 0.0),
                config=config,
                upstream_benchmarks=upstream_benchmarks,
            )
            traceability = build_traceability(
                report_id=report_id,
                dataset_id=request.dataset_id,
                upload_id=upload_id,
                template_key=template.template_key,
                upstream=upstream,
            )
            summaries = apply_template_to_summaries(
                base_report["summaries"],
                module_sections=module_sections,
                enabled_sections=enabled_sections,
                recommendations=recommendations,
                benchmark_summary=benchmark_summary,
                traceability=traceability,
            )
            html_rendered = _render_template(engine.template_path, summaries)
            export_paths = dict(base_report.get("export_paths", {}))

            if config.html_enabled:
                html_path, _ = export_html_report(
                    report_id=report_id,
                    summaries=summaries,
                    html_rendered=html_rendered,
                    output_dir=config.storage_dir,
                )
                export_paths["html"] = str(html_path)
            if config.csv_enabled:
                csv_path, _ = export_csv_report(
                    report_id=report_id,
                    summaries=summaries,
                    dashboard=base_report.get("dashboard_dataset", {}),
                    output_dir=config.storage_dir,
                )
                export_paths["csv"] = str(csv_path)

            upstream_execution_ids = {
                "detection_execution_id": upstream.get("detection", {}).get("analysis_id"),
                "computation_id": upstream.get("computation", {}).get("computation_id"),
                "classification_execution_id": upstream.get("classification", {}).get(
                    "execution_id"
                ),
                "recurrence_analysis_id": upstream.get("recurrence", {}).get("analysis_id"),
                "correlation_analysis_id": upstream.get("correlation", {}).get("analysis_id"),
                "die_analysis_id": upstream.get("die_analysis", {}).get("analysis_id"),
                "wafer_analysis_id": upstream.get("wafer_analysis", {}).get("analysis_id"),
                "fault_prediction_execution_id": upstream.get("fault_prediction", {}).get(
                    "execution_id"
                ),
            }

            payload = {
                **base_report,
                "report_id": report_id,
                "report_name": request.report_name
                or template.name,
                "report_version": 1,
                "template_id": template.id,
                "template_key": template.template_key,
                "dataset_id": request.dataset_id,
                "upload_id": upload_id,
                "status": "completed",
                "config_version": config.version,
                "actor": request.actor,
                "completeness_score": completeness,
                "consistency_score": consistency,
                "benchmark_summary": benchmark_summary,
                "traceability": traceability,
                "upstream_execution_ids": upstream_execution_ids,
                "summaries": summaries,
                "executive_report": summaries.get("executive_summary", {}),
                "engineering_report": summaries.get("engineering_summary", {}),
                "recommendations": recommendations,
                "export_paths": export_paths,
                "html_preview": html_rendered,
                "meets_performance_target": benchmark_summary["meets_performance_target"],
            }

            await self.repo.save_report(payload)
            await self.repo.save_benchmarks(report_id, benchmark_summary, config)
            processing_ms = round((time.perf_counter() - started) * 1000, 2)
            audit.status = "completed"
            audit.processing_ms = processing_ms
            audit.benchmark_metrics = benchmark_summary
            audit.completed_at = audit.created_at
            await self.session.commit()
            return self._serialize_generate_response(payload)
        except (ReportHandoffGateError, ReportValidationError) as exc:
            audit.status = "failed"
            audit.errors = exc.issues
            audit.processing_ms = round((time.perf_counter() - started) * 1000, 2)
            await self.session.commit()
            raise
        except Exception as exc:
            audit.status = "failed"
            audit.errors = [{"code": "INTERNAL_ERROR", "message": str(exc)}]
            audit.processing_ms = round((time.perf_counter() - started) * 1000, 2)
            await self.session.commit()
            raise

    async def export(
        self,
        request: ExportReportRequest,
        *,
        export_id: str | None = None,
    ) -> dict[str, Any]:
        export_id = export_id or str(uuid.uuid4())
        report = await self.repo.get_report(request.report_id)
        legacy = None
        if report is None:
            legacy = await self.repo.get_legacy_run(request.report_id)
            if legacy is None:
                raise ValueError(f"Report not found: report_id={request.report_id}")

        audit = await self.repo.create_audit(
            report_id=request.report_id,
            action="export",
            status="processing",
            actor=request.actor,
            export_format=request.format,
            upload_id=report.upload_id if report else legacy.upload_id,
            dataset_id=report.dataset_id if report else None,
        )
        await self.session.commit()
        started = time.perf_counter()
        try:
            config = ReportingConfig.load()
            summaries = (
                report.report_json.get("summaries", {})
                if report
                else legacy.report_json.get("summaries", {})
            )
            dashboard = (
                report.dashboard_json if report else legacy.dashboard_json
            )
            report_id = request.report_id
            path: Path | None = None
            processing_ms = 0.0

            if request.format == "json":
                path, _ = export_json_report(
                    report_id=report_id,
                    summaries=summaries,
                    dashboard=dashboard,
                    analysis={},
                    module_outputs={},
                    export_meta={"report_id": report_id},
                    output_dir=config.storage_dir,
                )
            elif request.format == "pdf":
                path, processing_ms = export_pdf_report(
                    report_id=report_id,
                    summaries=summaries,
                    html_rendered=(
                        report.report_json.get("html_preview")
                        if report
                        else legacy.report_json.get("html_preview")
                    ),
                    output_dir=config.storage_dir,
                )
            elif request.format == "xlsx":
                path, processing_ms = export_excel_report(
                    report_id=report_id,
                    summaries=summaries,
                    dashboard=dashboard,
                    output_dir=config.storage_dir,
                )
            elif request.format == "html":
                path, processing_ms = export_html_report(
                    report_id=report_id,
                    summaries=summaries,
                    html_rendered=(
                        report.report_json.get("html_preview")
                        if report
                        else legacy.report_json.get("html_preview")
                    ),
                    output_dir=config.storage_dir,
                )
            elif request.format == "csv":
                path, processing_ms = export_csv_report(
                    report_id=report_id,
                    summaries=summaries,
                    dashboard=dashboard,
                    output_dir=config.storage_dir,
                )
            else:
                raise ValueError(f"Unsupported export format: {request.format}")

            file_size = path.stat().st_size if path else 0
            export_payload = {
                "export_id": export_id,
                "report_id": report_id,
                "format": request.format,
                "file_path": str(path) if path else "",
                "file_size_bytes": file_size,
                "status": "completed",
                "processing_ms": processing_ms,
                "actor": request.actor,
                "metadata_json": {"requirement": "FA-FR-010"},
            }
            await self.repo.save_export(export_payload)
            audit.status = "completed"
            audit.processing_ms = round((time.perf_counter() - started) * 1000, 2)
            audit.completed_at = audit.created_at
            await self.session.commit()
            return export_payload
        except Exception as exc:
            audit.status = "failed"
            audit.errors = [{"code": "EXPORT_FAILED", "message": str(exc)}]
            audit.processing_ms = round((time.perf_counter() - started) * 1000, 2)
            await self.session.commit()
            raise

    async def get_report_detail(self, report_id: str) -> dict[str, Any]:
        report = await self.repo.get_report(report_id)
        if report:
            return {
                "report_id": report.id,
                "report_name": report.report_name,
                "report_version": report.report_version,
                "upload_id": report.upload_id,
                "dataset_id": report.dataset_id,
                "status": report.status,
                "legacy": False,
                "completeness_score": report.completeness_score,
                "consistency_score": report.consistency_score,
                "processing_ms": report.processing_ms,
                "executive_report": report.executive_summary,
                "engineering_report": report.engineering_summary,
                "benchmark_summary": report.benchmark_summary,
                "recommendations": report.report_json.get("recommendations", []),
                "module_sections": report.report_json.get("summaries", {}).get(
                    "module_sections", {}
                ),
                "dashboard_dataset": report.dashboard_json,
                "traceability": report.traceability_json,
                "upstream_execution_ids": report.upstream_execution_ids,
                "export_paths": report.report_json.get("export_paths", {}),
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "completed_at": report.completed_at.isoformat()
                if report.completed_at
                else None,
            }
        legacy = await self.repo.get_legacy_run(report_id)
        if legacy is None:
            raise ValueError(f"Report not found: report_id={report_id}")
        return {
            "report_id": legacy.id,
            "upload_id": legacy.upload_id,
            "status": legacy.status,
            "legacy": True,
            "processing_ms": legacy.processing_ms,
            "executive_report": legacy.report_json.get("executive_report", {}),
            "engineering_report": legacy.report_json.get("engineering_report", {}),
            "failure_summary": legacy.report_json.get("failure_summary", {}),
            "yield_report": legacy.report_json.get("yield_report", {}),
            "root_cause_report": legacy.report_json.get("root_cause_report", {}),
            "dashboard_dataset": legacy.dashboard_json,
            "export_paths": {
                "pdf": legacy.pdf_path,
                "excel": legacy.excel_path,
                "json": legacy.json_path,
            },
            "created_at": legacy.created_at.isoformat() if legacy.created_at else None,
        }

    def _serialize_generate_response(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "report_id": payload["report_id"],
            "status": payload.get("status", "completed"),
            "upload_id": payload.get("upload_id"),
            "dataset_id": payload.get("dataset_id"),
            "template_key": payload.get("template_key"),
            "completeness_score": payload.get("completeness_score", 0.0),
            "consistency_score": payload.get("consistency_score", 0.0),
            "processing_ms": payload.get("processing_ms", 0.0),
            "meets_performance_target": payload.get("meets_performance_target", False),
            "executive_report": payload.get("executive_report", {}),
            "engineering_report": payload.get("engineering_report", {}),
            "benchmark_summary": payload.get("benchmark_summary", {}),
            "recommendations": payload.get("recommendations", []),
            "dashboard_dataset": payload.get("dashboard_dataset", {}),
            "export_paths": payload.get("export_paths", {}),
            "traceability": payload.get("traceability", {}),
            "upstream_execution_ids": payload.get("upstream_execution_ids", {}),
        }
