"""
PA-FR-006 Pattern Clustering — deterministic agglomerative clustering engine.

Reads PA-FR-005 embeddings only. Does not modify PA-FR-001..005 outputs.
"""
from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass, field
from itertools import combinations
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import yaml
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist

from compute_device import cosine_distance_condensed

EMBEDDINGS_FILENAME = "PA-FR-005_pattern_embeddings.json"
EMBEDDING_DIMENSION = 128
DISTANCE_PRECISION = 8
CENTROID_PRECISION = 8
SIMILARITY_PRECISION = 6

DEFAULT_CONFIG: Dict[str, Any] = {
    "algorithm": "Agglomerative",
    "linkage": "Average",
    "similarity_metric": "Cosine",
    "similarity_threshold": 0.90,
    "singleton_clusters": True,
    "cluster_version": "auto",
}


class ClusteringAbortedError(Exception):
    """Raised when clustering cannot proceed due to invalid or mixed inputs."""


class ClusteringConfigError(Exception):
    """Raised when runtime configuration is invalid."""


@dataclass
class ClusteringConfig:
    algorithm: str
    linkage: str
    similarity_metric: str
    similarity_threshold: float
    singleton_clusters: bool
    cluster_version: str

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ClusteringConfig":
        threshold = float(payload.get("similarity_threshold", 0.90))
        if threshold < 0.0 or threshold > 1.0:
            raise ClusteringConfigError("similarity_threshold must be between 0.00 and 1.00")
        algorithm = str(payload.get("algorithm", "Agglomerative"))
        linkage = str(payload.get("linkage", "Average"))
        metric = str(payload.get("similarity_metric", "Cosine"))
        if algorithm != "Agglomerative":
            raise ClusteringConfigError(f"Unsupported algorithm: {algorithm}")
        if linkage != "Average":
            raise ClusteringConfigError(f"Unsupported linkage: {linkage}")
        if metric.lower() != "cosine":
            raise ClusteringConfigError(f"Unsupported similarity_metric: {metric}")
        return cls(
            algorithm=algorithm,
            linkage=linkage,
            similarity_metric=metric,
            similarity_threshold=threshold,
            singleton_clusters=bool(payload.get("singleton_clusters", True)),
            cluster_version=str(payload.get("cluster_version", "auto")),
        )


@dataclass
class PatternRecord:
    pattern_id: str
    embedding: List[float]
    feature_version: str


@dataclass
class ClusterResult:
    cluster_id: str
    member_ids: List[str]
    representative_pattern: str
    centroid: List[float]
    average_intra_similarity: float


@dataclass
class PatternAssignment:
    pattern_id: str
    cluster_id: str
    similarity_to_centroid: float


@dataclass
class ClusteringRunResult:
    config: ClusteringConfig
    cluster_version: int
    embedding_version: str
    patterns: List[PatternAssignment]
    clusters: List[ClusterResult]
    file_rollup: Dict[str, Any]
    centroids_by_cluster: Dict[str, List[float]] = field(default_factory=dict)


def pattern_sort_key(pattern_id: str) -> List[Any]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", pattern_id)]


def load_clustering_config(config_path: str) -> ClusteringConfig:
    if not os.path.exists(config_path):
        return ClusteringConfig.from_dict(DEFAULT_CONFIG)
    document = load_clustering_config_document(config_path)
    clustering = document.get("clustering", document)
    return ClusteringConfig.from_dict(clustering)


def load_clustering_config_document(config_path: str) -> Dict[str, Any]:
    """Load the full clustering YAML document, preserving structure for round-trip saves."""
    if not os.path.exists(config_path):
        return {"clustering": dict(DEFAULT_CONFIG)}
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if "clustering" not in payload:
        payload = {"clustering": payload if payload else dict(DEFAULT_CONFIG)}
    return payload


