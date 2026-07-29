"""CSV export for FA-FR-010 engineering reports."""

from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Any


def export_csv_report(
    *,
    report_id: str,
    summaries: dict[str, Any],
    dashboard: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, float]:
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_id}.csv"

    rows: list[list[str]] = []
    rows.append(["section", "key", "value"])
    meta = summaries.get("metadata", {})
    for key, value in meta.items():
        rows.append(["metadata", key, str(value)])

    exec_sum = summaries.get("executive_summary", {})
    for key, value in exec_sum.items():
        if not isinstance(value, (dict, list)):
            rows.append(["executive_summary", key, str(value)])

    for mode in summaries.get("top_failure_modes", [])[:50]:
        rows.append(
            [
                "top_failure_modes",
                str(mode.get("fault_category", "")),
                str(mode.get("count", "")),
            ]
        )

    for rec in summaries.get("engineering_recommendations", summaries.get("recommended_corrective_actions", []))[:50]:
        rows.append(
            [
                "recommendations",
                str(rec.get("priority", rec.get("recommendation_code", ""))),
                str(rec.get("action", rec.get("recommendation", ""))),
            ]
        )

    benchmark = summaries.get("benchmark_summary", {})
    for key, value in benchmark.items():
        if not isinstance(value, (dict, list)):
            rows.append(["benchmark_summary", key, str(value)])

    for card in dashboard.get("summary_cards", []):
        rows.append(["dashboard_card", str(card.get("label", "")), str(card.get("value", ""))])

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return path, elapsed_ms
