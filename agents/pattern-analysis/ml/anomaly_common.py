"""Shared PA-ML-002 anomaly train/inference helpers."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def feature_training_stats(
    matrix: np.ndarray, feature_names: Sequence[str]
) -> Dict[str, Dict[str, float]]:
    stats: Dict[str, Dict[str, float]] = {}
    for index, name in enumerate(feature_names):
        column = matrix[:, index]
        stats[str(name)] = {
            "mean": float(np.mean(column)),
            "std": float(float(np.std(column)) or 1.0),
        }
    return stats


def build_anomaly_pipeline(*, contamination: float = 0.01) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                IsolationForest(
                    n_estimators=200,
                    contamination=contamination,
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )


def raw_anomaly_scores(model: Any, matrix: np.ndarray) -> np.ndarray:
    clf = model
    if hasattr(model, "named_steps") and "clf" in model.named_steps:
        clf = model.named_steps["clf"]
    # Lower score_samples => more anomalous; flip so higher = more anomalous.
    return -np.asarray(clf.score_samples(matrix), dtype=np.float64)


def calibrate_scores(
    raw_scores: np.ndarray,
    calibration: Mapping[str, Any],
) -> np.ndarray:
    low = float(calibration.get("raw_min", np.min(raw_scores)))
    high = float(calibration.get("raw_max", np.max(raw_scores)))
    if high <= low:
        return np.full(raw_scores.shape, 0.5, dtype=np.float64)
    scaled = (raw_scores - low) / (high - low)
    return np.clip(scaled, 0.0, 1.0)


def scaled_feature_row(
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


def score_calibration_from_raw(raw_scores: np.ndarray) -> Dict[str, float]:
    return {
        "raw_min": float(np.min(raw_scores)),
        "raw_max": float(np.max(raw_scores)),
    }


def write_model_bundle(
    *,
    model_dir: str,
    pipeline: Pipeline,
    schema: Dict[str, Any],
    card: Dict[str, Any],
) -> None:
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(pipeline, os.path.join(model_dir, "model.joblib"))
    with open(
        os.path.join(model_dir, "feature_schema.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(schema, handle, indent=2, sort_keys=True)
    with open(os.path.join(model_dir, "model_card.json"), "w", encoding="utf-8") as handle:
        json.dump(card, handle, indent=2, sort_keys=True, allow_nan=False)


def anomaly_flags(model: Any, matrix: np.ndarray) -> np.ndarray:
    clf = model
    if hasattr(model, "named_steps") and "clf" in model.named_steps:
        clf = model.named_steps["clf"]
    return (clf.predict(matrix) == -1).astype(np.int64)
