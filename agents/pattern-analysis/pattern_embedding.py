"""
PA-FR-005 Pattern Embedding Generation — deterministic hybrid embedding extension layer.

Reads:
  - output/PA-FR-005_scan_vector_cache.json (scan bit sequences)
  - output/PA-FR-003_metadata_metrics.json
  - output/PA-FR-004_toggle_coverage.json

Does not re-parse STIL/ATE or modify PA-FR-001..004 outputs.
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import statistics
import time
from datetime import datetime, timezone
from itertools import groupby
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_VERSION = "1.0"
FEATURE_VERSION = "1.0"
ALGORITHM_NAME = "DeterministicHybridEmbedding"
SIMILARITY_METRIC = "cosine"
EMBEDDING_DIMENSION = 128
PART1_DIMENSION = 120
PART2_DIMENSION = 8
WINDOW_COUNT = 64
MAX_CHAINS = 23
FLOAT_PRECISION = 6

# PA-PERF-009 — internal only (not public YAML). Serial remains permanent golden reference.
# True only after Engineering Validation Gate passes (feature + phase + L1 parity).
ENABLE_VECTORIZED_EMBEDDING_FEATURES = True
# CI/debug: dual-run serial+optimized; mismatch → serial fallback.
VALIDATE_EMBEDDING_FEATURE_PARITY = False

CACHE_FILENAME = "PA-FR-005_scan_vector_cache.json"
METADATA_FILENAME = "PA-FR-003_metadata_metrics.json"
COVERAGE_FILENAME = "PA-FR-004_toggle_coverage.json"
EMBEDDINGS_FILENAME = "PA-FR-005_pattern_embeddings.json"
MANIFEST_FILENAME = "embedding_manifest.json"
LOG_FILENAME = "PA-FR-005_embedding_generation.log"

PART1_FEATURE_ORDER: List[str] = (
    [f"window_density_{i}" for i in range(WINDOW_COUNT)]
    + [
        "global_ones_ratio",
        "global_zeros_ratio",
        "global_xs_ratio",
        "global_transition_rate",
        "global_mean_run_norm",
        "global_max_run_norm",
        "global_run_variance_norm",
        "global_shannon_entropy",
    ]
    + [
        f"chain_{chain_index:02d}_{metric}"
        for chain_index in range(1, MAX_CHAINS + 1)
        for metric in ("ones_ratio", "transition_rate")
    ]
    + [
        "cross_chain_ones_ratio_mean",
        "cross_chain_ones_ratio_std",
    ]
)

PART2_METADATA_ORDER: List[str] = [
    "chain_count",
    "max_chain_length",
    "compression_ratio",
    "toggle_coverage",
    "toggle_density",
    "toggle_count",
    "total_scan_flip_flops",
    "vector_count",
]


class EmbeddingGenerationError(Exception):
    """Raised when a single pattern cannot be embedded."""


def deterministic_timestamp(pattern_id: str) -> str:
    seed = int(hashlib.sha256(pattern_id.encode("utf-8")).hexdigest()[:8], 16)
    seconds = seed % 86400
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"2026-01-01T{hours:02d}:{minutes:02d}:{secs:02d}Z"


def round_float(value: float) -> float:
    return round(float(value), FLOAT_PRECISION)


def round_vector(values: Sequence[float]) -> List[float]:
    return [round_float(v) for v in values]


def pattern_sort_key(pattern_id: str) -> List[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", pattern_id)]


def chain_sort_key(chain_id: str) -> int:
    """
    Stable chain ordering for deterministic embeddings.

    Prefer CH<num> numeric ordering. If the naming scheme is different,
    fall back to deterministic lexical ordering.
    """
    match = re.match(r"CH(\d+)", chain_id or "", re.IGNORECASE)
    if match:
        return (0, int(match.group(1)))  # type: ignore[return-value]
    # Try to find any digits; otherwise fall back to lexical.
    digits = re.findall(r"\d+", chain_id or "")
    if digits:
        return (1, int(digits[0]))  # type: ignore[return-value]
    return (2, str(chain_id or "").lower())  # type: ignore[return-value]


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def count_care_transitions(sequence: str) -> int:
    transitions = 0
    last_val: Optional[int] = None
    for symbol in sequence:
        if symbol == "1":
            current = 1
        elif symbol == "0":
            current = 0
        else:
            current = None
        if last_val is not None and current is not None and last_val != current:
            transitions += 1
        if current is not None:
            last_val = current
    return transitions


def _symbol_histogram(sequence: str) -> Tuple[int, int, int]:
    """Single-pass 0/1/X counts (PA-PERF-009 Tier-1)."""
    count_0 = 0
    count_1 = 0
    count_x = 0
    for symbol in sequence:
        if symbol == "0":
            count_0 += 1
        elif symbol == "1":
            count_1 += 1
        elif symbol == "X":
            count_x += 1
    return count_0, count_1, count_x


def _symbol_distribution_from_counts(
    count_0: int,
    count_1: int,
    count_x: int,
    length: int,
) -> Tuple[float, float, float]:
    if length == 0:
        return 0.0, 0.0, 0.0
    return (
        count_0 / length,
        count_1 / length,
        count_x / length,
    )


def _shannon_entropy_from_counts(
    count_0: int,
    count_1: int,
    count_x: int,
    length: int,
) -> float:
    if length == 0:
        return 0.0
    entropy = 0.0
    for count in (count_0, count_1, count_x):
        if count == 0:
            continue
        probability = count / length
        entropy -= probability * math.log2(probability)
    return entropy


def symbol_distribution(sequence: str) -> Tuple[float, float, float]:
    if not sequence:
        return 0.0, 0.0, 0.0
    length = len(sequence)
    ones = sequence.count("1") / length
    zeros = sequence.count("0") / length
    xs = sequence.count("X") / length
    return zeros, ones, xs


def shannon_entropy_base2(sequence: str) -> float:
    if not sequence:
        return 0.0
    length = len(sequence)
    entropy = 0.0
    for symbol in ("0", "1", "X"):
        count = sequence.count(symbol)
        if count == 0:
            continue
        probability = count / length
        entropy -= probability * math.log2(probability)
    return entropy


def run_length_features(sequence: str) -> Tuple[float, float, float]:
    if not sequence:
        return 0.0, 0.0, 0.0
    runs = [len(list(group)) for _, group in groupby(sequence)]
    length = len(sequence)
    mean_run = statistics.mean(runs) / length
    max_run = max(runs) / length
    variance = statistics.pvariance(runs) / (length * length) if len(runs) > 1 else 0.0
    return mean_run, max_run, variance


def sliding_window_densities(sequence: str, window_count: int = WINDOW_COUNT) -> List[float]:
    if not sequence:
        return [0.0] * window_count
    length = len(sequence)
    densities: List[float] = []
    for index in range(window_count):
        start = (index * length) // window_count
        end = ((index + 1) * length) // window_count
        if end <= start:
            end = min(start + 1, length)
        window = sequence[start:end]
        if not window:
            densities.append(0.0)
        else:
            densities.append(window.count("1") / len(window))
    return densities


def per_chain_features(chains: Sequence[Dict[str, str]]) -> Tuple[List[float], float, float]:
    ordered = sorted(chains, key=lambda item: chain_sort_key(item.get("scan_chain_id", "")))

    # Geometry-robust: compute cross-chain statistics across *all* chains,
    # not just the first MAX_CHAINS slots we explicitly encode.
    ones_all: List[float] = []
    for ch in ordered:
        sequence = ch.get("bit_sequence") or ""
        _, ones_ratio, _ = symbol_distribution(sequence)
        ones_all.append(ones_ratio)

    features: List[float] = []
    for chain_index in range(MAX_CHAINS):
        if chain_index < len(ordered):
            sequence = ordered[chain_index]["bit_sequence"]
            _, ones_ratio, _ = symbol_distribution(sequence)
            transition_rate = 0.0
            if len(sequence) > 1:
                transition_rate = count_care_transitions(sequence) / (len(sequence) - 1)
        else:
            ones_ratio = 0.0
            transition_rate = 0.0
        features.extend([ones_ratio, transition_rate])

    if ones_all:
        mean_value = statistics.mean(ones_all)
        std_value = statistics.pstdev(ones_all) if len(ones_all) > 1 else 0.0
    else:
        mean_value = 0.0
        std_value = 0.0

    features.extend([mean_value, std_value])
    return features, mean_value, std_value


def per_chain_features_optimized(chains: Sequence[Dict[str, str]]) -> Tuple[List[float], float, float]:
    """Tier-1: single-pass histogram for ones_ratio; serial care transitions."""
    ordered = sorted(chains, key=lambda item: chain_sort_key(item.get("scan_chain_id", "")))

    ones_all: List[float] = []
    for ch in ordered:
        sequence = ch.get("bit_sequence") or ""
        _c0, count_1, _cx = _symbol_histogram(sequence)
        length = len(sequence)
        ones_all.append(count_1 / length if length else 0.0)

    features: List[float] = []
    for chain_index in range(MAX_CHAINS):
        if chain_index < len(ordered):
            sequence = ordered[chain_index]["bit_sequence"]
            _c0, count_1, _cx = _symbol_histogram(sequence)
            length = len(sequence)
            ones_ratio = count_1 / length if length else 0.0
            transition_rate = 0.0
            if length > 1:
                transition_rate = count_care_transitions(sequence) / (length - 1)
        else:
            ones_ratio = 0.0
            transition_rate = 0.0
        features.extend([ones_ratio, transition_rate])

    if ones_all:
        mean_value = statistics.mean(ones_all)
        std_value = statistics.pstdev(ones_all) if len(ones_all) > 1 else 0.0
    else:
        mean_value = 0.0
        std_value = 0.0

    features.extend([mean_value, std_value])
    return features, mean_value, std_value


def extract_part1_features_serial(
    sequence: str,
    chains: Sequence[Dict[str, str]],
) -> List[float]:
    """Permanent golden reference (pre-PERF-009 semantics)."""
    window_features = sliding_window_densities(sequence, WINDOW_COUNT)
    zeros_ratio, ones_ratio, xs_ratio = symbol_distribution(sequence)
    transition_rate = 0.0
    if len(sequence) > 1:
        transition_rate = count_care_transitions(sequence) / (len(sequence) - 1)
    mean_run, max_run, run_variance = run_length_features(sequence)
    entropy = shannon_entropy_base2(sequence)
    chain_features, _, _ = per_chain_features(chains)

    part1 = window_features + [
        ones_ratio,
        zeros_ratio,
        xs_ratio,
        transition_rate,
        mean_run,
        max_run,
        run_variance,
        entropy,
    ] + chain_features

    if len(part1) != PART1_DIMENSION:
        raise EmbeddingGenerationError(
            f"Part 1 dimension mismatch: expected {PART1_DIMENSION}, got {len(part1)}"
        )
    return round_vector(part1)


def extract_part1_features_optimized(
    sequence: str,
    chains: Sequence[Dict[str, str]],
) -> List[float]:
    """
    PA-PERF-009 Tier-1: fused histogram for globals + chain ones;
    windows / transitions / run-length remain serial.
    """
    window_features = sliding_window_densities(sequence, WINDOW_COUNT)
    length = len(sequence)
    count_0, count_1, count_x = _symbol_histogram(sequence)
    zeros_ratio, ones_ratio, xs_ratio = _symbol_distribution_from_counts(
        count_0, count_1, count_x, length
    )
    transition_rate = 0.0
    if length > 1:
        transition_rate = count_care_transitions(sequence) / (length - 1)
    mean_run, max_run, run_variance = run_length_features(sequence)
    entropy = _shannon_entropy_from_counts(count_0, count_1, count_x, length)
    chain_features, _, _ = per_chain_features_optimized(chains)

    part1 = window_features + [
        ones_ratio,
        zeros_ratio,
        xs_ratio,
        transition_rate,
        mean_run,
        max_run,
        run_variance,
        entropy,
    ] + chain_features

    if len(part1) != PART1_DIMENSION:
        raise EmbeddingGenerationError(
            f"Part 1 dimension mismatch: expected {PART1_DIMENSION}, got {len(part1)}"
        )
    return round_vector(part1)


def extract_part1_features(sequence: str, chains: Sequence[Dict[str, str]]) -> List[float]:
    """Production wrapper: serial golden until ENABLE; optional dual-run validation."""
    if not ENABLE_VECTORIZED_EMBEDDING_FEATURES:
        return extract_part1_features_serial(sequence, chains)

    optimized = extract_part1_features_optimized(sequence, chains)
    if VALIDATE_EMBEDDING_FEATURE_PARITY:
        serial = extract_part1_features_serial(sequence, chains)
        if serial != optimized:
            logger.error(
                "PA-PERF-009 Part-1 parity failure; falling back to serial "
                "(120-d feature vector mismatch)."
            )
            return serial
    return optimized


def min_max_normalize_serial(values: Sequence[float]) -> List[float]:
    """Permanent golden reference for cohort Part-2 min-max."""
    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    normalized: List[float] = []
    for value in values:
        if max_value == min_value:
            scaled = 0.0
        else:
            scaled = (value - min_value) / (max_value - min_value)
        normalized.append(round_float(min(1.0, max(0.0, scaled))))
    return normalized


def min_max_normalize_numpy(values: Sequence[float]) -> List[float]:
    """PA-PERF-009 Tier-1: float64 column min-max + same per-element rounding."""
    if not values:
        return []
    arr = np.asarray(values, dtype=np.float64)
    min_value = float(np.min(arr))
    max_value = float(np.max(arr))
    if max_value == min_value:
        return [0.0] * len(values)
    scaled = (arr - min_value) / (max_value - min_value)
    scaled = np.clip(scaled, 0.0, 1.0)
    return [round_float(float(v)) for v in scaled]


def min_max_normalize(values: Sequence[float]) -> List[float]:
    """Production wrapper for Part-2 cohort normalization."""
    if not ENABLE_VECTORIZED_EMBEDDING_FEATURES:
        return min_max_normalize_serial(values)

    optimized = min_max_normalize_numpy(values)
    if VALIDATE_EMBEDDING_FEATURE_PARITY:
        serial = min_max_normalize_serial(values)
        if serial != optimized:
            logger.error(
                "PA-PERF-009 Part-2 min-max parity failure; falling back to serial."
            )
            return serial
    return optimized


def build_metadata_rows(
    metadata: Dict[str, Any],
    pattern_lookup: Dict[str, Dict[str, Any]],
    pattern_ids: Sequence[str],
) -> Dict[str, List[float]]:
    rows: Dict[str, List[float]] = {name: [] for name in PART2_METADATA_ORDER}

    for pattern_id in pattern_ids:
        pattern_stats = pattern_lookup.get(pattern_id)
        if pattern_stats is None:
            raise EmbeddingGenerationError(f"Missing toggle coverage for pattern {pattern_id}")

        rows["chain_count"].append(float(metadata.get("chain_count", 0)))
        rows["max_chain_length"].append(float(metadata.get("max_chain_length", 0)))
        rows["compression_ratio"].append(float(metadata.get("compression_ratio", 0)))
        rows["toggle_coverage"].append(float(pattern_stats.get("toggle_coverage_pct", 0)))
        rows["toggle_density"].append(float(pattern_stats.get("toggle_density_pct", 0)))
        rows["toggle_count"].append(float(pattern_stats.get("toggle_count", 0)))
        rows["total_scan_flip_flops"].append(float(metadata.get("total_flip_flops", 0)))
        rows["vector_count"].append(float(metadata.get("vector_count", 0)))

    return rows


def extract_part2_features(metadata_rows: Dict[str, List[float]], pattern_index: int) -> List[float]:
    values = [metadata_rows[name][pattern_index] for name in PART2_METADATA_ORDER]
    if len(values) != PART2_DIMENSION:
        raise EmbeddingGenerationError("Part 2 dimension mismatch")
    return values


def build_manifest() -> Dict[str, Any]:
    return {
        "embedding_version": EMBEDDING_VERSION,
        "feature_version": FEATURE_VERSION,
        "algorithm": ALGORITHM_NAME,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "similarity_metric": SIMILARITY_METRIC,
        "part1_dimension": PART1_DIMENSION,
        "part2_dimension": PART2_DIMENSION,
        "part1_feature_order": PART1_FEATURE_ORDER,
        "part2_metadata_order": PART2_METADATA_ORDER,
        "symbol_preservation": ["0", "1", "X"],
        "notes": {
            "transition_rate": "Care-bit transitions only (0<->1); X excluded from transitions.",
            "min_max_edge_case": "If min == max for a metadata feature, normalized value is 0.0.",
        },
    }


def write_manifest(output_dir: str) -> str:
    path = os.path.join(output_dir, MANIFEST_FILENAME)
    write_json(path, build_manifest())
    return path


class EmbeddingLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.lines: List[str] = []

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.lines.append(line)

    def flush(self) -> None:
        with open(self.log_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(self.lines) + "\n")


def try_persist_pgvector(
    embeddings: Sequence[Dict[str, Any]],
    source_file: str,
    logger: EmbeddingLogger,
) -> None:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        logger.log("WARNING: pgvector not configured (DATABASE_URL missing); JSON output only.")
        return

    try:
        import psycopg2
        from psycopg2.extras import Json
    except ImportError:
        logger.log("WARNING: psycopg2 not installed; skipping pgvector persistence.")
        return

    try:
        connection = psycopg2.connect(database_url)
    except Exception as exc:
        logger.log(f"WARNING: pgvector connection failed: {exc}")
        return

    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pattern_embeddings (
                        pattern_id TEXT NOT NULL,
                        embedding VECTOR(128) NOT NULL,
                        embedding_dimension INTEGER NOT NULL DEFAULT 128,
                        embedding_version TEXT NOT NULL,
                        algorithm_name TEXT NOT NULL,
                        feature_version TEXT NOT NULL,
                        source_file TEXT,
                        created_timestamp TIMESTAMPTZ NOT NULL,
                        PRIMARY KEY (pattern_id, embedding_version)
                    )
                    """
                )

                for item in embeddings:
                    vector_literal = "[" + ",".join(str(v) for v in item["embedding"]) + "]"
                    cursor.execute(
                        """
                        SELECT embedding::text
                        FROM pattern_embeddings
                        WHERE pattern_id = %s AND embedding_version = %s
                        """,
                        (item["pattern_id"], EMBEDDING_VERSION),
                    )
                    existing = cursor.fetchone()
                    if existing and existing[0]:
                        existing_values = [
                            round_float(float(part))
                            for part in existing[0].strip("[]").split(",")
                            if part.strip()
                        ]
                        if existing_values == item["embedding"]:
                            continue

                    cursor.execute(
                        """
                        INSERT INTO pattern_embeddings (
                            pattern_id, embedding, embedding_dimension, embedding_version,
                            algorithm_name, feature_version, source_file, created_timestamp
                        ) VALUES (%s, %s::vector, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (pattern_id, embedding_version)
                        DO UPDATE SET
                            embedding = EXCLUDED.embedding,
                            algorithm_name = EXCLUDED.algorithm_name,
                            feature_version = EXCLUDED.feature_version,
                            source_file = EXCLUDED.source_file,
                            created_timestamp = EXCLUDED.created_timestamp
                        """,
                        (
                            item["pattern_id"],
                            vector_literal,
                            EMBEDDING_DIMENSION,
                            EMBEDDING_VERSION,
                            ALGORITHM_NAME,
                            FEATURE_VERSION,
                            source_file,
                            item["created_timestamp"],
                        ),
                    )
        logger.log("pgvector persistence completed.")
    except Exception as exc:
        logger.log(f"WARNING: pgvector persistence failed: {exc}")
    finally:
        connection.close()


