"""ATE tester log ingestion module for the Failure Analysis Agent.

Supports three log formats:

* Compact per-die scan format: ``P{n} | CH{m} EXPECTED_OUTPUT:...`` lines with
  indented ``ACTUAL_OUTPUT`` / ``STATUS`` (P/F) and optional ``PATTERN_METRICS``.
* New per-die scan format (large, streamed): one file per die, each PATTERN_ID
  block contains multiple CHANNEL_ID sub-blocks (one per scan chain) with
  EXPECTED_OUTPUT / ACTUAL_OUTPUT and electrical context. These files can be
  hundreds of MB, so they are parsed line-by-line and only FAIL records are
  retained in memory (PASS executions are reduced to counters).
* Legacy format (small): one file per die with ``[PATTERN_ID : N]`` blocks and
  ``EXPECTED_SIGNATURE`` / ``ACTUAL_SIGNATURE`` fields.

Customer tester logs are typically ASCII text with custom headers and no
standard template (FA-FR-001 reviewer note). Additional per-customer parsers
can be added without changing the analysis pipeline.
"""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

HEADER_FIELD_PATTERN = re.compile(r"^([A-Z0-9_]+)\s*:\s*(.*)$")
PATTERN_BLOCK_START = re.compile(r"^\[PATTERN_ID\s*:\s*(\d+)\]$")
BLOCK_SEPARATOR = re.compile(r"^-{3,}$")
COMPACT_CHANNEL_START = re.compile(
    r"^P(\d+)\s*\|\s*CH(\d+)\s+EXPECTED_OUTPUT:(.*)$",
    re.IGNORECASE,
)
COMPACT_CONTINUATION = re.compile(
    r"^\s+(ACTUAL_OUTPUT|STATUS):(.*)$",
    re.IGNORECASE,
)

# Electrical / context fields retained for failing channel executions.
_FAIL_CONTEXT_FIELDS = (
    "CHANNEL_ID",
    "SCAN_IN_SIGNAL",
    "SCAN_OUT_SIGNAL",
    "IR_DROP_MV",
    "THERMAL_C",
    "TRANSITION_FAULTS",
    "SETUP_SLACK_PS",
    "HOLD_SLACK_PS",
    "TEST_TIME_MS",
)


@dataclass(frozen=True)
class PatternResult:
    """Single pattern/channel execution result from a tester log."""

    pattern_id: str
    scan_chain_id: str
    expected_signature: str
    actual_signature: str
    status: str
    raw_fields: dict[str, str] = field(default_factory=dict)

    @property
    def is_fail(self) -> bool:
        return self.status.upper() == "FAIL"


@dataclass
class DieLog:
    """Parsed representation of one die-level ATE log file.

    For streamed large logs, ``patterns`` is left empty and the analytics rely
    on ``stored_failing`` (failing executions), ``total_executions`` and
    ``pattern_test_counts``. For legacy logs, ``patterns`` holds every record.
    """

    source_path: str
    tester_name: str
    device_name: str
    lot_id: str
    wafer_id: str
    die_id: str
    header_fields: dict[str, str] = field(default_factory=dict)
    patterns: list[PatternResult] = field(default_factory=list)
    stored_failing: list[PatternResult] | None = None
    total_executions: int = 0
    pattern_test_counts: dict[str, int] = field(default_factory=dict)
    declared_patterns: int = 0
    scan_chains: int = 0
    malformed_blocks: int = 0

    @property
    def failing_patterns(self) -> list[PatternResult]:
        if self.stored_failing is not None:
            return self.stored_failing
        return [p for p in self.patterns if p.is_fail]

    @property
    def is_failing_die(self) -> bool:
        return bool(self.failing_patterns)

    @property
    def execution_count(self) -> int:
        """Total pattern/channel executions (denominator for rates)."""
        return self.total_executions or len(self.patterns)

    @property
    def expected_executions(self) -> int:
        """Executions the header declares (patterns x scan chains)."""
        if self.scan_chains and self.declared_patterns:
            return self.scan_chains * self.declared_patterns
        return self.declared_patterns or self.execution_count

    @property
    def parse_completeness(self) -> float:
        """Fraction of declared executions successfully parsed (FA-FR-002)."""
        expected = self.expected_executions
        if expected <= 0:
            return 1.0
        return min(self.execution_count / expected, 1.0)

    def test_counts(self) -> dict[str, int]:
        """Number of executions per PATTERN_ID."""
        if self.pattern_test_counts:
            return self.pattern_test_counts
        counts: dict[str, int] = {}
        for p in self.patterns:
            counts[p.pattern_id] = counts.get(p.pattern_id, 0) + 1
        return counts


