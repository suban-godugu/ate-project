"""
PA-FR-008 Similarity Engine — pairwise and Top-N similarity analysis.
Reuses PA-FR-006 cosine_similarity and pattern_sort_key without duplication.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from cluster_engine import (
    ClusteringAbortedError,
    EMBEDDINGS_FILENAME,
    PatternRecord,
    cosine_similarity,
    load_embeddings,
    pattern_sort_key,
)
from compute_device import batch_cosine_similarities
from similarity_config import SimilarityConfig, SimilarityCategory, load_similarity_config
from similarity_validator import (
    SimilarityAbortError,
    SimilarityValidationError,
    validate_embedding_versions,
    validate_metric_supported,
    validate_pairwise_patterns,
    validate_pattern_exists,
    validate_reference_pattern,
    validate_top_n,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PairwiseSimilarityResult:
    pattern_a: str
    pattern_b: str
    similarity_score: float
    category: str
    engine_latency_ms: int
    budget_exceeded: bool
    embedding_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_a": self.pattern_a,
            "pattern_b": self.pattern_b,
            "similarity_score": self.similarity_score,
            "category": self.category,
            "engine_latency_ms": self.engine_latency_ms,
            "budget_exceeded": self.budget_exceeded,
            "embedding_version": self.embedding_version,
            # Reserved for PA-FR-009 enrichment — not populated in Stage 1.
            "pass_fail_context": None,
        }


@dataclass(frozen=True)
class TopNSimilarityRow:
    rank: int
    pattern_id: str
    similarity: float
    category: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "pattern_id": self.pattern_id,
            "similarity": self.similarity,
            "category": self.category,
        }


@dataclass(frozen=True)
class TopNSimilarityResult:
    reference_pattern: str
    requested_top_n: int
    returned_count: int
    available_count: int
    partial_result: bool
    results: Tuple[TopNSimilarityRow, ...]
    engine_latency_ms: int
    budget_exceeded: bool
    embedding_version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_pattern": self.reference_pattern,
            "requested_top_n": self.requested_top_n,
            "returned_count": self.returned_count,
            "available_count": self.available_count,
            "partial_result": self.partial_result,
            "results": [row.to_dict() for row in self.results],
            "engine_latency_ms": self.engine_latency_ms,
            "budget_exceeded": self.budget_exceeded,
            "embedding_version": self.embedding_version,
            # Reserved for PA-FR-009 enrichment — not populated in Stage 1.
            "pass_fail_context": None,
        }


class SimilarityEngine:
    """Core similarity engine. Future CachingSimilarityEngine / ANN wrappers sit in front."""

    def __init__(
        self,
        config: SimilarityConfig,
        embeddings_map: Dict[str, PatternRecord],
        embedding_version: str,
    ) -> None:
        self.config = config
        self.embeddings_map = embeddings_map
        self.embedding_version = embedding_version
        validate_metric_supported(config)
        # Future hook: if config.cache_enabled, wrap compute paths with a cache layer.
        if config.cache_enabled:
            logger.debug("similarity.cache_enabled is true — cache layer not implemented in Stage 1.")
        if config.ann_enabled:
            logger.debug("similarity.ann_enabled is true — ANN layer not implemented in Stage 1.")

    @classmethod
    def from_workspace(
        cls,
        workspace_dir: str,
        output_dir: str,
        config_path: Optional[str] = None,
    ) -> "SimilarityEngine":
        config_file = config_path or os.path.join(workspace_dir, "config", "similarity.yaml")
        config = load_similarity_config(config_file)
        embeddings_path = os.path.join(output_dir, EMBEDDINGS_FILENAME)
        try:
            payload, records = load_embeddings(embeddings_path)
        except ClusteringAbortedError as exc:
            raise SimilarityAbortError(str(exc)) from exc
        embedding_version = str(payload.get("embedding_version") or records[0].feature_version if records else "1.0")
        embeddings_map = {record.pattern_id: record for record in records}
        return cls(config=config, embeddings_map=embeddings_map, embedding_version=embedding_version)

    def classify_similarity(self, score: float) -> str:
        for category in self.config.categories_descending:
            if score >= category.min_threshold:
                return category.label
        fallback = self.config.categories_descending[-1]
        return fallback.label

    def _round_score(self, score: float) -> float:
        return round(float(score), self.config.display_precision)

    def compute_pair(self, pattern_a: str, pattern_b: str) -> PairwiseSimilarityResult:
        validate_pairwise_patterns(pattern_a, pattern_b)
        pattern_a_id = str(pattern_a).strip()
        pattern_b_id = str(pattern_b).strip()

        start = time.perf_counter()
        record_a = validate_pattern_exists(pattern_a_id, self.embeddings_map)
        record_b = validate_pattern_exists(pattern_b_id, self.embeddings_map)
        validate_embedding_versions(record_a, record_b)
        raw_score = cosine_similarity(record_a.embedding, record_b.embedding)
        rounded_score = self._round_score(raw_score)
        category = self.classify_similarity(rounded_score)
        engine_latency_ms = round((time.perf_counter() - start) * 1000)
        budget_exceeded = engine_latency_ms > self.config.response_time_budget_ms
        if budget_exceeded:
            logger.warning(
                "Pairwise similarity exceeded response_time_budget_ms=%s (actual=%s)",
                self.config.response_time_budget_ms,
                engine_latency_ms,
            )
        return PairwiseSimilarityResult(
            pattern_a=pattern_a_id,
            pattern_b=pattern_b_id,
            similarity_score=rounded_score,
            category=category,
            engine_latency_ms=engine_latency_ms,
            budget_exceeded=budget_exceeded,
            embedding_version=record_a.feature_version,
        )

    def compute_top_n(self, reference_pattern: str, requested_top_n: int) -> TopNSimilarityResult:
        reference_id = validate_reference_pattern(reference_pattern)
        top_n = validate_top_n(requested_top_n, self.config)

        start = time.perf_counter()
        reference_record = validate_pattern_exists(reference_id, self.embeddings_map)

        candidate_ids: List[str] = []
        candidate_vectors: List[Sequence[float]] = []
        for pattern_id, record in self.embeddings_map.items():
            if pattern_id == reference_id:
                continue
            validate_embedding_versions(reference_record, record)
            candidate_ids.append(pattern_id)
            candidate_vectors.append(record.embedding)

        raw_scores = batch_cosine_similarities(
            reference_record.embedding,
            candidate_vectors,
        )
        candidates: List[Dict[str, Any]] = []
        for pattern_id, raw_score in zip(candidate_ids, raw_scores):
            rounded_score = self._round_score(raw_score)
            candidates.append(
                {
                    "pattern_id": pattern_id,
                    "similarity": rounded_score,
                    "category": self.classify_similarity(rounded_score),
                }
            )

        candidates.sort(key=lambda item: (-item["similarity"], pattern_sort_key(item["pattern_id"])))
        available_count = len(candidates)
        selected = candidates[:top_n]
        rows = tuple(
            TopNSimilarityRow(
                rank=index + 1,
                pattern_id=item["pattern_id"],
                similarity=item["similarity"],
                category=item["category"],
            )
            for index, item in enumerate(selected)
        )
        returned_count = len(rows)
        partial_result = returned_count < top_n
        engine_latency_ms = round((time.perf_counter() - start) * 1000)
        budget_exceeded = engine_latency_ms > self.config.response_time_budget_ms
        if budget_exceeded:
            logger.warning(
                "Top-N similarity exceeded response_time_budget_ms=%s (actual=%s)",
                self.config.response_time_budget_ms,
                engine_latency_ms,
            )

        return TopNSimilarityResult(
            reference_pattern=reference_id,
            requested_top_n=top_n,
            returned_count=returned_count,
            available_count=available_count,
            partial_result=partial_result,
            results=rows,
            engine_latency_ms=engine_latency_ms,
            budget_exceeded=budget_exceeded,
            embedding_version=reference_record.feature_version,
        )
