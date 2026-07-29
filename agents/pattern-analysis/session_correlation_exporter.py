"""Analysis Session outcome correlation.

Builds a session-native projection from preserved execution records. This module
never reads, writes, or invokes PA-FR-009 artifacts or legacy correlation code.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Iterable, List, Tuple, Optional

from analysis_session import SESSION_GENERATED_BY
from robustness_config import lot_from_relpath


def source_lot(
    row: Dict[str, Any],
    robustness_cfg: Optional[object] = None,
) -> str:
    relpath = str(row.get("source_log_relpath") or row.get("source_log") or "")
    return lot_from_relpath(relpath, config=robustness_cfg)


def _key(row: Dict[str, Any]) -> Tuple[str, str]:
    return str(row.get("pattern_id") or ""), str(row.get("scan_chain_id") or "")


def _round_percent(value: float) -> float:
    return round(float(value), 2)


def build_session_correlation_analytics(
    outcomes: Iterable[Dict[str, Any]],
    *,
    top_n: int = 10,
    robustness_cfg: Optional[object] = None,
) -> Dict[str, Any]:
    """Build bounded dashboard aggregates without returning execution histories."""
    rows = [row for row in outcomes if isinstance(row, dict)]
    latest = {"PASS": 0, "FAIL": 0, "Unknown": 0}
    chain_failures: Dict[str, int] = defaultdict(int)
    quality_counts: Dict[str, int] = defaultdict(int)
    clean_count = 0

    for row in rows:
        result = str(row.get("latest_result") or "").upper()
        latest[result if result in ("PASS", "FAIL") else "Unknown"] += 1
        chain_failures[str(row.get("scan_chain_id") or "")] += int(
            row.get("fail_count") or 0
        )
        flags = list(row.get("data_quality_flags") or [])
        if flags:
            for flag in flags:
                quality_counts[str(flag)] += 1
        else:
            clean_count += 1
    quality_counts["NO_FLAGS"] = clean_count

    bounded_top_n = max(1, min(int(top_n or 10), 100))
    top_chains = [
        {"scan_chain_id": chain_id, "fail_count": fail_count}
        for chain_id, fail_count in sorted(
            chain_failures.items(), key=lambda item: (-item[1], item[0])
        )
        if fail_count > 0
    ][:bounded_top_n]
    top_patterns = [
        {
            "pattern_id": str(row.get("pattern_id") or ""),
            "scan_chain_id": str(row.get("scan_chain_id") or ""),
            "fail_count": int(row.get("fail_count") or 0),
        }
        for row in sorted(
            rows,
            key=lambda item: (
                -int(item.get("fail_count") or 0),
                str(item.get("pattern_id") or ""),
                str(item.get("scan_chain_id") or ""),
            ),
        )
        if int(row.get("fail_count") or 0) > 0
    ][:bounded_top_n]

    total = len(rows)
    issue_count = total - clean_count
    health = {
        "pass_rate": _round_percent(latest["PASS"] / total * 100) if total else 0,
        "fail_rate": _round_percent(latest["FAIL"] / total * 100) if total else 0,
        "unknown_rate": _round_percent(latest["Unknown"] / total * 100) if total else 0,
        "issues_rate": _round_percent(issue_count / total * 100) if total else 0,
        "clean_rate": _round_percent(clean_count / total * 100) if total else 0,
        "total": total,
    }
    total_fail_events = sum(int(row.get("fail_count") or 0) for row in rows)
    top_fail_events = sum(item["fail_count"] for item in top_chains)
    duplicate_count = quality_counts.get("DUPLICATE_HISTORY", 0)
    insights = [f"{health['pass_rate']}% of correlated rows passed."]
    if total_fail_events and top_chains:
        insights.append(
            f"{top_chains[0]['scan_chain_id']} has the highest FAIL count."
        )
    insights.append(
        "No duplicate history records detected."
        if duplicate_count == 0
        else f"{duplicate_count} duplicate history record(s) detected."
    )
    insights.append(f"Only {health['issues_rate']}% of rows contain quality issues.")
    top_share = (
        _round_percent(top_fail_events / total_fail_events * 100)
        if total_fail_events
        else 0
    )
    insights.append(
        f"Top {bounded_top_n} scan chains contribute {top_share}% of all FAIL events."
    )
    return {
        "pass_fail_distribution": latest,
        "health": health,
        "top_failing_scan_chains": top_chains,
        "top_failing_patterns": top_patterns,
        "data_quality_overview": [
            {"label": label, "value": value}
            for label, value in sorted(
                quality_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        "total_fail_events": total_fail_events,
        "insights": insights,
    }


def build_session_correlation(
    executions: Iterable[Dict[str, Any]],
    *,
    session_hash: str | None = None,
    robustness_cfg: Optional[object] = None,
) -> Dict[str, Any]:
    """Aggregate every execution by pattern and scan chain with full provenance."""
    rows = [dict(row) for row in executions if isinstance(row, dict)]
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    lots = set()
    for row in rows:
        grouped[_key(row)].append(row)
        lots.add(source_lot(row, robustness_cfg=robustness_cfg))

    outcomes: List[Dict[str, Any]] = []
    for (pattern_id, scan_chain_id), members in sorted(grouped.items()):
        members.sort(
            key=lambda row: (
                int(row.get("run_id") or 0),
                str(row.get("source_log_relpath") or row.get("source_log") or ""),
            )
        )
        history = []
        record_lots = set()
        for row in members:
            lot = source_lot(row, robustness_cfg=robustness_cfg)
            record_lots.add(lot)
            history.append(
                {
                    "run_id": int(row.get("run_id") or 0),
                    "result": str(row.get("latest_result") or "UNKNOWN").upper(),
                    "source_log": row.get("source_log"),
                    "source_log_relpath": row.get("source_log_relpath"),
                    "source_lot": lot,
                    "toggle_count": row.get("toggle_count"),
                    "toggle_coverage_pct": row.get("toggle_coverage_pct"),
                    "toggle_density_pct": row.get("toggle_density_pct"),
                }
            )
        pass_count = sum(item["result"] == "PASS" for item in history)
        fail_count = sum(item["result"] == "FAIL" for item in history)
        unknown_count = len(history) - pass_count - fail_count
        latest_result = history[-1]["result"] if history else None
        outcomes.append(
            {
                "pattern_id": pattern_id,
                "scan_chain_id": scan_chain_id,
                "history": history,
                "latest_result": latest_result,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "unknown_count": unknown_count,
                "execution_count": len(history),
                "source_lots": sorted(record_lots),
                "lot_count": len(record_lots),
                "cross_lot": len(record_lots) > 1,
                "data_quality_flags": [] if history else ["NO_EXECUTIONS"],
            }
        )

    pass_total = sum(row["pass_count"] for row in outcomes)
    fail_total = sum(row["fail_count"] for row in outcomes)
    unknown_total = sum(row["unknown_count"] for row in outcomes)
    return {
        "generated_by": SESSION_GENERATED_BY,
        "correlation_version": "session-1.0",
        "session_hash": session_hash,
        "available": bool(outcomes),
        "execution_count": len(rows),
        "outcome_count": len(outcomes),
        "unique_patterns": len({row["pattern_id"] for row in outcomes}),
        "lot_count": len(lots),
        "lots": sorted(lots),
        "pass_count": pass_total,
        "fail_count": fail_total,
        "unknown_count": unknown_total,
        "cross_lot_outcomes": sum(bool(row["cross_lot"]) for row in outcomes),
        "validation_status": "PASSED" if outcomes else "EMPTY",
        "outcomes": outcomes,
    }