class LogIngestionError(Exception):
    """Raised when a log file cannot be parsed."""


def discover_log_files(root_dir: str | Path, *, recursive: bool = False) -> list[Path]:
    """Locate `.log` files in *root_dir*.

    By default only the top-level directory is scanned so that unrelated logs in
    sub-folders are not pulled in. Pass ``recursive=True`` to search nested
    directories as well.
    """
    root = Path(root_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"Log directory does not exist: {root}")

    finder = root.rglob if recursive else root.glob
    log_files = sorted(finder("*.log"))
    if not log_files:
        scope = "under" if recursive else "directly in"
        raise FileNotFoundError(f"No .log files found {scope}: {root}")

    logger.info("Discovered %d log file(s) in %s", len(log_files), root)
    return log_files


# --------------------------------------------------------------------------- #
# New streaming scan-format parser
# --------------------------------------------------------------------------- #
def _open_text(path: Path):
    """Open a text file trying common encodings, returning a file handle."""
    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            handle = path.open("r", encoding=encoding, errors="strict")
            handle.readline()
            handle.seek(0)
            return handle
        except UnicodeDecodeError as exc:
            last_error = exc
    # Fall back to permissive decoding rather than failing the whole file.
    logger.warning("Falling back to lossy decoding for %s: %s", path, last_error)
    return path.open("r", encoding="utf-8", errors="replace")


def _looks_like_compact_format(path: Path) -> bool:
    """Detect ``P{n} | CH{m} EXPECTED_OUTPUT`` compact scan logs."""
    with _open_text(path) as handle:
        for i, line in enumerate(handle):
            if COMPACT_CHANNEL_START.match(line.strip()):
                return True
            if i > 500:
                break
    return False


def _looks_like_new_format(path: Path) -> bool:
    """Peek at the first lines to detect the streamed CHANNEL_ID scan format."""
    with _open_text(path) as handle:
        for i, line in enumerate(handle):
            stripped = line.strip()
            if stripped.startswith("CHANNEL_ID"):
                return True
            if stripped.startswith("[PATTERN_ID") or COMPACT_CHANNEL_START.match(stripped):
                return False
            if i > 500:
                break
    return False


def _normalize_status(value: str) -> str:
    """Map compact STATUS codes (P/F) to PASS/FAIL."""
    token = value.strip().upper()
    if token in {"P", "PASS"}:
        return "PASS"
    if token in {"F", "FAIL"}:
        return "FAIL"
    return token


def _build_die_log_from_stream(
    path: Path,
    header: dict[str, str],
    *,
    failing: list[PatternResult],
    test_counts: dict[str, int],
    total_exec: int,
    malformed: int,
) -> DieLog:
    device = header.get("DEVICE_NAME")
    lot = header.get("LOT_ID")
    die = header.get("DIE_LABEL") or header.get("DIE_ID")
    missing = [
        name
        for name, val in (("DEVICE_NAME", device), ("LOT_ID", lot), ("DIE_LABEL", die))
        if not val
    ]
    if missing:
        raise LogIngestionError(
            f"{path}: missing required header field(s): {', '.join(missing)}"
        )

    wafer_id = header.get("WAFER_ID") or f"WF_{lot}"
    declared = 0
    try:
        declared = int(header.get("TOTAL_PATTERNS", "0"))
    except ValueError:
        declared = len(test_counts)
    try:
        scan_chains = int(header.get("SCAN_CHAINS", "0"))
    except ValueError:
        scan_chains = 0

    return DieLog(
        source_path=str(path),
        tester_name=header.get("TESTER_NAME", ""),
        device_name=device,
        lot_id=lot,
        wafer_id=wafer_id,
        die_id=die,
        header_fields=header,
        patterns=[],
        stored_failing=failing,
        total_executions=total_exec,
        pattern_test_counts=test_counts,
        declared_patterns=declared or len(test_counts),
        scan_chains=scan_chains,
        malformed_blocks=malformed,
    )


