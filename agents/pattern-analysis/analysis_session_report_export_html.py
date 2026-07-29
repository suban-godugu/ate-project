"""Standalone HTML exporter for PA-FR-010.AS Engineering Report."""
from __future__ import annotations

import json
from html import escape
from typing import Any, List, Mapping, Sequence

from analysis_session_report_explanations import (
    build_observation,
    get_chart_guide,
    get_kpi_tooltip,
    get_section_guide,
    get_table_guide,
)


def _format(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        text = f"{value:,.4f}".rstrip("0").rstrip(".")
        return text or "0"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, (list, tuple)):
        return ", ".join(_format(item) for item in value) or "—"
    if isinstance(value, Mapping):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def _text(value: Any) -> str:
    return escape(_format(value), quote=True)


def _paragraphs(text: str) -> str:
    if not text:
        return ""
    return "".join(
        f"<p>{_text(line)}</p>"
        for line in text.split("\n")
        if line.strip()
    )


def _max_numeric(values: Sequence[Any]) -> float:
    numbers: List[float] = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            continue
    return max(numbers) if numbers else 0.0


def _render_guide_block(title: str, body: str, *, css_class: str = "guide-block") -> str:
    if not body:
        return ""
    return (
        f'<div class="{css_class}">'
        f'<h3>{_text(title)}</h3>'
        f"{body}"
        "</div>"
    )


def _render_section_guide(section_id: str) -> str:
    guide = get_section_guide(section_id)
    if not guide:
        return ""
    blocks = ['<div class="report-guide">']
    if guide.get("description"):
        blocks.append(
            _render_guide_block("Description", f"<p>{_text(guide['description'])}</p>")
        )
    if guide.get("why_it_matters"):
        blocks.append(
            _render_guide_block(
                "Why It Matters",
                f"<p>{_text(guide['why_it_matters'])}</p>",
            )
        )
    if guide.get("formula"):
        blocks.append(
            _render_guide_block(
                "Formula / Logic",
                f'<pre class="guide-formula">{_text(guide["formula"])}</pre>',
            )
        )
    if guide.get("example"):
        blocks.append(
            '<div class="guide-example">'
            '<span class="guide-example-badge">Educational Example</span>'
            f"{_paragraphs(guide['example'])}"
            "</div>"
        )
    if guide.get("interpretation"):
        blocks.append(
            _render_guide_block(
                "Interpretation",
                f"<p>{_text(guide['interpretation'])}</p>",
            )
        )
    if guide.get("info_card"):
        blocks.append(
            f'<div class="info-card"><p>{_text(guide["info_card"])}</p></div>'
        )
    blocks.append("</div>")
    return "".join(blocks)


def _render_chart_guide(chart_title: str) -> str:
    guide = get_chart_guide(chart_title)
    if not guide:
        return ""
    parts = ['<div class="chart-guide">']
    if guide.get("description"):
        parts.append(f"<p><strong>What this shows:</strong> {_text(guide['description'])}</p>")
    if guide.get("how_to_read"):
        parts.append(f"<p><strong>How to read:</strong> {_text(guide['how_to_read'])}</p>")
    if guide.get("example"):
        parts.append(f'<p class="guide-example-inline">{_text(guide["example"])}</p>')
    parts.append("</div>")
    return "".join(parts)


def _render_table_guide(table: Mapping[str, Any]) -> str:
    title = str(table.get("title") or "")
    guide = get_table_guide(title)
    if not guide:
        return ""
    parts = ['<div class="table-guide">']
    if guide.get("description"):
        parts.append(f"<p>{_text(guide['description'])}</p>")
    columns = guide.get("columns")
    if isinstance(columns, Mapping) and columns:
        items = "".join(
            f"<li><strong>{_text(col)}</strong> — {_text(desc)}</li>"
            for col, desc in columns.items()
        )
        parts.append(f"<p><strong>Columns:</strong></p><ul>{items}</ul>")
    if guide.get("example_row"):
        parts.append(
            f'<p class="guide-example-inline">{_text(guide["example_row"])}</p>'
        )
    parts.append("</div>")
    return "".join(parts)


