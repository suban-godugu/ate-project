"""PDF report generation via ReportLab."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def export_pdf_report(
    *,
    report_id: str,
    summaries: dict[str, Any],
    html_rendered: str | None,
    output_dir: Path,
) -> tuple[Path, float]:
    """Generate PDF engineering report."""
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_id}.pdf"

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise RuntimeError("reportlab is required for PDF export") from exc

    doc = SimpleDocTemplate(str(path), pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = styles["BodyText"]

    story: list[Any] = []
    meta = summaries.get("metadata", {})
    story.append(Paragraph(meta.get("report_title", "Failure Analysis Report"), title_style))
    story.append(Paragraph(f"Report ID: {report_id}", body_style))
    story.append(Paragraph(f"Generated: {meta.get('generated_at', '')}", body_style))
    story.append(Paragraph(f"Upload: {meta.get('original_filename', '')}", body_style))
    story.append(Spacer(1, 0.2 * inch))

    exec_sum = summaries.get("executive_summary", {})
    story.append(Paragraph("Executive Summary", section_style))
    story.append(Paragraph(exec_sum.get("headline", ""), body_style))
    exec_table = _kv_table(
        [
            ("Dies Tested", exec_sum.get("total_dies_tested")),
            ("Failing Dies", exec_sum.get("total_failing_dies")),
            ("Die Failure Rate", exec_sum.get("overall_die_failure_rate")),
            ("Overall Yield %", exec_sum.get("overall_yield_pct")),
            ("Top Fault Category", exec_sum.get("top_fault_category")),
            ("Top Root Cause", exec_sum.get("top_predicted_root_cause")),
            ("Prediction Confidence", exec_sum.get("top_prediction_confidence")),
        ]
    )
    story.append(exec_table)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Engineering Observations", section_style))
    for obs in summaries.get("engineering_observations", []):
        story.append(Paragraph(f"• {obs}", body_style))

    story.append(Paragraph("Top Failure Modes", section_style))
    mode_rows = [["Fault Category", "Count"]]
    for mode in summaries.get("top_failure_modes", [])[:8]:
        mode_rows.append([str(mode.get("fault_category", "")), str(mode.get("count", ""))])
    story.append(_data_table(mode_rows))

    story.append(Paragraph("Root Cause Summary", section_style))
    rc_rows = [["Scan Chain", "Fault Type", "Confidence"]]
    for pred in summaries.get("root_cause_summary", {}).get("predictions", [])[:8]:
        rc_rows.append(
            [
                str(pred.get("scan_chain_id", "")),
                str(pred.get("predicted_fault_type", "")),
                str(pred.get("confidence_score", "")),
            ]
        )
    story.append(_data_table(rc_rows))

    story.append(Paragraph("Recommended Corrective Actions", section_style))
    for rec in summaries.get("recommended_corrective_actions", [])[:10]:
        action = rec.get("action", "")
        priority = rec.get("priority", "")
        story.append(Paragraph(f"[{priority}] {action}", body_style))

    if html_rendered:
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("Rendered Template Excerpt", section_style))
        excerpt = html_rendered[:500].replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(excerpt, body_style))

    doc.build(story)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return path, elapsed_ms


def _kv_table(rows: list[tuple[str, Any]]) -> Any:
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    data = [[k, str(v if v is not None else "")] for k, v in rows]
    table = Table(data, colWidths=[180, 300])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ]
        )
    )
    return table


def _data_table(rows: list[list[str]]) -> Any:
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    table = Table(rows, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    return table
