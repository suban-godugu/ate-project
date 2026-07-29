"""Health and readiness probes for orchestrators."""

from __future__ import annotations

import os
from typing import Any, Dict

from src.config import get_settings
from src.data.input_registry import input_inventory
from src.data.paths import COMPILED_DATASET_PATH, MODEL_WEIGHTS_PATH


def health_payload() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "scan-debug-recommendation-agent",
        "env": settings.app_env,
    }


def readiness_payload(training_in_progress: bool = False) -> Dict[str, Any]:
    settings = get_settings()
    inventory = input_inventory()
    dataset_ok = os.path.isfile(COMPILED_DATASET_PATH)
    weights_ok = os.path.isfile(MODEL_WEIGHTS_PATH)
    inputs_ok = bool(inventory.get("ready"))
    ready = (
        inputs_ok
        and dataset_ok
        and (weights_ok or not settings.is_production)
        and not training_in_progress
    )
    return {
        "status": "ready" if ready else "not_ready",
        "checks": {
            "inputs": inputs_ok,
            "missing_inputs": inventory.get("missing", []),
            "compiled_dataset": dataset_ok,
            "model_weights": weights_ok,
            "training_in_progress": training_in_progress,
        },
    }
