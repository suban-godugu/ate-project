"""
PA-FR-009 Correlation Validator — data quality flags and validation rules.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Set, Tuple

NO_MATCHING_SCAN_CHAIN = "NO_MATCHING_SCAN_CHAIN"
MISSING_PATTERN = "MISSING_PATTERN"
BIT_MISMATCH = "BIT_MISMATCH"
JOIN_FAILURE = "JOIN_FAILURE"
DUPLICATE_HISTORY = "DUPLICATE_HISTORY"
INVALID_SCAN_CHAIN = "INVALID_SCAN_CHAIN"

ALL_DATA_QUALITY_FLAGS = (
    NO_MATCHING_SCAN_CHAIN,
    MISSING_PATTERN,
    BIT_MISMATCH,
    JOIN_FAILURE,
    DUPLICATE_HISTORY,
    INVALID_SCAN_CHAIN,
)

SCAN_CHAIN_PATTERN = re.compile(r"^CH\d+$", re.IGNORECASE)


class CorrelationValidationError(ValueError):
    """Raised when correlation inputs fail validation."""


class DuplicateRunIdError(AssertionError):
    """Internal invariant: duplicate run_id assignment indicates a bug."""


def normalize_pattern_id(value: str) -> str:
    return str(value).strip().upper()


def normalize_scan_chain_id(value: str) -> str:
    normalized = str(value).strip().upper()
    if normalized.startswith("CH") and normalized[2:].isdigit():
        return f"CH{int(normalized[2:])}"
    return normalized


def is_valid_scan_chain_id(scan_chain_id: str) -> bool:
    return bool(SCAN_CHAIN_PATTERN.match(scan_chain_id))


def validate_metadata_row(row: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    pattern_id = row.get("pattern_id")
    scan_chain_id = row.get("scan_chain_id")
    if not pattern_id or not scan_chain_id:
        flags.append(JOIN_FAILURE)
        return flags
    normalized_chain = normalize_scan_chain_id(str(scan_chain_id))
    if not is_valid_scan_chain_id(normalized_chain):
        flags.append(INVALID_SCAN_CHAIN)
    return flags


def detect_duplicate_history_events(
    history: Iterable[Dict[str, Any]],
) -> Set[Tuple[str, str, str, int]]:
    seen: Set[Tuple[str, str, str, int]] = set()
    duplicates: Set[Tuple[str, str, str, int]] = set()
    for entry in history:
        event_key = (
            str(entry.get("pattern_id", "")),
            str(entry.get("scan_chain_id", "")),
            str(entry.get("source_log", "")),
            int(entry.get("status_line_number", -1)),
        )
        if event_key in seen:
            duplicates.add(event_key)
        seen.add(event_key)
    return duplicates


def assert_unique_run_ids(rows: Iterable[Dict[str, Any]]) -> None:
    run_ids = [row["run_id"] for row in rows if "run_id" in row]
    if len(run_ids) != len(set(run_ids)):
        raise DuplicateRunIdError("Duplicate run_id assignment detected in normalized ATE rows.")
