"""
PA-FR-006 Cluster Manifest — provenance metadata and integrity hash generation.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

from cluster_engine import ClusteringRunResult

HASH_METHOD = "Canonical SHA-256"
CANONICAL_HASH_VERSION = "2"
CANONICAL_HASH_DESCRIPTION = (
    "Deterministic SHA-256 computed from clustering results only. Runtime metadata is excluded."
)
CANONICAL_HASH_SCOPE = (
    "configuration",
    "pattern_assignments",
)
CANONICAL_HASH_EXCLUDES = (
    "generated_timestamp",
    "cluster_version",
    "canonical_cluster_hash",
    "cluster_hash",
    "hash_method",
    "canonical_hash_version",
    "canonical_hash_description",
    "canonical_hash_scope",
    "canonical_hash_excludes",
)

MANIFEST_HASH_EXCLUDE = frozenset(
    {
        "canonical_cluster_hash",
        "cluster_hash",
        "hash_method",
        "generated_timestamp",
        "cluster_version",
        "canonical_hash_version",
        "canonical_hash_description",
        "canonical_hash_scope",
        "canonical_hash_excludes",
    }
)

PATTERN_CLUSTERS_HASH_EXCLUDE = frozenset({"cluster_version"})


def canonical_json_bytes(data: dict) -> bytes:
    """Deterministic canonical form: recursively sorted keys, compact separators, UTF-8."""
    canonical_str = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    canonical_str = canonical_str.replace("\r\n", "\n").rstrip() + "\n"
    return canonical_str.encode("utf-8")


def compute_canonical_hash(data: dict) -> str:
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


def build_manifest_payload(
    result: ClusteringRunResult,
    canonical_cluster_hash: str,
    generated_timestamp: str | None = None,
) -> Dict[str, Any]:
    timestamp = generated_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "algorithm": result.file_rollup["algorithm"],
        "linkage": result.file_rollup["linkage"],
        "distance_metric": result.file_rollup["distance_metric"],
        "similarity_metric": result.file_rollup["similarity_metric"],
        "similarity_threshold": result.file_rollup["similarity_threshold"],
        "threshold": result.file_rollup["similarity_threshold"],
        "embedding_version": result.embedding_version,
        "cluster_version": result.cluster_version,
        "generated_timestamp": timestamp,
        "generated_by": "PA-FR-006",
        "generated_file": "PA-FR-006_pattern_clusters.json",
        "total_patterns": result.file_rollup.get("total_patterns", 0),
        "total_clusters": result.file_rollup["total_clusters"],
        "hash_method": HASH_METHOD,
        "canonical_cluster_hash": canonical_cluster_hash,
        "canonical_hash_version": CANONICAL_HASH_VERSION,
        "canonical_hash_description": CANONICAL_HASH_DESCRIPTION,
        "canonical_hash_scope": list(CANONICAL_HASH_SCOPE),
        "canonical_hash_excludes": list(CANONICAL_HASH_EXCLUDES),
    }


def compute_canonical_cluster_hash(
    manifest_data: Dict[str, Any],
    pattern_clusters_data: Dict[str, Any],
) -> str:
    """
    SHA-256 over canonical JSON of deterministic clustering content only.

    Runtime metadata (timestamps, version numbers, hash fields) is excluded from
    the hash input but remains in exported JSON/manifest files.
    """
    manifest_for_hash = {
        key: value
        for key, value in manifest_data.items()
        if key not in MANIFEST_HASH_EXCLUDE
    }
    pattern_clusters_for_hash = {
        key: value
        for key, value in pattern_clusters_data.items()
        if key not in PATTERN_CLUSTERS_HASH_EXCLUDE
    }
    combined = {
        "manifest": manifest_for_hash,
        "pattern_clusters": pattern_clusters_for_hash,
    }
    return compute_canonical_hash(combined)
