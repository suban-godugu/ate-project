"""IEEE 1450 STIL parser — extracts pattern/scan/timing/signal metadata only.

Does not infer pass/fail, yield, or test results (those belong to STDF).
"""

from __future__ import annotations

import gzip
import io
import logging
import re
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger("verilumen.stil")

_STIL_VERSION_RE = re.compile(r"^\s*STIL\s+([\d.]+)\s*;", re.IGNORECASE)

# IEEE 1450-1999 (STIL 1.0) top-level block keywords
_TOP_LEVEL_KEYWORDS = (
    "Header",
    "Signals",
    "SignalGroups",
    "Timing",
    "ScanStructures",
    "PatternBurst",
    "PatternExec",
    "Pattern",
    "MacroDefs",
    "Procedures",
    "Spec",
    "Core",
)


def _match_block_start(stripped: str) -> tuple[str, str | None] | None:
    """Return (block_keyword, optional_entity_name) for a block opening line."""
    named = re.match(
        r"(Pattern|PatternBurst|PatternExec)\s+(\w+)\s*\{",
        stripped,
        re.IGNORECASE,
    )
    if named:
        return named.group(1), named.group(2)
    plain = re.match(r"(\w+)\s*\{", stripped)
    if plain:
        return plain.group(1), None
    return None


_STIL_1_0_BLOCKS = frozenset(_TOP_LEVEL_KEYWORDS)

# IEEE 1450.1 / STIL 1.1 additions — reported as unsupported for 1.0-only parser
_STIL_1_1_BLOCKS = frozenset({"Environment", "Selector", "ActiveScanChains"})

# Known vendor / tool-specific top-level constructs (not IEEE 1450 core)
_VENDOR_BLOCKS = frozenset(
    {
        "CTLMode",
        "EdtRules",
        "SVF",
        "Tessent",
        "Internal",
        "DCLevels",
        "PinLevels",
        "TestMode",
    }
)

class StilParseError(Exception):
    """Base STIL parse error with diagnostic code."""

    code: str = "stil_error"

    def __init__(self, message: str, *, line: int | None = None):
        self.line = line
        loc = f" (line {line})" if line is not None else ""
        super().__init__(f"{message}{loc}")


class StilUnsupportedVersion(StilParseError):
    code = "unsupported_version"


class StilMalformedGrammar(StilParseError):
    code = "malformed_grammar"


class StilMissingSection(StilParseError):
    code = "missing_section"


class StilUnsupportedExtension(StilParseError):
    code = "unsupported_extension"

    def __init__(self, message: str, extensions: list[str], *, line: int | None = None):
        self.extensions = extensions
        super().__init__(message, line=line)


class StilCorruptedFile(StilParseError):
    code = "corrupted_file"


@dataclass
class StilSignal:
    name: str
    direction: str | None = None
    width: int | None = None


@dataclass
class StilScanChain:
    name: str
    chain_length: int | None = None
    scan_in: str | None = None
    scan_out: str | None = None
    scan_enable: str | None = None
    compression: str | None = None
    scan_order: str | None = None
    capture_cycles: int | None = None
    shift_cycles: int | None = None


@dataclass
class StilPattern:
    name: str
    pattern_id: str | None = None
    pattern_length: int | None = None
    vector_count: int | None = None
    cycle_count: int | None = None
    pattern_group: str | None = None
    pattern_category: str | None = None
    timing_wft: str | None = None


