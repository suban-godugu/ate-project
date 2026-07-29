"""Machine learning root cause prediction (modular, replaceable models)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from backend.root_cause.feature_extraction import FEATURE_NAMES

logger = logging.getLogger(__name__)

ML_MIN_TRAINING_SAMPLES = 4


@dataclass
class MLPrediction:
    predicted_fault_type: str
    predicted_root_cause: str
    confidence: float
    method: str = "ml"
    model_id: str = ""
    explanation: str = ""
    feature_importance: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicted_fault_type": self.predicted_fault_type,
            "predicted_root_cause": self.predicted_root_cause,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "model_id": self.model_id,
            "explanation": self.explanation,
            "feature_importance": self.feature_importance,
        }


class MLPredictor:
    """Train and apply sklearn / XGBoost models for root cause prediction."""

    def __init__(self, *, prefer_xgboost: bool = True, min_samples: int = ML_MIN_TRAINING_SAMPLES) -> None:
        self.prefer_xgboost = prefer_xgboost
        self.min_samples = min_samples
        self._bundle: dict[str, Any] | None = None

    @property
    def is_trained(self) -> bool:
        return self._bundle is not None

    def train(self, labeled: list[tuple[list[float], str, dict[str, Any]]]) -> bool:
        if len(labeled) < self.min_samples:
            return False

        x_train = [row[0] for row in labeled]
        y_train = [row[1] for row in labeled]
        if len(set(y_train)) < 2:
            return False

        bundle = _train_xgboost(x_train, y_train)
        if bundle is None and self.prefer_xgboost:
            bundle = _train_random_forest(x_train, y_train)
        elif bundle is None:
            bundle = _train_random_forest(x_train, y_train)

        if bundle is None:
            return False

        self._bundle = bundle
        return True

    def predict(self, features: list[float], ctx: dict[str, Any]) -> MLPrediction | None:
        if self._bundle is None:
            return None

        model = self._bundle["model"]
        encoder = self._bundle["encoder"]
        proba = model.predict_proba([features])[0]
        best_idx = int(proba.argmax())
        confidence = float(proba[best_idx])
        label = str(encoder.inverse_transform([best_idx])[0])
        importance = _feature_importance(model, features)

        return MLPrediction(
            predicted_fault_type=label,
            predicted_root_cause=label,
            confidence=confidence,
            model_id=str(self._bundle.get("model_id", "ml_root_cause_v1")),
            explanation=_ml_explanation(importance, confidence, label),
            feature_importance=importance,
        )


def _train_random_forest(
    x_train: list[list[float]],
    y_train: list[str],
) -> dict[str, Any] | None:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        logger.info("scikit-learn not installed; ML root cause prediction skipped")
        return None

    encoder = LabelEncoder()
    encoder.fit(y_train)
    y_enc = encoder.transform(y_train)
    model = RandomForestClassifier(
        n_estimators=50,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(x_train, y_enc)
    return {
        "model": model,
        "encoder": encoder,
        "model_id": "random_forest_root_cause_v1",
        "training_samples": len(x_train),
    }


def _train_xgboost(
    x_train: list[list[float]],
    y_train: list[str],
) -> dict[str, Any] | None:
    try:
        from sklearn.preprocessing import LabelEncoder
        from xgboost import XGBClassifier
    except ImportError:
        return None

    encoder = LabelEncoder()
    encoder.fit(y_train)
    y_enc = encoder.transform(y_train)
    model = XGBClassifier(
        n_estimators=40,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        eval_metric="mlogloss",
    )
    model.fit(x_train, y_enc)
    return {
        "model": model,
        "encoder": encoder,
        "model_id": "xgboost_root_cause_v1",
        "training_samples": len(x_train),
    }


def _feature_importance(model: Any, features: list[float]) -> dict[str, float]:
    importances = getattr(model, "feature_importances_", [])
    return {
        FEATURE_NAMES[i]: round(float(importances[i]), 6)
        for i in range(min(len(FEATURE_NAMES), len(importances)))
    }


def _ml_explanation(importance: dict[str, float], confidence: float, label: str) -> str:
    if not importance:
        return f"ML predicts '{label}' with confidence={confidence:.2f}"
    top = sorted(importance.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
    parts = ", ".join(f"{k}={v:+.4f}" for k, v in top)
    return f"ML predicts '{label}' (confidence={confidence:.2f}); top features: {parts}"
