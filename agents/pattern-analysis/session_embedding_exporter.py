"""
Session embedding exporter — writes PA-Analysis-Session_embeddings.json only.

Reuses locked pattern_embedding feature extractors in-memory.
Never writes PA-FR-005_pattern_embeddings.json.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence

from analysis_session import SESSION_GENERATED_BY
from pattern_embedding import (
    ALGORITHM_NAME,
    EMBEDDING_DIMENSION,
    EMBEDDING_VERSION,
    FEATURE_VERSION,
    SIMILARITY_METRIC,
    EmbeddingGenerationError,
    build_metadata_rows,
    deterministic_timestamp,
    extract_part1_features,
    extract_part2_features,
    load_json,
    min_max_normalize,
    pattern_sort_key,
)
from session_config import SessionConfig
from session_log_cache import SessionLogEntry


def _default_metadata() -> Dict[str, Any]:
    return {
        "chain_count": 0,
        "max_chain_length": 0,
        "compression_ratio": 0.0,
        "total_flip_flops": 0,
        "vector_count": 0,
        "source_file": "",
    }


def _load_optional_metadata(metadata_path: Optional[str]) -> Dict[str, Any]:
    if not metadata_path or not os.path.exists(metadata_path):
        return _default_metadata()
    payload = load_json(metadata_path)
    merged = _default_metadata()
    merged.update(payload)
    return merged


def _pattern_coverage_lookup_from_entries(
    log_entries: Sequence[SessionLogEntry],
) -> Dict[tuple, Dict[str, Any]]:
    """Map (pattern_id, source_log_relpath|source_name) → pattern_level coverage row."""
    lookup: Dict[tuple, Dict[str, Any]] = {}
    for entry in log_entries:
        for row in entry.coverage.get("pattern_level") or []:
            pattern_id = str(row.get("pattern_id", ""))
            lookup[(pattern_id, entry.relative_path)] = row
            lookup[(pattern_id, entry.source_name)] = row
    return lookup


def _pattern_coverage_lookup(
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
) -> Dict[tuple, Dict[str, Any]]:
    """Legacy path: parse each log again (used when no shared cache is supplied)."""
    from ate_parser import ATEParser
    from coverage_calculator import CoverageCalculator

    parser = ATEParser()
    calculator = CoverageCalculator()
    lookup: Dict[tuple, Dict[str, Any]] = {}

    for absolute_path, relative_path in zip(absolute_log_paths, relative_log_paths):
        ate_data = parser.parse(absolute_path)
        coverage = calculator.calculate_coverage(ate_data)
        source_name = os.path.basename(absolute_path)
        for row in coverage.get("pattern_level") or []:
            pattern_id = str(row.get("pattern_id", ""))
            lookup[(pattern_id, relative_path)] = row
            lookup[(pattern_id, source_name)] = row
    return lookup


def build_session_embeddings(
    *,
    stil_file: str,
    scan_vectors: Dict[str, Any],
    absolute_log_paths: Sequence[str],
    relative_log_paths: Sequence[str],
    config: Optional[SessionConfig] = None,
    metadata_path: Optional[str] = None,
    log_entries: Optional[Sequence[SessionLogEntry]] = None,
) -> Dict[str, Any]:
    """
    Build per-execution embeddings (one vector per pattern × source log).

    embedding_strategy must be per_execution (Phase B agreed default).
    When log_entries is provided (E0), coverage is taken from the shared cache.
    """
    config = config or SessionConfig()
    strategy = config.embedding_strategy
    if strategy != "per_execution":
        raise ValueError(
            f"Unsupported embedding_strategy '{strategy}'. "
            "Phase B supports only 'per_execution'."
        )

    metadata = _load_optional_metadata(metadata_path)
    if log_entries is not None:
        coverage_lookup = _pattern_coverage_lookup_from_entries(log_entries)
    else:
        coverage_lookup = _pattern_coverage_lookup(absolute_log_paths, relative_log_paths)

    vector_rows = sorted(
        scan_vectors.get("vectors") or [],
        key=lambda item: (
            pattern_sort_key(str(item.get("pattern_id", ""))),
            str(item.get("source_log_relpath", item.get("source_log", ""))),
            int(item.get("run_id", 0)),
        ),
    )

    # Build pattern_lookup and ordered units for Part-2 min-max normalization cohort.
    units: List[Dict[str, Any]] = []
    pattern_lookup: Dict[str, Dict[str, Any]] = {}
    unit_keys: List[str] = []

    for row in vector_rows:
        pattern_id = str(row.get("pattern_id", ""))
        relpath = str(row.get("source_log_relpath", ""))
        source_log = str(row.get("source_log", ""))
        coverage = coverage_lookup.get((pattern_id, relpath)) or coverage_lookup.get(
            (pattern_id, source_log)
        )
        if coverage is None:
            continue
        unit_key = f"{pattern_id}::{relpath or source_log}"
        pattern_lookup[unit_key] = coverage
        unit_keys.append(unit_key)
        units.append(row)

    metadata_rows = build_metadata_rows(metadata, pattern_lookup, unit_keys)
    normalized_metadata: Dict[str, List[float]] = {
        name: min_max_normalize(values) for name, values in metadata_rows.items()
    }

    embeddings: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []

    for index, row in enumerate(units):
        pattern_id = str(row.get("pattern_id", ""))
        source_log = str(row.get("source_log", ""))
        relpath = str(row.get("source_log_relpath", ""))
        run_id = int(row.get("run_id", 0))
        sequence = row.get("concatenated_sequence", "")
        chains = row.get("chains") or []
        try:
            if not sequence:
                raise EmbeddingGenerationError("missing scan vector")
            part1 = extract_part1_features(sequence, chains)
            part2 = extract_part2_features(normalized_metadata, index)
            combined = part1 + part2
            if len(combined) != EMBEDDING_DIMENSION:
                raise EmbeddingGenerationError(
                    f"invalid embedding length {len(combined)} "
                    f"(expected {EMBEDDING_DIMENSION})"
                )
            embeddings.append(
                {
                    "pattern_id": pattern_id,
                    "source_log": source_log,
                    "source_log_relpath": relpath,
                    "run_id": run_id,
                    "embedding": combined,
                    "source_file": stil_file,
                    "feature_version": FEATURE_VERSION,
                    "created_timestamp": deterministic_timestamp(
                        f"{pattern_id}|{relpath or source_log}|{run_id}"
                    ),
                }
            )
        except EmbeddingGenerationError as exc:
            skipped.append(
                {
                    "pattern_id": pattern_id,
                    "source_log": source_log,
                    "reason": str(exc),
                }
            )

    embeddings.sort(
        key=lambda item: (
            str(item.get("pattern_id", "")),
            str(item.get("source_log", "")),
            int(item.get("run_id", 0)),
        )
    )

    return {
        "generated_by": SESSION_GENERATED_BY,
        "embedding_strategy": strategy,
        "embedding_version": EMBEDDING_VERSION,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "algorithm": ALGORITHM_NAME,
        "similarity_metric": SIMILARITY_METRIC,
        "patterns_embedded": len(embeddings),
        "patterns_skipped": len(skipped),
        "skipped": skipped,
        "embeddings": embeddings,
    }
