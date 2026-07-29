"""
PA-PERF-005 — Warm Analysis Session cache (secondary; outside L1 byte-identity set).

Detects identical engineering inputs and reuses existing L1 artifacts.
Never performs engineering calculations. Never mutates session_hash math.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np
import yaml

from analysis_session import (
    SESSION_ARTIFACT_FILENAMES,
    SESSION_CLUSTERING_JSON,
    SESSION_CORRELATION_JSON,
    SESSION_EMBEDDINGS_JSON,
    SESSION_EXECUTIONS_JSON,
    SESSION_GENERATED_BY,
    SESSION_MANIFEST_JSON,
    SESSION_REDUNDANCY_JSON,
    SESSION_SCAN_VECTORS_JSON,
    SESSION_SIMILARITY_JSON,
    SESSION_SUMMARY_JSON,
    AnalysisSession,
    build_session_manifest,
    resolve_session_log_paths,
)
from analysis_session_similarity_exporter import ARTIFACT_VERSION as SIMILARITY_ARTIFACT_VERSION
from pattern_embedding import EMBEDDING_VERSION, FEATURE_VERSION

logger = logging.getLogger(__name__)

CACHE_RECORD_FILENAME = "PA-Analysis-Session_cache_record.json"
CACHE_PIPELINE_VERSION = "1.0"
PROJECT_VERSION = "paa-v2"
CACHE_RECORD_SCHEMA_VERSION = "1.0"

# Matches session_correlation_exporter correlation_version stamp.
CORRELATION_VERSION = "session-1.0"

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


@dataclass(frozen=True)
class WarmCacheResult:
    hit: bool
    reason: str
    session: Optional[AnalysisSession] = None
    validation_ms: float = 0.0
    session_hash: Optional[str] = None


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _git_commit_hash(repo_dir: str) -> Optional[str]:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if completed.returncode != 0:
            return None
        text = (completed.stdout or "").strip()
        return text or None
    except (OSError, subprocess.SubprocessError):
        return None


def _load_yaml_section(path: str, root_key: Optional[str] = None) -> Any:
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return None
    if root_key:
        return payload.get(root_key, payload)
    return payload


def _resolve_config_candidate(workspace_dir: str, relative: str) -> str:
    local = os.path.join(workspace_dir, "config", relative)
    if os.path.exists(local):
        return local
    return os.path.join(_REPO_ROOT, "config", relative)


def build_environment_metadata(*, repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """Runtime/env metadata for cache invalidation after upgrades (not L1)."""
    root = repo_dir or _REPO_ROOT
    try:
        import scipy

        scipy_version = getattr(scipy, "__version__", "unknown")
    except Exception:
        scipy_version = "unavailable"
    return {
        "python_version": sys.version.split()[0],
        "numpy_version": getattr(np, "__version__", "unknown"),
        "scipy_version": scipy_version,
        "project_version": PROJECT_VERSION,
        "git_commit": _git_commit_hash(root),
    }


def build_algorithm_versions() -> Dict[str, Any]:
    return {
        "cache_pipeline_version": CACHE_PIPELINE_VERSION,
        "session_generated_by": SESSION_GENERATED_BY,
        "embedding_version": EMBEDDING_VERSION,
        "feature_version": FEATURE_VERSION,
        "similarity_artifact_version": SIMILARITY_ARTIFACT_VERSION,
        "correlation_version": CORRELATION_VERSION,
        "cluster_version": 1,
    }


def build_config_fingerprint(
    workspace_dir: str,
    *,
    analysis_session_config_path: Optional[str] = None,
) -> str:
    """Hash analysis_session + clustering/similarity/redundancy YAML that affect L1."""
    analysis_path = analysis_session_config_path or _resolve_config_candidate(
        workspace_dir, "analysis_session.yaml"
    )
    payload = {
        "analysis_session": _load_yaml_section(analysis_path, "analysis_session"),
        "clustering": _load_yaml_section(
            _resolve_config_candidate(workspace_dir, "clustering.yaml"),
            "clustering",
        ),
        "similarity": _load_yaml_section(
            _resolve_config_candidate(workspace_dir, "similarity.yaml"),
            None,
        ),
        "redundancy": _load_yaml_section(
            _resolve_config_candidate(workspace_dir, "redundancy.yaml"),
            None,
        ),
    }
    return _canonical_sha256(payload)


def resolve_stil_absolute_path(workspace_dir: str, stil_file: str) -> str:
    if stil_file and os.path.isabs(stil_file) and os.path.exists(stil_file):
        return os.path.abspath(stil_file)
    candidate = os.path.join(workspace_dir, stil_file) if stil_file else workspace_dir
    return os.path.abspath(candidate)


def build_cache_identity(
    *,
    workspace_dir: str,
    stil_file: str,
    requested_log_paths: Sequence[str],
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build warm-cache identity (secondary). Does not alter L1 session_hash inputs.
    """
    absolute_paths, relative_paths = resolve_session_log_paths(
        workspace_dir, requested_log_paths
    )
    stil_abs = resolve_stil_absolute_path(workspace_dir, stil_file)
    stil_hash = file_sha256(stil_abs) if os.path.exists(stil_abs) else "missing-stil"

    ate_entries = [
        {
            "relative_path": rel_path,
            "sha256": file_sha256(abs_path),
        }
        for abs_path, rel_path in zip(absolute_paths, relative_paths)
    ]

    # Preview session_hash using the same L1 manifest fields (stable timestamp).
    preview_manifest = build_session_manifest(
        stil_file=stil_file,
        input_ate_logs=list(relative_paths),
        generated_timestamp="1970-01-01T00:00:00Z",
    )
    session_hash = str(preview_manifest.get("session_hash") or "")

    return {
        "stil_file": stil_file,
        "stil_sha256": stil_hash,
        "ate_logs": ate_entries,
        "config_fingerprint": build_config_fingerprint(
            workspace_dir,
            analysis_session_config_path=config_path,
        ),
        "algorithm_versions": build_algorithm_versions(),
        "environment": build_environment_metadata(),
        "session_hash": session_hash,
        "input_ate_logs": list(relative_paths),
    }


