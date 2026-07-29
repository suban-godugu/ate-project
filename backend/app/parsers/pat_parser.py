"""Vendor-specific PAT parser framework — metadata only, no invented grammar.

PAT is not a universal standard. Supported vendor grammars are registered only after
a real sample is validated. Until then, parsing returns unsupported_pat_format.
"""

from __future__ import annotations

import gzip
import logging
import re
from dataclasses import dataclass, field
from typing import Callable

logger = logging.getLogger("verilumen.pat")

# Content signatures that indicate a file is PAT-like (detection aid — not parse grammar)
_PAT_TEXT_MARKERS = re.compile(
    r"(?im)"
    r"(?:^PAT_FILE\b|^PATTERN\b|^PAT_HEADER\b|^\s*VECTOR\b|^\s*WAVETBL\b|"
    r"IG-XL|UltraFlex|J750|V93000|Advantest|PAT_REVISION|PAT_VERSION)"
)

# Known vendor hints — detected for diagnostics; parsing requires registry entry + sample
_VENDOR_HINTS: list[tuple[str, re.Pattern[str]]] = [
    ("teradyne", re.compile(r"(?i)(IG-XL|UltraFlex|J750|Teradyne)")),
    ("advantest", re.compile(r"(?i)(V93000|93000|Advantest|SmarTest)")),
    ("generic_pat_text", re.compile(r"(?im)^PAT_FILE\b")),
]

# Populated only when a real vendor PAT grammar is validated against a fixture
_SUPPORTED_PARSERS: dict[str, Callable[[bytes, str], "PatParseResult"]] = {}


class PatParseError(Exception):
    code: str = "pat_error"

    def __init__(self, message: str, *, line: int | None = None):
        self.line = line
        loc = f" (line {line})" if line is not None else ""
        super().__init__(f"{message}{loc}")


class PatMalformedGrammar(PatParseError):
    code = "malformed_grammar"


class PatCorruptedFile(PatParseError):
    code = "corrupted_file"


class PatEncodingError(PatParseError):
    code = "encoding_error"


class PatUnsupportedFormat(PatParseError):
    code = "unsupported_pat_format"

    def __init__(
        self,
        message: str,
        *,
        vendor_hint: str | None = None,
        supported_vendors: list[str] | None = None,
        line: int | None = None,
    ):
        self.vendor_hint = vendor_hint
        self.supported_vendors = supported_vendors or list(_SUPPORTED_PARSERS.keys())
        super().__init__(message, line=line)


class PatUnsupportedVendor(PatParseError):
    code = "unsupported_vendor"

    def __init__(self, message: str, *, vendor: str, line: int | None = None):
        self.vendor = vendor
        super().__init__(message, line=line)


class PatUnsupportedVersion(PatParseError):
    code = "unsupported_version"


@dataclass
class PatPattern:
    name: str | None = None
    pattern_id: str | None = None
    revision: str | None = None
    category: str | None = None
    description: str | None = None
    pattern_group: str | None = None
    execution_order: int | None = None
    pattern_length: int | None = None
    vector_count: int | None = None
    cycle_count: int | None = None
    size_bytes: int | None = None
    compression: str | None = None
    attributes: dict = field(default_factory=dict)


@dataclass
class PatScanChain:
    name: str | None = None
    chain_length: int | None = None
    capture_cycles: int | None = None
    shift_cycles: int | None = None
    compression_ratio: float | None = None


@dataclass
class PatParseResult:
    vendor: str | None = None
    vendor_version: str | None = None
    header: dict[str, str] = field(default_factory=dict)
    patterns: list[PatPattern] = field(default_factory=list)
    scan_chains: list[PatScanChain] = field(default_factory=list)
    pins: list[str] = field(default_factory=list)
    signal_groups: list[str] = field(default_factory=list)
    clock_pins: list[str] = field(default_factory=list)
    reset_pins: list[str] = field(default_factory=list)
    control_pins: list[str] = field(default_factory=list)
    timing_sets: list[dict] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    file_size_bytes: int = 0

    @property
    def patterns_found(self) -> int:
        return len(self.patterns)

    def to_summary_dict(self) -> dict:
        return {
            "format": "pat",
            "vendor": self.vendor,
            "vendor_version": self.vendor_version,
            "patterns_found": self.patterns_found,
            "scan_chains": len(self.scan_chains),
            "pin_count": len(self.pins),
            "pattern_names": [p.name for p in self.patterns if p.name],
            "scan_chain_names": [c.name for c in self.scan_chains if c.name],
            "generator": self.header.get("Generator") or self.header.get("Tool"),
            "pattern_group": self.header.get("Pattern-Group"),
            "pattern_category": self.header.get("Pattern-Category"),
            "warnings": self.warnings,
        }

    def to_metadata_dict(self) -> dict:
        return {
            "vendor": self.vendor,
            "vendor_version": self.vendor_version,
            "header": self.header,
            "patterns": [p.__dict__ for p in self.patterns],
            "scan_chains": [c.__dict__ for c in self.scan_chains],
            "pins": self.pins,
            "signal_groups": self.signal_groups,
            "clock_pins": self.clock_pins,
            "reset_pins": self.reset_pins,
            "control_pins": self.control_pins,
            "timing_sets": self.timing_sets,
            "comments": self.comments,
            "warnings": self.warnings,
            "file_size_bytes": self.file_size_bytes,
        }

    def to_chains_dict(self) -> dict:
        return {
            "chains": [
                {
                    "chain_id": c.name,
                    "chain_length": c.chain_length,
                    "capture_cycles": c.capture_cycles,
                    "shift_cycles": c.shift_cycles,
                    "compression_ratio": c.compression_ratio,
                    "status": "defined",
                }
                for c in self.scan_chains
            ]
        }


