"""TSSI Waveform Generation Language (WGL) parser — metadata only.

Extracts pattern, waveform, pin/signal, scan, and timing metadata.
Does not infer pass/fail, yield, or diagnosis (STDF domain).
"""

from __future__ import annotations

import gzip
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger("verilumen.wgl")

_WGL_PROGRAM_START = re.compile(r"^\s*waveform\s*(?:\(\s*\))?\s*$", re.IGNORECASE)

# TSSI WGL block keywords (BNF WaveformBlocks)
_WGL_BLOCKS = frozenset(
    {
        "signal",
        "signals",
        "timeplate",
        "timeplates",
        "pattern",
        "patterns",
        "scanchain",
        "pingroup",
        "pingroups",
        "timegen",
        "timegens",
        "format",
        "formats",
        "timeset",
        "timesets",
        "register",
        "registers",
        "symbolic",
        "symbolics",
        "subroutine",
        "subroutines",
        "scancell",
        "scancells",
        "scanstate",
        "scanstates",
        "equationsheet",
        "equationdefaults",
        "pmode",
    }
)

# Vendor-specific constructs outside standard WGL — warn and skip
_WGL_VENDOR_BLOCKS = frozenset(
    {
        "ctlmode",
        "edtrules",
        "tessent",
        "internal",
        "dblevels",
        "pinlevels",
        "testmode",
        "stil",
    }
)


class WglParseError(Exception):
    code: str = "wgl_error"

    def __init__(self, message: str, *, line: int | None = None):
        self.line = line
        loc = f" (line {line})" if line is not None else ""
        super().__init__(f"{message}{loc}")


class WglMalformedGrammar(WglParseError):
    code = "malformed_grammar"


class WglCorruptedFile(WglParseError):
    code = "corrupted_file"


class WglEncodingError(WglParseError):
    code = "encoding_error"


@dataclass
class WglPin:
    name: str
    direction: str | None = None
    width: int | None = None
    atepin: str | None = None
    group: str | None = None


@dataclass
class WglScanChain:
    name: str
    members: list[str] = field(default_factory=list)
    radix: str | None = None
    scan_in: str | None = None
    scan_out: str | None = None
    compression: str | None = None
    scan_order: str | None = None


@dataclass
class WglPattern:
    name: str
    pattern_id: str | None = None
    pattern_group: str | None = None
    pattern_category: str | None = None
    description: str | None = None
    version: str | None = None
    vector_count: int | None = None
    cycle_count: int | None = None
    pattern_length: int | None = None
    shift_cycles: int | None = None
    capture_cycles: int | None = None
    timeplate: str | None = None


@dataclass
class WglWaveform:
    name: str
    period: str | None = None
    frequency_mhz: float | None = None
    drive_states: list[str] = field(default_factory=list)
    compare_states: list[str] = field(default_factory=list)


