"""Machine learning fault classifiers (Random Forest + XGBoost)."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any

from backend.classification.taxonomy_manager import TaxonomyManager

logger = logging.getLogger(__name__)

ML_MIN_TRAINING_SAMPLES = 4

FEATURE_NAMES = [
    "hard_bin",
    "soft_bin",
    "setup_slack_ps",
    "hold_slack_ps",
    "ir_drop_mv",
    "thermal_c",
    "transition_faults",
    "x",
    "y",
    "tester_bucket",
    "fail_type_bucket",
]


@dataclass
class MLClassification:
    fault_category: str
    confidence: float
    method: str = "ml"
    explanation: str = ""
    model_id: str = ""
    feature_importance: dict[str, float] = field(default_factory=dict)
    supporting_parameters: dict[str, Any] = field(default_factory=dict)
    failure_signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_category": self.fault_category,
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "explanation": self.explanation,
            "model_id": self.model_id,
            "feature_importance": self.feature_importance,
            "supporting_parameters": self.supporting_parameters,
            "failure_signature": self.failure_signature,
        }


class MLClassifier:
    """Train and apply sklearn / XGBoost models on rule-labeled samples."""

    def __init__(self, *, prefer_xgboost: bool = True) -> None:
        self.prefer_xgboost = prefer_xgboost
        self._bundle: dict[str, Any] | None = None

    @property
    def is_trained(self) -> bool:
        return self._bundle is not None

    def train(
        self,
        labeled: list[tuple[list[float], str, dict[str, Any]]],
        taxonomy: TaxonomyManager,
    ) -> bool:
        if len(labeled) < ML_MIN_TRAINING_SAMPLES:
            return False

        x_train = [row[0] for row in labeled]
        y_train = [taxonomy.normalize_category(row[1]) for row in labeled]
        if len(set(y_train)) < 2:
            return False

        bundle = _train_xgboost(x_train, y_train, taxonomy)
        if bundle is None and self.prefer_xgboost:
            bundle = _train_random_forest(x_train, y_train, taxonomy)
        elif bundle is None:
            bundle = _train_random_forest(x_train, y_train, taxonomy)

        if bundle is None:
            return False

        self._bundle = bundle
        return True

    def predict(
        self,
        features: list[float],
        ctx: dict[str, Any],
        taxonomy: TaxonomyManager,
    ) -> MLClassification | None:
        if self._bundle is None:
            return None

        model = self._bundle["model"]
        encoder = self._bundle["encoder"]
        proba = model.predict_proba([features])[0]
        best_idx = int(proba.argmax())
        confidence = float(proba[best_idx])
        fault_category = taxonomy.normalize_category(
            str(encoder.inverse_transform([best_idx])[0])
        )
        importance = _feature_importance(model, features)

        return MLClassification(
            fault_category=fault_category,
            confidence=confidence,
            method="ml",
            model_id=str(self._bundle.get("model_id", "ml_v1")),
            explanation=_ml_explanation(importance, confidence),
            feature_importance=importance,
            supporting_parameters={k: ctx.get(k) for k in FEATURE_NAMES if ctx.get(k)},
            failure_signature=_signature_from_ctx(ctx),
        )


def feature_vector(ctx: dict[str, Any]) -> list[float]:
    def num(key: str) -> float:
        try:
            return float(ctx.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0.0

    tester_bucket = int(
        hashlib.md5(str(ctx.get("tester_id", "")).encode()).hexdigest()[:4], 16
    ) % 100
    fail_type_bucket = int(
        hashlib.md5(str(ctx.get("FAIL_TYPE", "")).encode()).hexdigest()[:4], 16
    ) % 100

    return [
        num("hard_bin"),
        num("soft_bin"),
        num("SETUP_SLACK_PS"),
        num("HOLD_SLACK_PS"),
        num("IR_DROP_MV"),
        num("THERMAL_C"),
        num("TRANSITION_FAULTS"),
        num("x"),
        num("y"),
        float(tester_bucket),
        float(fail_type_bucket),
    ]


def _train_random_forest(
    x_train: list[list[float]],
    y_train: list[str],
    taxonomy: TaxonomyManager,
) -> dict[str, Any] | None:
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        logger.info("scikit-learn not installed; ML classification skipped")
        return None

    encoder = LabelEncoder()
    encoder.fit(taxonomy.categories + [taxonomy.unclassified])
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
        "model_id": "random_forest_v1",
        "training_samples": len(x_train),
    }


def _train_xgboost(
    x_train: list[list[float]],
    y_train: list[str],
    taxonomy: TaxonomyManager,
) -> dict[str, Any] | None:
    try:
        from sklearn.preprocessing import LabelEncoder
        from xgboost import XGBClassifier
    except ImportError:
        return None

    encoder = LabelEncoder()
    encoder.fit(taxonomy.categories + [taxonomy.unclassified])
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
        "model_id": "xgboost_v1",
        "training_samples": len(x_train),
    }


def _feature_importance(model: Any, features: list[float]) -> dict[str, float]:
    try:
        import numpy as np
        import shap

        explainer = shap.TreeExplainer(model)
        shap_output = explainer.shap_values(np.array([features]))
        if isinstance(shap_output, list):
            values = shap_output[0][0]
        else:
            values = shap_output[0]
        return {
            FEATURE_NAMES[i]: round(float(values[i]), 6)
            for i in range(min(len(FEATURE_NAMES), len(values)))
        }
    except Exception:
        importances = getattr(model, "feature_importances_", [])
        return {
            FEATURE_NAMES[i]: round(float(importances[i]), 6)
            for i in range(min(len(FEATURE_NAMES), len(importances)))
        }


def _ml_explanation(importance: dict[str, float], confidence: float) -> str:
    if not importance:
        return f"ML prediction confidence={confidence:.2f}"
    top = sorted(importance.items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]
    parts = ", ".join(f"{k}={v:+.4f}" for k, v in top)
    return f"ML prediction (confidence={confidence:.2f}); top features: {parts}"


def _signature_from_ctx(ctx: dict[str, Any]) -> str:
    return "|".join(
        str(ctx.get(k, ""))
        for k in ("FAIL_TYPE", "ROOT_CAUSE_HINT", "failing_test")
        if ctx.get(k)
    )
