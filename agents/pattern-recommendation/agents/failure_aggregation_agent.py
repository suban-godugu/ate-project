"""
Failure Aggregation Agent
=========================
Discovers STIL/ATE execution logs, parses failed pattern IDs, aggregates
recurring failures across logs, assigns severity by coverage, and writes
structured reports for dashboards and downstream agents.

This agent does NOT perform root-cause analysis or recommendations.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

# ---------------------------------------------------------------------------
# Paths (resolved relative to project root — never hardcoded dataset sizes)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(
    os.environ.get(
        "BACKEND_DATA_DIR",
        os.path.join(
            os.environ.get("UPLOAD_INPUT_ROOT", r"C:\personal\input all file"),
            "pattern-recommendation",
        ),
    )
)
OUTPUTS_DIR = Path(
    os.environ.get(
        "BACKEND_OUTPUT_DIR",
        os.path.join(
            os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output"),
            "pattern-recommendation",
        ),
    )
)
PARSED_LOGS_DIR = OUTPUTS_DIR / "parsed_logs"

JSON_OUTPUT = OUTPUTS_DIR / "failure_summary.json"
CSV_OUTPUT = OUTPUTS_DIR / "failure_summary.csv"
MD_OUTPUT = OUTPUTS_DIR / "failure_report.md"
DASHBOARD_OUTPUT = OUTPUTS_DIR / "dashboard_data.json"

# Severity thresholds (percentage-based only)
SEVERITY_HIGH = 70.0
SEVERITY_MEDIUM = 30.0

_FAILED_IDS_RE = re.compile(
    r"FAILED_PATTERN_IDS\s*:\s*(?P<value>.*?)\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_LOT_ID_RE = re.compile(
    r"LOT_ID\s*:\s*(?P<value>\S+)",
    re.IGNORECASE,
)
# Optional filename/path lot token (e.g. LOT_1, Lot01) — only used if present
_PATH_LOT_RE = re.compile(r"(?i)\b(LOT[_\-]?\d+)\b")

logger = logging.getLogger("failure_aggregation_agent")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ParsedLog:
    """Minimal parsed representation of one execution log."""

    log_name: str
    FAILED_PATTERN_IDS: List[str]
    lot_id: Optional[str] = None
    source_path: str = ""

    @property
    def is_failed(self) -> bool:
        return len(self.FAILED_PATTERN_IDS) > 0


@dataclass
class PatternAggregate:
    pattern_id: str
    failed_logs: int
    coverage_percent: float
    severity: str
    affected_lots: List[str] = field(default_factory=list)
    failing_logs: List[str] = field(default_factory=list)
    rank: int = 0


@dataclass
class DatasetSummary:
    total_logs: int
    failed_logs: int
    good_logs: int
    unique_patterns: int
    total_pattern_occurrences: int = 0
    total_lots: Optional[int] = None


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_logs(data_dir: Path = DATA_DIR) -> List[Path]:
    """Recursively discover every ``*.log`` file under ``data_dir``."""
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    logs = sorted(data_dir.rglob("*.log"))
    logger.info("Discovered %d log file(s) under %s", len(logs), data_dir)
    return logs


def _relative_log_name(log_path: Path, data_dir: Path = DATA_DIR) -> str:
    """Stable unique name relative to data/ (handles duplicate basenames)."""
    try:
        return log_path.resolve().relative_to(data_dir.resolve()).as_posix()
    except ValueError:
        return log_path.name


def _parsed_json_path(log_name: str, parsed_dir: Path = PARSED_LOGS_DIR) -> Path:
    safe = log_name.replace("/", "__").replace("\\", "__")
    if not safe.endswith(".json"):
        safe = f"{safe}.json" if not safe.endswith(".log") else safe[:-4] + ".json"
    return parsed_dir / safe


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _normalize_pattern_id(raw: str) -> str:
    """Normalize a raw pattern token to a stable string ID."""
    token = raw.strip().strip(",")
    if not token:
        return ""
    if token.upper() in {"NONE", "N/A", "NA", "-", "NULL"}:
        return ""
    # Already prefixed (Pattern_1052 / P1052)
    if re.match(r"(?i)^pattern[_\-]?\d+$", token):
        num = re.search(r"\d+", token)
        return f"Pattern_{num.group()}" if num else token
    if re.match(r"(?i)^p\d+$", token):
        return f"Pattern_{token[1:]}"
    if token.isdigit():
        return f"Pattern_{token}"
    return token


def _parse_pattern_id_list(value: str) -> List[str]:
    """Parse FAILED_PATTERN_IDS value into unique ordered pattern IDs (once per log)."""
    if not value or value.strip().upper() in {"NONE", "N/A", "NA", "-", ""}:
        return []

    # Split on commas or whitespace
    parts = re.split(r"[,;\s]+", value.strip())
    seen: Set[str] = set()
    ordered: List[str] = []
    for part in parts:
        pid = _normalize_pattern_id(part)
        if pid and pid not in seen:
            seen.add(pid)
            ordered.append(pid)
    return ordered


def _extract_lot_id(header_text: str, log_path: Path, log_name: str) -> Optional[str]:
    """Extract lot id from metadata when available; else optional path token."""
    match = _LOT_ID_RE.search(header_text)
    if match:
        return match.group("value").strip()

    # Optional: path / filename only if a clear LOT token appears
    for candidate in (log_name, str(log_path)):
        m = _PATH_LOT_RE.search(candidate)
        if m:
            return m.group(1).upper().replace("-", "_")
    return None


def _read_head_and_tail(path: Path, head_bytes: int = 8192, tail_bytes: int = 16384) -> Tuple[str, str]:
    """Read start and end of a potentially large log without loading the whole file."""
    size = path.stat().st_size
    with path.open("rb") as fh:
        head = fh.read(min(head_bytes, size)).decode("utf-8", errors="replace")
        if size <= head_bytes + tail_bytes:
            return head, head
        fh.seek(max(0, size - tail_bytes))
        tail = fh.read().decode("utf-8", errors="replace")
    return head, tail


def parse_single_log(log_path: Path, data_dir: Path = DATA_DIR) -> ParsedLog:
    """Parse one log into FAILED_PATTERN_IDS (unique) and optional lot metadata."""
    log_name = _relative_log_name(log_path, data_dir)
    head, tail = _read_head_and_tail(log_path)

    match = _FAILED_IDS_RE.search(tail) or _FAILED_IDS_RE.search(head)
    if match:
        pattern_ids = _parse_pattern_id_list(match.group("value"))
    else:
        # Fallback: collect unique pattern IDs from STATUS:F lines (full scan)
        pattern_ids = _parse_failures_from_status(log_path)

    lot_id = _extract_lot_id(head, log_path, log_name)
    return ParsedLog(
        log_name=log_name,
        FAILED_PATTERN_IDS=pattern_ids,
        lot_id=lot_id,
        source_path=str(log_path.resolve()),
    )


def _parse_failures_from_status(log_path: Path) -> List[str]:
    """Fallback full-file scan for pattern failures (STATUS may be on a following line)."""
    header_re = re.compile(r"^P(?P<pid>\d+)\s*\|", re.IGNORECASE)
    seen: Set[str] = set()
    ordered: List[str] = []
    current: Optional[str] = None

    with log_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            stripped = line.strip()
            hm = header_re.match(stripped)
            if hm:
                current = hm.group("pid")
                # Same-line STATUS:F (rare)
                if re.search(r"STATUS\s*:\s*F\b", stripped, re.IGNORECASE):
                    pid = _normalize_pattern_id(current)
                    if pid and pid not in seen:
                        seen.add(pid)
                        ordered.append(pid)
                continue
            if current and re.search(r"STATUS\s*:\s*F\b", stripped, re.IGNORECASE):
                pid = _normalize_pattern_id(current)
                if pid and pid not in seen:
                    seen.add(pid)
                    ordered.append(pid)
    return ordered

def parse_logs(
    log_paths: Optional[Sequence[Path]] = None,
    data_dir: Path = DATA_DIR,
    parsed_dir: Path = PARSED_LOGS_DIR,
    force: bool = False,
) -> List[ParsedLog]:
    """
    Parse every discovered log and write JSON under ``outputs/parsed_logs/``.

    Skips re-parsing when a valid parsed JSON already exists unless ``force``.
    """
    paths = list(log_paths) if log_paths is not None else discover_logs(data_dir)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    results: List[ParsedLog] = []

    for path in paths:
        log_name = _relative_log_name(path, data_dir)
        out_path = _parsed_json_path(log_name, parsed_dir)

        if out_path.is_file() and not force:
            try:
                with out_path.open("r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                results.append(
                    ParsedLog(
                        log_name=raw.get("log_name", log_name),
                        FAILED_PATTERN_IDS=list(raw.get("FAILED_PATTERN_IDS", [])),
                        lot_id=raw.get("lot_id"),
                        source_path=raw.get("source_path", str(path)),
                    )
                )
                continue
            except (json.JSONDecodeError, OSError, TypeError) as exc:
                logger.warning("Re-parsing %s (cached JSON unreadable: %s)", log_name, exc)

        logger.info("Parsing %s", log_name)
        parsed = parse_single_log(path, data_dir)
        payload = {
            "log_name": parsed.log_name,
            "FAILED_PATTERN_IDS": parsed.FAILED_PATTERN_IDS,
            "lot_id": parsed.lot_id,
            "source_path": parsed.source_path,
        }
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        results.append(parsed)

    logger.info("Parsed %d log(s)", len(results))
    return results


def load_parsed_logs(parsed_dir: Path = PARSED_LOGS_DIR) -> List[ParsedLog]:
    """Load previously written parsed JSON files."""
    if not parsed_dir.is_dir():
        return []

    results: List[ParsedLog] = []
    for path in sorted(parsed_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        results.append(
            ParsedLog(
                log_name=raw["log_name"],
                FAILED_PATTERN_IDS=list(raw.get("FAILED_PATTERN_IDS", [])),
                lot_id=raw.get("lot_id"),
                source_path=raw.get("source_path", ""),
            )
        )
    logger.info("Loaded %d parsed log(s) from %s", len(results), parsed_dir)
    return results


# ---------------------------------------------------------------------------
# Aggregation & severity
# ---------------------------------------------------------------------------


def assign_severity(coverage_percent: float) -> str:
    """Map coverage percentage to HIGH / MEDIUM / LOW."""
    if coverage_percent >= SEVERITY_HIGH:
        return "HIGH"
    if coverage_percent >= SEVERITY_MEDIUM:
        return "MEDIUM"
    return "LOW"


def calculate_statistics(parsed_logs: Sequence[ParsedLog]) -> DatasetSummary:
    """Discover dataset statistics from parsed content (no hardcoded counts)."""
    total_logs = len(parsed_logs)
    failed_logs = sum(1 for log in parsed_logs if log.is_failed)
    good_logs = total_logs - failed_logs

    all_patterns: Set[str] = set()
    total_occurrences = 0
    lots: Set[str] = set()

    for log in parsed_logs:
        # Already unique per log
        all_patterns.update(log.FAILED_PATTERN_IDS)
        total_occurrences += len(log.FAILED_PATTERN_IDS)
        if log.lot_id:
            lots.add(log.lot_id)

    return DatasetSummary(
        total_logs=total_logs,
        failed_logs=failed_logs,
        good_logs=good_logs,
        unique_patterns=len(all_patterns),
        total_pattern_occurrences=total_occurrences,
        total_lots=len(lots) if lots else None,
    )


def aggregate_patterns(parsed_logs: Sequence[ParsedLog]) -> List[PatternAggregate]:
    """
    Aggregate unique-log failure counts per pattern.

    Complexity ~ O(total unique pattern entries across logs).
    """
    # pattern_id -> set of log names
    pattern_to_logs: Dict[str, Set[str]] = defaultdict(set)
    # pattern_id -> set of lot ids
    pattern_to_lots: Dict[str, Set[str]] = defaultdict(set)

    failed_log_count = sum(1 for log in parsed_logs if log.is_failed)
    total_logs = len(parsed_logs)
    # Denominator: failed logs when classification exists; else all logs
    denominator = failed_log_count if failed_log_count > 0 else max(total_logs, 1)

    for log in parsed_logs:
        # Pattern counted once per log (set + already-deduped list)
        for pid in log.FAILED_PATTERN_IDS:
            pattern_to_logs[pid].add(log.log_name)
            if log.lot_id:
                pattern_to_lots[pid].add(log.lot_id)

    aggregates: List[PatternAggregate] = []
    for pid, log_names in pattern_to_logs.items():
        failed = len(log_names)
        coverage = round((failed / denominator) * 100.0, 2)
        lots = sorted(pattern_to_lots.get(pid, set()))
        aggregates.append(
            PatternAggregate(
                pattern_id=pid,
                failed_logs=failed,
                coverage_percent=coverage,
                severity=assign_severity(coverage),
                affected_lots=lots,
                failing_logs=sorted(log_names),
            )
        )

    aggregates.sort(
        key=lambda p: (-p.failed_logs, -p.coverage_percent, _pattern_sort_key(p.pattern_id))
    )
    for idx, item in enumerate(aggregates, start=1):
        item.rank = idx
    return aggregates


def _pattern_sort_key(pattern_id: str) -> Tuple[int, Any]:
    """Natural sort for Pattern_N vs opaque string IDs."""
    m = re.search(r"(\d+)$", pattern_id)
    if m:
        return (0, int(m.group(1)))
    return (1, pattern_id)


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------


def generate_json(
    summary: DatasetSummary,
    patterns: Sequence[PatternAggregate],
    output_path: Path = JSON_OUTPUT,
) -> Path:
    """Write ``outputs/failure_summary.json``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "summary": {
            "total_logs": summary.total_logs,
            "failed_logs": summary.failed_logs,
            "good_logs": summary.good_logs,
            "unique_patterns": summary.unique_patterns,
            "total_pattern_occurrences": summary.total_pattern_occurrences,
        },
        "patterns": [
            {
                "rank": p.rank,
                "pattern_id": p.pattern_id,
                "failed_logs": p.failed_logs,
                "coverage_percent": p.coverage_percent,
                "severity": p.severity,
                "affected_lots": p.affected_lots,
                "failing_logs": p.failing_logs,
            }
            for p in patterns
        ],
    }
    if summary.total_lots is not None:
        payload["summary"]["total_lots"] = summary.total_lots

    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    logger.info("Wrote %s", output_path)
    return output_path


