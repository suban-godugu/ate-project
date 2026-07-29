"""Standalone HTML exporter for PA-FR-010.3."""
from __future__ import annotations

from html import escape
from typing import Any, Mapping, Sequence

from report_presentation_builder import format_cell_value


def _text(value: Any) -> str:
    return escape(format_cell_value(value), quote=True)


def _render_chart(chart: Mapping[str, Any]) -> str:
    title = _text(chart.get("title"))
    data = chart.get("data")
    if isinstance(data, Mapping):
        rows = "".join(
            f"<tr><th>{_text(key)}</th><td>{_text(value)}</td></tr>"
            for key, value in sorted(data.items(), key=lambda item: str(item[0]))
        )
        return (
            f'<div class="chart"><h4>{title}</h4>'
            f'<table class="compact"><tbody>{rows}</tbody></table></div>'
        )
    if not isinstance(data, Sequence) or isinstance(data, (str, bytes)):
        return ""

    points = [item for item in data if isinstance(item, Mapping)]
    numeric = []
    for item in points:
        value = item.get("value", item.get("cluster_size"))
        if isinstance(value, (int, float)):
            numeric.append(float(value))
    maximum = max(numeric, default=0.0)
    bars = []
    for item in points:
        label = item.get("label", item.get("cluster_id", "Value"))
        value = item.get("value", item.get("cluster_size"))
        numeric_value = float(value) if isinstance(value, (int, float)) else 0.0
        if chart.get("type") == "percentage_bars":
            width = max(0.0, min(100.0, numeric_value))
        else:
            width = (numeric_value / maximum * 100.0) if maximum else 0.0
        bars.append(
            '<div class="chart-row">'
            f'<div class="chart-label">{_text(label)}</div>'
            f'<div class="chart-track"><span style="width:{width:.4f}%"></span></div>'
            f'<div class="chart-value">{_text(value)}</div>'
            "</div>"
        )
    return f'<div class="chart"><h4>{title}</h4>{"".join(bars)}</div>'


def _render_table(table: Mapping[str, Any]) -> str:
    columns = list(table.get("columns") or [])
    rows = list(table.get("rows") or [])
    headers = "".join(
        f"<th>{_text(str(column).replace('_', ' ').title())}</th>"
        for column in columns
    )
    body = "".join(
        "<tr>"
        + "".join(f"<td>{_text(row.get(column))}</td>" for column in columns)
        + "</tr>"
        for row in rows
    )
    empty = (
        f'<tr><td colspan="{max(1, len(columns))}" class="empty">No rows available.</td></tr>'
        if not rows
        else ""
    )
    return (
        '<div class="table-block">'
        f'<h3>{_text(table.get("title"))}</h3>'
        '<div class="table-scroll"><table>'
        f"<thead><tr>{headers}</tr></thead><tbody>{body}{empty}</tbody>"
        "</table></div></div>"
    )