@dataclass
class StilParseResult:
    stil_version: str | None = None
    header: dict[str, str] = field(default_factory=dict)
    signals: list[StilSignal] = field(default_factory=list)
    signal_groups: dict[str, str] = field(default_factory=dict)
    waveform_tables: list[dict] = field(default_factory=list)
    timing_sets: list[dict] = field(default_factory=list)
    scan_structures: list[StilScanChain] = field(default_factory=list)
    patterns: list[StilPattern] = field(default_factory=list)
    pattern_bursts: list[dict] = field(default_factory=list)
    pattern_execs: list[dict] = field(default_factory=list)
    macro_defs: list[str] = field(default_factory=list)
    procedures: list[str] = field(default_factory=list)
    ports: list[dict] = field(default_factory=list)
    pins: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported_extensions: list[str] = field(default_factory=list)
    block_counts: dict[str, int] = field(default_factory=dict)
    clock_signals: list[str] = field(default_factory=list)
    reset_signals: list[str] = field(default_factory=list)
    control_signals: list[str] = field(default_factory=list)

    @property
    def patterns_found(self) -> int:
        return len(self.patterns)

    @property
    def scan_chains(self) -> int:
        return len(self.scan_structures)

    def to_summary_dict(self) -> dict:
        return {
            "format": "stil",
            "stil_version": self.stil_version,
            "title": self.header.get("Title"),
            "source": self.header.get("Source"),
            "date": self.header.get("Date"),
            "patterns_found": self.patterns_found,
            "scan_chains": self.scan_chains,
            "signal_count": len(self.signals),
            "signal_group_count": len(self.signal_groups),
            "waveform_table_count": len(self.waveform_tables),
            "pattern_names": [p.name for p in self.patterns],
            "scan_chain_names": [s.name for s in self.scan_structures],
            "warnings": self.warnings,
            "block_counts": self.block_counts,
        }

    def to_metadata_dict(self) -> dict:
        return {
            "stil_version": self.stil_version,
            "header": self.header,
            "signals": [
                {"name": s.name, "direction": s.direction, "width": s.width} for s in self.signals
            ],
            "signal_groups": self.signal_groups,
            "waveform_tables": self.waveform_tables,
            "timing_sets": self.timing_sets,
            "scan_structures": [
                {
                    "name": s.name,
                    "chain_length": s.chain_length,
                    "scan_in": s.scan_in,
                    "scan_out": s.scan_out,
                    "scan_enable": s.scan_enable,
                    "compression": s.compression,
                    "scan_order": s.scan_order,
                    "capture_cycles": s.capture_cycles,
                    "shift_cycles": s.shift_cycles,
                }
                for s in self.scan_structures
            ],
            "patterns": [
                {
                    "name": p.name,
                    "pattern_id": p.pattern_id,
                    "pattern_length": p.pattern_length,
                    "vector_count": p.vector_count,
                    "cycle_count": p.cycle_count,
                    "pattern_group": p.pattern_group,
                    "pattern_category": p.pattern_category,
                    "timing_wft": p.timing_wft,
                }
                for p in self.patterns
            ],
            "pattern_bursts": self.pattern_bursts,
            "pattern_execs": self.pattern_execs,
            "macro_defs": self.macro_defs,
            "procedures": self.procedures,
            "ports": self.ports,
            "pins": self.pins,
            "clock_signals": self.clock_signals,
            "reset_signals": self.reset_signals,
            "control_signals": self.control_signals,
            "comments": self.comments,
            "warnings": self.warnings,
            "block_counts": self.block_counts,
        }

    def to_chains_dict(self) -> dict:
        """Scan structure metadata for MinIO scan-chains.json (not test failures)."""
        return {
            "chains": [
                {
                    "chain_id": s.name,
                    "chain_length": s.chain_length,
                    "scan_in": s.scan_in,
                    "scan_out": s.scan_out,
                    "scan_enable": s.scan_enable,
                    "compression": s.compression,
                    "scan_order": s.scan_order,
                    "status": "defined",
                }
                for s in self.scan_structures
            ]
        }


def decompress_stil_bytes(file_name: str, data: bytes) -> tuple[bytes, str]:
    """Decompress .stil.gz payloads; returns (bytes, logical_file_name)."""
    lower = file_name.lower()
    if lower.endswith(".gz"):
        inner = file_name[:-3]
        try:
            return gzip.decompress(data), inner
        except gzip.BadGzipFile as exc:
            raise StilCorruptedFile(f"Invalid gzip STIL payload: {exc}") from exc
    return data, file_name


def _strip_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i : i + 2] == "//":
            while i < n and text[i] != "\n":
                i += 1
        elif text[i : i + 2] == "/*":
            end = text.find("*/", i + 2)
            if end == -1:
                break
            i = end + 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def _iter_stil_lines(data: bytes, chunk_size: int = 65536) -> Iterator[tuple[int, str]]:
    """Stream-decode UTF-8 STIL content line by line for low memory use."""
    buffer = ""
    line_no = 0
    stream = io.BytesIO(data)
    while True:
        chunk = stream.read(chunk_size)
        if not chunk and not buffer:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line_no += 1
            yield line_no, line.rstrip("\r")
        if not chunk:
            if buffer.strip():
                line_no += 1
                yield line_no, buffer.rstrip("\r")
            break


