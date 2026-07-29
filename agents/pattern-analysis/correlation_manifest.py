"""
PA-FR-009 Correlation Manifest — provenance metadata and canonical hash generation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from cluster_manifest import compute_canonical_hash

CORRELATION_VERSION = 1
MANIFEST_HASH_EXCLUDE = frozenset(
    {
        "correlation_hash",
        "generated_timestamp",
    }
)


def build_manifest_payload(
    *,
    input_stil: str,
    input_ate_logs: List[str],
    metadata_rows: int,
    ate_rows: int,
    matched_rows: int,
    unmatched_metadata: int,
    unmatched_ate: int,
    duplicate_histories: int,
    validation_status: str,
    generated_timestamp: str | None = None,
) -> Dict[str, Any]:
    timestamp = generated_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "generated_by": "PA-FR-009",
        "correlation_version": CORRELATION_VERSION,
        "generated_timestamp": timestamp,
        "input_stil": input_stil,
        "input_ate_logs": sorted(input_ate_logs),
        "metadata_rows": metadata_rows,
        "ate_rows": ate_rows,
        "matched_rows": matched_rows,
        "unmatched_metadata": unmatched_metadata,
        "unmatched_ate": unmatched_ate,
        "duplicate_histories": duplicate_histories,
        "validation_status": validation_status,
    }


def attach_correlation_hash(manifest: Dict[str, Any]) -> Dict[str, Any]:
    hash_input = {
        key: value
        for key, value in manifest.items()
        if key not in MANIFEST_HASH_EXCLUDE
    }
    manifest["correlation_hash"] = compute_canonical_hash(hash_input)
    return manifest
