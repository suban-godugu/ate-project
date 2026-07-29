"""Model training pipeline for labelled failure datasets."""

from __future__ import annotations

import json
import logging
import pickle
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class ModelTrainingPipeline:
    """
    Train Random Forest / XGBoost / Gradient Boosting / LightGBM when labelled
    data is available. Compare models, persist the winner, and support retrain.
    """

    def __init__(
        self,
        *,
        model_store_dir: Path | str,
        test_size: float = 0.2,
        validation_size: float = 0.1,
        random_state: int = 42,
        min_labelled_samples: int = 20,
    ) -> None:
        self.model_store_dir = Path(model_store_dir)
        self.model_store_dir.mkdir(parents=True, exist_ok=True)
        self.test_size = test_size
        self.validation_size = validation_size
        self.random_state = random_state
        self.min_labelled_samples = min_labelled_samples

    def train_from_labelled_rows(
        self,
        rows: list[dict[str, Any]],
        *,
        feature_keys: list[str] | None = None,
        label_key: str = "label",
    ) -> dict[str, Any]:
        start = time.perf_counter()
        if len(rows) < self.min_labelled_samples:
            return {
                "trained": False,
                "reason": (
                    f"Insufficient labelled samples ({len(rows)} < {self.min_labelled_samples})."
                ),
                "sample_count": len(rows),
            }

        feature_keys = feature_keys or _infer_feature_keys(rows, label_key)
        x, y, used_keys = _build_matrices(rows, feature_keys, label_key)
        if len(set(y)) < 2:
            return {
                "trained": False,
                "reason": "Need at least two distinct labels for supervised training.",
                "sample_count": len(rows),
                "labels": sorted(set(y)),
            }

        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder

        encoder = LabelEncoder()
        y_enc = encoder.fit_transform(y)

        # Small-sample path: single holdout split when not enough for 3-way split
        if len(rows) < 10:
            x_train, x_test, y_train, y_test = train_test_split(
                x,
                y_enc,
                test_size=max(1, int(len(rows) * self.test_size)) / len(rows)
                if len(rows) > 2
                else 0.5,
                random_state=self.random_state,
                stratify=y_enc if _can_stratify(y_enc) else None,
            )
            x_val, y_val = x_test, y_test
        else:
            x_train, x_temp, y_train, y_temp = train_test_split(
                x,
                y_enc,
                test_size=self.test_size + self.validation_size,
                random_state=self.random_state,
                stratify=y_enc if _can_stratify(y_enc) else None,
            )
            if len(x_temp) < 2:
                x_val, y_val = x_temp, y_temp
                x_test, y_test = x_temp, y_temp
            else:
                relative_val = self.validation_size / (
                    self.test_size + self.validation_size
                )
                x_val, x_test, y_val, y_test = train_test_split(
                    x_temp,
                    y_temp,
                    test_size=max(0.2, 1.0 - relative_val),
                    random_state=self.random_state,
                    stratify=y_temp if _can_stratify(y_temp) else None,
                )

        candidates = _build_candidate_models(self.random_state)
        comparisons: list[dict[str, Any]] = []
        best_name = ""
        best_model = None
        best_score = -1.0

        for name, model in candidates.items():
            try:
                model.fit(x_train, y_train)
                val_score = float(model.score(x_val, y_val))
                test_score = float(model.score(x_test, y_test))
                comparisons.append(
                    {
                        "model": name,
                        "validation_accuracy": round(val_score, 6),
                        "test_accuracy": round(test_score, 6),
                    }
                )
                if val_score > best_score:
                    best_score = val_score
                    best_name = name
                    best_model = model
            except Exception as exc:
                logger.warning("Model %s failed: %s", name, exc)
                comparisons.append({"model": name, "error": str(exc)})

        if best_model is None:
            return {
                "trained": False,
                "reason": "All candidate models failed to train.",
                "comparisons": comparisons,
            }

        version = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        artifact_dir = self.model_store_dir / f"eval_model_{version}"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        model_path = artifact_dir / "model.pkl"
        meta_path = artifact_dir / "metadata.json"

        with model_path.open("wb") as handle:
            pickle.dump(
                {
                    "model": best_model,
                    "encoder": encoder,
                    "feature_keys": used_keys,
                    "model_name": best_name,
                },
                handle,
            )

        metadata = {
            "trained": True,
            "model_name": best_name,
            "model_version": version,
            "model_path": str(model_path),
            "feature_keys": used_keys,
            "labels": list(encoder.classes_),
            "sample_count": len(rows),
            "train_count": len(x_train),
            "validation_count": len(x_val),
            "test_count": len(x_test),
            "validation_accuracy": round(best_score, 6),
            "comparisons": comparisons,
            "duration_ms": round((time.perf_counter() - start) * 1000, 3),
            "retrain_supported": True,
        }
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        latest = self.model_store_dir / "latest.json"
        latest.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return metadata

    def load_latest(self) -> dict[str, Any] | None:
        latest = self.model_store_dir / "latest.json"
        if not latest.exists():
            return None
        return json.loads(latest.read_text(encoding="utf-8"))