def _parse_new_format(path: Path) -> DieLog:
    """Stream-parse the large per-die scan log, retaining only FAIL records."""
    header: dict[str, str] = {}
    failing: list[PatternResult] = []
    test_counts: dict[str, int] = {}
    total_exec = 0
    malformed = 0

    in_body = False
    cur_pid: str | None = None
    ch: dict[str, str] = {}
    ch_status: str | None = None
    ch_has_channel = False
    ch_scan_chain = ""
    ch_expected = ""
    ch_actual = ""

    def finalize_channel() -> None:
        nonlocal total_exec, malformed
        if ch_status is None:
            # A channel block was opened but had no STATUS line -> malformed.
            if ch_has_channel:
                malformed += 1
            return
        total_exec += 1
        if cur_pid is not None:
            test_counts[cur_pid] = test_counts.get(cur_pid, 0) + 1
        status = _normalize_status(ch_status)
        if status == "FAIL" and cur_pid is not None:
            context = {k: ch[k] for k in _FAIL_CONTEXT_FIELDS if k in ch}
            context["STATUS"] = "FAIL"
            failing.append(
                PatternResult(
                    pattern_id=sys.intern(cur_pid),
                    scan_chain_id=sys.intern(ch_scan_chain),
                    expected_signature=ch_expected,
                    actual_signature=ch_actual,
                    status="FAIL",
                    raw_fields=context,
                )
            )

    with _open_text(path) as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("="):
                continue

            if stripped.startswith("PATTERN_ID"):
                finalize_channel()
                ch = {}
                ch_status = None
                ch_has_channel = False
                ch_scan_chain = ch_expected = ch_actual = ""
                in_body = True
                cur_pid = stripped.split(":", 1)[1].strip()
                continue

            if not in_body:
                match = HEADER_FIELD_PATTERN.match(stripped)
                if match:
                    header[match.group(1)] = match.group(2).strip()
                continue

            if stripped.startswith("CHANNEL_ID"):
                finalize_channel()
                ch = {"CHANNEL_ID": stripped.split(":", 1)[1].strip()}
                ch_status = None
                ch_has_channel = True
                ch_scan_chain = ch_expected = ch_actual = ""
                continue

            if BLOCK_SEPARATOR.match(stripped):
                finalize_channel()
                ch = {}
                ch_status = None
                ch_has_channel = False
                ch_scan_chain = ch_expected = ch_actual = ""
                continue

            match = HEADER_FIELD_PATTERN.match(stripped)
            if not match:
                continue
            key, value = match.group(1), match.group(2).strip()
            if key == "STATUS":
                ch_status = _normalize_status(value)
            elif key == "SCAN_CHAIN_ID":
                ch_scan_chain = value
            elif key == "EXPECTED_OUTPUT":
                ch_expected = value
            elif key == "ACTUAL_OUTPUT":
                ch_actual = value
            else:
                ch[key] = value

        finalize_channel()

    return _build_die_log_from_stream(
        path, header, failing=failing, test_counts=test_counts,
        total_exec=total_exec, malformed=malformed,
    )


