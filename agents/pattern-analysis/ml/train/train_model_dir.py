"""Shared helpers for resolving PA-ML model output directories.

Goal: make training write into the same directory layout inference uses,
based on config/ml.yaml `ml.models_root`.
"""

from __future__ import annotations

import os
from typing import Optional

from ml.config import load_ml_config, resolve_ml_config_path


def resolve_training_model_dir(
    *,
    workspace_dir: str,
    model_family: str,
    model_version: str,
    config_path: Optional[str] = None,
) -> str:
    """Return absolute model_dir for training outputs."""
    cfg_path = resolve_ml_config_path(workspace_dir, config_path)
    config = load_ml_config(cfg_path)

    root = str(getattr(config, "models_root", "models") or "models")
    if not os.path.isabs(root):
        root = os.path.join(workspace_dir, root)
    return os.path.join(root, model_family, model_version)

