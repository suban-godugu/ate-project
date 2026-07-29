"""
PA-Analysis-Session — orchestration pathway for multi-log STIL + ATE workflows.

This module does NOT modify, extend, or write any completed FR artifact
(PA-FR-004, PA-FR-005, etc.). It produces separate session JSON files only.

Single-log workflows continue to use the legacy pipeline unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

SESSION_GENERATED_BY = "PA-Analysis-Session"
SESSION_MANIFEST_JSON = "PA-Analysis-Session_manifest.json"
SESSION_EXECUTIONS_JSON = "PA-Analysis-Session_executions.json"
SESSION_SUMMARY_JSON = "PA-Analysis-Session_summary.json"
SESSION_SCAN_VECTORS_JSON = "PA-Analysis-Session_scan_vectors.json"
SESSION_EMBEDDINGS_JSON = "PA-Analysis-Session_embeddings.json"
SESSION_SIMILARITY_JSON = "PA-Analysis-Session_similarity.json"
SESSION_CLUSTERING_JSON = "PA-Analysis-Session_clustering.json"
SESSION_REDUNDANCY_JSON = "PA-Analysis-Session_redundancy.json"
SESSION_CORRELATION_JSON = "PA-Analysis-Session_correlation.json"

SESSION_ARTIFACT_FILENAMES = (
    SESSION_MANIFEST_JSON,
    SESSION_EXECUTIONS_JSON,
    SESSION_SUMMARY_JSON,
    SESSION_SCAN_VECTORS_JSON,
    SESSION_EMBEDDINGS_JSON,
    SESSION_SIMILARITY_JSON,
    SESSION_CLUSTERING_JSON,
    SESSION_REDUNDANCY_JSON,
    SESSION_CORRELATION_JSON,
)

MANIFEST_HASH_EXCLUDE = frozenset(
    {
        "session_hash",
        "generated_timestamp",
    }
)


class SessionPathError(ValueError):
    """Raised when session log paths cannot be resolved."""


def workspace_relative_path(path: str, workspace_dir: str) -> str:
    absolute = os.path.abspath(path)
    workspace = os.path.abspath(workspace_dir)
    try:
        return os.path.relpath(absolute, workspace).replace("\\", "/")
    except ValueError:
        return os.path.basename(absolute)


def requires_session_path(selected_logs: Sequence[str]) -> bool:
    """Return True when the orchestration layer must use the session pathway."""
    return len(selected_logs) > 1


def resolve_session_log_paths(
    workspace_dir: str,
    requested_paths: Sequence[str],
) -> Tuple[List[str], List[str]]:
    """
    Resolve and deterministically order ATE log paths for a session.

    Ordering matches PA-FR-009 convention: lexicographic by workspace-relative path.
    Returns (absolute_paths, workspace_relative_paths).
    """
    if not requested_paths:
        raise SessionPathError("At least two ATE log paths are required for a session.")
    if len(requested_paths) < 2:
        raise SessionPathError("Analysis Session requires two or more ATE log files.")

    resolved: List[str] = []
    for item in requested_paths:
        candidate = item if os.path.isabs(item) else os.path.join(workspace_dir, item)
        if not os.path.exists(candidate):
            raise SessionPathError(f"ATE log not found: {item}")
        resolved.append(os.path.abspath(candidate))

    rel_paths = [workspace_relative_path(path, workspace_dir) for path in resolved]
    ordered = sorted(zip(resolved, rel_paths), key=lambda pair: pair[1])
    absolute_paths = [item[0] for item in ordered]
    relative_paths = [item[1] for item in ordered]
    return absolute_paths, relative_paths


def compute_session_hash(manifest: Dict[str, Any]) -> str:
    hash_input = {
        key: value
        for key, value in manifest.items()
        if key not in MANIFEST_HASH_EXCLUDE
    }
    canonical = json.dumps(hash_input, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_session_manifest(
    *,
    stil_file: str,
    input_ate_logs: List[str],
    generated_timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build session manifest.

    execution_count = number of input ATE log files (N).
    Total pattern×chain×log rows live in summary.execution_record_count / executions[].
    """
    timestamp = generated_timestamp or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest: Dict[str, Any] = {
        "generated_by": SESSION_GENERATED_BY,
        "stil_file": stil_file,
        "input_ate_logs": list(input_ate_logs),
        "execution_count": len(input_ate_logs),
        "generated_timestamp": timestamp,
    }
    manifest["session_hash"] = compute_session_hash(manifest)
    return manifest


@dataclass(frozen=True)
class AnalysisSession:
    """In-memory Analysis Session — canonical source for multi-log workflows."""

    manifest: Dict[str, Any]
    executions: List[Dict[str, Any]]
    summary: Dict[str, Any]
    scan_vectors: Optional[Dict[str, Any]] = None
    embeddings: Optional[Dict[str, Any]] = None
    similarity: Optional[Dict[str, Any]] = None
    clustering: Optional[Dict[str, Any]] = None
    redundancy: Optional[Dict[str, Any]] = None
    correlation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "manifest": self.manifest,
            "executions": self.executions,
            "summary": self.summary,
        }
        if self.scan_vectors is not None:
            payload["scan_vectors"] = self.scan_vectors
        if self.embeddings is not None:
            payload["embeddings"] = self.embeddings
        if self.similarity is not None:
            payload["similarity"] = self.similarity
        if self.clustering is not None:
            payload["clustering"] = self.clustering
        if self.redundancy is not None:
            payload["redundancy"] = self.redundancy
        if self.correlation is not None:
            payload["correlation"] = self.correlation
        return payload
