"""Service layer for FA-FR-010 engineering reporting."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from backend.ingestion.record_loader import load_test_records
from backend.reporting.report_engine import ReportEngine
from backend.reporting.report_repository import ReportRepository


class ReportService:
    def __init__(
        self,
        repo: ReportRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.engine = ReportEngine(config_path=config_path)

    async def generate_report(self, upload_id: str) -> dict[str, Any]:
        upload = await self.repo.get_upload(upload_id)
        if upload is None:
            raise ValueError(f"Upload not found: upload_id={upload_id}")
        test_records = await self.repo.load_test_records(upload_id)
        return await self._generate(
            test_records,
            scope_id=upload_id,
            upload_meta={
                "upload_id": upload_id,
                "original_filename": upload.original_filename,
                "records_accepted": upload.records_accepted,
                "integrity_pct": upload.integrity_pct,
                "status": upload.status,
            },
        )

    async def generate_dataset_report(
        self,
        dataset_id: str,
        *,
        primary_upload_id: str | None = None,
    ) -> dict[str, Any]:
        test_records = await load_test_records(self.repo._session, dataset_id=dataset_id)
        upload = None
        if primary_upload_id:
            upload = await self.repo.get_upload(primary_upload_id)
        return await self._generate(
            test_records,
            scope_id=dataset_id,
            upload_meta={
                "upload_id": primary_upload_id or dataset_id,
                "original_filename": upload.original_filename if upload else f"dataset:{dataset_id}",
                "records_accepted": len(test_records),
                "integrity_pct": 100.0 if test_records else 0.0,
                "status": "completed" if test_records else "empty",
            },
            module_scope_id=primary_upload_id or dataset_id,
        )

    async def _generate(
        self,
        test_records: list,
        *,
        scope_id: str,
        upload_meta: dict[str, Any],
        module_scope_id: str | None = None,
    ) -> dict[str, Any]:
        if not test_records:
            raise ValueError(f"No records found for scope={scope_id}")

        die_logs = test_records_to_die_logs(test_records)
        module_outputs = await self.repo.load_module_outputs(module_scope_id or scope_id)

        report = self.engine.generate(
            die_logs=die_logs,
            test_records=test_records,
            upload_meta=upload_meta,
            module_outputs=module_outputs,
            upload_id=scope_id,
        )
        await self.repo.save_run(report)

        return {
            "report_id": report["report_id"],
            "upload_id": scope_id,
            "processing_ms": report["processing_ms"],
            "pdf_ms": report["pdf_ms"],
            "excel_ms": report["excel_ms"],
            "meets_performance_target": report["meets_performance_target"],
            "executive_report": report["executive_report"],
            "engineering_report": report["engineering_report"],
            "failure_summary": report["failure_summary"],
            "yield_report": report["yield_report"],
            "root_cause_report": report["root_cause_report"],
            "dashboard_dataset": report["dashboard_dataset"],
            "export_paths": report["export_paths"],
        }

    async def get_report(self, report_id: str) -> dict[str, Any]:
        run = await self.repo.get_run(report_id)
        if run is None:
            raise ValueError(f"Report not found: report_id={report_id}")
        return {
            "report_id": run.id,
            "upload_id": run.upload_id,
            "status": run.status,
            "processing_ms": run.processing_ms,
            "total_dies": run.total_dies,
            "failing_dies": run.failing_dies,
            "overall_yield_pct": run.overall_yield_pct,
            "executive_report": run.report_json.get("executive_report", {}),
            "engineering_report": run.report_json.get("engineering_report", {}),
            "failure_summary": run.report_json.get("failure_summary", {}),
            "yield_report": run.report_json.get("yield_report", {}),
            "root_cause_report": run.report_json.get("root_cause_report", {}),
            "dashboard_dataset": run.dashboard_json,
            "export_paths": {
                "pdf": run.pdf_path,
                "excel": run.excel_path,
                "json": run.json_path,
            },
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }

    async def get_export_path(self, report_id: str, fmt: str) -> Path:
        run = await self.repo.get_run(report_id)
        if run is None:
            raise ValueError(f"Report not found: report_id={report_id}")

        path_map = {
            "pdf": run.pdf_path,
            "excel": run.excel_path,
            "json": run.json_path,
        }
        path_str = path_map.get(fmt)
        if not path_str:
            raise ValueError(f"{fmt.upper()} export not available for report_id={report_id}")

        path = Path(path_str)
        if not path.exists():
            raise ValueError(f"Export file missing on disk: {path}")
        return path