def generate_csv(
    patterns: Sequence[PatternAggregate],
    output_path: Path = CSV_OUTPUT,
) -> Path:
    """Write ``outputs/failure_summary.csv`` (dashboard-ready)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Rank",
        "Pattern ID",
        "Failed Logs",
        "Coverage %",
        "Severity",
        "Affected Lots",
        "Failing Log Count",
        "Failing Logs",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for p in patterns:
            writer.writerow(
                {
                    "Rank": p.rank,
                    "Pattern ID": p.pattern_id,
                    "Failed Logs": p.failed_logs,
                    "Coverage %": p.coverage_percent,
                    "Severity": p.severity,
                    "Affected Lots": ", ".join(p.affected_lots),
                    "Failing Log Count": len(p.failing_logs),
                    "Failing Logs": ", ".join(p.failing_logs),
                }
            )
    logger.info("Wrote %s", output_path)
    return output_path


def generate_dashboard_data(
    patterns: Sequence[PatternAggregate],
    output_path: Path = DASHBOARD_OUTPUT,
) -> Path:
    """
    Write dashboard-ready rows for Streamlit / FastAPI / React DataGrid.

    Same columns as the CSV, as a JSON array of objects.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "Rank": p.rank,
            "Pattern ID": p.pattern_id,
            "Failed Logs": p.failed_logs,
            "Coverage %": p.coverage_percent,
            "Severity": p.severity,
            "Affected Lots": p.affected_lots,
            "Failing Log Count": len(p.failing_logs),
            "Failing Logs": p.failing_logs,
        }
        for p in patterns
    ]
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    logger.info("Wrote %s", output_path)
    return output_path