def _parse_compact_format(path: Path) -> DieLog:
    """Stream-parse ``P{n} | CH{m}`` compact scan logs, retaining only FAIL records."""
    header: dict[str, str] = {}
    failing: list[PatternResult] = []
    test_counts: dict[str, int] = {}
    total_exec = 0
    malformed = 0

    in_body = False
    in_metrics = False
    cur_pid: str | None = None
    metrics_pattern_id: str | None = None
    pattern_metrics: dict[str, str] = {}
    ch: dict[str, str] = {}
    ch_status: str | None = None
    ch_has_channel = False
    ch_scan_chain = ""
    ch_expected = ""
    ch_actual = ""

    def backfill_metrics() -> None:
        nonlocal failing, pattern_metrics, metrics_pattern_id
        if not pattern_metrics or metrics_pattern_id is None:
            pattern_metrics = {}
            metrics_pattern_id = None
            return
        pid = metrics_pattern_id
        rebuilt: list[PatternResult] = []
        for fail in failing:
            if fail.pattern_id == pid:
                context = {**fail.raw_fields, **pattern_metrics}
                rebuilt.append(
                    PatternResult(
                        pattern_id=fail.pattern_id,
                        scan_chain_id=fail.scan_chain_id,
                        expected_signature=fail.expected_signature,
                        actual_signature=fail.actual_signature,
                        status=fail.status,
                        raw_fields=context,
                    )
                )
            else:
                rebuilt.append(fail)
        failing = rebuilt
        pattern_metrics = {}
        metrics_pattern_id = None

    def finalize_channel() -> None:
        nonlocal total_exec, malformed
        if ch_status is None:
            if ch_has_channel:
                malformed += 1
            return
        total_exec += 1
        if cur_pid is not None:
            test_counts[cur_pid] = test_counts.get(cur_pid, 0) + 1
        status = _normalize_status(ch_status)
        if status == "FAIL" and cur_pid is not None:
            context = {k: ch[k] for k in _FAIL_CONTEXT_FIELDS if k in ch}
            context["CHANNEL_ID"] = ch.get("CHANNEL_ID", "")
            context["STATUS"] = "FAIL"
            failing.append(
                PatternResult(
                    pattern_id=sys.intern(cur_pid),
                    scan_chain_id=sys.intern(ch_scan_chain),
                    expected_signature=ch_expected,
                    actual_signature=ch_actual,
                    status="FAIL",
                    raw_fields=context,
                )
            )

    with _open_text(path) as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("="):
                continue

            compact_match = COMPACT_CHANNEL_START.match(stripped)
            if compact_match:
                in_body = True
                if in_metrics:
                    in_metrics = False
                    backfill_metrics()
                finalize_channel()
                pid_num, ch_num, expected = compact_match.groups()
                cur_pid = pid_num.lstrip("0") or "0"
                ch = {"CHANNEL_ID": ch_num}
                ch_status = None
                ch_has_channel = True
                ch_scan_chain = f"CH{ch_num}"
                ch_expected = expected.strip()
                ch_actual = ""
                continue

            continuation = COMPACT_CONTINUATION.match(line)
            if continuation and ch_has_channel:
                key, value = continuation.group(1).upper(), continuation.group(2).strip()
                if key == "STATUS":
                    ch_status = _normalize_status(value)
                elif key == "ACTUAL_OUTPUT":
                    ch_actual = value
                continue

            if stripped == "PATTERN_METRICS":
                finalize_channel()
                metrics_pattern_id = cur_pid
                in_metrics = True
                pattern_metrics = {}
                continue

            if in_metrics:
                if BLOCK_SEPARATOR.match(stripped):
                    in_metrics = False
                    backfill_metrics()
                    continue
                metrics_match = HEADER_FIELD_PATTERN.match(stripped)
                if metrics_match:
                    pattern_metrics[metrics_match.group(1)] = metrics_match.group(2).strip()
                continue

            if not in_body:
                header_match = HEADER_FIELD_PATTERN.match(stripped)
                if header_match:
                    header[header_match.group(1)] = header_match.group(2).strip()
                continue

        if in_metrics:
            backfill_metrics()
        finalize_channel()

    return _build_die_log_from_stream(
        path, header, failing=failing, test_counts=test_counts,
        total_exec=total_exec, malformed=malformed,
    )


# --------------------------------------------------------------------------- #
# Legacy format parser (kept for backward compatibility)
# --------------------------------------------------------------------------- #
def _parse_header(lines: Iterator[str]) -> tuple[dict[str, str], Iterator[str]]:
    header: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("="):
            continue
        if PATTERN_BLOCK_START.match(stripped):
            return header, _prepend_line(stripped, lines)
        match = HEADER_FIELD_PATTERN.match(stripped)
        if match:
            header[match.group(1)] = match.group(2).strip()
    return header, iter(())


def _prepend_line(first_line: str, remaining: Iterator[str]) -> Iterator[str]:
    yield first_line
    yield from remaining


