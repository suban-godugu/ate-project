"""
PA-FR-006.6.1 — startup verification for canonical hash (operational diagnostics only).
"""
from __future__ import annotations

from cluster_manifest import (
    CANONICAL_HASH_EXCLUDES,
    CANONICAL_HASH_SCOPE,
    CANONICAL_HASH_VERSION,
    HASH_METHOD,
    compute_canonical_cluster_hash,
)


class CanonicalHashStartupError(RuntimeError):
    """Raised when canonical hash startup self-test fails."""


STARTUP_SELF_TEST_MANIFEST = {
    "algorithm": "Agglomerative",
    "similarity_threshold": 0.99,
    "threshold": 0.99,
    "generated_timestamp": "2026-01-01T00:00:00Z",
    "cluster_version": 1,
    "canonical_cluster_hash": "startup-self-test",
    "hash_method": HASH_METHOD,
}

STARTUP_SELF_TEST_PATTERN_CLUSTERS = {
    "cluster_version": 1,
    "patterns": [
        {
            "pattern_id": "P001",
            "cluster_id": "C001",
            "similarity_to_centroid": 1.0,
        }
    ],
}


def _hash_scope_display() -> str:
    if CANONICAL_HASH_SCOPE == ("configuration", "pattern_assignments"):
        return "Configuration + Pattern Assignments"
    return " + ".join(part.replace("_", " ").title() for part in CANONICAL_HASH_SCOPE)


def run_canonical_hash_startup_verification() -> None:
    """Print startup banner, excluded-field diagnostics, and run one deterministic self-test."""
    print("==================================================")
    print()
    print("PA-FR-006 Canonical Hash")
    print()
    print(f"Version              : {CANONICAL_HASH_VERSION}")
    print()
    print("Algorithm            : SHA-256")
    print()
    print("Specification        : Deterministic")
    print()
    print("Runtime Metadata     : Excluded")
    print()
    print(f"Hash Scope           : {_hash_scope_display()}")
    print()
    print("==================================================")
    print()
    print("Excluded Runtime Fields")
    print()
    for field in CANONICAL_HASH_EXCLUDES:
        print(f"- {field}")
    print()

    hash_run_1 = compute_canonical_cluster_hash(
        STARTUP_SELF_TEST_MANIFEST,
        STARTUP_SELF_TEST_PATTERN_CLUSTERS,
    )
    hash_run_2 = compute_canonical_cluster_hash(
        STARTUP_SELF_TEST_MANIFEST,
        STARTUP_SELF_TEST_PATTERN_CLUSTERS,
    )
    if hash_run_1 != hash_run_2:
        print("Canonical Hash Self-Test : FAILED")
        raise CanonicalHashStartupError(
            "Canonical hash startup self-test failed: repeated hashing produced different digests."
        )
    print("Canonical Hash Self-Test : PASSED")