def generate_markdown(
    summary: DatasetSummary,
    patterns: Sequence[PatternAggregate],
    output_path: Path = MD_OUTPUT,
) -> Path:
    """Write ``outputs/failure_report.md``."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    high = sum(1 for p in patterns if p.severity == "HIGH")
    medium = sum(1 for p in patterns if p.severity == "MEDIUM")
    low = sum(1 for p in patterns if p.severity == "LOW")

    top20 = list(patterns[:20])
    # Top coverage: re-sort copy by coverage then failed_logs
    by_coverage = sorted(
        patterns,
        key=lambda p: (-p.coverage_percent, -p.failed_logs, _pattern_sort_key(p.pattern_id)),
    )[:20]

    lines: List[str] = [
        "# Failure Aggregation Report",
        "",
        "## Dataset Summary",
        "",
        f"| Metric | Value |",
        f"| --- | ---: |",
        f"| Total Logs | {summary.total_logs} |",
        f"| Failed Logs | {summary.failed_logs} |",
        f"| Good Logs | {summary.good_logs} |",
        f"| Unique Patterns | {summary.unique_patterns} |",
        f"| Total Pattern Occurrences | {summary.total_pattern_occurrences} |",
    ]
    if summary.total_lots is not None:
        lines.append(f"| Total Lots | {summary.total_lots} |")

    lines.extend(
        [
            "",
            "## Severity Distribution",
            "",
            f"| Severity | Count |",
            f"| --- | ---: |",
            f"| High | {high} |",
            f"| Medium | {medium} |",
            f"| Low | {low} |",
            "",
            "## Top 20 Recurring Patterns",
            "",
            "| Rank | Pattern ID | Failed Logs | Coverage % | Severity | Affected Lots |",
            "| ---: | --- | ---: | ---: | --- | --- |",
        ]
    )
    for p in top20:
        lots = ", ".join(p.affected_lots) if p.affected_lots else "—"
        lines.append(
            f"| {p.rank} | {p.pattern_id} | {p.failed_logs} | "
            f"{p.coverage_percent:.2f} | {p.severity} | {lots} |"
        )

    lines.extend(
        [
            "",
            "## Top Coverage Patterns",
            "",
            "| Pattern ID | Failed Logs | Coverage % | Severity |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for p in by_coverage:
        lines.append(
            f"| {p.pattern_id} | {p.failed_logs} | {p.coverage_percent:.2f} | {p.severity} |"
        )

    avg_coverage = (
        round(sum(p.coverage_percent for p in patterns) / len(patterns), 2) if patterns else 0.0
    )
    max_failed = max((p.failed_logs for p in patterns), default=0)
    lines.extend(
        [
            "",
            "## Summary Statistics",
            "",
            f"- Patterns ranked: **{len(patterns)}**",
            f"- Average coverage: **{avg_coverage}%**",
            f"- Max failed-log count for a single pattern: **{max_failed}**",
            f"- Coverage denominator: "
            f"**{'failed logs' if summary.failed_logs > 0 else 'total logs'}** "
            f"({summary.failed_logs if summary.failed_logs > 0 else summary.total_logs})",
            "",
            "---",
            "",
            "_Generated by Failure Aggregation Agent. Aggregation only — no root-cause analysis._",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Wrote %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main(
    data_dir: Path = DATA_DIR,
    force_reparse: bool = False,
) -> Dict[str, Any]:
    """Run discovery → parse → aggregate → report generation."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    PARSED_LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_paths = discover_logs(data_dir)
    if not log_paths:
        logger.warning("No *.log files found under %s", data_dir)
        summary = DatasetSummary(0, 0, 0, 0, 0, None)
        generate_json(summary, [])
        generate_csv([])
        generate_dashboard_data([])
        generate_markdown(summary, [])
        return {"summary": asdict(summary), "patterns": []}

    parsed = parse_logs(log_paths, data_dir=data_dir, force=force_reparse)
    summary = calculate_statistics(parsed)
    patterns = aggregate_patterns(parsed)

    generate_json(summary, patterns)
    generate_csv(patterns)
    generate_dashboard_data(patterns)
    generate_markdown(summary, patterns)

    logger.info(
        "Done. logs=%d failed=%d good=%d unique_patterns=%d",
        summary.total_logs,
        summary.failed_logs,
        summary.good_logs,
        summary.unique_patterns,
    )
    return {
        "summary": asdict(summary),
        "pattern_count": len(patterns),
    }


if __name__ == "__main__":
    main()
