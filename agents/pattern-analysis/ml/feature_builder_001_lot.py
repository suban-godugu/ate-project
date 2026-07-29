"""PA-ML-001-LOT feature builder — pattern × LOT grain (aggregated from log rows)."""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from ml.contracts import (
    DEFAULT_EMBEDDING_DIM,
    FEATURE_SCHEMA_VERSION_LOT,
    FORBIDDEN_FEATURE_NAMES,
    LOT_SCALAR_FEATURE_NAMES,
)
from ml.feature_builder_001 import (
    _embedding_feature_names,
    build_feature_rows_from_output_dir as _build_log_rows_from_output_dir,
    build_feature_rows_from_payloads as _build_log_rows_from_payloads,
    matrix_from_rows,
)


def lot_unit_id(pattern_id: str, source_lot: str) -> str:
    return f"{pattern_id}::{source_lot}"


def feature_names_for_dim_lot(dim: int = DEFAULT_EMBEDDING_DIM) -> List[str]:
    names = list(_embedding_feature_names(dim)) + list(LOT_SCALAR_FEATURE_NAMES)
    for name in names:
        if name in FORBIDDEN_FEATURE_NAMES:
            raise ValueError(f"Forbidden feature name in schema: {name}")
    return names


def build_feature_schema_lot(dim: int = DEFAULT_EMBEDDING_DIM) -> Dict[str, Any]:
    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION_LOT,
        "embedding_dimension": int(dim),
        "feature_names": feature_names_for_dim_lot(dim),
        "forbidden_feature_names": sorted(FORBIDDEN_FEATURE_NAMES),
        "grain": "pattern_x_lot",
        "label": "any_FAIL_in_pattern_x_lot_equals_1",
    }


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _mode_cluster_id(members: Sequence[Mapping[str, Any]]) -> str:
    counts: Counter[str] = Counter()
    for row in members:
        cluster_id = str(row.get("cluster_id") or "")
        if cluster_id:
            counts[cluster_id] += 1
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _aggregate_log_rows_to_lot(
    log_bundle: Mapping[str, Any],
    *,
    include_labels: bool,
) -> Dict[str, Any]:
    dim = int(log_bundle.get("embedding_dimension") or DEFAULT_EMBEDDING_DIM)
    feature_names = feature_names_for_dim_lot(dim)
    log_rows = log_bundle.get("rows") or []

    grouped: Dict[Tuple[str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in log_rows:
        if not isinstance(row, Mapping):
            continue
        pattern_id = str(row.get("pattern_id") or "")
        source_lot = str(row.get("source_lot") or "Ungrouped")
        grouped[(pattern_id, source_lot)].append(row)

    rows_out: List[Dict[str, Any]] = []
    for pattern_id, source_lot in sorted(grouped.keys()):
        members = grouped[(pattern_id, source_lot)]
        embeddings: List[List[float]] = []
        for member in members:
            features = member.get("features")
            if not isinstance(features, Mapping):
                continue
            vector = [
                float(features.get(f"emb_{index}") or 0.0) for index in range(dim)
            ]
            embeddings.append(vector)
        if not embeddings:
            continue

        scalar_keys = (
            "toggle_coverage_pct",
            "toggle_density_pct",
            "toggle_count",
            "similarity_to_centroid",
            "redundancy_neighbor_count",
            "redundancy_max_raw_similarity",
            "redundancy_max_confidence",
        )
        scalar_means: Dict[str, float] = {}
        for key in scalar_keys:
            scalar_means[key] = _mean(
                [
                    float(
                        (member.get("features") or {}).get(key) or 0.0
                    )
                    for member in members
                    if isinstance(member.get("features"), Mapping)
                ]
            )

        mode_cluster = _mode_cluster_id(members)
        cluster_codes = {
            str(member.get("cluster_id") or ""): float(
                (member.get("features") or {}).get("cluster_id_code") or 0.0
            )
            for member in members
            if isinstance(member.get("features"), Mapping)
        }
        cluster_id_code = float(cluster_codes.get(mode_cluster, 0.0))

        features: Dict[str, float] = {
            f"emb_{index}": _mean([vector[index] for vector in embeddings])
            for index in range(dim)
        }
        features.update(scalar_means)
        features["cluster_id_code"] = cluster_id_code
        features["log_count_in_lot"] = float(len(members))

        for name in FORBIDDEN_FEATURE_NAMES:
            features.pop(name, None)

        record: Dict[str, Any] = {
            "unit_id": lot_unit_id(pattern_id, source_lot),
            "pattern_id": pattern_id,
            "source_lot": source_lot,
            "log_count_in_lot": int(len(members)),
            "cluster_id": mode_cluster,
            "features": {name: features[name] for name in feature_names},
        }

        if include_labels:
            labels = [
                int(member["label"])
                for member in members
                if member.get("label") is not None
            ]
            if not labels:
                continue
            record["label"] = 1 if any(label == 1 for label in labels) else 0

        rows_out.append(record)

    return {
        "feature_schema_version": FEATURE_SCHEMA_VERSION_LOT,
        "embedding_dimension": dim,
        "feature_names": feature_names,
        "session_hash": log_bundle.get("session_hash"),
        "rows": rows_out,
    }


def build_lot_feature_rows_from_payloads(
    *,
    embeddings_payload: Optional[Mapping[str, Any]],
    executions_payload: Optional[Mapping[str, Any]] = None,
    clustering_payload: Optional[Mapping[str, Any]] = None,
    redundancy_payload: Optional[Mapping[str, Any]] = None,
    manifest_payload: Optional[Mapping[str, Any]] = None,
    include_labels: bool = False,
) -> Dict[str, Any]:
    log_bundle = _build_log_rows_from_payloads(
        embeddings_payload=embeddings_payload,
        executions_payload=executions_payload,
        clustering_payload=clustering_payload,
        redundancy_payload=redundancy_payload,
        manifest_payload=manifest_payload,
        include_labels=include_labels,
    )
    return _aggregate_log_rows_to_lot(log_bundle, include_labels=include_labels)


def build_lot_feature_rows_from_output_dir(
    output_dir: str,
    *,
    include_labels: bool = False,
) -> Dict[str, Any]:
    log_bundle = _build_log_rows_from_output_dir(
        output_dir,
        include_labels=include_labels,
    )
    return _aggregate_log_rows_to_lot(log_bundle, include_labels=include_labels)


__all__ = [
    "build_feature_schema_lot",
    "build_lot_feature_rows_from_output_dir",
    "build_lot_feature_rows_from_payloads",
    "feature_names_for_dim_lot",
    "lot_unit_id",
    "matrix_from_rows",
]
