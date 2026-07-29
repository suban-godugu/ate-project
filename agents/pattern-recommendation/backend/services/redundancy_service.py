"""Redundancy detection engine using clustering and embeddings."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.redundancy import (
    ClusterList,
    ClusterSummary,
    RedundancyList,
    RedundancyStatistics,
    RedundantPattern,
)
from backend.services.data_loader import DataLoader, get_data_loader
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.utils.pattern_ids import normalize_pattern_id


class RedundancyService:
    """
    Identify redundant patterns from clustering (+ embeddings fallback).

    Does not score removals, ordering, or other recommendations.
    """

    def __init__(
        self,
        data_loader: DataLoader,
        feature_builder: PatternFeatureBuilder,
    ) -> None:
        self._data_loader = data_loader
        self._feature_builder = feature_builder
        self._lock = RLock()
        self._pattern_index: dict[str, RedundantPattern] = {}
        self._cluster_index: dict[str, ClusterSummary] = {}
        self._built_at: datetime | None = None
        self._similarity_threshold: float = 0.0

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> None:
        if not self.is_ready():
            self.analyze()

    def analyze(self) -> RedundancyStatistics:
        """Run deterministic redundancy analysis and cache results."""
        logger = get_logger()
        logger.info("Cluster analysis started")

        # Ensure canonical pattern index exists for downstream consistency.
        self._feature_builder.ensure_built()

        clustering = self._data_loader.get_clustering()
        logger.info("Cluster loading completed")

        threshold = _as_float(clustering.get("similarity_threshold"))
        clusters_raw = clustering.get("clusters", [])
        if not isinstance(clusters_raw, list):
            clusters_raw = []

        embedding_index: dict[str, list[float]] | None = None
        pattern_entries: dict[str, RedundantPattern] = {}
        cluster_summaries: list[ClusterSummary] = []

        for cluster in clusters_raw:
            if not isinstance(cluster, dict):
                continue
            summary, entries, embedding_index = self._analyze_cluster(
                cluster=cluster,
                threshold=threshold,
                embedding_index=embedding_index,
            )
            if summary is None:
                continue
            cluster_summaries.append(summary)
            for entry in entries:
                previous = pattern_entries.get(entry.pattern_id)
                pattern_entries[entry.pattern_id] = _prefer_pattern_entry(
                    previous, entry
                )

        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._pattern_index = pattern_entries
            self._cluster_index = {
                item.cluster_id: item for item in cluster_summaries
            }
            self._built_at = built_at
            self._similarity_threshold = threshold

        redundant_count = sum(
            1 for item in pattern_entries.values() if item.redundant_flag
        )
        logger.info(
            "Cluster analysis completed clusters=%d redundant_patterns=%d",
            len(cluster_summaries),
            redundant_count,
        )
        logger.info("Redundancy cache built")
        return self.get_statistics()

    def refresh(self) -> RedundancyStatistics:
        get_logger().info("Redundancy refresh requested")
        # Rebuild from loader caches; do not clear unrelated pattern/execution work
        # unless clustering/embeddings need reload — clear only those roles.
        stats = self.analyze()
        get_logger().info(
            "Redundancy refresh completed clusters=%d redundant_patterns=%d",
            stats.clusters,
            stats.redundant_patterns,
        )
        return stats

    def get_redundant_patterns(self) -> RedundancyList:
        self.ensure_built()
        with self._lock:
            patterns = sorted(
                (
                    item
                    for item in self._pattern_index.values()
                    if item.redundant_flag
                ),
                key=lambda item: (
                    item.cluster_id,
                    -item.similarity_to_representative,
                    item.pattern_id,
                ),
            )
            return RedundancyList(
                patterns=patterns,
                total=len(patterns),
                built_at=self._built_at,
                similarity_threshold=self._similarity_threshold,
            )

    def get_clusters(self) -> ClusterList:
        self.ensure_built()
        with self._lock:
            clusters = sorted(
                self._cluster_index.values(),
                key=lambda item: item.cluster_id,
            )
            return ClusterList(
                clusters=clusters,
                total=len(clusters),
                built_at=self._built_at,
                similarity_threshold=self._similarity_threshold,
            )

    def get_pattern(self, pattern_id: str) -> RedundantPattern:
        self.ensure_built()
        canonical = normalize_pattern_id(pattern_id)
        with self._lock:
            item = self._pattern_index.get(canonical)
            if item is None and pattern_id in self._pattern_index:
                item = self._pattern_index[pattern_id]
        if item is None:
            raise AppException(
                f"Redundancy information for pattern '{pattern_id}' not found",
                status_code=404,
                details={"pattern_id": pattern_id},
            )
        return item

    def get_cluster_index(self) -> dict[str, ClusterSummary]:
        self.ensure_built()
        with self._lock:
            return dict(self._cluster_index)

    def get_pattern_index(self) -> dict[str, RedundantPattern]:
        """Return a shallow copy of the pattern redundancy index."""
        self.ensure_built()
        with self._lock:
            return dict(self._pattern_index)

    def get_statistics(self) -> RedundancyStatistics:
        self.ensure_built()
        with self._lock:
            clusters = list(self._cluster_index.values())
            patterns = list(self._pattern_index.values())

        if not clusters:
            return RedundancyStatistics()

        representatives = sum(1 for item in patterns if item.is_representative)
        redundant = sum(1 for item in patterns if item.redundant_flag)
        avg_size = sum(item.cluster_size for item in clusters) / len(clusters)
        avg_sim = sum(item.average_similarity for item in clusters) / len(clusters)
        return RedundancyStatistics(
            clusters=len(clusters),
            representatives=representatives,
            redundant_patterns=redundant,
            average_cluster_size=round(avg_size, 6),
            average_similarity=round(avg_sim, 6),
        )

    def _analyze_cluster(
        self,
        *,
        cluster: dict[str, Any],
        threshold: float,
        embedding_index: dict[str, list[float]] | None,
    ) -> tuple[
        ClusterSummary | None,
        list[RedundantPattern],
        dict[str, list[float]] | None,
    ]:
        cluster_id = str(cluster.get("cluster_id", "")).strip()
        if not cluster_id:
            return None, [], embedding_index

        representative = normalize_pattern_id(cluster.get("representative_pattern"))
        average_similarity = _as_float(cluster.get("average_similarity"))
        members = _extract_member_patterns(cluster)
        if representative and representative not in members:
            members.insert(0, representative)
        if not members:
            return None, [], embedding_index

        member_similarities = _member_similarities_from_cluster(cluster)

        entries: list[RedundantPattern] = []
        redundant_members: list[str] = []

        for pattern_id in members:
            is_representative = pattern_id == representative
            similarity = member_similarities.get(pattern_id)

            if similarity is None:
                if is_representative:
                    similarity = 1.0
                else:
                    if embedding_index is None:
                        embedding_index = self._load_embedding_index()
                    similarity = _cosine_between_patterns(
                        embedding_index,
                        representative,
                        pattern_id,
                    )

            similarity = float(similarity)
            redundant_flag = (not is_representative) and (
                similarity >= threshold
            )
            if redundant_flag:
                redundant_members.append(pattern_id)

            entries.append(
                RedundantPattern(
                    pattern_id=pattern_id,
                    cluster_id=cluster_id,
                    representative_pattern=representative,
                    similarity_to_representative=round(similarity, 6),
                    cluster_average_similarity=round(average_similarity, 6),
                    is_representative=is_representative,
                    redundant_flag=redundant_flag,
                )
            )

        summary = ClusterSummary(
            cluster_id=cluster_id,
            representative=representative,
            members=members,
            redundant_members=sorted(redundant_members),
            cluster_size=len(members),
            average_similarity=round(average_similarity, 6),
        )
        return summary, entries, embedding_index

    def _load_embedding_index(self) -> dict[str, list[float]]:
        logger = get_logger()
        logger.info("Loading embeddings for redundancy similarity fallback")
        payload = self._data_loader.get_embeddings()
        index = _build_pattern_embedding_index(payload)
        logger.info(
            "Embedding index ready patterns_with_vectors=%d",
            len(index),
        )
        return index


def _prefer_pattern_entry(
    existing: RedundantPattern | None,
    candidate: RedundantPattern,
) -> RedundantPattern:
    """Resolve multi-cluster collisions into one pattern-level record."""
    if existing is None:
        return candidate
    if candidate.is_representative and not existing.is_representative:
        return candidate
    if existing.is_representative and not candidate.is_representative:
        return existing
    if candidate.redundant_flag and not existing.redundant_flag:
        return candidate
    if existing.redundant_flag and not candidate.redundant_flag:
        return existing
    if (
        candidate.similarity_to_representative
        > existing.similarity_to_representative
    ):
        return candidate
    return existing


def _extract_member_patterns(cluster: dict[str, Any]) -> list[str]:
    """Discover unique normalized member pattern IDs for a cluster."""
    ordered: list[str] = []
    seen: set[str] = set()

    raw_members = cluster.get("member_patterns")
    if isinstance(raw_members, list):
        for item in raw_members:
            pid = normalize_pattern_id(item)
            if pid and pid not in seen:
                seen.add(pid)
                ordered.append(pid)

    executions = cluster.get("executions")
    if isinstance(executions, list):
        for item in executions:
            if not isinstance(item, dict):
                continue
            pid = normalize_pattern_id(item.get("pattern_id"))
            if pid and pid not in seen:
                seen.add(pid)
                ordered.append(pid)

    return ordered


def _member_similarities_from_cluster(cluster: dict[str, Any]) -> dict[str, float]:
    """
    Aggregate per-member similarity from clustering metadata when present.

    Uses similarity_to_centroid / similarity_to_representative fields when
    available. Values are averaged across a member's cluster executions.
    """
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)

    executions = cluster.get("executions")
    if not isinstance(executions, list):
        return {}

    for item in executions:
        if not isinstance(item, dict):
            continue
        pid = normalize_pattern_id(item.get("pattern_id"))
        if not pid:
            continue
        if "similarity_to_representative" in item:
            value = _as_float(item.get("similarity_to_representative"))
        elif "similarity_to_centroid" in item:
            value = _as_float(item.get("similarity_to_centroid"))
        else:
            continue
        sums[pid] += value
        counts[pid] += 1

    return {
        pid: sums[pid] / counts[pid]
        for pid in sums
        if counts[pid] > 0
    }


def _build_pattern_embedding_index(payload: Any) -> dict[str, list[float]]:
    """Average embedding vectors per normalized pattern ID."""
    rows = payload.get("embeddings", []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return {}

    sums: dict[str, list[float]] = {}
    counts: dict[str, int] = defaultdict(int)

    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = normalize_pattern_id(row.get("pattern_id"))
        vector = row.get("embedding")
        if not pid or not isinstance(vector, list) or not vector:
            continue
        floats = [_as_float(v) for v in vector]
        if pid not in sums:
            sums[pid] = floats
        else:
            current = sums[pid]
            if len(current) != len(floats):
                continue
            sums[pid] = [a + b for a, b in zip(current, floats, strict=True)]
        counts[pid] += 1

    return {
        pid: [value / counts[pid] for value in vector]
        for pid, vector in sums.items()
        if counts[pid] > 0
    }


def _cosine_between_patterns(
    index: dict[str, list[float]],
    left: str,
    right: str,
) -> float:
    a = index.get(left)
    b = index.get(right)
    if not a or not b:
        return 0.0
    return _cosine_similarity(a, b)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = 0.0
    norm_l = 0.0
    norm_r = 0.0
    for a, b in zip(left, right, strict=True):
        dot += a * b
        norm_l += a * a
        norm_r += b * b
    if norm_l <= 0.0 or norm_r <= 0.0:
        return 0.0
    return dot / (math.sqrt(norm_l) * math.sqrt(norm_r))


def _as_float(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


_redundancy_service: RedundancyService | None = None
_service_lock = RLock()


def get_redundancy_service(
    data_loader: DataLoader | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
) -> RedundancyService:
    """Return the process-wide RedundancyService singleton."""
    global _redundancy_service
    with _service_lock:
        if _redundancy_service is None:
            loader = data_loader or get_data_loader()
            builder = feature_builder or get_pattern_feature_builder(loader)
            _redundancy_service = RedundancyService(loader, builder)
        return _redundancy_service


def reset_redundancy_service() -> None:
    """Clear the RedundancyService singleton."""
    global _redundancy_service
    with _service_lock:
        _redundancy_service = None