def _collect_block_lines(lines: Iterator[tuple[int, str]], start_line: int, first_line: str) -> tuple[str, int]:
    """Collect a braced block starting at first_line; return text and ending line."""
    text_parts = [first_line]
    depth = first_line.count("{") - first_line.count("}")
    end_line = start_line
    if depth <= 0:
        raise StilMalformedGrammar("Expected '{' to open block", line=start_line)
    for line_no, line in lines:
        end_line = line_no
        text_parts.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0:
            break
    else:
        raise StilMalformedGrammar("Unclosed block — missing '}'", line=end_line)
    return "\n".join(text_parts), end_line


def _parse_header_block(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for m in re.finditer(r'(\w+)\s+"([^"]*)"\s*;', body):
        fields[m.group(1)] = m.group(2)
    for m in re.finditer(r"(\w+)\s+(\S+)\s*;", body):
        key = m.group(1)
        if key not in fields:
            fields[key] = m.group(2).strip(";")
    return fields


def _parse_signals_block(body: str) -> list[StilSignal]:
    signals: list[StilSignal] = []
    for m in re.finditer(
        r"(\w+)\s+(In|Out|InOut|Supply|Pseudo|V|I)\s*(?:\[(\d+)\])?\s*;",
        body,
        re.IGNORECASE,
    ):
        direction = m.group(2)
        if direction.lower() in {"in", "out", "inout", "supply", "pseudo"}:
            direction = direction[0].upper() + direction[1:].lower()
            if direction == "Inout":
                direction = "InOut"
        width = int(m.group(3)) if m.group(3) else None
        signals.append(StilSignal(name=m.group(1), direction=direction, width=width))
    return signals


def _parse_signal_groups_block(body: str) -> dict[str, str]:
    groups: dict[str, str] = {}
    for m in re.finditer(r"(\w+)\s*=\s*'([^']*)'\s*;", body):
        groups[m.group(1)] = m.group(2)
    for m in re.finditer(r'(\w+)\s*=\s*"([^"]*)"\s*;', body):
        groups[m.group(1)] = m.group(2)
    return groups


def _parse_scan_structures_block(body: str) -> list[StilScanChain]:
    chains: list[StilScanChain] = []
    for block_m in re.finditer(r"(\w+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}", body, re.DOTALL):
        name = block_m.group(1)
        inner = block_m.group(2)
        chain = StilScanChain(name=name)
        len_m = re.search(r"ScanLength\s+(\d+)\s*;", inner, re.IGNORECASE)
        if len_m:
            chain.chain_length = int(len_m.group(1))
        for attr, field_name in (
            (r"ScanIn\s+(\w+)\s*;", "scan_in"),
            (r"ScanOut\s+(\w+)\s*;", "scan_out"),
            (r"ScanEnable\s+(\w+)\s*;", "scan_enable"),
            (r"ScanOrder\s+(\w+)\s*;", "scan_order"),
            (r"Compression\s+(\w+)\s*;", "compression"),
        ):
            m = re.search(attr, inner, re.IGNORECASE)
            if m:
                setattr(chain, field_name, m.group(1))
        cap = re.search(r"CaptureCycles\s+(\d+)\s*;", inner, re.IGNORECASE)
        if cap:
            chain.capture_cycles = int(cap.group(1))
        shift = re.search(r"ShiftCycles\s+(\d+)\s*;", inner, re.IGNORECASE)
        if shift:
            chain.shift_cycles = int(shift.group(1))
        chains.append(chain)
    return chains


def _count_vectors_or_cycles(body: str) -> tuple[int | None, int | None]:
    vector_count = None
    cycle_count = None
    v_block = re.search(r"\bV\s*\{([^}]*)\}", body, re.DOTALL | re.IGNORECASE)
    if v_block:
        lines = [ln.strip() for ln in v_block.group(1).splitlines() if ln.strip() and not ln.strip().startswith("//")]
        vector_count = len([ln for ln in lines if "=" in ln or re.match(r"^\w+\s+\S+", ln)])
    c_block = re.search(r"\bC\s*\{([^}]*)\}", body, re.DOTALL | re.IGNORECASE)
    if c_block:
        cycle_count = len(re.findall(r"\{", c_block.group(1))) or len(c_block.group(1).split(";"))
    return vector_count, cycle_count


def _parse_patterns_block(body: str) -> list[StilPattern]:
    patterns: list[StilPattern] = []
    for block_m in re.finditer(r"(\w+)\s*\{", body):
        name = block_m.group(1)
        if name.lower() in {"w", "v", "c", "macro", "call"}:
            continue
        start = block_m.start()
        sub = body[start:]
        depth = 0
        end_idx = 0
        for i, ch in enumerate(sub):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        if not end_idx:
            continue
        inner_block = sub[:end_idx]
        inner_body = inner_block[inner_block.find("{") + 1 : inner_block.rfind("}")]
        pat = StilPattern(name=name, pattern_id=name)
        wft = re.search(r"\bW\s+(\w+)\s*;", inner_body, re.IGNORECASE)
        if wft:
            pat.timing_wft = wft.group(1)
        pat.vector_count, pat.cycle_count = _count_vectors_or_cycles(inner_body)
        if pat.vector_count:
            pat.pattern_length = pat.vector_count
        patterns.append(pat)
    return patterns


def _parse_timing_block(body: str) -> tuple[list[dict], list[dict]]:
    waveform_tables: list[dict] = []
    timing_sets: list[dict] = []
    for wft_m in re.finditer(
        r"WaveformTable\s+(\w+)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}",
        body,
        re.DOTALL | re.IGNORECASE,
    ):
        name = wft_m.group(1)
        inner = wft_m.group(2)
        period_m = re.search(r"Period\s+'([^']+)'\s*;", inner, re.IGNORECASE)
        period = period_m.group(1) if period_m else None
        freq = None
        if period:
            num_m = re.match(r"([\d.]+)\s*(\w+)?", period)
            if num_m:
                try:
                    val = float(num_m.group(1))
                    unit = (num_m.group(2) or "s").lower()
                    seconds = val
                    if unit.startswith("n"):
                        seconds = val * 1e-9
                    elif unit.startswith("u"):
                        seconds = val * 1e-6
                    elif unit.startswith("m"):
                        seconds = val * 1e-3
                    if seconds:
                        freq = round(1.0 / seconds / 1e6, 4)
                except ValueError:
                    pass
        waveform_tables.append({"name": name, "period": period, "clock_frequency_mhz": freq})
        timing_sets.append({"name": name, "period": period})
    return waveform_tables, timing_sets


def _classify_block_name(name: str, version: str) -> str:
    """Return 'ok', 'vendor', or 'version'."""
    if name in _VENDOR_BLOCKS:
        return "vendor"
    if version.startswith("1.0") and name in _STIL_1_1_BLOCKS:
        return "version"
    if name not in _STIL_1_0_BLOCKS and name not in _STIL_1_1_BLOCKS:
        return "vendor"
    return "ok"


def parse_stil_text(text: str) -> StilParseResult:
    """Parse IEEE 1450 STIL text content."""
    result = StilParseResult()
    cleaned = _strip_comments(text)
    if not cleaned.strip():
        raise StilCorruptedFile("Empty STIL file")

    version_m = _STIL_VERSION_RE.search(cleaned)
    if not version_m:
        raise StilMalformedGrammar("Missing STIL version declaration (expected 'STIL 1.0;')")
    result.stil_version = version_m.group(1)
    if not result.stil_version.startswith("1."):
        raise StilUnsupportedVersion(f"Unsupported STIL version: {result.stil_version}")

    line_iter = iter(enumerate(cleaned.splitlines(), start=1))
    version_seen = False

    for line_no, line in line_iter:
        stripped = line.strip()
        if not stripped:
            continue
        if not version_seen:
            if _STIL_VERSION_RE.match(stripped):
                version_seen = True
            continue

        block_match = _match_block_start(stripped)
        if not block_match:
            if stripped.endswith(";") or stripped == "}":
                continue
            raise StilMalformedGrammar(f"Unexpected statement outside block: {stripped[:80]}", line=line_no)

        block_name, entity_name = block_match
        classification = _classify_block_name(block_name, result.stil_version or "1.0")
        if classification == "vendor":
            result.unsupported_extensions.append(block_name)
            logger.warning("Unsupported STIL vendor extension block: %s (line %s)", block_name, line_no)
            _collect_block_lines(line_iter, line_no, stripped)
            continue
        if classification == "version":
            result.warnings.append(f"STIL 1.1 block '{block_name}' encountered in {result.stil_version} file")
            _collect_block_lines(line_iter, line_no, stripped)
            continue

        block_text, _ = _collect_block_lines(line_iter, line_no, stripped)
        body = block_text[block_text.find("{") + 1 : block_text.rfind("}")]

        if block_name.lower() == "pattern" and entity_name:
            pat = StilPattern(name=entity_name, pattern_id=entity_name)
            wft = re.search(r"\bW\s+(\w+)\s*;", body, re.IGNORECASE)
            if wft:
                pat.timing_wft = wft.group(1)
            pat.vector_count, pat.cycle_count = _count_vectors_or_cycles(body)
            if pat.vector_count:
                pat.pattern_length = pat.vector_count
            result.patterns.append(pat)
            result.block_counts[block_name] = result.block_counts.get(block_name, 0) + 1
            continue

        if block_name.lower() == "patternburst" and entity_name:
            result.pattern_bursts.append({"name": entity_name})
            result.block_counts[block_name] = result.block_counts.get(block_name, 0) + 1
            continue

        if block_name.lower() == "patternexec" and entity_name:
            result.pattern_execs.append({"name": entity_name})
            result.block_counts[block_name] = result.block_counts.get(block_name, 0) + 1
            continue

        result.block_counts[block_name] = result.block_counts.get(block_name, 0) + 1

        if block_name == "Header":
            result.header = _parse_header_block(body)
        elif block_name == "Signals":
            result.signals.extend(_parse_signals_block(body))
            for sig in result.signals:
                low = sig.name.lower()
                if "clk" in low or "clock" in low:
                    result.clock_signals.append(sig.name)
                elif "reset" in low or "rst" in low:
                    result.reset_signals.append(sig.name)
                elif "en" in low or "ctrl" in low or "scan" in low:
                    result.control_signals.append(sig.name)
        elif block_name == "SignalGroups":
            result.signal_groups.update(_parse_signal_groups_block(body))
        elif block_name == "Timing":
            wfts, sets_ = _parse_timing_block(body)
            result.waveform_tables.extend(wfts)
            result.timing_sets.extend(sets_)
        elif block_name == "ScanStructures":
            result.scan_structures.extend(_parse_scan_structures_block(body))
        elif block_name == "Pattern":
            result.patterns.extend(_parse_patterns_block(body))
        elif block_name == "PatternBurst":
            for m in re.finditer(r"(\w+)\s*\{", body):
                result.pattern_bursts.append({"name": m.group(1)})
        elif block_name == "PatternExec":
            for m in re.finditer(r"(\w+)\s*\{", body):
                result.pattern_execs.append({"name": m.group(1)})
        elif block_name == "MacroDefs":
            result.macro_defs.extend(re.findall(r"(\w+)\s*\{", body))
        elif block_name == "Procedures":
            result.procedures.extend(re.findall(r"(\w+)\s*\{", body))

    if result.unsupported_extensions:
        raise StilUnsupportedExtension(
            f"Unsupported vendor extension(s): {', '.join(sorted(set(result.unsupported_extensions)))}",
            sorted(set(result.unsupported_extensions)),
        )

    if not result.signals and not result.patterns and not result.scan_structures:
        result.warnings.append("No Signals, Patterns, or ScanStructures blocks found")

    return result


def parse_stil_bytes(data: bytes, file_name: str = "upload.stil") -> StilParseResult:
    """Parse STIL from raw bytes; handles .stil.gz via file_name."""
    try:
        raw, logical_name = decompress_stil_bytes(file_name, data)
    except StilCorruptedFile:
        raise
    except Exception as exc:
        raise StilCorruptedFile(f"Unable to read STIL payload: {exc}") from exc

    if not logical_name.lower().endswith(".stil") and not _STIL_VERSION_RE.search(
        raw[:4096].decode("utf-8", errors="replace")
    ):
        raise StilMalformedGrammar("Content does not appear to be IEEE 1450 STIL")

    text = raw.decode("utf-8", errors="replace")
    return parse_stil_text(text)