def _render_observation_block(section_id: str, section: Mapping[str, Any]) -> str:
    observation = build_observation(
        section_id,
        section.get("kpis") or [],
        section.get("tables") or [],
    )
    if not observation:
        return ""
    return (
        '<div class="guide-observation">'
        "<h3>Key Observation</h3>"
        f"<p>{_text(observation)}</p>"
        "</div>"
    )


def _render_chart(chart: Mapping[str, Any]) -> str:
    raw_title = str(chart.get("title") or "")
    title = _text(raw_title)
    guide = _render_chart_guide(raw_title)
    data = chart.get("data")
    if not isinstance(data, list) or not data:
        return guide
    peak = _max_numeric(
        [
            item.get("value") if isinstance(item, Mapping) else None
            for item in data
        ]
        + [
            item.get("count") if isinstance(item, Mapping) else None
            for item in data
        ]
    )
    rows = []
    for item in data:
        if not isinstance(item, Mapping):
            continue
        label = item.get("label")
        value = item.get("value")
        if value is None:
            value = item.get("count")
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        width = (numeric / peak * 100.0) if peak > 0 else 0.0
        rows.append(
            '<div class="chart-row">'
            f'<div class="chart-label">{_text(label)}</div>'
            f'<div class="chart-track"><span style="width:{width:.4f}%"></span></div>'
            f'<div class="chart-value">{_text(value)}</div>'
            "</div>"
        )
    if not rows:
        return guide
    return (
        f"{guide}"
        f'<div class="chart"><h4>{title}</h4>{"".join(rows)}</div>'
    )


def _render_table(table: Mapping[str, Any]) -> str:
    guide = _render_table_guide(table)
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
    if not rows:
        body = (
            f'<tr><td colspan="{max(1, len(columns))}" class="empty">'
            "No rows available.</td></tr>"
        )
    note = ""
    if table.get("truncated") or (
        table.get("total_rows") and table.get("displayed_rows") != table.get("total_rows")
    ):
        note = (
            f'<p class="table-note">Showing {_text(table.get("displayed_rows"))} of '
            f'{_text(table.get("total_rows"))} rows. Full data remains in session artifacts.</p>'
        )
    elif rows:
        note = (
            '<p class="table-note">Top results for readability. '
            "Full datasets remain in PA-Analysis-Session_*.json.</p>"
        )
    return (
        f"{guide}"
        '<div class="table-block">'
        f'<h3>{_text(table.get("title"))}</h3>'
        f"{note}"
        '<div class="table-scroll"><table>'
        f"<thead><tr>{headers}</tr></thead><tbody>{body}</tbody>"
        "</table></div></div>"
    )


def _render_kpi_grid(kpis: Sequence[Mapping[str, Any]]) -> str:
    items = []
    for item in kpis:
        if not isinstance(item, Mapping):
            continue
        label = str(item.get("label") or "")
        tooltip = get_kpi_tooltip(label)
        title_attr = f' title="{_text(tooltip)}"' if tooltip else ""
        items.append(
            '<div class="kpi">'
            f"<span{title_attr}>{_text(label)}</span>"
            f'<strong>{_text(item.get("display"))}</strong>'
            "</div>"
        )
    return f'<div class="kpi-grid">{"".join(items)}</div>'


