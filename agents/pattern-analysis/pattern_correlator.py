"""
PA-FR-009 Pattern Correlator — the single join implementation for pattern outcomes.

Join key: (pattern_id, scan_chain_id) only.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from correlation_config import CorrelationConfig
from correlation_validator import (
    BIT_MISMATCH,
    DUPLICATE_HISTORY,
    JOIN_FAILURE,
    MISSING_PATTERN,
    NO_MATCHING_SCAN_CHAIN,
    assert_unique_run_ids,
    detect_duplicate_history_events,
    normalize_pattern_id,
    normalize_scan_chain_id,
    validate_metadata_row,
)


@dataclass
class CorrelationRunResult:
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    orphan_ate_rows: List[Dict[str, Any]] = field(default_factory=list)
    matched_rows: int = 0
    unmatched_metadata: int = 0
    unmatched_ate: int = 0
    duplicate_histories: int = 0
    metadata_rows: int = 0
    ate_rows: int = 0


def assign_run_ids(normalized_rows: List[Dict[str, Any]], sorted_log_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Assign deterministic run_id values across sorted log files in encounter order.

    Rows must already be grouped by source_log_relpath encounter within each file.
    """
    path_order = {path: index for index, path in enumerate(sorted_log_paths)}
    ordered_rows = sorted(
        normalized_rows,
        key=lambda row: (
            path_order.get(row.get("source_log_relpath", ""), len(path_order)),
            int(row.get("status_line_number", 0)),
        ),
    )
    run_id_counter = 1
    for row in ordered_rows:
        row["run_id"] = run_id_counter
        run_id_counter += 1
    assert_unique_run_ids(ordered_rows)
    return ordered_rows


def _metadata_key(row: Dict[str, Any]) -> Tuple[str, str]:
    return (
        normalize_pattern_id(str(row["pattern_id"])),
        normalize_scan_chain_id(str(row["scan_chain_id"])),
    )


def _ate_key(row: Dict[str, Any]) -> Tuple[str, str]:
    return (
        normalize_pattern_id(str(row["pattern_id"])),
        normalize_scan_chain_id(str(row["scan_chain_id"])),
    )


def _history_entry_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "run_id": int(row["run_id"]),
        "result": row["result"],
        "source_log": row.get("source_log", ""),
        "status_line_number": int(row["status_line_number"]),
    }
    die_label = row.get("die_label")
    if die_label:
        entry["die_label"] = die_label
    entry["pattern_id"] = row["pattern_id"]
    entry["scan_chain_id"] = row["scan_chain_id"]
    return entry


def _compute_statistics(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    pass_count = sum(1 for item in history if item["result"] == "PASS")
    fail_count = sum(1 for item in history if item["result"] == "FAIL")
    latest_result = history[-1]["result"] if history else None
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "latest_result": latest_result,
    }


def _detect_bit_mismatch(row: Dict[str, Any]) -> bool:
    expected = row.get("expected") or ""
    actual = row.get("actual") or ""
    if not expected or not actual:
        return False
    return expected != actual


def build_outcome_record(
    metadata_row: Dict[str, Any],
    matching_rows: List[Dict[str, Any]],
    config: CorrelationConfig,
) -> Dict[str, Any]:
    pattern_id, scan_chain_id = _metadata_key(metadata_row)
    flags: List[str] = list(validate_metadata_row(metadata_row))

    history = [_history_entry_from_row(row) for row in matching_rows]
    history.sort(key=lambda item: int(item["run_id"]))

    duplicate_events = detect_duplicate_history_events(history)
    if duplicate_events:
        flags.append(DUPLICATE_HISTORY)

    if any(_detect_bit_mismatch(row) for row in matching_rows):
        flags.append(BIT_MISMATCH)

    if not history:
        if config.flag_missing_rows:
            flags.append(NO_MATCHING_SCAN_CHAIN)
    elif JOIN_FAILURE in flags:
        flags.append(JOIN_FAILURE)

    stats = _compute_statistics(history)
    deduped_flags = sorted(set(flags))
    record: Dict[str, Any] = {
        "pattern_id": pattern_id,
        "scan_chain_id": scan_chain_id,
        "history": history if config.export_history else [],
        "latest_result": stats["latest_result"],
        "pass_count": stats["pass_count"],
        "fail_count": stats["fail_count"],
        "data_quality_flags": deduped_flags,
    }
    return record


def correlate(
    metadata_rows: Iterable[Dict[str, Any]],
    ate_rows: Iterable[Dict[str, Any]],
    config: CorrelationConfig,
) -> CorrelationRunResult:
    metadata_list = list(metadata_rows)
    ate_list = list(ate_rows)

    ate_by_key: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in ate_list:
        ate_by_key[_ate_key(row)].append(row)

    metadata_keys: Set[Tuple[str, str]] = set()
    patterns: List[Dict[str, Any]] = []
    matched_ate_rows = 0
    unmatched_metadata = 0
    duplicate_histories = 0

    for metadata_row in metadata_list:
        key = _metadata_key(metadata_row)
        metadata_keys.add(key)
        matching = sorted(ate_by_key.get(key, []), key=lambda row: int(row["run_id"]))
        if not matching:
            unmatched_metadata += 1
        record = build_outcome_record(metadata_row, matching, config)
        if DUPLICATE_HISTORY in record["data_quality_flags"]:
            duplicate_histories += 1
        patterns.append(record)

    patterns.sort(key=lambda item: (item["pattern_id"], item["scan_chain_id"]))

    orphan_ate_rows: List[Dict[str, Any]] = []
    unmatched_ate = 0
    for key, rows in ate_by_key.items():
        if key in metadata_keys:
            matched_ate_rows += len(rows)
            continue
        unmatched_ate += len(rows)
        if config.strict_join:
            for row in rows:
                orphan_ate_rows.append(
                    {
                        "pattern_id": key[0],
                        "scan_chain_id": key[1],
                        "history": [_history_entry_from_row(row)] if config.export_history else [],
                        "latest_result": row["result"],
                        "pass_count": 1 if row["result"] == "PASS" else 0,
                        "fail_count": 0 if row["result"] == "PASS" else 1,
                        "data_quality_flags": [MISSING_PATTERN],
                    }
                )

    orphan_ate_rows.sort(key=lambda item: (item["pattern_id"], item["scan_chain_id"], item["history"][0]["run_id"] if item["history"] else 0))

    return CorrelationRunResult(
        patterns=patterns,
        orphan_ate_rows=orphan_ate_rows,
        matched_rows=matched_ate_rows,
        unmatched_metadata=unmatched_metadata,
        unmatched_ate=unmatched_ate,
        duplicate_histories=duplicate_histories,
        metadata_rows=len(metadata_list),
        ate_rows=len(ate_list),
    )
