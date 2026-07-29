"""JSON export for engineering reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_json_report(
    *,
    report_id: str,
    summaries: dict[str, Any],
    dashboard: dict[str, Any],
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
    export_meta: dict[str, Any],
    output_dir: Path,
) -> tuple[Path, float]:
    """Write full structured JSON export and return path + size_kb."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{report_id}.json"

    payload = {
        "report_id": report_id,
        "export_format": "json",
        "export_metadata": export_meta,
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
        "lot_summary": summaries.get("lot_summary", []),
        "wafer_summary": summaries.get("wafer_summary", []),
        "die_summary": summaries.get("die_summary", {}),
        "recommended_corrective_actions": summaries.get("recommended_corrective_actions", []),
        "requirement_traceability": summaries.get("requirement_traceability", {}),
        "dashboard_dataset": dashboard,
        "analysis_core": _trim_analysis(analysis),
        "module_outputs": _trim_module_outputs(module_outputs),
    }

    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    size_kb = round(path.stat().st_size / 1024, 2)
    return path, size_kb


def _trim_analysis(analysis: dict[str, Any]) -> dict[str, Any]:
    """Keep JSON export focused — omit very large nested arrays."""
    trimmed = dict(analysis)
    for key in ("failing_patterns",):
        if key in trimmed and isinstance(trimmed[key], list) and len(trimmed[key]) > 100:
            trimmed[key] = trimmed[key][:100]
            trimmed[f"{key}_truncated"] = True
    return trimmed


def _trim_module_outputs(module_outputs: dict[str, Any]) -> dict[str, Any]:
    trimmed: dict[str, Any] = {}
    for key, value in module_outputs.items():
        if isinstance(value, dict):
            copy = dict(value)
            for large_key in ("wafer_heatmap", "legacy_report", "predictions"):
                if large_key in copy and isinstance(copy[large_key], list):
                    if len(copy[large_key]) > 50:
                        copy[large_key] = copy[large_key][:50]
                        copy[f"{large_key}_truncated"] = True
            trimmed[key] = copy
        else:
            trimmed[key] = value
    return trimmed
