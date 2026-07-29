"""
Session clustering exporter — writes PA-Analysis-Session_clustering.json only.

Reuses cluster_engine.run_clustering_engine in-memory.
Never writes PA-FR-006_* artifacts.

Large sessions: learn centroids from a capped sample, then assign EVERY
session embedding unit to the nearest centroid so all LOTs/executions remain
represented for downstream Phase 7 redundancy.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from analysis_session import SESSION_GENERATED_BY
from robustness_config import load_robustness_config, lot_from_relpath
from cluster_engine import (
    ClusteringAbortedError,
    ClusteringConfig,
    PatternRecord,
    SIMILARITY_PRECISION,
    cosine_similarity,
    load_clustering_config,
    pattern_sort_key,
    run_clustering_engine,
)
from session_perf_trace import SessionPerfTrace, optional_phase

logger = logging.getLogger(__name__)

# Agglomerative clustering is O(n^2). Cap the learning sample for speed.
DEFAULT_SESSION_CLUSTERING_MAX_UNITS = 2500

# PA-PERF-007 — internal only (not public YAML).
# Engineering Validation Gate passed (tests/test_vectorized_cluster_assign.py).
ENABLE_VECTORIZED_CLUSTER_ASSIGN = True
# CI/debug: dual-run serial+vectorized; on mismatch return serial (immediate fallback).
VALIDATE_CLUSTER_ASSIGN_PARITY = False


def _lot_label_from_relpath(
    relpath: str,
    robustness_cfg: Optional[object] = None,
) -> str:
    return lot_from_relpath(relpath, config=robustness_cfg)


def _unit_id(row: Dict[str, Any]) -> str:
    pattern_id = str(row.get("pattern_id") or "")
    relpath = str(row.get("source_log_relpath") or "")
    source_log = str(row.get("source_log") or "")
    return f"{pattern_id}::{relpath or source_log}"


def _resolve_clustering_config_path(workspace_dir: str, config_path: Optional[str] = None) -> str:
    if config_path:
        return config_path
    candidate = os.path.join(workspace_dir, "config", "clustering.yaml")
    if os.path.exists(candidate):
        return candidate
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config",
        "clustering.yaml",
    )


def _empty_payload(
    *,
    config: ClusteringConfig,
    embedding_version: str,
    embedding_strategy: str,
    lots: List[str],
    execution_record_count: Any,
    session_hash: Optional[str],
) -> Dict[str, Any]:
    return {
        "generated_by": SESSION_GENERATED_BY,
        "available": True,
        "algorithm": config.algorithm,
        "linkage": config.linkage,
        "similarity_metric": config.similarity_metric,
        "similarity_threshold": config.similarity_threshold,
        "embedding_version": embedding_version,
        "embedding_strategy": embedding_strategy,
        "cluster_version": 1,
        "session_hash": session_hash,
        "lot_count": len(lots),
        "lots": lots,
        "execution_record_count": execution_record_count,
        "patterns_clustered": 0,
        "total_clusters": 0,
        "largest_cluster": 0,
        "smallest_cluster": 0,
        "average_cluster_size": 0,
        "singleton_clusters": 0,
        "clusters": [],
        "unit_assignments": [],
        "centroids": {},
        "charts": {
            "size_distribution": [],
            "lot_contribution": [],
            "execution_distribution": [],
        },
    }


def _build_charts(clusters: List[Dict[str, Any]], lots: Sequence[str]) -> Dict[str, Any]:
    size_distribution = [
        {
            "cluster_id": cluster["cluster_id"],
            "label": cluster["cluster_id"],
            "count": int(cluster.get("execution_count") or 0),
        }
        for cluster in clusters
    ]
    lot_counts: Dict[str, int] = {str(lot): 0 for lot in lots}
    for cluster in clusters:
        for exec_row in cluster.get("executions") or []:
            lot = str(exec_row.get("source_lot") or "Ungrouped")
            lot_counts[lot] = lot_counts.get(lot, 0) + 1
    lot_contribution = [
        {"label": lot, "count": count}
        for lot, count in sorted(lot_counts.items(), key=lambda item: item[0])
        if count > 0 or lot in lots
    ]
    buckets = [("1", 1, 1), ("2-5", 2, 5), ("6-20", 6, 20), ("21+", 21, 10**9)]
    bucket_counts = {label: 0 for label, _, _ in buckets}
    for cluster in clusters:
        size = int(cluster.get("execution_count") or 0)
        for label, low, high in buckets:
            if low <= size <= high:
                bucket_counts[label] += 1
                break
    execution_distribution = [
        {"label": label, "count": bucket_counts[label]} for label, _, _ in buckets
    ]
    return {
        "size_distribution": size_distribution[:50],
        "lot_contribution": lot_contribution,
        "execution_distribution": execution_distribution,
    }


def _downsample_records(
    records: List[PatternRecord],
    max_units: int,
) -> List[PatternRecord]:
    """Deterministic stride sample after stable sort. Preserves LOT/pattern spread."""
    if max_units <= 0 or len(records) <= max_units:
        return records
    ordered = sorted(records, key=lambda item: pattern_sort_key(item.pattern_id))
    step = len(ordered) / float(max_units)
    sampled: List[PatternRecord] = []
    seen = set()
    for index in range(max_units):
        pos = min(len(ordered) - 1, int(index * step))
        record = ordered[pos]
        if record.pattern_id in seen:
            for offset in range(1, len(ordered)):
                alt = ordered[(pos + offset) % len(ordered)]
                if alt.pattern_id not in seen:
                    record = alt
                    break
        if record.pattern_id in seen:
            continue
        seen.add(record.pattern_id)
        sampled.append(record)
    return sampled


def _assignment_row(
    *,
    uid: str,
    meta: Dict[str, Any],
    cluster_id: str,
    similarity: float,
    sampled: bool,
) -> Dict[str, Any]:
    return {
        "unit_id": uid,
        "pattern_id": meta.get("pattern_id"),
        "source_log": meta.get("source_log"),
        "source_log_relpath": meta.get("source_log_relpath"),
        "source_lot": meta.get("source_lot") or "Ungrouped",
        "run_id": meta.get("run_id"),
        "cluster_id": cluster_id,
        "similarity_to_centroid": similarity,
        "sampled": sampled,
    }


def _assignments_identity_equal(
    left: Sequence[Dict[str, Any]],
    right: Sequence[Dict[str, Any]],
) -> bool:
    """Engineering Validation Gate — per-unit cluster_id / similarity / sampled."""
    if len(left) != len(right):
        return False
    for a, b in zip(left, right):
        if a.get("unit_id") != b.get("unit_id"):
            return False
        if a.get("cluster_id") != b.get("cluster_id"):
            return False
        if a.get("similarity_to_centroid") != b.get("similarity_to_centroid"):
            return False
        if bool(a.get("sampled")) != bool(b.get("sampled")):
            return False
    return True


def _assign_all_units_to_centroids_serial(
    all_records: Sequence[PatternRecord],
    unit_meta: Dict[str, Dict[str, Any]],
    centroids_by_cluster: Dict[str, List[float]],
    sampled_ids: set[str],
    sample_assignment_map: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Golden reference: nested Python cosine assignment (pre-PERF-007)."""
    if not centroids_by_cluster:
        return []
    centroid_items: List[Tuple[str, List[float]]] = sorted(
        centroids_by_cluster.items(),
        key=lambda item: item[0],
    )
    assignments: List[Dict[str, Any]] = []
    for record in sorted(all_records, key=lambda item: pattern_sort_key(item.pattern_id)):
        uid = record.pattern_id
        meta = unit_meta.get(uid) or {}
        if uid in sampled_ids and uid in sample_assignment_map:
            sample_asg = sample_assignment_map[uid]
            cluster_id = sample_asg.cluster_id
            similarity = sample_asg.similarity_to_centroid
            sampled = True
        else:
            best_id = centroid_items[0][0]
            best_sim = -2.0
            for cluster_id, centroid in centroid_items:
                sim = cosine_similarity(record.embedding, centroid)
                if sim > best_sim or (sim == best_sim and cluster_id < best_id):
                    best_sim = sim
                    best_id = cluster_id
            cluster_id = best_id
            similarity = round(float(best_sim), SIMILARITY_PRECISION)
            sampled = False
        assignments.append(
            _assignment_row(
                uid=uid,
                meta=meta,
                cluster_id=cluster_id,
                similarity=similarity,
                sampled=sampled,
            )
        )
    return assignments