def identity_matches(expected: Mapping[str, Any], recorded: Mapping[str, Any]) -> bool:
    """Compare identity payloads (order-sensitive for ate_logs)."""
    keys = (
        "stil_file",
        "stil_sha256",
        "ate_logs",
        "config_fingerprint",
        "algorithm_versions",
        "environment",
        "session_hash",
        "input_ate_logs",
    )
    for key in keys:
        if expected.get(key) != recorded.get(key):
            return False
    return True


def load_cache_record(output_dir: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(output_dir, CACHE_RECORD_FILENAME)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_cache_record(
    output_dir: str,
    *,
    identity: Mapping[str, Any],
    artifact_hashes: Mapping[str, str],
    session_hash: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, CACHE_RECORD_FILENAME)
    record = {
        "generated_by": SESSION_GENERATED_BY,
        "artifact": "cache_record",
        "schema_version": CACHE_RECORD_SCHEMA_VERSION,
        "session_hash": session_hash,
        "identity": dict(identity),
        "l1_artifact_sha256": {
            name: artifact_hashes[name]
            for name in SESSION_ARTIFACT_FILENAMES
            if name in artifact_hashes
        },
    }
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, sort_keys=True, ensure_ascii=False)
    os.replace(temporary, path)
    return path


def _load_optional_json(output_dir: str, filename: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(output_dir, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid artifact object: {filename}")
    return payload


def load_analysis_session_from_artifacts(output_dir: str) -> AnalysisSession:
    """Rebuild AnalysisSession from on-disk L1 JSON (no engineering recompute)."""

    def _load_required(filename: str) -> Dict[str, Any]:
        payload = _load_optional_json(output_dir, filename)
        if payload is None:
            raise ValueError(f"Missing required artifact: {filename}")
        return payload

    manifest = _load_required(SESSION_MANIFEST_JSON)
    executions_payload = _load_required(SESSION_EXECUTIONS_JSON)
    executions = executions_payload.get("executions")
    if not isinstance(executions, list):
        raise ValueError("Invalid executions artifact")
    summary = _load_required(SESSION_SUMMARY_JSON)
    return AnalysisSession(
        manifest=manifest,
        executions=executions,
        summary=summary,
        scan_vectors=_load_optional_json(output_dir, SESSION_SCAN_VECTORS_JSON),
        embeddings=_load_optional_json(output_dir, SESSION_EMBEDDINGS_JSON),
        similarity=_load_optional_json(output_dir, SESSION_SIMILARITY_JSON),
        clustering=_load_optional_json(output_dir, SESSION_CLUSTERING_JSON),
        redundancy=_load_optional_json(output_dir, SESSION_REDUNDANCY_JSON),
        correlation=_load_optional_json(output_dir, SESSION_CORRELATION_JSON),
    )


def validate_warm_cache(
    output_dir: str,
    identity: Mapping[str, Any],
) -> WarmCacheResult:
    """
    Validate secondary cache record + L1 digests.
    On any failure: hit=False with reason (caller runs full pipeline).
    """
    started = time.perf_counter()

    def _result(
        hit: bool,
        reason: str,
        session: Optional[AnalysisSession] = None,
    ) -> WarmCacheResult:
        return WarmCacheResult(
            hit=hit,
            reason=reason,
            session=session,
            validation_ms=round((time.perf_counter() - started) * 1000.0, 3),
            session_hash=str(identity.get("session_hash") or "") or None,
        )

    record = load_cache_record(output_dir)
    if record is None:
        return _result(False, "missing_cache_record")

    recorded_identity = record.get("identity")
    if not isinstance(recorded_identity, Mapping):
        return _result(False, "invalid_cache_record_identity")

    if not identity_matches(identity, recorded_identity):
        return _result(False, "identity_mismatch")

    recorded_hash = str(record.get("session_hash") or "")
    expected_hash = str(identity.get("session_hash") or "")
    if not recorded_hash or recorded_hash != expected_hash:
        return _result(False, "session_hash_mismatch")

    l1_hashes = record.get("l1_artifact_sha256")
    if not isinstance(l1_hashes, Mapping) or not l1_hashes:
        return _result(False, "missing_l1_digests")

    for filename, expected_digest in l1_hashes.items():
        path = os.path.join(output_dir, str(filename))
        if not os.path.exists(path):
            return _result(False, f"missing_artifact:{filename}")
        if not expected_digest:
            return _result(False, f"missing_digest:{filename}")
        actual = file_sha256(path)
        if actual != expected_digest:
            return _result(False, f"hash_mismatch:{filename}")

    # Core trio must always be present for a valid warm session.
    for required in (
        SESSION_MANIFEST_JSON,
        SESSION_EXECUTIONS_JSON,
        SESSION_SUMMARY_JSON,
    ):
        if required not in l1_hashes:
            return _result(False, f"missing_digest:{required}")

    manifest_path = os.path.join(output_dir, SESSION_MANIFEST_JSON)
    try:
        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return _result(False, "unreadable_manifest")
    if not isinstance(manifest, dict):
        return _result(False, "invalid_manifest")
    if str(manifest.get("session_hash") or "") != expected_hash:
        return _result(False, "manifest_session_hash_mismatch")

    try:
        session = load_analysis_session_from_artifacts(output_dir)
    except (OSError, ValueError, json.JSONDecodeError, TypeError) as exc:
        return _result(False, f"load_failed:{exc}")

    return _result(True, "hit", session=session)


def try_warm_cache(
    *,
    workspace_dir: str,
    output_dir: str,
    stil_file: str,
    requested_log_paths: Sequence[str],
    config_path: Optional[str] = None,
    enabled: bool = True,
) -> Tuple[WarmCacheResult, Dict[str, Any]]:
    """
    Build identity and validate cache. Returns (result, identity).
    When enabled=False, returns miss without reading the record.
    """
    identity = build_cache_identity(
        workspace_dir=workspace_dir,
        stil_file=stil_file,
        requested_log_paths=requested_log_paths,
        config_path=config_path,
    )
    if not enabled:
        return (
            WarmCacheResult(
                hit=False,
                reason="cache_disabled",
                session_hash=str(identity.get("session_hash") or "") or None,
            ),
            identity,
        )
    result = validate_warm_cache(output_dir, identity)
    if result.hit:
        logger.info(
            "Analysis Session warm cache HIT session_hash=%s validation_ms=%.3f",
            result.session_hash,
            result.validation_ms,
        )
    else:
        logger.info(
            "Analysis Session warm cache MISS/INVALID reason=%s session_hash=%s "
            "validation_ms=%.3f",
            result.reason,
            identity.get("session_hash"),
            result.validation_ms,
        )
    return result, identity
