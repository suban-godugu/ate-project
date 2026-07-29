"""PA-FR-010.3 single-log report generation orchestrator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping

from report_export_excel import export_excel
from report_export_html import export_html
from report_export_pdf import export_pdf
from report_presentation_builder import build_report_presentation
from report_preview_builder import load_report_model


class ReportGenerationError(ValueError):
    """Raised for unsupported report generation requests."""


@dataclass(frozen=True)
class GeneratedReport:
    content: bytes
    media_type: str
    filename: str
    model_hash: str


Exporter = Callable[[Mapping[str, Any]], bytes]

EXPORTERS: Dict[str, tuple[Exporter, str, str]] = {
    "html": (
        export_html,
        "text/html; charset=utf-8",
        "PA-FR-010_pattern_quality_report.html",
    ),
    "pdf": (
        export_pdf,
        "application/pdf",
        "PA-FR-010_pattern_quality_report.pdf",
    ),
    "excel": (
        export_excel,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "PA-FR-010_pattern_quality_report.xlsx",
    ),
}


def generate_report(
    report_model: Mapping[str, Any],
    requested_format: str,
) -> GeneratedReport:
    """Generate one report directly from an already-loaded PA-FR-010.1 model."""
    normalized_format = str(requested_format or "").strip().lower()
    export_config = EXPORTERS.get(normalized_format)
    if export_config is None:
        raise ReportGenerationError(
            "Unsupported report format. Expected html, pdf, or excel."
        )
    presentation = build_report_presentation(report_model, table_limit=None)
    exporter, media_type, filename = export_config
    content = exporter(presentation)
    model_hash = str(
        (report_model.get("generation_metadata") or {}).get("model_hash") or ""
    )
    return GeneratedReport(
        content=content,
        media_type=media_type,
        filename=filename,
        model_hash=model_hash,
    )


def generate_report_from_output(
    output_dir: str,
    requested_format: str,
) -> GeneratedReport:
    """Load only PA-FR-010_report_model.json and generate the requested report."""
    return generate_report(load_report_model(output_dir), requested_format)
