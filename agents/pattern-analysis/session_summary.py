"""
Session summary derivation — computed only from preserved execution records.

Summary metrics are config-driven; no hardcoded aggregation in engines.
"""
from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List, Sequence

from session_config import SessionConfig, load_session_config


def _pattern_chain_key(pattern_id: str, scan_chain_id: str) -> str:
    return f"{pattern_id}|{scan_chain_id}"


def _round_metric(value: float, places: int = 4) -> float:
    return round(float(value), places)


def derive_session_summary(
    executions: Sequence[Dict[str, Any]],
    config: SessionConfig | None = None,
) -> Dict[str, Any]:
    """
    Build derived session summaries from execution records.

    Executions are never modified or discarded; this produces a separate view only.
    """
    config = config or SessionConfig()
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for record in executions:
        key = _pattern_chain_key(
            str(record.get("pattern_id", "")),
            str(record.get("scan_chain_id", "")),
        )
        grouped.setdefault(key, []).append(record)

    by_pattern_chain: Dict[str, Dict[str, Any]] = {}
    for key, rows in sorted(grouped.items()):
        coverages = [float(row["toggle_coverage_pct"]) for row in rows if row.get("toggle_coverage_pct") is not None]
        densities = [float(row["toggle_density_pct"]) for row in rows if row.get("toggle_density_pct") is not None]
        pass_count = sum(1 for row in rows if row.get("latest_result") == "PASS")
        fail_count = sum(1 for row in rows if row.get("latest_result") == "FAIL")

        metrics: Dict[str, Any] = {
            "execution_count": len(rows),
            "pass_count": pass_count,
            "fail_count": fail_count,
        }
        if coverages:
            metrics["toggle_coverage_pct_avg"] = _round_metric(mean(coverages))
            metrics["toggle_coverage_pct_max"] = _round_metric(max(coverages))
            metrics["toggle_coverage_pct_min"] = _round_metric(min(coverages))
        if densities:
            metrics["toggle_density_pct_avg"] = _round_metric(mean(densities))

        filtered = {
            metric: metrics[metric]
            for metric in config.pattern_chain_summary_metrics
            if metric in metrics
        }
        by_pattern_chain[key] = filtered

    return {
        "generated_by": "PA-Analysis-Session",
        "by_pattern_chain": by_pattern_chain,
        "execution_record_count": len(executions),
    }


def load_summary_from_config_path(config_path: str) -> SessionConfig:
    return load_session_config(config_path)