def _assign_all_units_to_centroids_vectorized(
    all_records: Sequence[PatternRecord],
    unit_meta: Dict[str, Dict[str, Any]],
    centroids_by_cluster: Dict[str, List[float]],
    sampled_ids: set[str],
    sample_assignment_map: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    PA-PERF-007: float64 matmul cosine for non-sampled units.

    Same sample bypass, tie-break (sim then lex cluster_id), and rounding as serial.
    """
    if not centroids_by_cluster:
        return []
    centroid_items: List[Tuple[str, List[float]]] = sorted(
        centroids_by_cluster.items(),
        key=lambda item: item[0],
    )
    cluster_ids = [item[0] for item in centroid_items]
    centroids = [item[1] for item in centroid_items]
    c_matrix = np.asarray(centroids, dtype=np.float64)
    c_norms = np.linalg.norm(c_matrix, axis=1)

    ordered = sorted(all_records, key=lambda item: pattern_sort_key(item.pattern_id))
    non_sampled_indices: List[int] = []
    non_sampled_embeddings: List[Sequence[float]] = []

    for index, record in enumerate(ordered):
        uid = record.pattern_id
        if uid in sampled_ids and uid in sample_assignment_map:
            continue
        non_sampled_indices.append(index)
        non_sampled_embeddings.append(record.embedding)

    winners: Dict[int, Tuple[str, float]] = {}
    if non_sampled_embeddings:
        u_matrix = np.asarray(non_sampled_embeddings, dtype=np.float64)
        u_norms = np.linalg.norm(u_matrix, axis=1)
        # Algebraic cosine: (U @ C.T) / outer(||U||, ||C||); zero-norm → 0.0
        denom = np.outer(u_norms, c_norms)
        dots = u_matrix @ c_matrix.T
        with np.errstate(divide="ignore", invalid="ignore"):
            sims = np.divide(dots, denom, out=np.zeros_like(dots), where=denom != 0.0)

        for row_i, unit_index in enumerate(non_sampled_indices):
            best_id = cluster_ids[0]
            best_sim = -2.0
            for col_j, cluster_id in enumerate(cluster_ids):
                sim = float(sims[row_i, col_j])
                if sim > best_sim or (sim == best_sim and cluster_id < best_id):
                    best_sim = sim
                    best_id = cluster_id
            winners[unit_index] = (
                best_id,
                round(float(best_sim), SIMILARITY_PRECISION),
            )

    assignments: List[Dict[str, Any]] = []
    for index, record in enumerate(ordered):
        uid = record.pattern_id
        meta = unit_meta.get(uid) or {}
        if uid in sampled_ids and uid in sample_assignment_map:
            sample_asg = sample_assignment_map[uid]
            assignments.append(
                _assignment_row(
                    uid=uid,
                    meta=meta,
                    cluster_id=sample_asg.cluster_id,
                    similarity=sample_asg.similarity_to_centroid,
                    sampled=True,
                )
            )
        else:
            cluster_id, similarity = winners[index]
            assignments.append(
                _assignment_row(
                    uid=uid,
                    meta=meta,
                    cluster_id=cluster_id,
                    similarity=similarity,
                    sampled=False,
                )
            )
    return assignments


def _assign_all_units_to_centroids(
    all_records: Sequence[PatternRecord],
    unit_meta: Dict[str, Dict[str, Any]],
    centroids_by_cluster: Dict[str, List[float]],
    sampled_ids: set[str],
    sample_assignment_map: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Production assign wrapper (PA-PERF-007).

    Default: serial golden path until ENABLE_VECTORIZED_CLUSTER_ASSIGN is True
    after the Engineering Validation Gate passes.
    """
    args = (
        all_records,
        unit_meta,
        centroids_by_cluster,
        sampled_ids,
        sample_assignment_map,
    )
    if not ENABLE_VECTORIZED_CLUSTER_ASSIGN:
        return _assign_all_units_to_centroids_serial(*args)

    vectorized = _assign_all_units_to_centroids_vectorized(*args)
    if VALIDATE_CLUSTER_ASSIGN_PARITY:
        serial = _assign_all_units_to_centroids_serial(*args)
        if not _assignments_identity_equal(serial, vectorized):
            logger.error(
                "PA-PERF-007 assign parity failure; falling back to serial "
                "(cluster_id / similarity_to_centroid / sampled mismatch)."
            )
            return serial
    return vectorized


def build_session_clustering(
    *,
    embeddings_payload: Optional[Dict[str, Any]],
    workspace_dir: str,
    summary: Optional[Dict[str, Any]] = None,
    input_ate_logs: Optional[Sequence[str]] = None,
    session_hash: Optional[str] = None,
    clustering_config_path: Optional[str] = None,
    max_units: int = DEFAULT_SESSION_CLUSTERING_MAX_UNITS,
    perf_trace: Optional[SessionPerfTrace] = None,
) -> Dict[str, Any]:
    """
    Cluster per-execution session embeddings (one unit per pattern × source log).

    Uses run_clustering_engine only — never writes PA-FR-006 artifacts.
    Large sessions learn centroids from a deterministic sample, then assign all units.
    """
    config = load_clustering_config(
        _resolve_clustering_config_path(workspace_dir, clustering_config_path)
    )
    robustness_cfg = load_robustness_config(workspace_dir)
    summary = summary or {}
    input_ate_logs = list(input_ate_logs or [])
    lots: List[str] = []
    seen_lots = set()
    for log_name in input_ate_logs:
        lot = _lot_label_from_relpath(log_name, robustness_cfg=robustness_cfg)
        if lot not in seen_lots:
            seen_lots.add(lot)
            lots.append(lot)

    embedding_version = "1.0"
    embedding_strategy = "per_execution"
    if isinstance(embeddings_payload, dict):
        embedding_version = str(embeddings_payload.get("embedding_version") or embedding_version)
        embedding_strategy = str(embeddings_payload.get("embedding_strategy") or embedding_strategy)

    if not isinstance(embeddings_payload, dict):
        return _empty_payload(
            config=config,
            embedding_version=embedding_version,
            embedding_strategy=embedding_strategy,
            lots=lots,
            execution_record_count=summary.get("execution_record_count"),
            session_hash=session_hash,
        )

    rows = [row for row in (embeddings_payload.get("embeddings") or []) if isinstance(row, dict)]
    if not rows:
        return _empty_payload(
            config=config,
            embedding_version=embedding_version,
            embedding_strategy=embedding_strategy,
            lots=lots,
            execution_record_count=summary.get("execution_record_count"),
            session_hash=session_hash,
        )

    unit_meta: Dict[str, Dict[str, Any]] = {}
    all_records: List[PatternRecord] = []
    for row in rows:
        embedding = row.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            continue
        uid = _unit_id(row)
        if uid in unit_meta:
            continue
        relpath = str(row.get("source_log_relpath") or "")
        source_log = str(row.get("source_log") or "")
        unit_meta[uid] = {
            "pattern_id": str(row.get("pattern_id") or ""),
            "source_log": source_log,
            "source_log_relpath": relpath,
            "source_lot": _lot_label_from_relpath(
                relpath or source_log, robustness_cfg=robustness_cfg
            ),
            "run_id": row.get("run_id"),
        }
        all_records.append(
            PatternRecord(
                pattern_id=uid,
                embedding=[float(v) for v in embedding],
                feature_version=str(row.get("feature_version") or "1.0"),
            )
        )

    if not all_records:
        return _empty_payload(
            config=config,
            embedding_version=embedding_version,
            embedding_strategy=embedding_strategy,
            lots=lots,
            execution_record_count=summary.get("execution_record_count"),
            session_hash=session_hash,
        )

    total_units = len(all_records)
    sample_records = _downsample_records(all_records, max_units)
    sampled_units = len(sample_records)
    sampled_ids = {record.pattern_id for record in sample_records}

    try:
        with optional_phase(perf_trace, "cluster_sample_linkage"):
            result = run_clustering_engine(
                sample_records,
                config,
                embedding_version=embedding_version,
                cluster_version=1,
                compute_silhouette=False,
                lightweight_metrics=True,
            )
    except ClusteringAbortedError:
        payload = _empty_payload(
            config=config,
            embedding_version=embedding_version,
            embedding_strategy=embedding_strategy,
            lots=lots,
            execution_record_count=summary.get("execution_record_count"),
            session_hash=session_hash,
        )
        payload["available"] = False
        payload["status"] = "ABORTED"
        return payload

    sample_assignment_map = {item.pattern_id: item for item in result.patterns}
    with optional_phase(perf_trace, "cluster_assign_all"):
        unit_assignments = _assign_all_units_to_centroids(
            all_records,
            unit_meta,
            result.centroids_by_cluster,
            sampled_ids,
            sample_assignment_map,
        )

    # Rebuild cluster explorer rows from ALL assigned units (not sample-only).
    by_cluster: Dict[str, List[Dict[str, Any]]] = {}
    for asg in unit_assignments:
        by_cluster.setdefault(str(asg["cluster_id"]), []).append(asg)

    clusters_out: List[Dict[str, Any]] = []
    for cluster in result.clusters:
        cluster_id = cluster.cluster_id
        members = by_cluster.get(cluster_id, [])
        members.sort(key=lambda item: pattern_sort_key(str(item.get("unit_id") or "")))
        cluster_lots: List[str] = []
        seen_cluster_lots = set()
        pattern_ids = set()
        executions = []
        for member in members:
            lot = member.get("source_lot") or "Ungrouped"
            if lot not in seen_cluster_lots:
                seen_cluster_lots.add(lot)
                cluster_lots.append(lot)
            pattern_ids.add(member.get("pattern_id") or "")
            executions.append(
                {
                    "unit_id": member.get("unit_id"),
                    "pattern_id": member.get("pattern_id"),
                    "source_lot": lot,
                    "source_log": member.get("source_log"),
                    "source_log_relpath": member.get("source_log_relpath"),
                    "run_id": member.get("run_id"),
                    "similarity_to_centroid": member.get("similarity_to_centroid"),
                    "sampled": bool(member.get("sampled")),
                }
            )
        rep_meta = unit_meta.get(cluster.representative_pattern) or {}
        clusters_out.append(
            {
                "cluster_id": cluster_id,
                "representative_pattern": rep_meta.get("pattern_id")
                or cluster.representative_pattern,
                "pattern_count": len({pid for pid in pattern_ids if pid}),
                "execution_count": len(executions),
                "lots": cluster_lots,
                "average_similarity": cluster.average_intra_similarity,
                "executions": executions,
            }
        )

    cluster_sizes = [int(c["execution_count"]) for c in clusters_out]
    singleton_count = sum(1 for size in cluster_sizes if size == 1)
    avg_size = round(total_units / len(clusters_out), 2) if clusters_out else 0.0

    return {
        "generated_by": SESSION_GENERATED_BY,
        "available": True,
        "algorithm": config.algorithm,
        "linkage": config.linkage,
        "similarity_metric": config.similarity_metric,
        "similarity_threshold": config.similarity_threshold,
        "embedding_version": embedding_version,
        "embedding_strategy": embedding_strategy,
        "cluster_version": result.cluster_version,
        "session_hash": session_hash,
        "lot_count": len(lots),
        "lots": lots,
        "execution_record_count": summary.get("execution_record_count"),
        "patterns_clustered": total_units,
        "units_total": total_units,
        "units_clustered": total_units,
        "units_sample_size": sampled_units,
        "units_downsampled": total_units > sampled_units,
        "total_clusters": len(clusters_out),
        "largest_cluster": max(cluster_sizes) if cluster_sizes else 0,
        "smallest_cluster": min(cluster_sizes) if cluster_sizes else 0,
        "average_cluster_size": avg_size,
        "singleton_clusters": singleton_count,
        "silhouette_score": None,
        "centroids": {
            cluster_id: list(centroid)
            for cluster_id, centroid in sorted(result.centroids_by_cluster.items())
        },
        "unit_assignments": unit_assignments,
        "clusters": clusters_out,
        "charts": _build_charts(clusters_out, lots),
    }