@dataclass
class WglParseResult:
    header: dict[str, str] = field(default_factory=dict)
    pins: list[WglPin] = field(default_factory=list)
    pin_groups: dict[str, list[str]] = field(default_factory=dict)
    waveforms: list[WglWaveform] = field(default_factory=list)
    timing_sets: list[dict] = field(default_factory=list)
    patterns: list[WglPattern] = field(default_factory=list)
    scan_chains: list[WglScanChain] = field(default_factory=list)
    procedures: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported_extensions: list[str] = field(default_factory=list)
    block_counts: dict[str, int] = field(default_factory=dict)
    clock_pins: list[str] = field(default_factory=list)
    reset_pins: list[str] = field(default_factory=list)
    enable_pins: list[str] = field(default_factory=list)

    @property
    def patterns_found(self) -> int:
        return len(self.patterns)

    @property
    def scan_chain_count(self) -> int:
        return len(self.scan_chains)

    def to_summary_dict(self) -> dict:
        return {
            "format": "wgl",
            "title": self.header.get("Title"),
            "device": self.header.get("Device"),
            "tester": self.header.get("Tester"),
            "patterns_found": self.patterns_found,
            "scan_chains": self.scan_chain_count,
            "pin_count": len(self.pins),
            "waveform_count": len(self.waveforms),
            "pattern_names": [p.name for p in self.patterns],
            "scan_chain_names": [c.name for c in self.scan_chains],
            "waveform_names": [w.name for w in self.waveforms],
            "warnings": self.warnings,
            "unsupported_extensions": self.unsupported_extensions,
            "block_counts": self.block_counts,
        }

    def to_metadata_dict(self) -> dict:
        return {
            "header": self.header,
            "pins": [
                {
                    "name": p.name,
                    "direction": p.direction,
                    "width": p.width,
                    "atepin": p.atepin,
                    "group": p.group,
                }
                for p in self.pins
            ],
            "pin_groups": self.pin_groups,
            "waveforms": [
                {
                    "name": w.name,
                    "period": w.period,
                    "frequency_mhz": w.frequency_mhz,
                    "drive_states": w.drive_states,
                    "compare_states": w.compare_states,
                }
                for w in self.waveforms
            ],
            "timing_sets": self.timing_sets,
            "patterns": [
                {
                    "name": p.name,
                    "pattern_id": p.pattern_id,
                    "pattern_group": p.pattern_group,
                    "pattern_category": p.pattern_category,
                    "description": p.description,
                    "version": p.version,
                    "vector_count": p.vector_count,
                    "cycle_count": p.cycle_count,
                    "pattern_length": p.pattern_length,
                    "shift_cycles": p.shift_cycles,
                    "capture_cycles": p.capture_cycles,
                    "timeplate": p.timeplate,
                }
                for p in self.patterns
            ],
            "scan_chains": [
                {
                    "name": c.name,
                    "members": c.members,
                    "radix": c.radix,
                    "scan_in": c.scan_in,
                    "scan_out": c.scan_out,
                    "compression": c.compression,
                    "scan_order": c.scan_order,
                }
                for c in self.scan_chains
            ],
            "procedures": self.procedures,
            "clock_pins": self.clock_pins,
            "reset_pins": self.reset_pins,
            "enable_pins": self.enable_pins,
            "comments": self.comments,
            "warnings": self.warnings,
            "unsupported_extensions": self.unsupported_extensions,
            "block_counts": self.block_counts,
        }

    def to_waveform_dict(self) -> dict:
        return {"waveforms": [w.__dict__ for w in self.waveforms], "timing_sets": self.timing_sets}

    def to_chains_dict(self) -> dict:
        return {
            "chains": [
                {
                    "chain_id": c.name,
                    "scan_in": c.scan_in,
                    "scan_out": c.scan_out,
                    "members": c.members,
                    "radix": c.radix,
                    "status": "defined",
                }
                for c in self.scan_chains
            ]
        }


def decompress_wgl_bytes(file_name: str, data: bytes) -> tuple[bytes, str]:
    lower = file_name.lower()
    if lower.endswith(".gz"):
        inner = file_name[:-3]
        try:
            return gzip.decompress(data), inner
        except gzip.BadGzipFile as exc:
            raise WglCorruptedFile(f"Invalid gzip WGL payload: {exc}") from exc
    return data, file_name


def _strip_comments(text: str) -> tuple[str, list[str]]:
    comments: list[str] = []
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("!"):
            comments.append(stripped.lstrip("!").strip())
            continue
        hash_idx = line.find("#")
        if hash_idx >= 0:
            comments.append(line[hash_idx + 1 :].strip())
            line = line[:hash_idx]
        out.append(line)
    return "\n".join(out), comments


def _parse_header_comments(comments: list[str]) -> dict[str, str]:
    header: dict[str, str] = {}
    for raw in comments:
        if not raw:
            continue
        if ":" in raw:
            key, val = raw.split(":", 1)
            header[key.strip()] = val.strip()
        else:
            header.setdefault("Title", raw)
    return header


def _period_to_mhz(period: str | None) -> float | None:
    if not period:
        return None
    m = re.match(r"([\d.]+)\s*(\w+)?", period.strip(), re.IGNORECASE)
    if not m:
        return None
    try:
        val = float(m.group(1))
    except ValueError:
        return None
    unit = (m.group(2) or "s").lower()
    seconds = val
    if unit.startswith("n"):
        seconds = val * 1e-9
    elif unit.startswith("u"):
        seconds = val * 1e-6
    elif unit.startswith("m"):
        seconds = val * 1e-3
    elif unit.startswith("p"):
        seconds = val * 1e-12
    return round(1.0 / seconds / 1e6, 4) if seconds else None


_BLOCK_START = re.compile(
    r"^\s*(signal|timeplate|pattern|scanchain|pingroup|timegen|format|timeset|"
    r"register|symbolic|subroutine|scancell|scanstate|equationsheet|equationdefaults|pmode)\b",
    re.IGNORECASE,
)


