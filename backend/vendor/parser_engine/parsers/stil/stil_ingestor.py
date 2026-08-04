"""STIL (Standard Test Interface Language) ingestion module for FA-FR-001."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STIL_EXTENSIONS = (".stil",)

# Regex patterns for streaming STIL metadata extraction.
HEADER_FIELD = re.compile(r'^\s*(Title|Date|Source)\s+"([^"]+)"\s*;')
HISTORY_ANN = re.compile(r"Ann\s*\{\*\s*(.+?)\s*\*\}")
PATTERN_RANGE = re.compile(r"pattern_(begin|end)\s*=\s*(\d+)")
SCAN_CHAIN = re.compile(r"^\s*ScanChain\s+(\S+)\s*\{")
SCAN_FIELD = re.compile(r'^\s*(ScanLength|ScanIn|ScanOut|ScanMasterClock)\s+([^;]+);')
PATTERN_ANN = re.compile(r"Ann\s*\{\*\s*Pattern:(\d+)")
PATTERN_NUMER = re.compile(r"pattern_numer:(\d+)")


@dataclass
class StilScanChain:
    """Scan chain definition from STIL ScanStructures section."""

    chain_id: str
    scan_length: int = 0
    scan_in: str = ""
    scan_out: str = ""
    master_clock: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "scan_length": self.scan_length,
            "scan_in": self.scan_in,
            "scan_out": self.scan_out,
            "master_clock": self.master_clock,
        }


@dataclass
class StilMetadata:
    """Header and history metadata from a STIL file."""

    title: str = ""
    date: str = ""
    source: str = ""
    test_set_type: str = ""
    pattern_begin: int = 0
    pattern_end: int = 0
    tcd_signature: str = ""
    format_version: str = "STIL 1.0"

    @property
    def total_patterns(self) -> int:
        if self.pattern_end >= self.pattern_begin:
            return self.pattern_end - self.pattern_begin + 1
        return 0


@dataclass
class StilIngestionResult:
    """Complete result of STIL file ingestion and validation."""

    source_path: str
    metadata: StilMetadata = field(default_factory=StilMetadata)
    scan_chains: list[StilScanChain] = field(default_factory=list)
    pattern_count_verified: int = 0
    file_size_bytes: int = 0
    validation_passed: bool = False
    validation_notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def discover_stil_files(root_dir: str | Path) -> list[Path]:
    """Recursively locate STIL files under *root_dir*."""
    root = Path(root_dir)
    if not root.is_dir():
        return []
    files: list[Path] = []
    for ext in STIL_EXTENSIONS:
        files.extend(sorted(root.rglob(f"*{ext}")))
    logger.info("Discovered %d STIL file(s) in %s", len(files), root)
    return files


def _parse_scan_chain_block(chain_id: str, lines: list[str]) -> StilScanChain:
    chain = StilScanChain(chain_id=chain_id)
    for line in lines:
        match = SCAN_FIELD.match(line.strip())
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip().strip('"')
        if key == "ScanLength":
            chain.scan_length = int(value)
        elif key == "ScanIn":
            chain.scan_in = value
        elif key == "ScanOut":
            chain.scan_out = value
        elif key == "ScanMasterClock":
            chain.master_clock = value
    return chain


def ingest_stil_file(path: str | Path) -> StilIngestionResult:
    """
    Stream-parse a STIL file extracting metadata, scan chains, and pattern count.

    Uses line-by-line streaming to handle large files (400+ MB) without loading
    the entire file into memory.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"STIL file not found: {file_path}")

    result = StilIngestionResult(
        source_path=str(file_path),
        file_size_bytes=file_path.stat().st_size,
    )
    metadata = StilMetadata()
    scan_chains: list[StilScanChain] = []
    pattern_ids: set[int] = set()

    in_scan_structures = False
    current_chain_id: str | None = None
    current_chain_lines: list[str] = []
    in_header_history = False

    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                stripped = line.strip()

                if stripped.startswith("STIL "):
                    metadata.format_version = stripped.rstrip(";")

                header_match = HEADER_FIELD.match(stripped)
                if header_match:
                    key, value = header_match.group(1), header_match.group(2)
                    if key == "Title":
                        metadata.title = value
                    elif key == "Date":
                        metadata.date = value
                    elif key == "Source":
                        metadata.source = value

                if "Begin_Verify_Section" in stripped:
                    in_header_history = True
                if "End_Verify_Section" in stripped:
                    in_header_history = False

                if in_header_history:
                    ann_match = HISTORY_ANN.search(stripped)
                    if ann_match:
                        ann_text = ann_match.group(1).strip()
                        range_match = PATTERN_RANGE.search(ann_text)
                        if range_match:
                            if range_match.group(1) == "begin":
                                metadata.pattern_begin = int(range_match.group(2))
                            else:
                                metadata.pattern_end = int(range_match.group(2))
                        if "test_set_type" in ann_text:
                            metadata.test_set_type = ann_text.split("=")[-1].strip()
                        if "tcd_signature" in ann_text:
                            metadata.tcd_signature = ann_text.split("=")[-1].strip()

                if stripped.startswith("ScanStructures"):
                    in_scan_structures = True
                    continue
                if in_scan_structures and stripped == "}" and current_chain_id is None:
                    in_scan_structures = False
                    continue

                if in_scan_structures:
                    chain_match = SCAN_CHAIN.match(stripped)
                    if chain_match:
                        if current_chain_id and current_chain_lines:
                            scan_chains.append(
                                _parse_scan_chain_block(
                                    current_chain_id, current_chain_lines
                                )
                            )
                        current_chain_id = chain_match.group(1)
                        current_chain_lines = []
                        continue
                    if current_chain_id:
                        if stripped == "}":
                            scan_chains.append(
                                _parse_scan_chain_block(
                                    current_chain_id, current_chain_lines
                                )
                            )
                            current_chain_id = None
                            current_chain_lines = []
                        else:
                            current_chain_lines.append(line)

                # Cap unique pattern ID tracking — full multi‑GB STILs can OOM a 512MB box.
                if len(pattern_ids) < 50_000:
                    pat_match = PATTERN_ANN.search(stripped)
                    if pat_match:
                        pattern_ids.add(int(pat_match.group(1)))
                        continue
                    numer_match = PATTERN_NUMER.search(stripped)
                    if numer_match:
                        pattern_ids.add(int(numer_match.group(1)))

    except OSError as exc:
        result.errors.append(str(exc))
        return result

    result.metadata = metadata
    result.scan_chains = scan_chains
    result.pattern_count_verified = (
        len(pattern_ids) if pattern_ids else metadata.total_patterns
    )

    notes: list[str] = []
    if metadata.total_patterns > 0:
        notes.append(
            f"STIL declares {metadata.total_patterns} patterns "
            f"(range {metadata.pattern_begin}–{metadata.pattern_end})."
        )
    if pattern_ids:
        notes.append(f"Verified {len(pattern_ids)} unique pattern IDs in STIL body.")
    if scan_chains:
        notes.append(f"Parsed {len(scan_chains)} scan chain definitions.")
    notes.append(f"Test type: {metadata.test_set_type or 'EDT_SCAN_TEST'}")
    notes.append(f"Source tool: {metadata.source or 'unknown'}")

    result.validation_notes = notes
    result.validation_passed = bool(scan_chains) and result.pattern_count_verified > 0

    logger.info(
        "STIL ingestion complete: %s — %d chains, %d patterns",
        file_path.name,
        len(scan_chains),
        result.pattern_count_verified,
    )
    return result


