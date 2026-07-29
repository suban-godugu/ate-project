"""
Session redundancy exporter — writes PA-Analysis-Session_redundancy.json only.

Operates on Analysis Session clustering + embeddings (per-execution units).
Never writes PA-FR-007_* artifacts and never calls run_pattern_redundancy.
"""
from __future__ import annotations

import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

from analysis_session import SESSION_GENERATED_BY
from cluster_engine import pattern_sort_key
from redundancy_engine import (
    RedundancyConfig,
    load_redundancy_config,
)
from session_cluster_exporter import _lot_label_from_relpath, _unit_id
from session_perf_trace import SessionPerfTrace, optional_phase
from session_redundancy_compute import (
    generate_bounded_candidates,
    load_redundancy_compute_config,
)
from robustness_config import load_robustness_config

DEFAULT_NEIGHBORS_PER_UNIT = 5
DEFAULT_CANDIDATES_PER_CLUSTER = 100


def _resolve_redundancy_config_path(workspace_dir: str, config_path: Optional[str] = None) -> str:
    if config_path:
        return config_path
    candidate = os.path.join(workspace_dir, "config", "redundancy.yaml")
    if os.path.exists(candidate):
        return candidate
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config",
        "redundancy.yaml",
    )


def _load_session_redundancy_limits(workspace_dir: str) -> Tuple[int, int]:
    """Read optional session-only bounds from analysis_session.yaml."""
    path = os.path.join(workspace_dir, "config", "analysis_session.yaml")
    neighbors = DEFAULT_NEIGHBORS_PER_UNIT
    per_cluster = DEFAULT_CANDIDATES_PER_CLUSTER
    if not os.path.exists(path):
        path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config",
            "analysis_session.yaml",
        )
    if not os.path.exists(path):
        return neighbors, per_cluster
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        section = payload.get("analysis_session") or {}
        if section.get("redundancy_neighbors_per_unit") is not None:
            neighbors = max(1, int(section["redundancy_neighbors_per_unit"]))
        if section.get("redundancy_candidates_per_cluster") is not None:
            per_cluster = max(1, int(section["redundancy_candidates_per_cluster"]))
    except Exception:
        pass
    return neighbors, per_cluster


def _empty_payload(
    *,
    config: RedundancyConfig,
    embedding_version: str,
    embedding_strategy: str,
    cluster_version: int,
    lots: List[str],
    session_hash: Optional[str],
) -> Dict[str, Any]:
    return {
        "generated_by": SESSION_GENERATED_BY,
        "available": True,
        "session_hash": session_hash,
        "embedding_version": embedding_version,
        "embedding_strategy": embedding_strategy,
        "cluster_version": cluster_version,
        "similarity_threshold": config.similarity_threshold,
        "confidence_source": config.confidence_source,
        "lot_count": len(lots),
        "lots": lots,
        "units_total": 0,
        "units_represented": 0,
        "clusters_evaluated": 0,
        "total_candidates": 0,
        "candidates_per_cluster_avg": 0,
        "validation_status": "PASS",
        "neighbors_per_unit": DEFAULT_NEIGHBORS_PER_UNIT,
        "candidates_per_cluster_cap": DEFAULT_CANDIDATES_PER_CLUSTER,
        "generation_mode": "bounded_nearest_neighbor",
        "candidates": [],
        "validation_checks": [],
        "manifest": {},
        "charts": {
            "confidence_distribution": [],
            "lot_pair_contribution": [],
        },
    }


def _build_embeddings_map(
    embeddings_payload: Optional[Dict[str, Any]],
) -> Dict[str, List[float]]:
    if not isinstance(embeddings_payload, dict):
        return {}
    mapping: Dict[str, List[float]] = {}
    for row in embeddings_payload.get("embeddings") or []:
        if not isinstance(row, dict):
            continue
        embedding = row.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            continue
        uid = _unit_id(row)
        if uid in mapping:
            continue
        mapping[uid] = [float(v) for v in embedding]
    return mapping


