"""
PA-ARCH-002 — Bounded-memory exact cosine redundancy computation.

Blockwise similarity evaluation without materializing a dense N×N matrix.
Preserves byte-identical outputs to the legacy dense implementation.
"""
from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import numpy as np

from cluster_engine import SIMILARITY_PRECISION, pattern_sort_key
from redundancy_engine import RedundancyConfig, compute_confidence, make_canonical_pair

logger = logging.getLogger(__name__)

DEFAULT_BLOCK_SIZE = 256
DEFAULT_PARALLEL_CLUSTERS = 1


@dataclass(frozen=True)
class RedundancyComputeConfig:
    block_size: int = DEFAULT_BLOCK_SIZE
    parallel_clusters: int = DEFAULT_PARALLEL_CLUSTERS


def load_redundancy_compute_config(workspace_dir: str) -> RedundancyComputeConfig:
    """Load PA-ARCH-002 compute knobs from analysis_session.yaml."""
    block_size = DEFAULT_BLOCK_SIZE
    parallel_clusters = DEFAULT_PARALLEL_CLUSTERS
    path = os.path.join(workspace_dir, "config", "analysis_session.yaml")
    if not os.path.exists(path):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config",
            "analysis_session.yaml",
        )
    if os.path.exists(path):
        try:
            import yaml

            with open(path, "r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle) or {}
            section = payload.get("analysis_session") or {}
            if section.get("redundancy_block_size") is not None:
                block_size = max(1, int(section["redundancy_block_size"]))
            if section.get("redundancy_parallel_clusters") is not None:
                parallel_clusters = max(1, int(section["redundancy_parallel_clusters"]))
        except Exception:
            pass
    return RedundancyComputeConfig(
        block_size=block_size,
        parallel_clusters=parallel_clusters,
    )


def normalize_embedding_matrix(matrix: np.ndarray) -> np.ndarray:
    """L2-normalize rows; zero-norm rows become all zeros (matches legacy behavior)."""
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe_norms = np.where(norms == 0.0, 1.0, norms)
    normalized = matrix / safe_norms
    zero_mask = norms.reshape(-1) == 0.0
    if np.any(zero_mask):
        normalized[zero_mask] = 0.0
    return normalized


def _score_block(
    normalized: np.ndarray,
    block_start: int,
    block_end: int,
) -> np.ndarray:
    """Exact cosine similarities for rows [block_start, block_end) against all N units."""
    return normalized[block_start:block_end] @ normalized.T


def _process_rows_from_score_block(
    *,
    score_block: np.ndarray,
    block_start: int,
    block_end: int,
    members: Sequence[Mapping[str, Any]],
    unit_ids: Sequence[str],
    cluster_id: str,
    config: RedundancyConfig,
    neighbors_per_unit: int,
    threshold: float,
    top_k: int,
    seen_pairs: Set[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    """Build candidate dicts for one block of rows (shared seen_pairs mutated in caller)."""
    cluster_pairs: List[Dict[str, Any]] = []
    for local_index, global_index in enumerate(range(block_start, block_end)):
        member = members[global_index]
        unit_a = unit_ids[global_index]
        row = score_block[local_index]
        top_idx = np.argpartition(-row, top_k - 1)[:top_k]
        scored = [
            (round(float(row[j]), SIMILARITY_PRECISION), members[int(j)])
            for j in top_idx
            if float(row[j]) >= threshold
        ]
        if not scored:
            continue
        scored.sort(
            key=lambda item: (
                -item[0],
                pattern_sort_key(str(item[1].get("unit_id") or "")),
            )
        )
        for raw, other in scored[:neighbors_per_unit]:
            unit_b = str(other["unit_id"])
            try:
                canon = make_canonical_pair(unit_a, unit_b)
            except ValueError:
                continue
            if canon in seen_pairs:
                continue
            if canon[0] == unit_a:
                left, right = member, other
            else:
                left, right = other, member
            confidence = compute_confidence(raw, config)
            cluster_pairs.append(
                {
                    "pattern_a": left.get("pattern_id"),
                    "pattern_b": right.get("pattern_id"),
                    "unit_a": left.get("unit_id"),
                    "unit_b": right.get("unit_id"),
                    "source_lot_a": left.get("source_lot") or "Ungrouped",
                    "source_lot_b": right.get("source_lot") or "Ungrouped",
                    "source_log_a": left.get("source_log"),
                    "source_log_b": right.get("source_log"),
                    "run_id_a": left.get("run_id"),
                    "run_id_b": right.get("run_id"),
                    "cluster_id": cluster_id,
                    "raw_similarity": raw,
                    "confidence_score": confidence,
                    "confidence_source": config.confidence_source,
                    "review_status": config.review_status,
                    "label": config.review_label,
                    "cross_lot": (left.get("source_lot") or "")
                    != (right.get("source_lot") or ""),
                }
            )
            seen_pairs.add(canon)
    return cluster_pairs


def _cluster_pairs_blockwise(
    *,
    cluster_id: str,
    members: List[Dict[str, Any]],
    embeddings_map: Mapping[str, Sequence[float]],
    config: RedundancyConfig,
    neighbors_per_unit: int,
    candidates_per_cluster: int,
    block_size: int,
    seen_pairs: Set[Tuple[str, str]],
) -> List[Dict[str, Any]]:
    unit_ids = [str(m["unit_id"]) for m in members]
    matrix = np.asarray([embeddings_map[uid] for uid in unit_ids], dtype=np.float64)
    normalized = normalize_embedding_matrix(matrix)

    n = len(members)
    top_k = max(1, min(neighbors_per_unit, n - 1))
    threshold = float(config.similarity_threshold)
    cluster_pairs: List[Dict[str, Any]] = []

    for block_start in range(0, n, block_size):
        block_end = min(block_start + block_size, n)
        score_block = _score_block(normalized, block_start, block_end)
        score_block[
            np.arange(block_end - block_start),
            np.arange(block_start, block_end),
        ] = -1.0
        cluster_pairs.extend(
            _process_rows_from_score_block(
                score_block=score_block,
                block_start=block_start,
                block_end=block_end,
                members=members,
                unit_ids=unit_ids,
                cluster_id=cluster_id,
                config=config,
                neighbors_per_unit=neighbors_per_unit,
                threshold=threshold,
                top_k=top_k,
                seen_pairs=seen_pairs,
            )
        )

    cluster_pairs.sort(
        key=lambda row: (
            -float(row["confidence_score"]),
            -float(row["raw_similarity"]),
            str(row.get("unit_a") or ""),
            str(row.get("unit_b") or ""),
        )
    )
    return cluster_pairs[:candidates_per_cluster]


def _cluster_task_args(
    cluster_id: str,
    members: List[Dict[str, Any]],
    embeddings_map: Dict[str, List[float]],
    config: RedundancyConfig,
    neighbors_per_unit: int,
    candidates_per_cluster: int,
    block_size: int,
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Worker: returns (cluster_id, members_copy, pairs) with local dedupe only."""
    filtered = [
        m for m in members if str(m.get("unit_id") or "") in embeddings_map
    ]
    if len(filtered) < 2:
        return cluster_id, filtered, []
    local_seen: Set[Tuple[str, str]] = set()
    pairs = _cluster_pairs_blockwise(
        cluster_id=cluster_id,
        members=filtered,
        embeddings_map=embeddings_map,
        config=config,
        neighbors_per_unit=neighbors_per_unit,
        candidates_per_cluster=candidates_per_cluster,
        block_size=block_size,
        seen_pairs=local_seen,
    )
    return cluster_id, filtered, pairs


def generate_bounded_candidates(
    *,
    by_cluster: Dict[str, List[Dict[str, Any]]],
    embeddings_map: Dict[str, List[float]],
    config: RedundancyConfig,
    neighbors_per_unit: int,
    candidates_per_cluster: int,
    compute_config: Optional[RedundancyComputeConfig] = None,
) -> List[Dict[str, Any]]:
    """
    Bounded nearest-neighbor pairs per cluster using blockwise exact cosine.

    Memory per cluster: O(N·D + block_size·N), not O(N²).
    """
    compute_config = compute_config or RedundancyComputeConfig()
    block_size = max(1, compute_config.block_size)
    parallel = max(1, compute_config.parallel_clusters)

    candidates: List[Dict[str, Any]] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    cluster_ids = sorted(by_cluster.keys())

    if parallel <= 1:
        for cluster_id in cluster_ids:
            members = [
                m for m in by_cluster[cluster_id]
                if str(m.get("unit_id") or "") in embeddings_map
            ]
            if len(members) < 2:
                continue
            cluster_pairs = _cluster_pairs_blockwise(
                cluster_id=cluster_id,
                members=members,
                embeddings_map=embeddings_map,
                config=config,
                neighbors_per_unit=neighbors_per_unit,
                candidates_per_cluster=candidates_per_cluster,
                block_size=block_size,
                seen_pairs=seen_pairs,
            )
            candidates.extend(cluster_pairs)
    else:
        # Parallel per cluster; merge in deterministic cluster_id order.
        # Global seen_pairs applied during merge to match serial dedupe semantics.
        worker_results: Dict[str, List[Dict[str, Any]]] = {}
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {
                executor.submit(
                    _cluster_task_args,
                    cluster_id,
                    list(by_cluster[cluster_id]),
                    embeddings_map,
                    config,
                    neighbors_per_unit,
                    candidates_per_cluster,
                    block_size,
                ): cluster_id
                for cluster_id in cluster_ids
            }
            for future in futures:
                cid, _members, pairs = future.result()
                worker_results[cid] = pairs
        for cluster_id in cluster_ids:
            for pair in worker_results.get(cluster_id, []):
                unit_a = str(pair.get("unit_a") or "")
                unit_b = str(pair.get("unit_b") or "")
                try:
                    canon = make_canonical_pair(unit_a, unit_b)
                except ValueError:
                    continue
                if canon in seen_pairs:
                    continue
                seen_pairs.add(canon)
                candidates.append(pair)

    candidates.sort(
        key=lambda row: (
            -float(row["confidence_score"]),
            -float(row["raw_similarity"]),
            str(row.get("unit_a") or ""),
            str(row.get("unit_b") or ""),
        )
    )
    return candidates


def generate_bounded_candidates_dense_reference(
    *,
    by_cluster: Dict[str, List[Dict[str, Any]]],
    embeddings_map: Dict[str, List[float]],
    config: RedundancyConfig,
    neighbors_per_unit: int,
    candidates_per_cluster: int,
) -> List[Dict[str, Any]]:
    """
    Legacy dense N×N implementation — test reference only (PA-ARCH-002 golden parity).
    """
    candidates: List[Dict[str, Any]] = []
    seen_pairs: Set[Tuple[str, str]] = set()
    threshold = float(config.similarity_threshold)

    for cluster_id in sorted(by_cluster.keys()):
        members = [
            m for m in by_cluster[cluster_id]
            if str(m.get("unit_id") or "") in embeddings_map
        ]
        if len(members) < 2:
            continue

        unit_ids = [str(m["unit_id"]) for m in members]
        matrix = np.asarray([embeddings_map[uid] for uid in unit_ids], dtype=np.float64)
        normalized = normalize_embedding_matrix(matrix)
        sims = normalized @ normalized.T
        np.fill_diagonal(sims, -1.0)

        cluster_pairs: List[Dict[str, Any]] = []
        n = len(members)
        top_k = max(1, min(neighbors_per_unit, n - 1))
        for i, member in enumerate(members):
            unit_a = unit_ids[i]
            row = sims[i]
            top_idx = np.argpartition(-row, top_k - 1)[:top_k]
            scored = [
                (round(float(row[j]), SIMILARITY_PRECISION), members[int(j)])
                for j in top_idx
                if float(row[j]) >= threshold
            ]
            if not scored:
                continue
            scored.sort(
                key=lambda item: (
                    -item[0],
                    pattern_sort_key(str(item[1].get("unit_id") or "")),
                )
            )
            for raw, other in scored[:neighbors_per_unit]:
                unit_b = str(other["unit_id"])
                try:
                    canon = make_canonical_pair(unit_a, unit_b)
                except ValueError:
                    continue
                if canon in seen_pairs:
                    continue
                if canon[0] == unit_a:
                    left, right = member, other
                else:
                    left, right = other, member
                confidence = compute_confidence(raw, config)
                cluster_pairs.append(
                    {
                        "pattern_a": left.get("pattern_id"),
                        "pattern_b": right.get("pattern_id"),
                        "unit_a": left.get("unit_id"),
                        "unit_b": right.get("unit_id"),
                        "source_lot_a": left.get("source_lot") or "Ungrouped",
                        "source_lot_b": right.get("source_lot") or "Ungrouped",
                        "source_log_a": left.get("source_log"),
                        "source_log_b": right.get("source_log"),
                        "run_id_a": left.get("run_id"),
                        "run_id_b": right.get("run_id"),
                        "cluster_id": cluster_id,
                        "raw_similarity": raw,
                        "confidence_score": confidence,
                        "confidence_source": config.confidence_source,
                        "review_status": config.review_status,
                        "label": config.review_label,
                        "cross_lot": (left.get("source_lot") or "")
                        != (right.get("source_lot") or ""),
                    }
                )
                seen_pairs.add(canon)

        cluster_pairs.sort(
            key=lambda row: (
                -float(row["confidence_score"]),
                -float(row["raw_similarity"]),
                str(row.get("unit_a") or ""),
                str(row.get("unit_b") or ""),
            )
        )
        candidates.extend(cluster_pairs[:candidates_per_cluster])

    candidates.sort(
        key=lambda row: (
            -float(row["confidence_score"]),
            -float(row["raw_similarity"]),
            str(row.get("unit_a") or ""),
            str(row.get("unit_b") or ""),
        )
    )
    return candidates
