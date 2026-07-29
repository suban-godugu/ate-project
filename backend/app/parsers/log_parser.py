from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class LogParseResult:
    lot_id: str | None = None
    wafer_id: str | None = None
    tester_code: str | None = None
    product_code: str | None = None
    test_program: str | None = None
    files_processed: int = 1
    patterns_found: int | None = None
    scan_chains: int | None = None
    memory_blocks: int | None = None
    logic_blocks: int | None = None
    wafer_count: int | None = None
    defects_found: int | None = None
    yield_pct: float | None = None
    estimated_cost: float | None = None
    estimated_savings: float | None = None
    failures: list[dict] = field(default_factory=list)
    raw_fields: dict = field(default_factory=dict)


def _first_match(patterns: list[re.Pattern[str]], text: str) -> str | None:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return None


def _first_int(patterns: list[re.Pattern[str]], text: str) -> int | None:
    val = _first_match(patterns, text)
    if val is None:
        return None
    digits = re.sub(r"[^\d]", "", val)
    return int(digits) if digits else None


def _first_float(patterns: list[re.Pattern[str]], text: str) -> float | None:
    val = _first_match(patterns, text)
    if val is None:
        return None
    cleaned = val.replace("%", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


_LOT_PATTERNS = [
    re.compile(r"(?i)\blot(?:\s*(?:id|#))?\s*[:=]\s*([A-Za-z0-9._-]+)"),
    re.compile(r"(?i)\blot\s+([A-Za-z0-9._-]+)"),
]
_WAFER_PATTERNS = [
    re.compile(r"(?i)\bwafer(?:\s*(?:id|#))?\s*[:=]\s*([A-Za-z0-9._-]+)"),
    re.compile(r"(?i)\bwafer\s+([A-Za-z0-9._-]+)"),
]
_TESTER_PATTERNS = [
    re.compile(r"(?i)\btester(?:\s*(?:id|#))?\s*[:=]\s*([A-Za-z0-9._-]+)"),
    re.compile(r"(?i)\b(?:node|station)\s*[:=]\s*([A-Za-z0-9._-]+)"),
]
_PRODUCT_PATTERNS = [
    re.compile(r"(?i)\b(?:product|part(?:\s*type)?|device)\s*[:=]\s*([A-Za-z0-9._-]+)"),
]
_PROGRAM_PATTERNS = [
    re.compile(r"(?i)\b(?:program|job|test\s*program)\s*[:=]\s*([A-Za-z0-9._-]+)"),
]
_YIELD_PATTERNS = [
    re.compile(r"(?i)\byield\s*[:=]\s*([\d.]+%?)"),
    re.compile(r"(?i)\bwafer\s+yield\s*[:=]\s*([\d.]+%?)"),
]
_PATTERNS_FOUND = [
    re.compile(r"(?i)\bpatterns?\s*(?:found|count|total)?\s*[:=]\s*(\d+)"),
]
_SCAN_CHAINS = [
    re.compile(r"(?i)\bscan\s*chains?\s*[:=]\s*(\d+)"),
]
_MEMORY_BLOCKS = [
    re.compile(r"(?i)\bmemory\s*blocks?\s*[:=]\s*(\d+)"),
    re.compile(r"(?i)\bmbist\s*blocks?\s*[:=]\s*(\d+)"),
]
_LOGIC_BLOCKS = [
    re.compile(r"(?i)\blogic\s*blocks?\s*[:=]\s*(\d+)"),
    re.compile(r"(?i)\blbist\s*blocks?\s*[:=]\s*(\d+)"),
]
_WAFER_COUNT = [
    re.compile(r"(?i)\bwafer\s*count\s*[:=]\s*(\d+)"),
    re.compile(r"(?i)\bwafers\s*processed\s*[:=]\s*(\d+)"),
]
_DEFECTS = [
    re.compile(r"(?i)\bdefects?\s*(?:found)?\s*[:=]\s*(\d+)"),
    re.compile(r"(?i)\bfail(?:ures|s)?\s*[:=]\s*(\d+)"),
]
_COST = [
    re.compile(r"(?i)\b(?:test\s*)?cost\s*[:=]\s*\$?\s*([\d,]+(?:\.\d+)?)"),
]
_SAVINGS = [
    re.compile(r"(?i)\b(?:estimated\s*)?savings\s*[:=]\s*\$?\s*([\d,]+(?:\.\d+)?)"),
]

_FAIL_LINE = re.compile(r"(?i)^\s*FAIL\b")


def parse_log_file(text: str) -> LogParseResult:
    result = LogParseResult()
    result.lot_id = _first_match(_LOT_PATTERNS, text)
    result.wafer_id = _first_match(_WAFER_PATTERNS, text)
    result.tester_code = _first_match(_TESTER_PATTERNS, text)
    result.product_code = _first_match(_PRODUCT_PATTERNS, text)
    result.test_program = _first_match(_PROGRAM_PATTERNS, text)
    result.patterns_found = _first_int(_PATTERNS_FOUND, text)
    result.scan_chains = _first_int(_SCAN_CHAINS, text)
    result.memory_blocks = _first_int(_MEMORY_BLOCKS, text)
    result.logic_blocks = _first_int(_LOGIC_BLOCKS, text)
    result.wafer_count = _first_int(_WAFER_COUNT, text)
    result.defects_found = _first_int(_DEFECTS, text)
    result.yield_pct = _first_float(_YIELD_PATTERNS, text)
    result.estimated_cost = _first_float(_COST, text)
    result.estimated_savings = _first_float(_SAVINGS, text)

    pattern_hits = set(re.findall(r"(?i)\bP[-\w]+\b", text))
    chain_hits = set(re.findall(r"(?i)\bSC[-\w]+\b", text))
    if result.patterns_found is None and pattern_hits:
        result.patterns_found = len(pattern_hits)
    if result.scan_chains is None and chain_hits:
        result.scan_chains = len(chain_hits)

    for line in text.splitlines():
        if not _FAIL_LINE.search(line):
            continue
        chain = _first_match([re.compile(r"\b(SC-\w+)")], line)
        pattern = _first_match([re.compile(r"\b(P-\w+)")], line)
        cycle = _first_int([re.compile(r"(?i)\bcycle\s*[:=]\s*(\d+)")], line)
        if chain or pattern:
            result.failures.append(
                {
                    "chain_id": chain or f"SC-LOG-{len(result.failures) + 1}",
                    "pattern_id": pattern,
                    "fail_cycle": cycle,
                    "fail_type": "log-reported",
                    "root_cause": line.strip()[:500],
                }
            )

    if result.defects_found is None and result.failures:
        result.defects_found = len(result.failures)

    result.raw_fields = {
        k: v
        for k, v in {
            "lot_id": result.lot_id,
            "wafer_id": result.wafer_id,
            "tester_code": result.tester_code,
            "product_code": result.product_code,
            "patterns_found": result.patterns_found,
            "scan_chains": result.scan_chains,
        }.items()
        if v is not None
    }
    return result
