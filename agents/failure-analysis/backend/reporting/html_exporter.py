"""Standalone HTML export for FA-FR-010 engineering reports."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def export_html_report(
    *,
    report_id: str,
    summaries: dict[str, Any],
    html_rendered: str | None,
    output_dir: Path,
) -> tuple[Path, float]:
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_id}.html"

    if html_rendered:
        content = html_rendered
    else:
        content = _fallback_html(report_id, summaries)

    path.write_text(content, encoding="utf-8")
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return path, elapsed_ms


def _fallback_html(report_id: str, summaries: dict[str, Any]) -> str:
    meta = summaries.get("metadata", {})
    exec_sum = summaries.get("executive_summary", {})
    title = meta.get("report_title", "Failure Analysis Report")
    headline = exec_sum.get("headline", "")
    observations = summaries.get("engineering_observations", [])
    obs_html = "".join(f"<li>{obs}</li>" for obs in observations[:20])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 2rem; color: #1a1a1a; }}
    h1 {{ color: #0f3d5c; }}
    .meta {{ color: #555; margin-bottom: 1.5rem; }}
    section {{ margin-bottom: 1.5rem; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">
    <div>Report ID: {report_id}</div>
    <div>Generated: {meta.get("generated_at", "")}</div>
    <div>Upload: {meta.get("original_filename", "")}</div>
  </div>
  <section>
    <h2>Executive Summary</h2>
    <p>{headline}</p>
    <p>Yield: {exec_sum.get("overall_yield_pct", "N/A")}%</p>
  </section>
  <section>
    <h2>Engineering Observations</h2>
    <ul>{obs_html}</ul>
  </section>
</body>
</html>"""
