"""
PA-FR-007 Redundancy Engine — same-cluster pair generation, confidence, and ranking.
"""
from __future__ import annotations

import itertools
import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

import yaml

from cluster_engine import (
    ClusteringAbortedError,
    EMBEDDINGS_FILENAME,
    SIMILARITY_PRECISION,
    cosine_similarity,
    load_embeddings,
)

PATTERN_CLUSTERS_JSON = "PA-FR-006_pattern_clusters.json"
CLUSTER_SUMMARY_JSON = "PA-FR-006_cluster_summary.json"

DEFAULT_REDUNDANCY_CONFIG: Dict[str, Any] = {
    "similarity_metric": "cosine",
    "similarity_threshold": 0.98,
    "embedding_only_confidence_weight": 0.50,
    "confidence_precision": 3,
    "display_precision": 1,
    "confidence_source": "Embedding Only",
    "review_status": "Pending Review",
    "review_label": "Candidate for Review",
    "enable_audit_logging": True,
    "enable_history": True,
}


class RedundancyConfigError(ValueError):
    """Raised when redundancy configuration is invalid."""


class RedundancyAbortedError(RuntimeError):
    """Raised when PA-FR-007 cannot safely continue."""


@dataclass(frozen=True)
class RedundancyConfig:
    similarity_metric: str
    similarity_threshold: float
    embedding_only_confidence_weight: float
    confidence_precision: int
    display_precision: int
    confidence_source: str
    review_status: str
    review_label: str
    enable_audit_logging: bool
    enable_history: bool

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "RedundancyConfig":
        merged = dict(DEFAULT_REDUNDANCY_CONFIG)
        merged.update(payload or {})
        threshold = float(merged["similarity_threshold"])
        if not 0.0 <= threshold <= 1.0:
            raise RedundancyConfigError("similarity_threshold must be between 0.00 and 1.00")
        weight = float(merged["embedding_only_confidence_weight"])
        if not 0.0 <= weight <= 1.0:
            raise RedundancyConfigError("embedding_only_confidence_weight must be between 0.00 and 1.00")
        metric = str(merged["similarity_metric"]).lower()
        if metric != "cosine":
            raise RedundancyConfigError(f"Unsupported similarity_metric: {merged['similarity_metric']}")
        return cls(
            similarity_metric=metric,
            similarity_threshold=threshold,
            embedding_only_confidence_weight=weight,
            confidence_precision=int(merged["confidence_precision"]),
            display_precision=int(merged["display_precision"]),
            confidence_source=str(merged["confidence_source"]),
            review_status=str(merged["review_status"]),
            review_label=str(merged["review_label"]),
            enable_audit_logging=bool(merged["enable_audit_logging"]),
            enable_history=bool(merged["enable_history"]),
        )


@dataclass(frozen=True)
class RedundancyCandidate:
    pattern_a: str
    pattern_b: str
    cluster_id: str
    raw_similarity: float
    confidence_score: float
    confidence_source: str
    review_status: str
    label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_a": self.pattern_a,
            "pattern_b": self.pattern_b,
            "cluster_id": self.cluster_id,
            "raw_similarity": self.raw_similarity,
            "confidence_score": self.confidence_score,
            "confidence_source": self.confidence_source,
            "review_status": self.review_status,
            "label": self.label,
        }


@dataclass
class RedundancyRunResult:
    candidates: List[RedundancyCandidate]
    embedding_version: str
    cluster_version: int
    similarity_threshold: float
    clusters_evaluated: int
    duplicate_pattern_ids: List[str]
    skipped_patterns_missing_embedding: List[str]
    skipped_patterns_missing_cluster: List[str]


def load_redundancy_config(config_path: str) -> RedundancyConfig:
    if not os.path.exists(config_path):
        return RedundancyConfig.from_dict(DEFAULT_REDUNDANCY_CONFIG)
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    redundancy = payload.get("redundancy", payload)
    return RedundancyConfig.from_dict(redundancy)


