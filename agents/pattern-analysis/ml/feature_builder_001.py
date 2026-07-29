"""PA-ML-001 feature builder — read-only join of L1 session artifacts."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from analysis_session import (
    SESSION_CLUSTERING_JSON,
    SESSION_EMBEDDINGS_JSON,
    SESSION_EXECUTIONS_JSON,
    SESSION_MANIFEST_JSON,
    SESSION_REDUNDANCY_JSON,
)
from ml.contracts import (
    DEFAULT_EMBEDDING_DIM,
    FORBIDDEN_FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
    SCALAR_FEATURE_NAMES,
)

from robustness_config import (
    RobustnessConfig,
    label_from_result,
    load_robustness_config,
    lot_from_relpath,
)


def unit_id_from_row(row: Mapping[str, Any]) -> str:
    pattern_id = str(row.get("pattern_id") or "")
    relpath = str(row.get("source_log_relpath") or "")
    source_log = str(row.get("source_log") or "")
    return f"{pattern_id}::{relpath or source_log}"


def _lot_from_path(path: str) -> str:
    normalized = str(path or "").replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else "Ungrouped"


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def _embedding_feature_names(dim: int) -> Tuple[str, ...]:
    return tuple(f"emb_{index}" for index in range(dim))


def feature_names_for_dim(dim: int = DEFAULT_EMBEDDING_DIM) -> List[str]:
    names = list(_embedding_feature_names(dim)) + list(SCALAR_FEATURE_NAMES)
    for name in names:
        if name in FORBIDDEN_FEATURE_NAMES:
            raise ValueError(f"Forbidden feature name in schema: {name}")
    return names


def build_feature_schema(dim: int = DEFAULT_EMBEDDING_DIM) -> Dict[str, Any]:
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "embedding_dimension": int(dim),
        "feature_names": feature_names_for_dim(dim),
        "forbidden_feature_names": sorted(FORBIDDEN_FEATURE_NAMES),
        "grain": "pattern_x_source_log",
        "label": "latest_result_FAIL_equals_1",
    }


def _index_executions(
    executions_payload: Optional[Mapping[str, Any]],
    *,
    robustness_cfg: Optional[RobustnessConfig] = None,
) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    aggregate_labels: Dict[str, int] = {}
    if not isinstance(executions_payload, Mapping):
        return indexed
    rows = executions_payload.get("executions")
    if not isinstance(rows, list):
        return indexed
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        uid = unit_id_from_row(row)
        if uid not in indexed:
            indexed[uid] = dict(row)
            label = _label_from_result(
                row.get("latest_result"),
                robustness_cfg=robustness_cfg,
            )
            if label is not None:
                aggregate_labels[uid] = max(aggregate_labels.get(uid, label), label)
    for uid, label in aggregate_labels.items():
        if uid in indexed:
            indexed[uid]["_aggregate_label"] = label
    return indexed


def _index_assignments(
    clustering_payload: Optional[Mapping[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    if not isinstance(clustering_payload, Mapping):
        return indexed
    rows = clustering_payload.get("unit_assignments")
    if not isinstance(rows, list):
        return indexed
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        uid = str(row.get("unit_id") or unit_id_from_row(row))
        if uid in indexed:
            continue
        indexed[uid] = dict(row)
    return indexed


def _redundancy_stats(
    redundancy_payload: Optional[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    stats: Dict[str, Dict[str, float]] = {}
    if not isinstance(redundancy_payload, Mapping):
        return stats
    candidates = redundancy_payload.get("candidates")
    if not isinstance(candidates, list):
        return stats
    for row in candidates:
        if not isinstance(row, Mapping):
            continue
        raw = float(row.get("raw_similarity") or 0.0)
        conf = float(row.get("confidence_score") or 0.0)
        for key in ("unit_a", "unit_b"):
            uid = str(row.get(key) or "")
            if not uid:
                continue
            bucket = stats.setdefault(
                uid,
                {
                    "redundancy_neighbor_count": 0.0,
                    "redundancy_max_raw_similarity": 0.0,
                    "redundancy_max_confidence": 0.0,
                },
            )
            bucket["redundancy_neighbor_count"] += 1.0
            bucket["redundancy_max_raw_similarity"] = max(
                bucket["redundancy_max_raw_similarity"], raw
            )
            bucket["redundancy_max_confidence"] = max(
                bucket["redundancy_max_confidence"], conf
            )
    return stats


def _cluster_code_map(assignments: Mapping[str, Mapping[str, Any]]) -> Dict[str, int]:
    cluster_ids = sorted(
        {
            str(row.get("cluster_id") or "")
            for row in assignments.values()
            if str(row.get("cluster_id") or "")
        }
    )
    return {cluster_id: index + 1 for index, cluster_id in enumerate(cluster_ids)}


def _label_from_result(
    latest_result: Any,
    *,
    robustness_cfg: Optional[RobustnessConfig] = None,
) -> Optional[int]:
    return label_from_result(latest_result, config=robustness_cfg)


def build_feature_rows_from_payloads(
    *,
    embeddings_payload: Optional[Mapping[str, Any]],
    executions_payload: Optional[Mapping[str, Any]] = None,
    clustering_payload: Optional[Mapping[str, Any]] = None,
    redundancy_payload: Optional[Mapping[str, Any]] = None,
    manifest_payload: Optional[Mapping[str, Any]] = None,
    include_labels: bool = False,
    robustness_cfg: Optional[RobustnessConfig] = None,
) -> Dict[str, Any]:
    """
    Build deterministic feature rows for PA-ML-001.

    When include_labels=False (online inference), latest_result is never attached.
    """
    if not isinstance(embeddings_payload, Mapping):
        return {
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "embedding_dimension": DEFAULT_EMBEDDING_DIM,
            "feature_names": feature_names_for_dim(DEFAULT_EMBEDDING_DIM),
            "session_hash": (
                manifest_payload.get("session_hash")
                if isinstance(manifest_payload, Mapping)
                else None
            ),
            "rows": [],
        }

    dim = int(embeddings_payload.get("embedding_dimension") or DEFAULT_EMBEDDING_DIM)
    feature_names = feature_names_for_dim(dim)
    executions = _index_executions(executions_payload, robustness_cfg=robustness_cfg)
    assignments = _index_assignments(clustering_payload)
    redundancy = _redundancy_stats(redundancy_payload)
    cluster_codes = _cluster_code_map(assignments)

    embedding_rows = [
        row
        for row in (embeddings_payload.get("embeddings") or [])
        if isinstance(row, Mapping)
    ]
    embedding_rows.sort(
        key=lambda row: (
            str(row.get("pattern_id") or ""),
            str(row.get("source_log_relpath") or row.get("source_log") or ""),
        )
    )

    rows_out: List[Dict[str, Any]] = []
    for row in embedding_rows:
        embedding = row.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != dim:
            continue
        uid = unit_id_from_row(row)
        exec_row = executions.get(uid) or {}
        asg = assignments.get(uid) or {}
        red = redundancy.get(uid) or {}
        cluster_id = str(asg.get("cluster_id") or "")
        source_log = str(row.get("source_log") or exec_row.get("source_log") or "")
        relpath = str(
            row.get("source_log_relpath") or exec_row.get("source_log_relpath") or ""
        )
        features = {
            f"emb_{index}": float(embedding[index]) for index in range(dim)
        }
        features.update(
            {
                "toggle_coverage_pct": float(exec_row.get("toggle_coverage_pct") or 0.0),
                "toggle_density_pct": float(exec_row.get("toggle_density_pct") or 0.0),
                "toggle_count": float(exec_row.get("toggle_count") or 0.0),
                "cluster_id_code": float(cluster_codes.get(cluster_id, 0)),
                "similarity_to_centroid": float(
                    asg.get("similarity_to_centroid") or 0.0
                ),
                "redundancy_neighbor_count": float(
                    red.get("redundancy_neighbor_count") or 0.0
                ),
                "redundancy_max_raw_similarity": float(
                    red.get("redundancy_max_raw_similarity") or 0.0
                ),
                "redundancy_max_confidence": float(
                    red.get("redundancy_max_confidence") or 0.0
                ),
            }
        )
        for name in FORBIDDEN_FEATURE_NAMES:
            features.pop(name, None)

        record: Dict[str, Any] = {
            "unit_id": uid,
            "pattern_id": str(row.get("pattern_id") or ""),
            "source_log": source_log,
            "source_log_relpath": relpath,
            "source_lot": str(
                asg.get("source_lot")
                or lot_from_relpath(relpath or source_log, config=robustness_cfg)
            ),
            "cluster_id": cluster_id,
            "features": {name: features[name] for name in feature_names},
        }
        if include_labels:
            label = exec_row.get("_aggregate_label")
            if label is None:
                label = _label_from_result(
                    exec_row.get("latest_result"), robustness_cfg=robustness_cfg
                )
            if label is None:
                continue
            record["label"] = int(label)
        rows_out.append(record)

    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "embedding_dimension": dim,
        "feature_names": feature_names,
        "session_hash": (
            (manifest_payload or {}).get("session_hash")
            if isinstance(manifest_payload, Mapping)
            else None
        )
        or (
            clustering_payload.get("session_hash")
            if isinstance(clustering_payload, Mapping)
            else None
        ),
        "rows": rows_out,
    }


def build_feature_rows_from_output_dir(
    output_dir: str,
    *,
    include_labels: bool = False,
) -> Dict[str, Any]:
    workspace_dir = os.path.dirname(output_dir)
    robustness_cfg = load_robustness_config(workspace_dir)
    return build_feature_rows_from_payloads(
        embeddings_payload=_load_json(os.path.join(output_dir, SESSION_EMBEDDINGS_JSON)),
        executions_payload=_load_json(os.path.join(output_dir, SESSION_EXECUTIONS_JSON)),
        clustering_payload=_load_json(os.path.join(output_dir, SESSION_CLUSTERING_JSON)),
        redundancy_payload=_load_json(os.path.join(output_dir, SESSION_REDUNDANCY_JSON)),
        manifest_payload=_load_json(os.path.join(output_dir, SESSION_MANIFEST_JSON)),
        include_labels=include_labels,
        robustness_cfg=robustness_cfg,
    )


def matrix_from_rows(
    feature_bundle: Mapping[str, Any],
) -> Tuple[List[List[float]], List[str], List[str]]:
    names = list(feature_bundle.get("feature_names") or [])
    rows = feature_bundle.get("rows") or []
    matrix: List[List[float]] = []
    unit_ids: List[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        features = row.get("features")
        if not isinstance(features, Mapping):
            continue
        matrix.append([float(features.get(name) or 0.0) for name in names])
        unit_ids.append(str(row.get("unit_id") or ""))
    return matrix, names, unit_ids
