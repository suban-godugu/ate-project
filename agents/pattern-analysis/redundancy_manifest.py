"""
PA-FR-007 Redundancy Manifest — provenance metadata for redundancy exports.
"""
from __future__ import annotations

from typing import Any, Dict

MANIFEST_VERSION = 1


def build_redundancy_manifest_payload(
    embedding_version: str,
    cluster_version: int,
    similarity_threshold: float,
    total_candidates: int,
    validation_status: str,
    generated_timestamp: str,
) -> Dict[str, Any]:
    return {
        "fr_id": "PA-FR-007",
        "generated_timestamp": generated_timestamp,
        "embedding_version": embedding_version,
        "cluster_version": cluster_version,
        "similarity_threshold": similarity_threshold,
        "total_candidates": total_candidates,
        "validation_status": validation_status,
        "manifest_version": MANIFEST_VERSION,
    }