def load_pattern_clusters(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise RedundancyAbortedError(f"Pattern clusters file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RedundancyAbortedError(f"Corrupted pattern clusters JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise RedundancyAbortedError("Pattern clusters payload must be a JSON object.")
    return payload


def load_cluster_summary(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise RedundancyAbortedError(f"Cluster summary file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise RedundancyAbortedError(f"Corrupted cluster summary JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise RedundancyAbortedError("Cluster summary payload must be a JSON object.")
    return payload


def make_canonical_pair(pattern_a: str, pattern_b: str) -> Tuple[str, str]:
    if pattern_a == pattern_b:
        raise ValueError("Self-comparison is not permitted")
    return tuple(sorted([pattern_a, pattern_b]))


def compute_confidence(raw_similarity: float, config: RedundancyConfig) -> float:
    confidence = raw_similarity * config.embedding_only_confidence_weight
    return round(confidence, config.confidence_precision)


def candidate_sort_key(candidate: RedundancyCandidate) -> Tuple[Any, ...]:
    return (
        -candidate.confidence_score,
        -candidate.raw_similarity,
        candidate.pattern_a,
        candidate.pattern_b,
    )


def sort_candidates(candidates: Sequence[RedundancyCandidate]) -> List[RedundancyCandidate]:
    return sorted(list(candidates), key=candidate_sort_key)


def _dedupe_assignments(
    assignments: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    seen: set[str] = set()
    deduped: List[Dict[str, Any]] = []
    duplicates: List[str] = []
    for assignment in assignments:
        pattern_id = str(assignment.get("pattern_id", "")).strip()
        if not pattern_id:
            continue
        if pattern_id in seen:
            duplicates.append(pattern_id)
            continue
        seen.add(pattern_id)
        deduped.append(assignment)
    return deduped, duplicates


def _group_assignments_by_cluster(
    assignments: Sequence[Dict[str, Any]],
    embeddings_map: Dict[str, Sequence[float]],
    known_cluster_ids: set[str],
) -> Tuple[Dict[str, List[str]], List[str], List[str]]:
    by_cluster: Dict[str, List[str]] = defaultdict(list)
    missing_embeddings: List[str] = []
    missing_clusters: List[str] = []
    for assignment in assignments:
        pattern_id = str(assignment.get("pattern_id", "")).strip()
        cluster_id = str(assignment.get("cluster_id", "")).strip()
        if not pattern_id:
            continue
        if pattern_id not in embeddings_map:
            missing_embeddings.append(pattern_id)
            continue
        if not cluster_id or cluster_id not in known_cluster_ids:
            missing_clusters.append(pattern_id)
            continue
        by_cluster[cluster_id].append(pattern_id)
    for cluster_id in by_cluster:
        by_cluster[cluster_id] = sorted(by_cluster[cluster_id])
    return by_cluster, missing_embeddings, missing_clusters


def _is_valid_similarity(value: float) -> bool:
    return math.isfinite(value) and -1.0 <= value <= 1.0


def generate_redundancy_candidates(
    assignments: Sequence[Dict[str, Any]],
    embeddings_map: Dict[str, Sequence[float]],
    known_cluster_ids: set[str],
    config: RedundancyConfig,
) -> Tuple[List[RedundancyCandidate], List[str], List[str], List[str]]:
    deduped_assignments, duplicate_pattern_ids = _dedupe_assignments(assignments)
    by_cluster, missing_embeddings, missing_clusters = _group_assignments_by_cluster(
        deduped_assignments,
        embeddings_map,
        known_cluster_ids,
    )

    candidates: List[RedundancyCandidate] = []
    seen_pairs: set[Tuple[str, str]] = set()

    for cluster_id, member_ids in by_cluster.items():
        if len(member_ids) < 2:
            continue
        for pattern_a, pattern_b in itertools.combinations(member_ids, 2):
            pair = (pattern_a, pattern_b)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            vector_a = embeddings_map[pattern_a]
            vector_b = embeddings_map[pattern_b]
            raw_similarity = round(cosine_similarity(vector_a, vector_b), SIMILARITY_PRECISION)
            if not _is_valid_similarity(raw_similarity):
                continue
            if raw_similarity < config.similarity_threshold:
                continue

            confidence_score = compute_confidence(raw_similarity, config)
            candidates.append(
                RedundancyCandidate(
                    pattern_a=pattern_a,
                    pattern_b=pattern_b,
                    cluster_id=cluster_id,
                    raw_similarity=raw_similarity,
                    confidence_score=confidence_score,
                    confidence_source=config.confidence_source,
                    review_status=config.review_status,
                    label=config.review_label,
                )
            )

    return sort_candidates(candidates), duplicate_pattern_ids, missing_embeddings, missing_clusters


def run_redundancy_engine(
    output_dir: str,
    workspace_dir: str | None = None,
) -> RedundancyRunResult:
    workspace = workspace_dir or os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(workspace, "config", "redundancy.yaml")
    config = load_redundancy_config(config_path)

    embeddings_path = os.path.join(output_dir, EMBEDDINGS_FILENAME)
    pattern_clusters_path = os.path.join(output_dir, PATTERN_CLUSTERS_JSON)
    cluster_summary_path = os.path.join(output_dir, CLUSTER_SUMMARY_JSON)

    try:
        _, embedding_records = load_embeddings(embeddings_path)
    except json.JSONDecodeError as exc:
        raise RedundancyAbortedError(f"Corrupted embeddings JSON: {embeddings_path}") from exc
    except ClusteringAbortedError as exc:
        raise RedundancyAbortedError(str(exc)) from exc
    embeddings_map = {record.pattern_id: record.embedding for record in embedding_records}
    embedding_version = embedding_records[0].feature_version if embedding_records else "1.0"

    pattern_clusters = load_pattern_clusters(pattern_clusters_path)
    cluster_summary = load_cluster_summary(cluster_summary_path)

    clusters_embedding_version = str(pattern_clusters.get("embedding_version", "")).strip()
    if not clusters_embedding_version:
        raise RedundancyAbortedError("Pattern clusters missing embedding_version.")
    if clusters_embedding_version != embedding_version:
        raise RedundancyAbortedError(
            f"Embedding version mismatch: PA-FR-005={embedding_version}, PA-FR-006={clusters_embedding_version}."
        )

    cluster_version = int(pattern_clusters.get("cluster_version", 1))
    assignments = pattern_clusters.get("patterns", [])
    if not isinstance(assignments, list):
        raise RedundancyAbortedError("Pattern clusters missing patterns array.")

    known_cluster_ids = {
        str(cluster.get("cluster_id"))
        for cluster in cluster_summary.get("clusters", [])
        if cluster.get("cluster_id")
    }

    candidates, duplicate_pattern_ids, missing_embeddings, missing_clusters = generate_redundancy_candidates(
        assignments,
        embeddings_map,
        known_cluster_ids,
        config,
    )

    clusters_evaluated = len(
        {
            cluster_id
            for cluster_id, members in _group_assignments_by_cluster(
                _dedupe_assignments(assignments)[0],
                embeddings_map,
                known_cluster_ids,
            )[0].items()
            if len(members) >= 2
        }
    )

    return RedundancyRunResult(
        candidates=candidates,
        embedding_version=embedding_version,
        cluster_version=cluster_version,
        similarity_threshold=config.similarity_threshold,
        clusters_evaluated=clusters_evaluated,
        duplicate_pattern_ids=duplicate_pattern_ids,
        skipped_patterns_missing_embedding=sorted(set(missing_embeddings)),
        skipped_patterns_missing_cluster=sorted(set(missing_clusters)),
    )
