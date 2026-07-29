"""
Session downstream adapter — Phase C infrastructure only.

Routes multi-log session artifacts toward FR-006–010 without modifying
cluster / similarity / redundancy engines.

Embedding projection policy is configurable and intentionally deferred:
no finalized multi-execution projection is applied in Phase C.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from analysis_session import (
    SESSION_EMBEDDINGS_JSON,
    SESSION_EXECUTIONS_JSON,
    SESSION_MANIFEST_JSON,
    SESSION_SCAN_VECTORS_JSON,
    SESSION_SUMMARY_JSON,
)
from session_config import SessionConfig, load_session_config

SESSION_RUNTIME_DIRNAME = "session_runtime"
PROJECTION_DEFERRED = "deferred"

DOWNSTREAM_DEFERRED_REASON = (
    "Multi-execution embedding projection policy is not finalized. "
    "Session artifacts are preserved; FR-006–008 engine invocation is deferred."
)


def session_runtime_dir(output_dir: str) -> str:
    return os.path.join(output_dir, SESSION_RUNTIME_DIRNAME)


def load_session_manifest(output_dir: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(output_dir, SESSION_MANIFEST_JSON)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def session_artifacts_present(output_dir: str) -> bool:
    required = (
        SESSION_MANIFEST_JSON,
        SESSION_EXECUTIONS_JSON,
        SESSION_SUMMARY_JSON,
        SESSION_SCAN_VECTORS_JSON,
        SESSION_EMBEDDINGS_JSON,
    )
    return all(os.path.exists(os.path.join(output_dir, name)) for name in required)


def is_projection_ready(config: Optional[SessionConfig] = None) -> bool:
    """True only when a finalized projection policy is configured (not Phase C)."""
    config = config or SessionConfig()
    policy = (config.downstream_embedding_projection or PROJECTION_DEFERRED).strip().lower()
    return policy not in ("", PROJECTION_DEFERRED, "none", "unset")


def ensure_session_runtime_dir(output_dir: str) -> str:
    """Create the session runtime staging directory (empty shell for future projection)."""
    path = session_runtime_dir(output_dir)
    os.makedirs(path, exist_ok=True)
    return path


def describe_downstream_readiness(
    output_dir: str,
    config: Optional[SessionConfig] = None,
) -> Dict[str, Any]:
    """
    Report whether session downstream phases can run.

    Phase C: always returns DEFERRED when projection policy is deferred,
    even if session artifacts exist. Does not invoke FR-006–008 engines.
    """
    config = config or SessionConfig()
    policy = config.downstream_embedding_projection or PROJECTION_DEFERRED
    artifacts_ready = session_artifacts_present(output_dir)
    runtime_dir = ensure_session_runtime_dir(output_dir)
    ready = artifacts_ready and is_projection_ready(config)

    status = "READY" if ready else "DEFERRED"
    payload: Dict[str, Any] = {
        "generated_by": "PA-Analysis-Session",
        "status": status,
        "projection_policy": policy,
        "session_artifacts_ready": artifacts_ready,
        "runtime_dir": runtime_dir,
        "engines_invoked": False,
    }
    if not ready:
        payload["reason"] = DOWNSTREAM_DEFERRED_REASON
    return payload


def prepare_session_downstream(
    output_dir: str,
    workspace_dir: str,
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Adapter entry point for multi-log orchestration.

    Sets up runtime infrastructure and returns readiness. Does not project
    embeddings and does not call cluster/similarity/redundancy engines.
    """
    resolved_config = config_path or os.path.join(workspace_dir, "config", "analysis_session.yaml")
    if not os.path.exists(resolved_config):
        resolved_config = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "config",
            "analysis_session.yaml",
        )
    config = load_session_config(resolved_config)
    return describe_downstream_readiness(output_dir, config=config)