def save_clustering_config_document(config_path: str, document: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(document, handle, default_flow_style=False, sort_keys=False)


def persist_similarity_threshold(config_path: str, threshold: float) -> ClusteringConfig:
    """Validate and persist a new similarity threshold to the clustering configuration."""
    document = load_clustering_config_document(config_path)
    clustering = document.setdefault("clustering", dict(DEFAULT_CONFIG))
    updated = dict(clustering)
    updated["similarity_threshold"] = threshold
    config = ClusteringConfig.from_dict(updated)
    clustering["similarity_threshold"] = config.similarity_threshold
    save_clustering_config_document(config_path, document)
    return config


def load_embeddings(embeddings_path: str) -> Tuple[Dict[str, Any], List[PatternRecord]]:
    if not os.path.exists(embeddings_path):
        raise ClusteringAbortedError(f"Embeddings file not found: {embeddings_path}")

    with open(embeddings_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    raw_embeddings = payload.get("embeddings", [])
    if not isinstance(raw_embeddings, list) or not raw_embeddings:
        raise ClusteringAbortedError("No embeddings found in PA-FR-005 output.")

    top_version = payload.get("embedding_version")
    feature_versions: Set[str] = set()
    records: List[PatternRecord] = []

    for index, item in enumerate(raw_embeddings):
        if not isinstance(item, dict):
            raise ClusteringAbortedError(f"Embedding record at index {index} is not an object.")
        pattern_id = item.get("pattern_id")
        embedding = item.get("embedding")
        feature_version = item.get("feature_version")
        if not pattern_id or not isinstance(embedding, list):
            raise ClusteringAbortedError(f"Invalid embedding record at index {index}.")
        if len(embedding) != EMBEDDING_DIMENSION:
            raise ClusteringAbortedError(
                f"Pattern {pattern_id} has invalid embedding dimension {len(embedding)} (expected {EMBEDDING_DIMENSION})."
            )
        for value in embedding:
            if value is None or not isinstance(value, (int, float)):
                raise ClusteringAbortedError(f"Pattern {pattern_id} contains invalid embedding values.")
            if not math.isfinite(float(value)):
                raise ClusteringAbortedError(f"Pattern {pattern_id} contains NaN or Infinity.")

        if feature_version is not None:
            feature_versions.add(str(feature_version))
        records.append(
            PatternRecord(
                pattern_id=str(pattern_id),
                embedding=[float(v) for v in embedding],
                feature_version=str(feature_version or top_version or "1.0"),
            )
        )

    versions = set(feature_versions)
    if top_version is not None:
        versions.add(str(top_version))
    versions.discard(None)
    if len(versions) > 1:
        raise ClusteringAbortedError(
            f"Mixed embedding versions detected: {sorted(versions)}. "
            f"Clustering requires a single consistent embedding_version."
        )

    embedding_version = next(iter(versions)) if versions else "1.0"
    records.sort(key=lambda item: pattern_sort_key(item.pattern_id))
    return payload, records


def round_distance(value: float) -> float:
    return round(float(value), DISTANCE_PRECISION)


def cosine_similarity(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    arr_a = np.asarray(vector_a, dtype=np.float64)
    arr_b = np.asarray(vector_b, dtype=np.float64)
    norm_a = np.linalg.norm(arr_a)
    norm_b = np.linalg.norm(arr_b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))


def cosine_distance(vector_a: Sequence[float], vector_b: Sequence[float]) -> float:
    return round_distance(1.0 - cosine_similarity(vector_a, vector_b))


def cluster_radius(centroid: Sequence[float], member_embeddings: Sequence[Sequence[float]]) -> float:
    """Maximum cosine distance from centroid to any cluster member."""
    if not member_embeddings:
        return 0.0
    if len(member_embeddings) == 1:
        return 0.0
    distances = [cosine_distance(centroid, member) for member in member_embeddings]
    return round(max(distances), DISTANCE_PRECISION)


def cluster_compactness(centroid: Sequence[float], member_embeddings: Sequence[Sequence[float]]) -> float:
    """Average cosine similarity between centroid and all cluster members."""
    if not member_embeddings:
        return 1.0
    if len(member_embeddings) == 1:
        return 1.0
    similarities = [cosine_similarity(centroid, member) for member in member_embeddings]
    return round(float(sum(similarities) / len(similarities)), DISTANCE_PRECISION)


def build_cluster_quality_metrics(
    clusters: Sequence[ClusterResult],
    embeddings_map: Dict[str, List[float]],
) -> Dict[str, Dict[str, float]]:
    """Compute additive PA-FR-006.1 quality metrics without altering clustering results."""
    metrics: Dict[str, Dict[str, float]] = {}
    for cluster in clusters:
        member_embeddings = [embeddings_map[pattern_id] for pattern_id in cluster.member_ids]
        metrics[cluster.cluster_id] = {
            "cluster_radius": cluster_radius(cluster.centroid, member_embeddings),
            "cluster_compactness": cluster_compactness(cluster.centroid, member_embeddings),
        }
    return metrics


def cluster_member_sort_key(member_ids: Sequence[str]) -> Tuple[List[Any], ...]:
    return tuple(pattern_sort_key(pattern_id) for pattern_id in sorted(member_ids))


def cluster_pair_tiebreak_key(members_a: Sequence[str], members_b: Sequence[str]) -> Tuple[Tuple[List[Any], ...], Tuple[List[Any], ...]]:
    key_a = cluster_member_sort_key(members_a)
    key_b = cluster_member_sort_key(members_b)
    if key_a <= key_b:
        return key_a, key_b
    return key_b, key_a


def average_linkage_distance(
    members_a: Sequence[str],
    members_b: Sequence[str],
    embeddings: Dict[str, List[float]],
) -> float:
    distances = [
        cosine_distance(embeddings[pattern_a], embeddings[pattern_b])
        for pattern_a in members_a
        for pattern_b in members_b
    ]
    return round_distance(float(np.mean(distances)))


def agglomerative_cluster(
    pattern_ids: Sequence[str],
    embeddings: Dict[str, List[float]],
    similarity_threshold: float,
) -> List[List[str]]:
    """
    Deterministic agglomerative clustering with average linkage and cosine distance.

    Uses scipy hierarchical clustering on a cosine distance matrix with distances
    rounded to DISTANCE_PRECISION before linkage. Pattern order is fixed by
    pattern_sort_key. Final clusters are sorted by lexicographic member ID list.

    Tie-breaking during merges is delegated to scipy's deterministic linkage
    on the rounded distance matrix; cluster IDs are assigned after clustering
    completes (see assign_cluster_ids).
    """
    distance_cutoff = round_distance(1.0 - similarity_threshold)
    sorted_ids = sorted(pattern_ids, key=pattern_sort_key)
    if len(sorted_ids) <= 1:
        return [sorted_ids] if sorted_ids else []

    matrix = np.array([embeddings[pattern_id] for pattern_id in sorted_ids], dtype=np.float64)
    gpu_condensed = cosine_distance_condensed(matrix)
    if gpu_condensed is not None:
        condensed = gpu_condensed
    else:
        condensed = pdist(matrix, metric="cosine")
    condensed = np.round(condensed, DISTANCE_PRECISION)
    linkage_matrix = linkage(condensed, method="average")
    labels = fcluster(linkage_matrix, t=distance_cutoff, criterion="distance")

    grouped: Dict[int, List[str]] = {}
    for pattern_id, label in zip(sorted_ids, labels):
        grouped.setdefault(int(label), []).append(pattern_id)

    clusters = [sorted(members, key=pattern_sort_key) for members in grouped.values()]
    return sorted(clusters, key=cluster_member_sort_key)


def compute_centroid(cluster_embeddings: Sequence[Sequence[float]]) -> List[float]:
    arr = np.array(cluster_embeddings, dtype=np.float64)
    centroid = arr.mean(axis=0)
    assert centroid.shape[0] == arr.shape[1]
    return [round(float(value), CENTROID_PRECISION) for value in centroid.tolist()]


def select_representative(
    cluster_patterns: Sequence[PatternRecord],
    centroid: Sequence[float],
) -> str:
    best_id: Optional[str] = None
    best_similarity = -2.0
    for record in sorted(cluster_patterns, key=lambda item: pattern_sort_key(item.pattern_id)):
        similarity = cosine_similarity(record.embedding, centroid)
        if similarity > best_similarity:
            best_id = record.pattern_id
            best_similarity = similarity
    if best_id is None:
        raise ClusteringAbortedError("Unable to select representative pattern for empty cluster.")
    return best_id


def average_intra_cluster_similarity(
    member_ids: Sequence[str],
    embeddings: Dict[str, List[float]],
) -> float:
    if len(member_ids) <= 1:
        return 1.0
    similarities = [
        cosine_similarity(embeddings[left], embeddings[right])
        for left, right in combinations(member_ids, 2)
    ]
    return round(float(np.mean(similarities)), SIMILARITY_PRECISION)


def average_inter_cluster_similarity(centroids: Sequence[Sequence[float]]) -> float:
    if len(centroids) <= 1:
        return 1.0
    similarities = [
        cosine_similarity(left, right)
        for left, right in combinations(centroids, 2)
    ]
    return round(float(np.mean(similarities)), SIMILARITY_PRECISION)


def compute_silhouette_score(
    assignments: Dict[str, str],
    embeddings: Dict[str, List[float]],
) -> float:
    """
    Standard silhouette using cosine distance.
    Singleton clusters contribute s(i) = 0 by convention.
    """
    clusters: Dict[str, List[str]] = {}
    for pattern_id, cluster_key in assignments.items():
        clusters.setdefault(cluster_key, []).append(pattern_id)

    scores: List[float] = []
    for pattern_id, cluster_key in assignments.items():
        cluster_members = clusters[cluster_key]
        if len(cluster_members) <= 1:
            scores.append(0.0)
            continue

        own_distances = [
            cosine_distance(embeddings[pattern_id], embeddings[other])
            for other in cluster_members
            if other != pattern_id
        ]
        a_value = float(np.mean(own_distances)) if own_distances else 0.0

        other_cluster_means: List[float] = []
        for other_key, other_members in clusters.items():
            if other_key == cluster_key:
                continue
            distances = [cosine_distance(embeddings[pattern_id], embeddings[other]) for other in other_members]
            other_cluster_means.append(float(np.mean(distances)))

        if not other_cluster_means:
            scores.append(0.0)
            continue

        b_value = min(other_cluster_means)
        denominator = max(a_value, b_value)
        if denominator == 0.0:
            scores.append(0.0)
        else:
            scores.append((b_value - a_value) / denominator)

    return round(float(np.mean(scores)), SIMILARITY_PRECISION) if scores else 0.0


def assign_cluster_ids(final_clusters: Sequence[Sequence[str]]) -> Dict[Tuple[str, ...], str]:
    ordered = sorted((tuple(sorted(cluster, key=pattern_sort_key)) for cluster in final_clusters), key=cluster_member_sort_key)
    return {cluster_tuple: f"C{index:03d}" for index, cluster_tuple in enumerate(ordered, start=1)}


def run_clustering_engine(
    records: Sequence[PatternRecord],
    config: ClusteringConfig,
    embedding_version: str,
    cluster_version: int,
    expected_dimension: int = EMBEDDING_DIMENSION,
    *,
    compute_silhouette: bool = True,
    lightweight_metrics: bool = False,
) -> ClusteringRunResult:
    embeddings_map = {record.pattern_id: record.embedding for record in records}
    records_by_id = {record.pattern_id: record for record in records}
    pattern_ids = [record.pattern_id for record in records]

    for record in records:
        if len(record.embedding) != expected_dimension:
            raise ClusteringAbortedError(
                f"Pattern {record.pattern_id} embedding dimension {len(record.embedding)} != {expected_dimension}"
            )

    final_clusters = agglomerative_cluster(pattern_ids, embeddings_map, config.similarity_threshold)
    cluster_id_map = assign_cluster_ids(final_clusters)

    cluster_results: List[ClusterResult] = []
    pattern_assignments: List[PatternAssignment] = []
    centroids_by_cluster: Dict[str, List[float]] = {}

    for cluster_members in final_clusters:
        cluster_tuple = tuple(sorted(cluster_members, key=pattern_sort_key))
        cluster_id = cluster_id_map[cluster_tuple]
        member_records = [records_by_id[pattern_id] for pattern_id in cluster_tuple]
        centroid = compute_centroid([embeddings_map[pattern_id] for pattern_id in cluster_tuple])
        centroids_by_cluster[cluster_id] = centroid
        representative = select_representative(member_records, centroid)
        if lightweight_metrics and len(cluster_members) > 32:
            # Approximate intra-similarity via mean similarity-to-centroid (O(k) vs O(k^2)).
            sims = [
                cosine_similarity(embeddings_map[pattern_id], centroid)
                for pattern_id in cluster_tuple
            ]
            intra_similarity = round(float(np.mean(sims)), SIMILARITY_PRECISION) if sims else 1.0
        else:
            intra_similarity = average_intra_cluster_similarity(cluster_members, embeddings_map)

        cluster_results.append(
            ClusterResult(
                cluster_id=cluster_id,
                member_ids=list(cluster_tuple),
                representative_pattern=representative,
                centroid=centroid,
                average_intra_similarity=intra_similarity,
            )
        )

        for pattern_id in cluster_tuple:
            similarity = round(cosine_similarity(embeddings_map[pattern_id], centroid), SIMILARITY_PRECISION)
            pattern_assignments.append(
                PatternAssignment(
                    pattern_id=pattern_id,
                    cluster_id=cluster_id,
                    similarity_to_centroid=similarity,
                )
            )

    pattern_assignments.sort(key=lambda item: pattern_sort_key(item.pattern_id))
    cluster_results.sort(key=lambda item: cluster_member_sort_key(item.member_ids))

    assignment_map = {item.pattern_id: item.cluster_id for item in pattern_assignments}
    if compute_silhouette:
        silhouette = compute_silhouette_score(assignment_map, embeddings_map)
    else:
        silhouette = None
    centroid_list = [centroids_by_cluster[cluster.cluster_id] for cluster in cluster_results]
    if lightweight_metrics and len(centroid_list) > 64:
        inter_similarity = None
    else:
        inter_similarity = average_inter_cluster_similarity(centroid_list)
    cluster_sizes = [len(cluster.member_ids) for cluster in cluster_results]
    singleton_count = sum(1 for size in cluster_sizes if size == 1)
    intra_values = [cluster.average_intra_similarity for cluster in cluster_results]
    avg_intra = round(float(np.mean(intra_values)), SIMILARITY_PRECISION) if intra_values else 0.0
    avg_size = round(len(pattern_ids) / len(cluster_results), 2) if cluster_results else 0.0

    file_rollup = {
        "generated_by": "PA-FR-006",
        "algorithm": config.algorithm,
        "linkage": config.linkage,
        "distance_metric": "Cosine",
        "similarity_metric": config.similarity_metric,
        "similarity_threshold": config.similarity_threshold,
        "embedding_version": embedding_version,
        "cluster_version": cluster_version,
        "total_patterns": len(pattern_ids),
        "total_clusters": len(cluster_results),
        "largest_cluster": max(cluster_sizes) if cluster_sizes else 0,
        "smallest_cluster": min(cluster_sizes) if cluster_sizes else 0,
        "singleton_clusters": singleton_count,
        "average_cluster_size": avg_size,
        "average_intra_cluster_similarity": avg_intra,
        "average_inter_cluster_similarity": inter_similarity,
        "silhouette_score": silhouette,
    }

    return ClusteringRunResult(
        config=config,
        cluster_version=cluster_version,
        embedding_version=embedding_version,
        patterns=pattern_assignments,
        clusters=cluster_results,
        file_rollup=file_rollup,
        centroids_by_cluster=centroids_by_cluster,
    )


def run_clustering_engine_from_vectors(
    pattern_vectors: Dict[str, List[float]],
    config: ClusteringConfig,
    embedding_version: str = "1.0",
    cluster_version: int = 1,
) -> ClusteringRunResult:
    """Test helper allowing arbitrary vector dimension (e.g. 3-dim worked example)."""
    dimension = len(next(iter(pattern_vectors.values())))
    records = [
        PatternRecord(pattern_id=pattern_id, embedding=vector, feature_version=embedding_version)
        for pattern_id, vector in sorted(pattern_vectors.items(), key=lambda item: pattern_sort_key(item[0]))
    ]
    return run_clustering_engine(
        records,
        config,
        embedding_version=embedding_version,
        cluster_version=cluster_version,
        expected_dimension=dimension,
    )
