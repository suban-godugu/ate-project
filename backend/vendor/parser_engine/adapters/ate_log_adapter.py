"""
PA-FR-009 ATE Log Adapter — Anti-Corruption Layer for raw ATE log format.

Parses raw ATE logs into normalized rows for pattern_correlator.py.
Contains zero correlation or join logic.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

def normalize_pattern_id(value: str) -> str:
    return str(value).strip().upper()


def normalize_scan_chain_id(value: str) -> str:
    normalized = str(value).strip().upper()
    if normalized.startswith("CH") and normalized[2:].isdigit():
        return f"CH{int(normalized[2:])}"
    return normalized


logger = logging.getLogger("pa_fr_009_ate_adapter")

EXP_PATTERN = re.compile(
    r"^(P\d+)\s*\|\s*(CH\d+)\s+EXPECTED_OUTPUT:(.*)$",
    re.IGNORECASE,
)
ACT_PATTERN = re.compile(r"^\s*ACTUAL_OUTPUT:(.*)$", re.IGNORECASE)
STATUS_PATTERN = re.compile(r"^\s*STATUS:(.*)$", re.IGNORECASE)
HEADER_FIELD_PATTERN = re.compile(r"^([A-Z0-9_]+)\s*:\s*(.+)$")


class MalformedRowError(ValueError):
    """Raised when a single ATE row cannot be normalized."""


@dataclass
class AteAdapterResult:
    rows: List[Dict[str, Any]] = field(default_factory=list)
    malformed_row_count: int = 0
    header_by_file: Dict[str, Dict[str, str]] = field(default_factory=dict)


def _expand_waveform(value: str) -> str:
    text = value.strip()
    text = re.sub(r"X@\{(\d+)\}", lambda match: "X" * int(match.group(1)), text)
    text = re.sub(r"@\{(\d+)\}X", lambda match: "X" * int(match.group(1)), text)
    text = re.sub(
        r"([HLX])@\{(\d+)\}",
        lambda match: match.group(1) * int(match.group(2)),
        text,
    )
    text = re.sub(
        r"@\{(\d+)\}([HLX])",
        lambda match: match.group(2) * int(match.group(1)),
        text,
    )
    return text


def _normalize_status(raw_status: str) -> str:
    status = raw_status.strip().upper()
    if status in {"P", "PASS"}:
        return "PASS"
    return "FAIL"


def _parse_header_fields(lines: List[str]) -> Dict[str, str]:
    header: Dict[str, str] = {}
    for line in lines:
        match = HEADER_FIELD_PATTERN.match(line.strip())
        if not match:
            continue
        header[match.group(1).upper()] = match.group(2).strip()
    return header


def _workspace_relative_path(path: str, workspace_dir: str) -> str:
    absolute = os.path.abspath(path)
    workspace = os.path.abspath(workspace_dir)
    try:
        return os.path.relpath(absolute, workspace).replace("\\", "/")
    except ValueError:
        return os.path.basename(absolute)


def parse_ate_log_file(
    file_path: str,
    workspace_dir: Optional[str] = None,
) -> AteAdapterResult:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ATE log file not found at: {file_path}")

    workspace = workspace_dir or os.path.dirname(os.path.abspath(file_path))
    source_log = _workspace_relative_path(file_path, workspace)
    source_name = os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
        raw_lines = handle.readlines()

    header = _parse_header_fields(raw_lines[:40])
    die_label = header.get("DIE_LABEL", "")

    rows: List[Dict[str, Any]] = []
    malformed_row_count = 0

    current_pattern: Optional[str] = None
    current_chain: Optional[str] = None
    current_expected: Optional[str] = None
    current_actual: Optional[str] = None
    expected_line_number: Optional[int] = None

    for line_number, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        match_expected = EXP_PATTERN.match(line)
        if match_expected:
            current_pattern = normalize_pattern_id(match_expected.group(1))
            current_chain = normalize_scan_chain_id(match_expected.group(2))
            current_expected = _expand_waveform(match_expected.group(3))
            current_actual = None
            expected_line_number = line_number
            continue

        match_actual = ACT_PATTERN.match(line)
        if match_actual and current_pattern and current_chain:
            current_actual = _expand_waveform(match_actual.group(1))
            continue

        match_status = STATUS_PATTERN.match(line)
        if match_status and current_pattern and current_chain:
            try:
                if expected_line_number is None:
                    raise MalformedRowError("STATUS encountered without EXPECTED_OUTPUT block.")
                status = _normalize_status(match_status.group(1))
                rows.append(
                    {
                        "pattern_id": current_pattern,
                        "scan_chain_id": current_chain,
                        "result": status,
                        "source_log": source_name,
                        "source_log_relpath": source_log,
                        "status_line_number": line_number,
                        "die_label": die_label,
                        "expected": current_expected or "",
                        "actual": current_actual or "",
                    }
                )
            except MalformedRowError as exc:
                malformed_row_count += 1
                logger.warning(
                    "Skipping malformed ATE row at %s:%s: %s Raw line: %r",
                    source_log,
                    line_number,
                    exc,
                    raw_line.rstrip(),
                )
            current_pattern = None
            current_chain = None
            current_expected = None
            current_actual = None
            expected_line_number = None
            continue

        if match_status and (not current_pattern or not current_chain):
            malformed_row_count += 1
            logger.warning(
                "Skipping malformed ATE row at %s:%s: STATUS without active pattern/channel. Raw line: %r",
                source_log,
                line_number,
                raw_line.rstrip(),
            )

    return AteAdapterResult(
        rows=rows,
        malformed_row_count=malformed_row_count,
        header_by_file={source_log: header},
    )


def parse_ate_log_files(
    file_paths: List[str],
    workspace_dir: Optional[str] = None,
) -> AteAdapterResult:
    combined = AteAdapterResult()
    for file_path in file_paths:
        result = parse_ate_log_file(file_path, workspace_dir=workspace_dir)
        combined.rows.extend(result.rows)
        combined.malformed_row_count += result.malformed_row_count
        combined.header_by_file.update(result.header_by_file)
    return combined
