"""Load config/ml.yaml — ML off by default."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

import yaml

DEFAULT_ENABLED = False
DEFAULT_MODEL_FAMILY = "pa_ml_001"
DEFAULT_MODEL_VERSION = "v0.1.0"
DEFAULT_ALLOW_EXPERIMENTAL = True


@dataclass(frozen=True)
class ModelEntry:
    enabled: bool = True
    version: str = DEFAULT_MODEL_VERSION


DEFAULT_MODELS: Dict[str, ModelEntry] = {
    "pa_ml_001": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_001_lot": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_002": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_002_lot": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_003": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_003_lot": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_004": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
    "pa_ml_004_lot": ModelEntry(enabled=True, version=DEFAULT_MODEL_VERSION),
}


@dataclass(frozen=True)
class MLConfig:
    enabled: bool = DEFAULT_ENABLED
    model_family: str = DEFAULT_MODEL_FAMILY
    model_version: str = DEFAULT_MODEL_VERSION
    allow_experimental: bool = DEFAULT_ALLOW_EXPERIMENTAL
    models_root: str = "models"
    models: Dict[str, ModelEntry] = field(default_factory=dict)


def resolve_ml_config_path(workspace_dir: str, config_path: Optional[str] = None) -> str:
    if config_path:
        return config_path
    candidate = os.path.join(workspace_dir, "config", "ml.yaml")
    if os.path.exists(candidate):
        return candidate
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config",
        "ml.yaml",
    )


def _parse_models(section: Mapping[str, object]) -> Dict[str, ModelEntry]:
    raw = section.get("models")
    if not isinstance(raw, Mapping):
        legacy_family = str(section.get("model_family") or DEFAULT_MODEL_FAMILY)
        legacy_version = str(section.get("model_version") or DEFAULT_MODEL_VERSION)
        models = dict(DEFAULT_MODELS)
        models[legacy_family] = ModelEntry(enabled=True, version=legacy_version)
        return models

    models: Dict[str, ModelEntry] = {}
    for family, payload in raw.items():
        if isinstance(payload, Mapping):
            models[str(family)] = ModelEntry(
                enabled=bool(payload.get("enabled", True)),
                version=str(payload.get("version") or DEFAULT_MODEL_VERSION),
            )
        else:
            models[str(family)] = ModelEntry(
                enabled=bool(payload),
                version=DEFAULT_MODEL_VERSION,
            )
    return models


def load_ml_config(config_path: str) -> MLConfig:
    if not os.path.exists(config_path):
        return MLConfig(models=dict(DEFAULT_MODELS))
    with open(config_path, "r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    section = payload.get("ml") or payload
    models = _parse_models(section if isinstance(section, Mapping) else {})
    return MLConfig(
        enabled=bool(section.get("enabled", DEFAULT_ENABLED)),
        model_family=str(section.get("model_family") or DEFAULT_MODEL_FAMILY),
        model_version=str(section.get("model_version") or DEFAULT_MODEL_VERSION),
        allow_experimental=bool(
            section.get("allow_experimental", DEFAULT_ALLOW_EXPERIMENTAL)
        ),
        models_root=str(section.get("models_root") or "models"),
        models=models,
    )


def is_model_enabled(config: MLConfig, model_family: str) -> bool:
    if not config.enabled:
        return False
    entry = config.models.get(model_family)
    if entry is not None:
        return entry.enabled
    if model_family == config.model_family:
        return True
    return False


def model_version_for(config: MLConfig, model_family: str) -> str:
    entry = config.models.get(model_family)
    if entry is not None:
        return entry.version
    if model_family == config.model_family:
        return config.model_version
    return DEFAULT_MODEL_VERSION