def generate_pattern_embeddings(output_dir: str) -> Dict[str, Any]:
    start_time = time.time()
    os.makedirs(output_dir, exist_ok=True)

    cache_path = os.path.join(output_dir, CACHE_FILENAME)
    metadata_path = os.path.join(output_dir, METADATA_FILENAME)
    coverage_path = os.path.join(output_dir, COVERAGE_FILENAME)
    embeddings_path = os.path.join(output_dir, EMBEDDINGS_FILENAME)
    log_path = os.path.join(output_dir, LOG_FILENAME)

    logger = EmbeddingLogger(log_path)
    logger.log("PA-FR-005 embedding generation started")

    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Scan vector cache not found: {cache_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata output not found: {metadata_path}")
    if not os.path.exists(coverage_path):
        raise FileNotFoundError(f"Toggle coverage output not found: {coverage_path}")

    cache = load_json(cache_path)
    metadata = load_json(metadata_path)
    coverage = load_json(coverage_path)

    pattern_lookup = {
        item["pattern_id"]: item for item in coverage.get("pattern_level", [])
    }
    cache_patterns = sorted(cache.get("patterns", []), key=lambda item: pattern_sort_key(item["pattern_id"]))
    valid_patterns: List[Dict[str, Any]] = []
    skipped_patterns: List[Dict[str, str]] = []

    for pattern_entry in cache_patterns:
        pattern_id = pattern_entry["pattern_id"]
        if pattern_id not in pattern_lookup:
            reason = "missing toggle coverage metadata"
            logger.log(f"SKIPPED {pattern_id} - {reason}")
            skipped_patterns.append({"pattern_id": pattern_id, "reason": reason})
            continue
        valid_patterns.append(pattern_entry)

    pattern_ids = [item["pattern_id"] for item in valid_patterns]
    logger.log(
        f"Loaded {len(cache_patterns)} patterns from cache; "
        f"{len(valid_patterns)} eligible after coverage join"
    )

    write_manifest(output_dir)

    metadata_rows = build_metadata_rows(metadata, pattern_lookup, pattern_ids)
    normalized_metadata: Dict[str, List[float]] = {
        name: min_max_normalize(values) for name, values in metadata_rows.items()
    }

    embeddings: List[Dict[str, Any]] = []
    source_file = cache.get("source_file", metadata.get("source_file", ""))

    for index, pattern_entry in enumerate(valid_patterns):
        pattern_id = pattern_entry["pattern_id"]
        per_pattern_start = time.time()
        try:
            sequence = pattern_entry.get("concatenated_sequence", "")
            chains = pattern_entry.get("chains", [])
            if not sequence:
                raise EmbeddingGenerationError("missing scan vector")

            part1 = extract_part1_features(sequence, chains)
            part2 = extract_part2_features(normalized_metadata, index)
            combined = part1 + part2
            if len(combined) != EMBEDDING_DIMENSION:
                raise EmbeddingGenerationError(
                    f"invalid embedding length {len(combined)} (expected {EMBEDDING_DIMENSION})"
                )

            created_timestamp = deterministic_timestamp(pattern_id)
            embeddings.append(
                {
                    "pattern_id": pattern_id,
                    "embedding": combined,
                    "source_file": source_file,
                    "feature_version": FEATURE_VERSION,
                    "created_timestamp": created_timestamp,
                }
            )
        except EmbeddingGenerationError as exc:
            logger.log(f"SKIPPED {pattern_id} - {exc}")
            skipped_patterns.append({"pattern_id": pattern_id, "reason": str(exc)})
        except Exception as exc:
            logger.log(f"SKIPPED {pattern_id} - unexpected error: {exc}")
            skipped_patterns.append({"pattern_id": pattern_id, "reason": str(exc)})

        if (index + 1) % 100 == 0:
            elapsed = time.time() - start_time
            logger.log(f"Progress: {index + 1}/{len(valid_patterns)} patterns processed ({elapsed:.1f}s)")

    total_time = time.time() - start_time
    embedded_count = len(embeddings)
    skipped_count = len(skipped_patterns)
    avg_ms = (total_time / embedded_count * 1000.0) if embedded_count else 0.0

    payload = {
        "generated_by": "PA-FR-005",
        "embedding_version": EMBEDDING_VERSION,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "algorithm": ALGORITHM_NAME,
        "similarity_metric": SIMILARITY_METRIC,
        "patterns_embedded": embedded_count,
        "patterns_skipped": skipped_count,
        "embeddings": embeddings,
    }
    write_json(embeddings_path, payload)

    try_persist_pgvector(embeddings, source_file, logger)

    logger.log(f"Completed: {embedded_count} embedded, {skipped_count} skipped")
    logger.log(f"Total time: {total_time:.1f}s | Avg per pattern: {avg_ms:.1f}ms")
    logger.flush()

    return {
        "generated_by": "PA-FR-005",
        "embedding_version": EMBEDDING_VERSION,
        "embedding_dimension": EMBEDDING_DIMENSION,
        "algorithm": ALGORITHM_NAME,
        "similarity_metric": SIMILARITY_METRIC,
        "patterns_embedded": embedded_count,
        "patterns_skipped": skipped_count,
        "skipped_patterns": skipped_patterns,
        "vector_store": "pgvector" if os.environ.get("DATABASE_URL") else "json_only",
        "records": [
            {
                "pattern_id": item["pattern_id"],
                "embedding_status": "Embedded",
                "embedding_dimension": EMBEDDING_DIMENSION,
                "embedding_version": EMBEDDING_VERSION,
                "algorithm": ALGORITHM_NAME,
                "generated_timestamp": item["created_timestamp"],
            }
            for item in embeddings
        ]
        + [
            {
                "pattern_id": item["pattern_id"],
                "embedding_status": "Skipped",
                "embedding_dimension": EMBEDDING_DIMENSION,
                "embedding_version": EMBEDDING_VERSION,
                "algorithm": ALGORITHM_NAME,
                "generated_timestamp": "-",
            }
            for item in skipped_patterns
        ],
        "output_files": {
            "embeddings_json": embeddings_path,
            "manifest_json": os.path.join(output_dir, MANIFEST_FILENAME),
            "generation_log": log_path,
        },
    }


if __name__ == "__main__":
    summary = generate_pattern_embeddings(os.path.join(os.path.dirname(__file__), "output"))
    print(json.dumps(summary, indent=2))
