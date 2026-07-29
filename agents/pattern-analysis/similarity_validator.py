"""
PA-FR-008 Similarity Validator — input and data-integrity checks.
"""
from __future__ import annotations

from typing import Dict, Optional

from cluster_engine import PatternRecord
from similarity_config import SimilarityConfig


class SimilarityValidationError(Exception):
    """User input problem — return 4xx-style error, not a crash."""


class SimilarityAbortError(Exception):
    """Data integrity problem — abort this request."""


def validate_metric_supported(config: SimilarityConfig) -> None:
    if config.metric != "cosine":
        raise SimilarityAbortError(f"Unsupported similarity metric: {config.metric}")


def validate_pairwise_patterns(pattern_a: str, pattern_b: str) -> None:
    pattern_a_id = str(pattern_a or "").strip()
    pattern_b_id = str(pattern_b or "").strip()
    if not pattern_a_id or not pattern_b_id:
        raise SimilarityValidationError("pattern_a and pattern_b are required.")
    if pattern_a_id == pattern_b_id:
        raise SimilarityValidationError(
            f"Pattern A and Pattern B must be different patterns (both were '{pattern_a_id}')"
        )


def validate_reference_pattern(reference_pattern: str) -> str:
    pattern_id = str(reference_pattern or "").strip()
    if not pattern_id:
        raise SimilarityValidationError("reference_pattern is required.")
    return pattern_id


def validate_top_n(requested_top_n: int, config: SimilarityConfig) -> int:
    if requested_top_n < 1:
        raise SimilarityValidationError("top_n must be at least 1.")
    if requested_top_n > config.max_top_n:
        raise SimilarityValidationError(
            f"Requested top_n={requested_top_n} exceeds configured max_top_n={config.max_top_n}"
        )
    return requested_top_n


def validate_pattern_exists(pattern_id: str, embeddings_map: Dict[str, PatternRecord]) -> PatternRecord:
    record = embeddings_map.get(pattern_id)
    if record is None:
        raise SimilarityValidationError(f"Pattern '{pattern_id}' was not found in the embedding index.")
    return record


def validate_embedding_versions(
    pattern_a: PatternRecord,
    pattern_b: PatternRecord,
) -> None:
    if pattern_a.feature_version != pattern_b.feature_version:
        raise SimilarityAbortError(
            "Mixed embedding versions detected: "
            f"{pattern_a.pattern_id} ({pattern_a.feature_version}) vs "
            f"{pattern_b.pattern_id} ({pattern_b.feature_version}). Comparison not permitted."
        )
