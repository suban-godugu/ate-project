"""Shared PA-ML inference helpers."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Mapping, Sequence

import numpy as np


def write_predictions_json(path: str, payload: Mapping[str, Any]) -> None:
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
    os.replace(temporary, path)


def coefficients_from_model(model: Any) -> tuple[list[float], float]:
    clf = model
    if hasattr(model, "named_steps") and "clf" in model.named_steps:
        clf = model.named_steps["clf"]
    coef = getattr(clf, "coef_", None)
    intercept = getattr(clf, "intercept_", None)
    if coef is None:
        return [], 0.0
    flat = np.asarray(coef).reshape(-1)
    intercept_value = (
        float(np.asarray(intercept).reshape(-1)[0]) if intercept is not None else 0.0
    )
    return [float(value) for value in flat], intercept_value


def scaled_feature_values(
    model: Any,
    feature_names: Sequence[str],
    feature_values: Mapping[str, float],
) -> Dict[str, float]:
    raw = [float(feature_values.get(name) or 0.0) for name in feature_names]
    if hasattr(model, "named_steps") and "scaler" in model.named_steps:
        scaled = model.named_steps["scaler"].transform([raw])[0]
        return {
            name: float(scaled[index]) for index, name in enumerate(feature_names)
        }
    return {name: float(feature_values.get(name) or 0.0) for name in feature_names}


def predict_scores(model: Any, matrix: Sequence[Sequence[float]]) -> np.ndarray:
    x = np.asarray(matrix, dtype=np.float64)
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x)[:, 1]
    decision = model.decision_function(x)
    return 1.0 / (1.0 + np.exp(-np.asarray(decision, dtype=np.float64)))
