"""
PA-FR-005 additive scan vector cache builder.

Writes per-pattern H/L/X scan response bit sequences to a standalone cache file.
Does not modify PA-FR-001 through PA-FR-004 outputs.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional

from ate_parser import ATEParser

CACHE_FILENAME = "PA-FR-005_scan_vector_cache.json"
GENERATED_BY = "PA-FR-005-scan-vector-cache"
SYMBOL_MAP = {"L": "0", "H": "1", "X": "X"}


def invert_bit(char: str) -> str:
    if char == "H":
        return "L"
    if char == "L":
        return "H"
    return char


def reconstruct_actual_stream(expected: str, actual: str, status: str) -> str:
    if actual and len(actual) == len(expected):
        return actual

    reconstructed: List[str] = []
    for i, exp_char in enumerate(expected):
        if actual and i < len(actual):
            reconstructed.append(actual[i])
        else:
            if status == "FAIL":
                reconstructed.append(invert_bit(exp_char))
            else:
                reconstructed.append(exp_char)
    return "".join(reconstructed)


def hl_stream_to_symbols(stream: str) -> str:
    symbols: List[str] = []
    for char in stream:
        if char in SYMBOL_MAP:
            symbols.append(SYMBOL_MAP[char])
        elif char in ("0", "1"):
            symbols.append(char)
    return "".join(symbols)


def chain_sort_key(chain_id: str) -> int:
    match = re.match(r"CH(\d+)", chain_id, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def pattern_sort_key(pattern_id: str) -> List[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", pattern_id)]


def build_scan_vector_cache_from_ate_data(
    ate_data: Dict[str, Any],
    source_file: str,
    ate_log_used: str,
) -> Dict[str, Any]:
    """Build scan-vector cache payload from already-parsed ATE data (no re-parse)."""
    patterns: List[Dict[str, Any]] = []
    for pattern_id in sorted(ate_data.keys(), key=pattern_sort_key):
        chains_raw = ate_data[pattern_id]
        chain_entries: List[Dict[str, str]] = []
        concatenated_parts: List[str] = []

        for chain_id in sorted(chains_raw.keys(), key=chain_sort_key):
            ch_data = chains_raw[chain_id]
            reconstructed = reconstruct_actual_stream(
                ch_data.get("expected", ""),
                ch_data.get("actual", ""),
                ch_data.get("status", "PASS"),
            )
            bit_sequence = hl_stream_to_symbols(reconstructed)
            chain_entries.append(
                {
                    "scan_chain_id": chain_id,
                    "bit_sequence": bit_sequence,
                }
            )
            concatenated_parts.append(bit_sequence)

        patterns.append(
            {
                "pattern_id": pattern_id,
                "chains": chain_entries,
                "concatenated_sequence": "".join(concatenated_parts),
            }
        )

    return {
        "generated_by": GENERATED_BY,
        "source_file": os.path.basename(source_file),
        "ate_log_used": os.path.basename(ate_log_used),
        "symbol_map": SYMBOL_MAP,
        "patterns": patterns,
    }


def build_scan_vector_cache(ate_log_path: str, source_file: str) -> Dict[str, Any]:
    parser = ATEParser()
    ate_data = parser.parse(ate_log_path)
    return build_scan_vector_cache_from_ate_data(
        ate_data,
        source_file=source_file,
        ate_log_used=os.path.basename(ate_log_path),
    )


def write_scan_vector_cache(
    output_dir: str,
    ate_log_path: Optional[str],
    source_file: str,
) -> Optional[str]:
    if not ate_log_path or not os.path.exists(ate_log_path):
        return None

    os.makedirs(output_dir, exist_ok=True)
    cache = build_scan_vector_cache(ate_log_path, source_file)
    cache_path = os.path.join(output_dir, CACHE_FILENAME)
    with open(cache_path, "w", encoding="utf-8") as handle:
        json.dump(cache, handle, indent=2)
    return cache_path
