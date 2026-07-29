"""
Session request helpers — resolve selected ATE logs for orchestration routing.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional, Sequence

from analysis_session import SESSION_MANIFEST_JSON, requires_session_path


def resolve_selected_ate_logs(
    ate_log_filename: Optional[str] = None,
    ate_log_filenames: Optional[Sequence[str]] = None,
) -> List[str]:
    """
    Backward-compatible selection:
      ate_log_filenames if provided, else [ate_log_filename] if provided, else [].
    """
    if ate_log_filenames:
        return [str(item) for item in ate_log_filenames if item]
    if ate_log_filename:
        return [str(ate_log_filename)]
    return []


def should_use_session_path(selected_logs: Sequence[str]) -> bool:
    return requires_session_path(selected_logs)


def load_session_ate_logs_from_manifest(output_dir: str) -> Optional[List[str]]:
    path = os.path.join(output_dir, SESSION_MANIFEST_JSON)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    logs = payload.get("input_ate_logs")
    if not isinstance(logs, list) or not logs:
        return None
    return [str(item) for item in logs]