def _parse_pattern_block(pattern_id: str, block_lines: list[str]) -> PatternResult:
    fields: dict[str, str] = {}
    for raw in block_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("FAIL_ANALYSIS"):
            continue
        match = HEADER_FIELD_PATTERN.match(stripped)
        if match:
            fields[match.group(1)] = match.group(2).strip()

    return PatternResult(
        pattern_id=pattern_id,
        scan_chain_id=fields.get("SCAN_CHAIN_ID", ""),
        expected_signature=fields.get("EXPECTED_SIGNATURE", ""),
        actual_signature=fields.get("ACTUAL_SIGNATURE", ""),
        status=fields.get("STATUS", "UNKNOWN"),
        raw_fields=fields,
    )


def parse_log_content(content: str, source_path: str | Path) -> DieLog:
    """Parse legacy raw log text into a :class:`DieLog`."""
    lines = content.splitlines()
    header, remaining = _parse_header(iter(lines))

    required = ("DEVICE_NAME", "LOT_ID", "WAFER_ID", "DIE_ID")
    missing = [key for key in required if key not in header]
    if missing:
        raise LogIngestionError(
            f"{source_path}: missing required header field(s): {', '.join(missing)}"
        )

    patterns: list[PatternResult] = []
    current_pattern_id: str | None = None
    current_block: list[str] = []

    for line in remaining:
        stripped = line.strip()
        if not stripped:
            continue

        pattern_match = PATTERN_BLOCK_START.match(stripped)
        if pattern_match:
            if current_pattern_id is not None:
                patterns.append(_parse_pattern_block(current_pattern_id, current_block))
            current_pattern_id = pattern_match.group(1)
            current_block = []
            continue

        if BLOCK_SEPARATOR.match(stripped):
            if current_pattern_id is not None and current_block:
                patterns.append(_parse_pattern_block(current_pattern_id, current_block))
                current_pattern_id = None
                current_block = []
            continue

        if current_pattern_id is not None:
            current_block.append(line)

    if current_pattern_id is not None and current_block:
        patterns.append(_parse_pattern_block(current_pattern_id, current_block))

    if not patterns:
        raise LogIngestionError(f"{source_path}: no pattern execution blocks found")

    return DieLog(
        source_path=str(source_path),
        tester_name=header.get("TESTER_NAME", ""),
        device_name=header["DEVICE_NAME"],
        lot_id=header["LOT_ID"],
        wafer_id=header["WAFER_ID"],
        die_id=header["DIE_ID"],
        header_fields=header,
        patterns=patterns,
    )


def read_log_file(path: str | Path) -> DieLog:
    """Read and parse a single log file, auto-detecting the format."""
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    if _looks_like_compact_format(file_path):
        return _parse_compact_format(file_path)

    if _looks_like_new_format(file_path):
        return _parse_new_format(file_path)

    last_error: Exception | None = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            content = file_path.read_text(encoding=encoding)
            return parse_log_content(content, file_path)
        except UnicodeDecodeError as exc:
            last_error = exc
            logger.debug("Encoding %s failed for %s: %s", encoding, file_path, exc)

    raise LogIngestionError(
        f"Unable to decode {file_path} with supported encodings"
    ) from last_error


def ingest_logs(
    root_dir: str | Path, *, recursive: bool = False
) -> tuple[list[DieLog], list[dict]]:
    """Discover and parse all tester logs in *root_dir*."""
    log_files = discover_log_files(root_dir, recursive=recursive)
    die_logs: list[DieLog] = []
    errors: list[dict] = []

    for log_path in log_files:
        try:
            die = read_log_file(log_path)
            die_logs.append(die)
            logger.info(
                "Ingested %s: %d patterns x channels = %d executions, %d failing",
                log_path.name,
                die.declared_patterns,
                die.execution_count,
                len(die.failing_patterns),
            )
        except (OSError, LogIngestionError, ValueError) as exc:
            logger.error("Failed to ingest %s: %s", log_path, exc)
            errors.append({"file": str(log_path), "error": str(exc)})

    logger.info(
        "Ingestion complete: %d succeeded, %d failed",
        len(die_logs),
        len(errors),
    )
    return die_logs, errors