def export_analysis_session_html(projection: Mapping[str, Any]) -> bytes:
    """Return a deterministic standalone UTF-8 Engineering Report."""
    provenance = projection.get("provenance") or {}
    validation = projection.get("validation") or {}
    metadata = projection.get("metadata") or {}
    title = projection.get("report_title") or "Semiconductor Pattern Analysis Engineering Report"
    subtitle = (
        projection.get("report_subtitle")
        or "Deterministic Engineering Analysis · Analysis Session Report"
    )
    badge = projection.get("engineering_status") or validation.get("status") or "—"

    toc_items = []
    sections_html = []
    for section in projection.get("sections") or []:
        section_id = str(section.get("id") or "")
        toc_items.append(
            f'<li><a href="#{_text(section_id)}">{_text(section.get("title"))}</a></li>'
        )
        purpose = section.get("purpose") or ""
        summary = section.get("summary") or ""
        findings = "".join(
            f"<li>{_text(item)}</li>" for item in (section.get("findings") or [])
        )
        findings_block = (
            f'<div class="findings"><h3>Engineering Findings</h3><ul>{findings}</ul></div>'
            if findings
            else ""
        )
        purpose_block = (
            f'<div class="narrative"><h3>Purpose</h3><p>{_text(purpose)}</p></div>'
            if purpose
            else ""
        )
        summary_block = (
            f'<div class="narrative"><h3>Summary</h3><p>{_text(summary)}</p></div>'
            if summary
            else ""
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
        is_appendix = section_id == "appendix"
        open_tag = (
            f'<details class="appendix" id="{_text(section_id)}">'
            if is_appendix
            else f'<section id="{_text(section_id)}">'
        )
        close_tag = "</details>" if is_appendix else "</section>"
        heading = (
            f"<summary><span>{_text(section.get('title'))}</span>"
            f'<span class="status status-{escape(status.lower())}">{_text(status)}</span></summary>'
            if is_appendix
            else (
                '<div class="section-heading">'
                f'<h2>{_text(section.get("title"))}</h2>'
                f'<span class="status status-{escape(status.lower())}">{_text(status)}</span>'
                "</div>"
            )
        )
        sections_html.append(
            f"{open_tag}{heading}"
            f"{_render_section_guide(section_id)}"
            f"{purpose_block}{summary_block}"
            '<h3 class="actual-results-heading">Actual Project Result</h3>'
            f"{_render_kpi_grid(section.get('kpis') or [])}"
            f"{charts}{findings_block}{warnings}{tables}"
            f"{_render_observation_block(section_id, section)}"
            f"{close_tag}"
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_text(title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink:#102033;
      --muted:#5b6b7c;
      --line:#d7deea;
      --panel:#f4f7fb;
      --accent:#0f4c81;
      --accent-soft:#e7f0f8;
      --good:#176b3a;
      --warn:#8a5700;
      --bad:#a12a2a;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:15px/1.5 "Segoe UI",Arial,sans-serif; color:var(--ink); background:#eef2f7; }}
    .layout {{ display:grid; grid-template-columns:240px minmax(0,1fr); gap:0; min-height:100vh; }}
    nav {{ position:sticky; top:0; align-self:start; height:100vh; overflow:auto; padding:24px 18px; background:#0f4c81; color:#fff; }}
    nav h1 {{ font-size:14px; margin:0 0 8px; letter-spacing:.04em; text-transform:uppercase; opacity:.85; }}
    nav ol {{ list-style:none; margin:0; padding:0; counter-reset:toc; }}
    nav ol li {{ display:flex; gap:10px; align-items:flex-start; margin:6px 0; }}
    nav ol li::before {{
      content: counter(toc) ".";
      counter-increment: toc;
      min-width: 1.75rem;
      text-align: right;
      font-variant-numeric: tabular-nums;
      flex-shrink: 0;
      opacity: 0.9;
    }}
    nav a {{ color:#d7e8f7; text-decoration:none; margin:0; line-height:1.35; }}
    nav a:hover {{ color:#fff; text-decoration:underline; }}
    main {{ padding:28px 32px 48px; }}
    .cover {{ background:linear-gradient(160deg,#0f4c81 0%,#1b6ca8 55%,#2f86c3 100%); color:#fff; border-radius:16px; padding:36px 32px; margin-bottom:22px; box-shadow:0 10px 30px rgba(15,76,129,.22); }}
    .cover h1 {{ margin:0 0 8px; font-size:34px; line-height:1.15; }}
    .cover .subtitle {{ margin:0 0 18px; font-size:16px; opacity:.92; }}
    .badge {{ display:inline-block; padding:8px 14px; border-radius:999px; background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.35); font-weight:700; letter-spacing:.04em; }}
    .meta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; margin-top:18px; }}
    .meta div {{ background:rgba(255,255,255,.12); border-radius:10px; padding:10px 12px; }}
    .meta span {{ display:block; font-size:11px; opacity:.8; text-transform:uppercase; letter-spacing:.04em; }}
    .meta strong, .meta code {{ display:block; margin-top:4px; overflow-wrap:anywhere; }}
    section, details.appendix {{ break-inside:avoid-page; margin:0 0 18px; padding:20px; border:1px solid var(--line); border-radius:14px; background:#fff; box-shadow:0 1px 2px rgba(16,32,51,.04); }}
    details.appendix summary {{ cursor:pointer; list-style:none; display:flex; justify-content:space-between; align-items:center; gap:12px; font-size:20px; font-weight:700; }}
    .section-heading {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-bottom:12px; }}
    h2 {{ margin:0; font-size:22px; }}
    h3 {{ margin:16px 0 8px; font-size:13px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }}
    h4 {{ margin:0 0 10px; font-size:14px; }}
    .status {{ padding:4px 10px; border-radius:999px; background:#eef2f7; font-size:11px; font-weight:700; text-transform:uppercase; white-space:nowrap; }}
    .status-complete {{ color:var(--good); background:#e8f7ee; }}
    .status-partial {{ color:var(--warn); background:#fff4d6; }}
    .status-missing {{ color:var(--bad); background:#feecec; }}
    .narrative p {{ margin:0; color:var(--ink); }}
    .report-guide {{ margin:0 0 14px; padding:14px; border:1px solid var(--line); border-radius:12px; background:#fcfdff; break-inside:avoid-page; }}
    .report-guide .guide-block {{ margin:0 0 10px; }}
    .report-guide .guide-block:last-child {{ margin-bottom:0; }}
    .report-guide .guide-block p {{ margin:0; color:var(--ink); font-size:14px; line-height:1.55; }}
    .report-guide h3 {{ margin:0 0 4px; font-size:11px; }}
    .guide-formula {{ margin:0; padding:10px 12px; border-radius:8px; background:var(--panel); border:1px solid var(--line); font:12px/1.5 Consolas,"Courier New",monospace; white-space:pre-wrap; color:var(--ink); overflow-x:auto; }}
    .guide-example {{ margin:10px 0 0; padding:10px 12px; border-radius:8px; border:1px dashed var(--accent); background:var(--accent-soft); }}
    .guide-example p {{ margin:4px 0 0; font-size:13px; color:var(--ink); }}
    .guide-example-badge {{ display:inline-block; padding:2px 8px; border-radius:4px; background:var(--accent); color:#fff; font-size:10px; font-weight:700; letter-spacing:.04em; text-transform:uppercase; }}
    .guide-example-inline {{ font-size:12px; color:var(--muted); font-style:italic; }}
    .info-card {{ margin:10px 0 0; padding:10px 12px; border-radius:8px; border-left:3px solid var(--accent); background:var(--panel); }}
    .info-card p {{ margin:0; font-size:13px; color:var(--ink); }}
    .actual-results-heading {{ margin-top:18px; padding-top:12px; border-top:1px solid var(--line); }}
    .guide-observation {{ margin-top:14px; padding:12px 14px; border-radius:10px; background:#f0f6fc; border:1px solid var(--line); break-inside:avoid-page; }}
    .guide-observation p {{ margin:0; font-size:14px; color:var(--ink); }}
    .chart-guide, .table-guide {{ margin:12px 0 6px; padding:10px 12px; border-radius:8px; background:var(--panel); border:1px solid var(--line); font-size:13px; }}
    .chart-guide p, .table-guide p {{ margin:0 0 6px; }}
    .chart-guide p:last-child, .table-guide p:last-child {{ margin-bottom:0; }}
    .table-guide ul {{ margin:4px 0 6px; padding-left:18px; font-size:12px; }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-top:12px; }}
    .kpi {{ padding:12px 14px; border-radius:12px; background:var(--panel); border:1px solid var(--line); }}
    .kpi span {{ display:block; color:var(--muted); font-size:10px; letter-spacing:.05em; text-transform:uppercase; font-weight:700; cursor:help; }}
    .kpi strong {{ display:block; margin-top:6px; font-size:22px; line-height:1.15; overflow-wrap:anywhere; }}
    .findings ul {{ margin:0; padding-left:18px; }}
    .warning {{ margin:10px 0; padding:9px 11px; border-left:3px solid #d99a00; background:#fff8e6; }}
    .chart {{ margin-top:14px; padding:14px; border:1px solid var(--line); border-radius:12px; background:#fcfdff; }}
    .chart-row {{ display:grid; grid-template-columns:160px 1fr 90px; gap:8px; align-items:center; margin:7px 0; }}
    .chart-label {{ overflow-wrap:anywhere; font-size:12px; }}
    .chart-track {{ height:12px; border-radius:6px; background:#edf1f7; overflow:hidden; }}
    .chart-track span {{ display:block; height:100%; background:var(--accent); }}
    .chart-value {{ text-align:right; font-variant-numeric:tabular-nums; font-size:12px; }}
    .table-note {{ margin:0 0 8px; color:var(--muted); font-size:12px; }}
    .table-scroll {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; table-layout:auto; }}
    th,td {{ padding:8px 9px; border:1px solid var(--line); text-align:left; vertical-align:top; word-break:normal; overflow-wrap:break-word; }}
    th {{ background:var(--accent-soft); position:sticky; top:0; white-space:nowrap; }}
    td {{ max-width:36rem; }}
    tbody tr:nth-child(even) {{ background:#fafbfd; }}
    .empty {{ text-align:center; color:var(--muted); }}
    footer {{ margin-top:24px; padding-top:14px; border-top:1px solid var(--line); color:var(--muted); font-size:12px; }}
    @page {{ margin:14mm; }}
    @media (max-width:960px) {{
      .layout {{ grid-template-columns:1fr; }}
      nav {{ position:relative; height:auto; }}
    }}
    @media print {{
      body {{ background:#fff; }}
      .layout {{ display:block; }}
      nav {{ display:none; }}
      main {{ padding:0; }}
      section, details.appendix {{ break-inside:auto; box-shadow:none; }}
      .table-scroll {{ overflow:visible; }}
    }}
  </style>
</head>
<body>
<div class="layout">
  <nav>
    <h1>Contents</h1>
    <ol>{"".join(toc_items)}</ol>
  </nav>
  <main>
    <header class="cover">
      <h1>{_text(title)}</h1>
      <p class="subtitle">{_text(subtitle)}</p>
      <div class="badge">{_text(badge)}</div>
      <div class="meta">
        <div><span>STIL</span><strong>{_text(metadata.get("stil_filename"))}</strong></div>
        <div><span>Generated</span><strong>{_text(provenance.get("generation_timestamp"))}</strong></div>
        <div><span>LOTs</span><strong>{_text(metadata.get("lot_count"))}</strong></div>
        <div><span>ATE Logs</span><strong>{_text(metadata.get("ate_log_count"))}</strong></div>
        <div><span>Session Hash</span><code>{_text(provenance.get("model_hash") and metadata.get("session_hash") or metadata.get("session_hash"))}</code></div>
        <div><span>Validation</span><strong>{_text(validation.get("status"))}</strong></div>
      </div>
    </header>
    {"".join(sections_html)}
    <footer>
      Generated from {_text(projection.get("source_artifact"))}.
      Model hash: {_text(provenance.get("model_hash"))}.
      Presentation-only Engineering Report — no recalculation of deterministic artifacts.
    </footer>
  </main>
</div>
</body>
</html>
"""
    return document.encode("utf-8")
