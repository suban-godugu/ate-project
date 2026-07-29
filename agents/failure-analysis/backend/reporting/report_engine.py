"""Main FA-FR-010 report generation orchestrator."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from analyzer import analyze_failures
from backend.reporting.dashboard_data import build_dashboard_dataset
from backend.reporting.excel_generator import export_excel_report
from backend.reporting.json_export import export_json_report
from backend.reporting.pdf_generator import export_pdf_report
from backend.reporting.summary_generator import build_summaries
from ingestor import DieLog

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "reporting.yaml"


class ReportEngine:
    """
    Failure summary & engineering reporting pipeline:
    aggregate → summaries → visualizations → exports → dashboard
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        raw = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        self.config = raw
        perf = raw.get("performance", {})
        self.report_target_ms = int(perf.get("report_generation_target_ms", 10000))
        self.pdf_target_ms = int(perf.get("pdf_generation_target_ms", 5000))
        self.excel_target_ms = int(perf.get("excel_export_target_ms", 5000))

        export_cfg = raw.get("export", {})
        storage = export_cfg.get("storage_dir", "backend/storage/reports")
        storage_path = Path(storage)
        if not storage_path.is_absolute():
            storage_path = Path(__file__).resolve().parents[2] / storage
        self.storage_dir = storage_path
        self.pdf_enabled = bool(export_cfg.get("pdf_enabled", True))
        self.excel_enabled = bool(export_cfg.get("excel_enabled", True))
        self.json_enabled = bool(export_cfg.get("json_enabled", True))

        template_rel = raw.get("report", {}).get(
            "template_path", "backend/reporting/templates/engineering_report.html.j2"
        )
        template_path = Path(template_rel)
        if not template_path.is_absolute():
            template_path = Path(__file__).resolve().parents[2] / template_path
        self.template_path = template_path

    def generate(
        self,
        *,
        die_logs: list[DieLog],
        test_records: list[TestRecord] | None = None,
        upload_meta: dict[str, Any],
        module_outputs: dict[str, Any] | None = None,
        upload_id: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        report_id = str(uuid.uuid4())

        analysis = analyze_failures(die_logs, test_records=test_records)
        modules = module_outputs or {}

        summaries = build_summaries(
            analysis=analysis,
            module_outputs=modules,
            upload_meta=upload_meta,
            config=self.config,
        )
        dashboard = build_dashboard_dataset(summaries, analysis, modules)
        html_rendered = _render_template(self.template_path, summaries)

        export_meta = {
            **summaries.get("metadata", {}),
            "report_id": report_id,
        }

        pdf_path: str | None = None
        excel_path: str | None = None
        json_path: str | None = None
        pdf_ms = 0.0
        excel_ms = 0.0
        json_size_kb = 0.0

        if self.json_enabled:
            json_file, json_size_kb = export_json_report(
                report_id=report_id,
                summaries=summaries,
                dashboard=dashboard,
                analysis=analysis,
                module_outputs=modules,
                export_meta=export_meta,
                output_dir=self.storage_dir,
            )
            json_path = str(json_file)

        if self.pdf_enabled:
            try:
                pdf_file, pdf_ms = export_pdf_report(
                    report_id=report_id,
                    summaries=summaries,
                    html_rendered=html_rendered,
                    output_dir=self.storage_dir,
                )
                pdf_path = str(pdf_file)
            except RuntimeError:
                pdf_path = None

        if self.excel_enabled:
            try:
                excel_file, excel_ms = export_excel_report(
                    report_id=report_id,
                    summaries=summaries,
                    dashboard=dashboard,
                    output_dir=self.storage_dir,
                )
                excel_path = str(excel_file)
            except RuntimeError:
                excel_path = None

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        return {
            "requirement": "FA-FR-010",
            "report_id": report_id,
            "upload_id": upload_id or upload_meta.get("upload_id"),
            "processing_ms": elapsed_ms,
            "pdf_ms": pdf_ms,
            "excel_ms": excel_ms,
            "json_size_kb": json_size_kb,
            "meets_performance_target": (
                elapsed_ms < self.report_target_ms
                and pdf_ms < self.pdf_target_ms
                and excel_ms < self.excel_target_ms
            ),
            "detection_pipeline": [
                "aggregate_statistics",
                "generate_engineering_summary",
                "generate_executive_summary",
                "generate_visualizations",
                "create_exportable_reports",
                "dashboard_update",
            ],
            "executive_report": summaries.get("executive_summary", {}),
            "engineering_report": summaries.get("engineering_summary", {}),
            "failure_summary": {
                "failure_trend_summary": summaries.get("failure_trend_summary", {}),
                "top_failure_modes": summaries.get("top_failure_modes", []),
                "engineering_observations": summaries.get("engineering_observations", []),
            },
            "yield_report": summaries.get("yield_summary", {}),
            "trend_analysis_report": summaries.get("failure_trend_summary", {}),
            "root_cause_report": summaries.get("root_cause_summary", {}),
            "summaries": summaries,
            "dashboard_dataset": dashboard,
            "html_preview": html_rendered,
            "export_paths": {
                "pdf": pdf_path,
                "excel": excel_path,
                "json": json_path,
            },
            "analysis_core": analysis,
            "module_outputs": modules,
        }


def _render_template(template_path: Path, summaries: dict[str, Any]) -> str:
    if not template_path.exists():
        return ""
    try:
        from jinja2 import Template

        template = Template(template_path.read_text(encoding="utf-8"))
        return template.render(**summaries)
    except ImportError:
        return template_path.read_text(encoding="utf-8")
    except Exception:
        return ""
