"""
Session execution normalizer — builds per-execution records from multiple ATE logs.

Uses locked single-file engines in-memory only (ATEParser, CoverageCalculator).
Does not write or modify any PA-FR-004 output artifacts.

E0: prefer a shared SessionLogEntry cache so each log is parsed once per session.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from session_log_cache import SessionLogEntry, build_session_log_cache


def _execution_sort_key(record: Dict[str, Any]) -> Tuple[str, str, int]:
    return (
        str(record.get("pattern_id", "")),
        str(record.get("scan_chain_id", "")),
        int(record.get("run_id", 0)),
    )


def _status_lookup(ate_data: Dict[str, Dict[str, Dict[str, str]]]) -> Dict[Tuple[str, str], str]:
    lookup: Dict[Tuple[str, str], str] = {}
    for pattern_id, chains in ate_data.items():
        for scan_chain_id, payload in chains.items():
            lookup[(str(pattern_id), str(scan_chain_id))] = payload.get("status", "FAIL")
    return lookup


def _executions_from_log_entries(log_entries: Sequence[SessionLogEntry]) -> List[Dict[str, Any]]:
    executions: List[Dict[str, Any]] = []
    run_id = 1

    for entry in log_entries:
        status_by_key = _status_lookup(entry.ate_data)
        chain_rows = sorted(
            entry.coverage.get("scan_chain_level") or [],
            key=lambda row: (str(row.get("pattern_id", "")), str(row.get("scan_chain_id", ""))),
        )
        for row in chain_rows:
            pattern_id = str(row.get("pattern_id", ""))
            scan_chain_id = str(row.get("scan_chain_id", ""))
            executions.append(
                {
                    "pattern_id": pattern_id,
                    "scan_chain_id": scan_chain_id,
                    "source_log": entry.source_name,
                    "source_log_relpath": entry.relative_path,
                    "run_id": run_id,
                    "toggle_count": row.get("toggle_count"),
                    "toggle_coverage_pct": row.get("toggle_coverage_pct"),
                    "toggle_density_pct": row.get("toggle_density_pct"),
                    "latest_result": status_by_key.get((pattern_id, scan_chain_id), "FAIL"),
                }
            )
            run_id += 1

    executions.sort(key=_execution_sort_key)
    return executions


def build_session_executions(
    workspace_dir: str,
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
    log_entries: Optional[Sequence[SessionLogEntry]] = None,
) -> List[Dict[str, Any]]:
    """
    Parse each ATE log with existing engines and preserve every execution.

    One execution record is emitted per (pattern_id, scan_chain_id, source_log).
    run_id values are assigned deterministically in sorted-log encounter order.

    When log_entries is provided (E0 single-pass), ate_data/coverage are reused
    and logs are not parsed again.
    """
    if log_entries is not None:
        return _executions_from_log_entries(log_entries)

    if len(absolute_log_paths) != len(relative_log_paths):
        raise ValueError("absolute_log_paths and relative_log_paths length mismatch.")

    # Backward-compatible path when callers have not built a shared cache.
    entries = build_session_log_cache(absolute_log_paths, relative_log_paths)
    return _executions_from_log_entries(entries)