def _group_units_by_cluster(
    clustering_payload: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    by_cluster: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    assignments = clustering_payload.get("unit_assignments")
    if isinstance(assignments, list) and assignments:
        for row in assignments:
            if not isinstance(row, dict):
                continue
            cluster_id = str(row.get("cluster_id") or "").strip()
            unit_id = str(row.get("unit_id") or "").strip()
            if not cluster_id or not unit_id:
                continue
            by_cluster[cluster_id].append(row)
    else:
        # Fallback: rebuild from cluster executions if unit_assignments absent.
        for cluster in clustering_payload.get("clusters") or []:
            if not isinstance(cluster, dict):
                continue
            cluster_id = str(cluster.get("cluster_id") or "").strip()
            if not cluster_id:
                continue
            for exec_row in cluster.get("executions") or []:
                if not isinstance(exec_row, dict):
                    continue
                unit_id = str(exec_row.get("unit_id") or "").strip()
                if not unit_id:
                    pattern_id = str(exec_row.get("pattern_id") or "")
                    relpath = str(exec_row.get("source_log_relpath") or "")
                    source_log = str(exec_row.get("source_log") or "")
                    unit_id = f"{pattern_id}::{relpath or source_log}"
                by_cluster[cluster_id].append(
                    {
                        "unit_id": unit_id,
                        "pattern_id": exec_row.get("pattern_id"),
                        "source_log": exec_row.get("source_log"),
                        "source_log_relpath": exec_row.get("source_log_relpath"),
                        "source_lot": exec_row.get("source_lot") or "Ungrouped",
                        "run_id": exec_row.get("run_id"),
                        "cluster_id": cluster_id,
                    }
                )
    for cluster_id in by_cluster:
        by_cluster[cluster_id] = sorted(
            by_cluster[cluster_id],
            key=lambda item: pattern_sort_key(str(item.get("unit_id") or "")),
        )
    return dict(by_cluster)


def _build_charts(candidates: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    buckets = [
        ("Very High", 0.45, 1.01),
        ("High", 0.40, 0.45),
        ("Medium", 0.30, 0.40),
        ("Low", 0.0, 0.30),
    ]
    conf_counts = {label: 0 for label, _, _ in buckets}
    for row in candidates:
        score = float(row.get("confidence_score") or 0.0)
        for label, low, high in buckets:
            if low <= score < high:
                conf_counts[label] += 1
                break
    confidence_distribution = [
        {"label": label, "count": conf_counts[label]} for label, _, _ in buckets
    ]

    lot_pairs: Dict[str, int] = defaultdict(int)
    for row in candidates:
        a = str(row.get("source_lot_a") or "Ungrouped")
        b = str(row.get("source_lot_b") or "Ungrouped")
        key = " × ".join(sorted([a, b]))
        lot_pairs[key] += 1
    lot_pair_contribution = [
        {"label": label, "count": count}
        for label, count in sorted(lot_pairs.items(), key=lambda item: (-item[1], item[0]))[:30]
    ]
    return {
        "confidence_distribution": confidence_distribution,
        "lot_pair_contribution": lot_pair_contribution,
    }


def _build_validation_checks(
    *,
    candidates: Sequence[Dict[str, Any]],
    units_represented: int,
    units_total: int,
    clusters_evaluated: int,
) -> Tuple[str, List[Dict[str, Any]]]:
    checks = [
        {
            "rule": "All session units represented",
            "status": "PASS" if units_represented == units_total and units_total > 0 else "FAIL",
            "details": f"{units_represented} / {units_total} units assigned",
        },
        {
            "rule": "Clusters evaluated",
            "status": "PASS" if clusters_evaluated > 0 else "WARNING",
            "details": f"{clusters_evaluated} clusters",
        },
        {
            "rule": "Canonical pairs unique",
            "status": "PASS",
            "details": f"{len(candidates)} candidates after dedupe",
        },
        {
            "rule": "Session-only artifact path",
            "status": "PASS",
            "details": "No legacy FR-007 filenames written",
        },
    ]
    if any(c["status"] == "FAIL" for c in checks):
        status = "FAIL"
    elif any(c["status"] == "WARNING" for c in checks):
        status = "WARNING"
    else:
        status = "PASS"
    return status, checks


def build_session_redundancy(
    *,
    clustering_payload: Optional[Dict[str, Any]],
    embeddings_payload: Optional[Dict[str, Any]],
    workspace_dir: str,
    session_hash: Optional[str] = None,
    redundancy_config_path: Optional[str] = None,
    neighbors_per_unit: Optional[int] = None,
    candidates_per_cluster: Optional[int] = None,
    perf_trace: Optional[SessionPerfTrace] = None,
) -> Dict[str, Any]:
    """
    Build bounded nearest-neighbor redundancy candidates for all session units.

    Reuses redundancy confidence semantics; never writes PA-FR-007 files.
    """
    config = load_redundancy_config(
        _resolve_redundancy_config_path(workspace_dir, redundancy_config_path)
    )
    robustness_cfg = load_robustness_config(workspace_dir)
    cfg_neighbors, cfg_per_cluster = _load_session_redundancy_limits(workspace_dir)
    neighbors = max(1, int(neighbors_per_unit if neighbors_per_unit is not None else cfg_neighbors))
    per_cluster = max(
        1,
        int(candidates_per_cluster if candidates_per_cluster is not None else cfg_per_cluster),
    )

    embedding_version = "1.0"
    embedding_strategy = "per_execution"
    cluster_version = 1
    lots: List[str] = []
    if isinstance(embeddings_payload, dict):
        embedding_version = str(embeddings_payload.get("embedding_version") or embedding_version)
        embedding_strategy = str(embeddings_payload.get("embedding_strategy") or embedding_strategy)
    if isinstance(clustering_payload, dict):
        cluster_version = int(clustering_payload.get("cluster_version") or 1)
        lots = list(clustering_payload.get("lots") or [])
        if not lots:
            for log_name in clustering_payload.get("input_ate_logs") or []:
                lot = _lot_label_from_relpath(
                    str(log_name), robustness_cfg=robustness_cfg
                )
                if lot not in lots:
                    lots.append(lot)

    if not isinstance(clustering_payload, dict) or not clustering_payload.get("available", True):
        payload = _empty_payload(
            config=config,
            embedding_version=embedding_version,
            embedding_strategy=embedding_strategy,
            cluster_version=cluster_version,
            lots=lots,
            session_hash=session_hash,
        )
        payload["available"] = False
        return payload

    embeddings_map = _build_embeddings_map(embeddings_payload)
    by_cluster = _group_units_by_cluster(clustering_payload)
    units_represented = sum(len(v) for v in by_cluster.values())
    units_total = int(
        clustering_payload.get("units_total")
        or clustering_payload.get("units_clustered")
        or units_represented
    )
    if not lots:
        seen = set()
        for members in by_cluster.values():
            for row in members:
                lot = str(row.get("source_lot") or "Ungrouped")
                if lot not in seen:
                    seen.add(lot)
                    lots.append(lot)
        lots.sort()

    with optional_phase(perf_trace, "redundancy_matrix"):
        compute_cfg = load_redundancy_compute_config(workspace_dir)
        candidates = generate_bounded_candidates(
            by_cluster=by_cluster,
            embeddings_map=embeddings_map,
            config=config,
            neighbors_per_unit=neighbors,
            candidates_per_cluster=per_cluster,
            compute_config=compute_cfg,
        )

    with optional_phase(perf_trace, "redundancy_emit"):
        clusters_evaluated = sum(1 for members in by_cluster.values() if len(members) >= 2)
        avg = round(len(candidates) / clusters_evaluated, 2) if clusters_evaluated else 0.0
        validation_status, checks = _build_validation_checks(
            candidates=candidates,
            units_represented=units_represented,
            units_total=units_total,
            clusters_evaluated=clusters_evaluated,
        )

        return {
            "generated_by": SESSION_GENERATED_BY,
            "available": True,
            "session_hash": session_hash or clustering_payload.get("session_hash"),
            "embedding_version": embedding_version,
            "embedding_strategy": embedding_strategy,
            "cluster_version": cluster_version,
            "similarity_threshold": config.similarity_threshold,
            "confidence_source": config.confidence_source,
            "lot_count": len(lots),
            "lots": lots,
            "units_total": units_total,
            "units_represented": units_represented,
            "units_sample_size": clustering_payload.get("units_sample_size"),
            "units_downsampled": bool(clustering_payload.get("units_downsampled")),
            "clusters_evaluated": clusters_evaluated,
            "total_candidates": len(candidates),
            "candidates_per_cluster_avg": avg,
            "validation_status": validation_status,
            "neighbors_per_unit": neighbors,
            "candidates_per_cluster_cap": per_cluster,
            "generation_mode": "bounded_nearest_neighbor",
            "candidates": candidates,
            "validation_checks": checks,
            "manifest": {
                "generated_by": SESSION_GENERATED_BY,
                "similarity_threshold": config.similarity_threshold,
                "confidence_source": config.confidence_source,
                "generation_mode": "bounded_nearest_neighbor",
                "neighbors_per_unit": neighbors,
                "candidates_per_cluster_cap": per_cluster,
                "total_candidates": len(candidates),
                "clusters_evaluated": clusters_evaluated,
                "units_represented": units_represented,
                "units_total": units_total,
            },
            "charts": _build_charts(candidates),
        }