def export_html(presentation: Mapping[str, Any]) -> bytes:
    """Return a complete offline HTML report."""
    provenance = presentation.get("provenance") or {}
    validation = presentation.get("validation") or {}
    sections_html = []
    for section in presentation.get("sections") or []:
        kpis = "".join(
            '<div class="kpi">'
            f'<span>{_text(item.get("label"))}</span>'
            f'<strong>{_text(item.get("display"))}</strong>'
            "</div>"
            for item in section.get("kpis") or []
        )
        warnings = "".join(
            f'<div class="warning">{_text(message)}</div>'
            for message in section.get("messages") or []
        )
        charts = "".join(
            _render_chart(chart) for chart in section.get("charts") or []
        )
        tables = "".join(
            _render_table(table) for table in section.get("tables") or []
        )
        status = str(section.get("status") or "Missing")
        sections_html.append(
            f'<section id="{_text(section.get("id"))}">'
            '<div class="section-heading">'
            f'<h2>{_text(section.get("title"))}</h2>'
            f'<span class="status status-{escape(status.lower())}">{_text(status)}</span>'
            "</div>"
            f'<div class="kpi-grid">{kpis}</div>{warnings}{charts}{tables}'
            "</section>"
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pattern Quality Report</title>
  <style>
    :root {{ color-scheme: light; --ink:#172033; --muted:#667085; --line:#d8dee8; --panel:#f7f9fc; --accent:#2563eb; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:14px/1.45 Arial, sans-serif; color:var(--ink); background:#fff; }}
    main {{ max-width:1200px; margin:0 auto; padding:32px; }}
    header {{ border-bottom:3px solid var(--accent); padding-bottom:20px; margin-bottom:24px; }}
    h1 {{ margin:0 0 8px; font-size:30px; }}
    h2 {{ margin:0; font-size:20px; }}
    h3 {{ margin:18px 0 8px; font-size:14px; }}
    h4 {{ margin:0 0 10px; font-size:13px; }}
    .meta {{ display:grid; grid-template-columns:180px 1fr; gap:6px 12px; color:var(--muted); }}
    .meta code {{ color:var(--ink); overflow-wrap:anywhere; }}
    section {{ break-inside:avoid-page; margin:0 0 22px; padding:18px; border:1px solid var(--line); border-radius:10px; }}
    .section-heading {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:14px; }}
    .status {{ padding:3px 9px; border-radius:999px; background:#eef2f7; font-size:11px; font-weight:700; text-transform:uppercase; }}
    .status-available,.status-passed {{ color:#176b3a; background:#e8f7ee; }}
    .status-partial,.status-warning {{ color:#8a5700; background:#fff4d6; }}
    .status-missing {{ color:#a12a2a; background:#feecec; }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; }}
    .kpi {{ padding:10px 12px; border-radius:8px; background:var(--panel); }}
    .kpi span {{ display:block; color:var(--muted); font-size:10px; letter-spacing:.04em; text-transform:uppercase; }}
    .kpi strong {{ display:block; margin-top:4px; overflow-wrap:anywhere; }}
    .warning {{ margin:10px 0; padding:9px 11px; border-left:3px solid #d99a00; background:#fff8e6; }}
    .table-scroll {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:11px; }}
    th,td {{ padding:7px 8px; border:1px solid var(--line); text-align:left; vertical-align:top; overflow-wrap:anywhere; }}
    th {{ background:#eef2f7; }}
    .empty {{ text-align:center; color:var(--muted); }}
    .chart {{ margin-top:14px; padding:12px; border:1px solid var(--line); border-radius:8px; }}
    .chart-row {{ display:grid; grid-template-columns:150px 1fr 90px; gap:8px; align-items:center; margin:7px 0; }}
    .chart-label {{ overflow-wrap:anywhere; }}
    .chart-track {{ height:12px; border-radius:6px; background:#edf1f7; overflow:hidden; }}
    .chart-track span {{ display:block; height:100%; background:var(--accent); }}
    .chart-value {{ text-align:right; font-variant-numeric:tabular-nums; }}
    .compact {{ max-width:600px; }}
    footer {{ margin-top:30px; padding-top:14px; border-top:1px solid var(--line); color:var(--muted); font-size:11px; }}
    @page {{ margin:16mm; }}
    @media print {{ main {{ max-width:none; padding:0; }} section {{ break-inside:auto; }} .table-scroll {{ overflow:visible; }} }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Pattern Quality Report</h1>
    <div class="meta">
      <span>Generation timestamp</span><strong>{_text(provenance.get("generation_timestamp"))}</strong>
      <span>Model hash</span><code>{_text(provenance.get("model_hash"))}</code>
      <span>Validation status</span><strong>{_text(validation.get("status"))}</strong>
    </div>
  </header>
  {"".join(sections_html)}
  <footer>
    Generated from {_text(presentation.get("source_artifact"))}. Model hash:
    {_text(provenance.get("model_hash"))}. Standalone offline report.
  </footer>
</main>
</body>
</html>
"""
    return document.encode("utf-8")