def extract_labels_from_die_logs(die_logs: list[Any]) -> list[dict[str, Any]]:
    """Build labelled feature rows from Verilumen fail_die/good_die headers."""
    rows: list[dict[str, Any]] = []
    for die in die_logs:
        header = getattr(die, "header_fields", {}) or {}
        source = str(getattr(die, "source_path", "")).lower()
        label = (
            header.get("DIE_LABEL")
            or header.get("DEFECT_TYPE")
            or ("FAIL" if "fail_die" in source else "PASS" if "good_die" in source else "")
        )
        if not label:
            continue
        rows.append(
            {
                "label": str(label),
                "is_failing": 1.0 if getattr(die, "is_failing_die", False) else 0.0,
                "failing_pattern_count": float(len(getattr(die, "failing_patterns", []) or [])),
                "execution_count": float(getattr(die, "execution_count", 0) or 0),
                "die_x": float(header.get("DIE_X") or 0),
                "die_y": float(header.get("DIE_Y") or 0),
                "lot_bucket": _bucket(str(getattr(die, "lot_id", ""))),
            }
        )
    return rows


def extract_labels_from_csv(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_csv(path)
    label_col = _find_label_column(frame.columns)
    if label_col is None:
        return []
    numeric = frame.select_dtypes(include=["number"]).copy()
    numeric["label"] = frame[label_col].astype(str)
    numeric = numeric.dropna()
    return numeric.to_dict(orient="records")


def _find_label_column(columns: Any) -> str | None:
    preferred = (
        "label",
        "DIE_LABEL",
        "die_label",
        "DEFECT_TYPE",
        "defect_type",
        "fault_type",
        "fault_category",
        "target",
        "y",
    )
    lower_map = {str(c).lower(): str(c) for c in columns}
    for name in preferred:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def _infer_feature_keys(rows: list[dict[str, Any]], label_key: str) -> list[str]:
    keys: list[str] = []
    for key, value in rows[0].items():
        if key == label_key:
            continue
        if isinstance(value, (int, float)):
            keys.append(key)
    return keys


def _build_matrices(
    rows: list[dict[str, Any]],
    feature_keys: list[str],
    label_key: str,
) -> tuple[np.ndarray, list[str], list[str]]:
    used = [k for k in feature_keys if k in rows[0]]
    x = np.array([[float(row.get(k, 0) or 0) for k in used] for row in rows], dtype=float)
    y = [str(row[label_key]) for row in rows]
    return x, y, used


def _can_stratify(y: np.ndarray) -> bool:
    _, counts = np.unique(y, return_counts=True)
    return bool(counts.min() >= 2)


def _bucket(value: str) -> float:
    return float(abs(hash(value)) % 100)


def _build_candidate_models(random_state: int) -> dict[str, Any]:
    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

    models: dict[str, Any] = {
        "random_forest": RandomForestClassifier(
            n_estimators=80,
            max_depth=10,
            random_state=random_state,
            class_weight="balanced",
        ),
        "gradient_boosting": GradientBoostingClassifier(random_state=random_state),
    }
    try:
        from xgboost import XGBClassifier

        models["xgboost"] = XGBClassifier(
            n_estimators=80,
            max_depth=6,
            learning_rate=0.1,
            random_state=random_state,
            eval_metric="mlogloss",
        )
    except ImportError:
        logger.info("xgboost unavailable; skipping")

    try:
        from lightgbm import LGBMClassifier

        models["lightgbm"] = LGBMClassifier(random_state=random_state)
    except ImportError:
        logger.info("lightgbm unavailable; skipping")

    return models
