"""Resolve immutable PA-ML model directories."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

from ml.config import MLConfig, model_version_for


def model_dir_for(
    workspace_dir: str,
    config: MLConfig,
    model_family: str,
) -> str:
    root = config.models_root
    if not os.path.isabs(root):
        root = os.path.join(workspace_dir, root)
    version = model_version_for(config, model_family)
    return os.path.join(root, model_family, version)


def load_model_card(model_dir: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(model_dir, "model_card.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def load_feature_schema(model_dir: str) -> Optional[Dict[str, Any]]:
    path = os.path.join(model_dir, "feature_schema.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def model_joblib_path(model_dir: str) -> str:
    return os.path.join(model_dir, "model.joblib")


def recommendation_policy_path(model_dir: str) -> str:
    from ml.contracts_004 import RECOMMENDATION_POLICY_JSON

    return os.path.join(model_dir, RECOMMENDATION_POLICY_JSON)


def load_recommendation_policy(model_dir: str) -> Optional[Dict[str, Any]]:
    path = recommendation_policy_path(model_dir)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else None


def resolve_usable_policy(
    workspace_dir: str,
    config: MLConfig,
    model_family: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return (model_dir, model_card, recommendation_policy) or (None, None, None)."""
    model_dir = model_dir_for(workspace_dir, config, model_family)
    card = load_model_card(model_dir)
    if not is_model_usable(card, allow_experimental=config.allow_experimental):
        return None, None, None
    policy = load_recommendation_policy(model_dir)
    if policy is None:
        return None, None, None
    return model_dir, card, policy


def is_model_usable(
    model_card: Optional[Dict[str, Any]],
    *,
    allow_experimental: bool,
) -> bool:
    if not isinstance(model_card, dict):
        return False
    status = str(model_card.get("status") or "").lower()
    if status == "production":
        return True
    if status == "experimental" and allow_experimental:
        return True
    return False


def resolve_usable_model(
    workspace_dir: str,
    config: MLConfig,
    model_family: str,
) -> Tuple[Optional[str], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return (model_dir, model_card, feature_schema) or (None, None, None)."""
    model_dir = model_dir_for(workspace_dir, config, model_family)
    card = load_model_card(model_dir)
    if not is_model_usable(card, allow_experimental=config.allow_experimental):
        return None, None, None
    if not os.path.exists(model_joblib_path(model_dir)):
        return None, None, None
    schema = load_feature_schema(model_dir)
    if schema is None:
        return None, None, None
    return model_dir, card, schema