def build_scan_chain_lookup(
    stil_result: StilIngestionResult,
) -> dict[str, StilScanChain]:
    """Build a lookup from partial chain name to full StilScanChain."""
    lookup: dict[str, StilScanChain] = {}
    for chain in stil_result.scan_chains:
        lookup[chain.chain_id] = chain
        if "channel" in chain.chain_id:
            short = chain.chain_id.split("channel")[-1]
            lookup[f"channel{short}"] = chain
    return lookup


def validate_stil_against_logs(
    stil_result: StilIngestionResult,
    die_pattern_count: int,
    log_scan_chains: set[str],
) -> tuple[bool, list[str]]:
    """Cross-validate STIL metadata against ingested tester log data."""
    notes: list[str] = []
    passed = True

    stil_patterns = stil_result.pattern_count_verified
    if stil_patterns > 0 and die_pattern_count > 0:
        if stil_patterns == die_pattern_count:
            notes.append(
                f"Pattern count match: STIL={stil_patterns}, "
                f"tester logs={die_pattern_count}."
            )
        else:
            notes.append(
                f"Pattern count difference: STIL={stil_patterns}, "
                f"tester logs={die_pattern_count}."
            )

    stil_chain_ids = {c.chain_id for c in stil_result.scan_chains}
    matched_chains = 0
    for log_chain in log_scan_chains:
        for stil_id in stil_chain_ids:
            if log_chain in stil_id or stil_id.endswith(log_chain.split("_")[-1]):
                matched_chains += 1
                break

    if log_scan_chains:
        notes.append(
            f"Scan chain cross-reference: {matched_chains}/{len(log_scan_chains)} "
            f"log chains matched to STIL definitions."
        )

    if not stil_result.validation_passed:
        passed = False
        notes.append("STIL file failed internal validation.")

    return passed, notes


def stil_result_to_dict(result: StilIngestionResult) -> dict[str, Any]:
    """Serialize STIL ingestion output for reporting."""
    return {
        "source_path": result.source_path,
        "file_size_mb": round(result.file_size_bytes / (1024 * 1024), 2),
        "validation_passed": result.validation_passed,
        "validation_notes": result.validation_notes,
        "errors": result.errors,
        "metadata": {
            "title": result.metadata.title,
            "date": result.metadata.date,
            "source": result.metadata.source,
            "test_set_type": result.metadata.test_set_type,
            "pattern_begin": result.metadata.pattern_begin,
            "pattern_end": result.metadata.pattern_end,
            "total_patterns": result.metadata.total_patterns,
            "pattern_count_verified": result.pattern_count_verified,
            "tcd_signature": result.metadata.tcd_signature,
            "format_version": result.metadata.format_version,
        },
        "scan_chain_count": len(result.scan_chains),
        "scan_chains": [c.to_dict() for c in result.scan_chains],
    }