def pat_text_markers_match(data: bytes) -> bool:
    """True when text content contains PAT-like signatures (not extension alone)."""
    sample = data[:8192].decode("utf-8", errors="replace")
    return bool(_PAT_TEXT_MARKERS.search(sample))


def looks_like_pat_binary(data: bytes) -> bool:
    """Heuristic for binary PAT candidates — high binary ratio, not STDF magic."""
    if len(data) < 4:
        return False
    if data[2:4] == bytes([0, 10]):  # STDF FAR-ish
        return False
    sample = data[:4096]
    printable = sum(1 for b in sample if 32 <= b <= 126 or b in (9, 10, 13)) / len(sample)
    return printable < 0.6


def looks_like_pat_content(data: bytes, logical_name: str) -> bool:
    """Content-aware PAT candidacy — never extension alone."""
    from pathlib import PurePath

    ext = PurePath(logical_name).suffix.lower()
    has_pat_ext = ext == ".pat" or logical_name.lower().endswith(".pat")

    if pat_text_markers_match(data):
        return True
    if has_pat_ext and looks_like_pat_binary(data):
        return True
    return False


def decompress_pat_bytes(file_name: str, data: bytes) -> tuple[bytes, str]:
    lower = file_name.lower()
    if lower.endswith(".gz"):
        inner = file_name[:-3]
        try:
            return gzip.decompress(data), inner
        except gzip.BadGzipFile as exc:
            raise PatCorruptedFile(f"Invalid gzip PAT payload: {exc}") from exc
    return data, file_name


def _parse_comment_header(comments: list[str]) -> dict[str, str]:
    header: dict[str, str] = {}
    for raw in comments:
        line = raw.lstrip("!#").strip()
        if not line:
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            header[key.strip()] = val.strip()
        else:
            header.setdefault("Notes", line)
    return header


def _extract_comment_lines(text: str) -> list[str]:
    comments: list[str] = []
    for line in text.splitlines()[:200]:
        stripped = line.strip()
        if stripped.startswith("!") or stripped.startswith("#"):
            comments.append(stripped)
    return comments


def identify_pat_vendor(data: bytes) -> str | None:
    """Return best-effort vendor hint from file header — does not imply support."""
    sample = data[:65536].decode("utf-8", errors="replace")
    for vendor_id, pattern in _VENDOR_HINTS:
        if pattern.search(sample):
            return vendor_id
    return None


def register_pat_vendor_parser(vendor_id: str, parser: Callable[[bytes, str], PatParseResult]) -> None:
    """Register a vendor parser after validating against a real PAT sample."""
    _SUPPORTED_PARSERS[vendor_id] = parser


def parse_pat_bytes(data: bytes, file_name: str = "upload.pat") -> PatParseResult:
    """Parse PAT if a supported vendor grammar is registered; otherwise fail gracefully."""
    try:
        raw, logical_name = decompress_pat_bytes(file_name, data)
    except PatCorruptedFile:
        raise
    except Exception as exc:
        raise PatCorruptedFile(f"Unable to read PAT payload: {exc}") from exc

    if not looks_like_pat_content(raw, logical_name):
        raise PatMalformedGrammar(
            "File does not match any known PAT content signature — "
            "provide a vendor PAT sample (Teradyne, Advantest, etc.)"
        )

    vendor_hint = identify_pat_vendor(raw)
    if vendor_hint and vendor_hint in _SUPPORTED_PARSERS:
        return _SUPPORTED_PARSERS[vendor_hint](raw, logical_name)

    comments = _extract_comment_lines(raw.decode("utf-8", errors="replace"))
    header = _parse_comment_header(comments)

    if vendor_hint:
        msg = (
            f"PAT vendor '{vendor_hint}' detected but no validated parser is registered. "
            "Add a real vendor PAT sample and register its grammar before parsing."
        )
    else:
        msg = (
            "PAT sample required — no supported vendor grammar registered. "
            "Provide a real Teradyne, Advantest, or toolchain-specific .pat file."
        )

    logger.warning(
        "Unsupported PAT format: file=%s vendor_hint=%s supported=%s",
        logical_name,
        vendor_hint,
        list(_SUPPORTED_PARSERS.keys()),
    )
    raise PatUnsupportedFormat(
        msg,
        vendor_hint=vendor_hint,
        supported_vendors=list(_SUPPORTED_PARSERS.keys()),
    )


def framework_status() -> dict:
    """Report parser framework readiness for verification."""
    return {
        "framework_ready": True,
        "supported_vendors": list(_SUPPORTED_PARSERS.keys()),
        "requires_real_sample": len(_SUPPORTED_PARSERS) == 0,
    }