def _find_matching_end(lines: list[str], start: int) -> int:
    depth = 1
    for i in range(start + 1, len(lines)):
        stripped = lines[i].strip()
        if not stripped:
            continue
        if _BLOCK_START.match(stripped):
            depth += 1
        elif stripped.lower() == "end":
            depth -= 1
            if depth <= 0:
                return i
    raise WglMalformedGrammar("Unclosed WGL block", line=start + 1)


def _parse_signal_block(body: str) -> list[WglPin]:
    pins: list[WglPin] = []
    for m in re.finditer(
        r"(\w+)\s*:\s*(input|output|bidir|mux)\s*;",
        body,
        re.IGNORECASE,
    ):
        direction = m.group(2).lower()
        pin = WglPin(name=m.group(1), direction=direction, width=None)
        atepin = re.search(rf"\b{m.group(1)}\b.*?atepin\s+(\S+)", body, re.IGNORECASE)
        if atepin:
            pin.atepin = atepin.group(1).rstrip(";")
        pins.append(pin)
    return pins


def _classify_pin(pin: WglPin, result: WglParseResult) -> None:
    low = pin.name.lower()
    if "clk" in low or "clock" in low:
        result.clock_pins.append(pin.name)
    elif "reset" in low or "rst" in low:
        result.reset_pins.append(pin.name)
    elif "en" in low or "enable" in low:
        result.enable_pins.append(pin.name)


def _parse_timeplate_block(name: str, block_text: str) -> WglWaveform:
    wf = WglWaveform(name=name)
    period_m = re.search(r"period\s+(\S+)", block_text, re.IGNORECASE)
    if period_m:
        wf.period = period_m.group(1).rstrip(";")
        wf.frequency_mhz = _period_to_mhz(wf.period)
    for m in re.finditer(r":=\s*(input|output)\[([^\]]+)\]", block_text, re.IGNORECASE):
        side = m.group(1).lower()
        edges = m.group(2)
        if side == "input":
            wf.drive_states.extend(re.findall(r":([A-Z]+)", edges, re.IGNORECASE))
        else:
            wf.compare_states.extend(re.findall(r":([A-Z]+)", edges, re.IGNORECASE))
    return wf


def _parse_pattern_block(name: str, body: str, header: dict[str, str]) -> WglPattern:
    pat = WglPattern(
        name=name,
        pattern_id=name,
        pattern_group=header.get("Pattern-Group"),
        pattern_category=header.get("Pattern-Category"),
        description=header.get("Description"),
        version=header.get("Version"),
    )
    vectors = re.findall(r"\bvector\s*\(", body, re.IGNORECASE)
    pat.vector_count = len(vectors) if vectors else None
    pat.pattern_length = pat.vector_count
    repeat_m = re.search(r"\brepeat\s+(\d+)\b", body, re.IGNORECASE)
    if repeat_m and pat.vector_count:
        pat.cycle_count = pat.vector_count * int(repeat_m.group(1))
    else:
        pat.cycle_count = pat.vector_count
    tp = re.search(r",\s*(\w+)\s*\)\s*:=", body)
    if tp:
        pat.timeplate = tp.group(1)
    shift = re.search(r"shift\s+(\d+)", body, re.IGNORECASE)
    if shift:
        pat.shift_cycles = int(shift.group(1))
    capture = re.search(r"capture\s+(\d+)", body, re.IGNORECASE)
    if capture:
        pat.capture_cycles = int(capture.group(1))
    return pat


def _parse_scanchain_block(body: str) -> list[WglScanChain]:
    chains: list[WglScanChain] = []
    for m in re.finditer(
        r"(\w+)\s*\[([^\]]+)\](?:\s*:\s*radix\s+(\w+))?\s*;",
        body,
        re.IGNORECASE,
    ):
        members = [x.strip() for x in m.group(2).split(",") if x.strip()]
        chain = WglScanChain(name=m.group(1), members=members, radix=m.group(3))
        if members:
            chain.scan_in = members[0].lstrip("!")
            chain.scan_out = members[-1].lstrip("!")
        chains.append(chain)
    return chains


def _skip_unknown_block(lines: list[str], start: int) -> int:
    try:
        return _find_matching_end(lines, start)
    except WglMalformedGrammar:
        return start


