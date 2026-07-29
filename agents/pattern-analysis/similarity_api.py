"""
PA-FR-008 Similarity API — request parsing and response formatting.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from similarity_engine import SimilarityEngine, PairwiseSimilarityResult, TopNSimilarityResult
from similarity_validator import SimilarityAbortError, SimilarityValidationError


def _resolve_top_n(requested: Optional[int], engine: SimilarityEngine) -> int:
    if requested is None:
        return engine.config.default_top_n
    return int(requested)


def handle_pair_similarity(
    pattern_a: str,
    pattern_b: str,
    workspace_dir: str,
    output_dir: str,
) -> Dict[str, Any]:
    engine = SimilarityEngine.from_workspace(workspace_dir, output_dir)
    result = engine.compute_pair(pattern_a, pattern_b)
    return result.to_dict()


def handle_top_n_similarity(
    reference_pattern: str,
    top_n: Optional[int],
    workspace_dir: str,
    output_dir: str,
) -> Dict[str, Any]:
    engine = SimilarityEngine.from_workspace(workspace_dir, output_dir)
    resolved_top_n = _resolve_top_n(top_n, engine)
    result = engine.compute_top_n(reference_pattern, resolved_top_n)
    return result.to_dict()


__all__ = [
    "SimilarityValidationError",
    "SimilarityAbortError",
    "handle_pair_similarity",
    "handle_top_n_similarity",
]