def parse_wgl_text(text: str) -> WglParseResult:
    cleaned, comment_lines = _strip_comments(text)
    result = WglParseResult(comments=comment_lines)
    result.header = _parse_header_comments(comment_lines)

    if not cleaned.strip():
        raise WglCorruptedFile("Empty WGL file")

    lines = cleaned.splitlines()
    first_non_empty = next((i for i, ln in enumerate(lines) if ln.strip()), None)
    if first_non_empty is None or not _WGL_PROGRAM_START.match(lines[first_non_empty].strip()):
        raise WglMalformedGrammar("WGL program must begin with 'waveform'")

    last_end = None
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip().lower() == "end":
            last_end = i
            break
    if last_end is None:
        raise WglMalformedGrammar("WGL program must terminate with 'end'")

    i = first_non_empty + 1
    while i < last_end:
        raw = lines[i].strip()
        if not raw:
            i += 1
            continue

        block_m = re.match(r"(\w+)(?:\s+(\w+))?", raw, re.IGNORECASE)
        if not block_m:
            i += 1
            continue

        keyword = block_m.group(1).lower()
        name = block_m.group(2)

        if keyword in _WGL_VENDOR_BLOCKS:
            ext = block_m.group(1)
            result.unsupported_extensions.append(ext)
            result.warnings.append(f"Unsupported WGL extension skipped: {ext}")
            logger.warning("Unsupported WGL vendor block: %s", ext)
            end_i = _skip_unknown_block(lines, i)
            i = end_i + 1
            continue

        if keyword not in _WGL_BLOCKS:
            ext = block_m.group(1)
            result.unsupported_extensions.append(ext)
            result.warnings.append(f"Unknown WGL block skipped: {ext}")
            logger.warning("Unknown WGL block: %s", ext)
            end_i = _skip_unknown_block(lines, i)
            i = end_i + 1
            continue

        end_i = _find_matching_end(lines, i)
        body = "\n".join(lines[i + 1 : end_i])
        block_text = "\n".join(lines[i : end_i + 1])
        result.block_counts[keyword] = result.block_counts.get(keyword, 0) + 1

        if keyword in ("signal", "signals"):
            for pin in _parse_signal_block(body):
                _classify_pin(pin, result)
                result.pins.append(pin)
        elif keyword == "timeplate":
            tp_name = name or "default"
            result.waveforms.append(_parse_timeplate_block(tp_name, block_text))
            result.timing_sets.append({"name": tp_name, "period": result.waveforms[-1].period})
        elif keyword == "pattern":
            pat_name = name or "unnamed"
            result.patterns.append(_parse_pattern_block(pat_name, body, result.header))
        elif keyword in ("scanchain",):
            if name:
                member_m = re.search(r"\[([^\]]+)\]", body)
                members = [x.strip() for x in member_m.group(1).split(",")] if member_m else []
                chain = WglScanChain(name=name, members=members)
                if members:
                    chain.scan_in = members[0].lstrip("!")
                    chain.scan_out = members[-1].lstrip("!")
                result.scan_chains.append(chain)
            else:
                result.scan_chains.extend(_parse_scanchain_block(body))
        elif keyword == "subroutine":
            sub_m = re.match(r"subroutine\s+(\w+)", raw, re.IGNORECASE)
            if sub_m:
                result.procedures.append(sub_m.group(1))
        elif keyword == "pingroup":
            for gm in re.finditer(r"(\w+)\s*=\s*\[([^\]]+)\]\s*;", body):
                result.pin_groups[gm.group(1)] = [p.strip() for p in gm.group(2).split(",")]

        i = end_i + 1

    if result.unsupported_extensions:
        result.warnings.append(
            "Unsupported WGL extension(s): " + ", ".join(sorted(set(result.unsupported_extensions)))
        )

    return result


def parse_wgl_bytes(data: bytes, file_name: str = "upload.wgl") -> WglParseResult:
    try:
        raw, logical_name = decompress_wgl_bytes(file_name, data)
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WglEncodingError(f"WGL file is not valid UTF-8: {exc}") from exc
    except WglCorruptedFile:
        raise
    except Exception as exc:
        raise WglCorruptedFile(f"Unable to read WGL payload: {exc}") from exc

    if not logical_name.lower().endswith(".wgl") and not _WGL_PROGRAM_START.match(
        text.lstrip().splitlines()[0] if text.strip() else ""
    ):
        raise WglMalformedGrammar("Content does not appear to be WGL (expected 'waveform' program start)")

    return parse_wgl_text(text)
