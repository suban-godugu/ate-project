"""Train LightGBM removal classifier."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ml.features.schema import REMOVAL_FEATURE_COLUMNS


def _load() -> tuple[pd.DataFrame, pd.DataFrame]:
    data_dir = _PROJECT_ROOT / "ml" / "data"
    features = pd.read_csv(data_dir / "pattern_features.csv")
    labels = pd.read_csv(data_dir / "removal_labels.csv")
    return features, labels


def _xy(features: pd.DataFrame, labels: pd.DataFrame, split: str):
    cols = ["pattern_id"] + [c for c in REMOVAL_FEATURE_COLUMNS if c in features.columns]
    cols += [c for c in ["unique_fail_contribution", "split"] if c in features.columns and c not in cols]
    feat = features[cols].copy()
    # labels already carry split; prefer feature split for consistency
    label_cols = ["pattern_id", "label"]
    merged = labels[label_cols].merge(feat, on="pattern_id", how="inner")
    part = merged[merged["split"] == split]
    if part.empty:
        return None, None, part
    x = part[REMOVAL_FEATURE_COLUMNS].astype(float)
    y = part["label"].astype(int)
    return x, y, part


def train() -> dict:
    features, labels = _load()
    x_train, y_train, _ = _xy(features, labels, "train")
    x_val, y_val, _ = _xy(features, labels, "val")
    x_test, y_test, test_part = _xy(features, labels, "test")

    if x_train is None or len(x_train) == 0:
        raise RuntimeError("No training rows for removal classifier")

    # Fall back val/test to train holdout if lot split left them empty.
    if x_val is None or len(x_val) == 0:
        x_val, y_val = x_train, y_train
    if x_test is None or len(x_test) == 0:
        x_test, y_test, test_part = x_val, y_val, None

    train_set = lgb.Dataset(x_train, label=y_train, feature_name=REMOVAL_FEATURE_COLUMNS)
    val_set = lgb.Dataset(
        x_val, label=y_val, reference=train_set, feature_name=REMOVAL_FEATURE_COLUMNS
    )

    params = {
        "objective": "binary",
        "metric": ["auc", "binary_logloss"],
        "learning_rate": 0.05,
        "num_leaves": 31,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "min_data_in_leaf": 5,
        "verbosity": -1,
        "seed": 42,
    }

    booster = lgb.train(
        params,
        train_set,
        num_boost_round=300,
        valid_sets=[train_set, val_set],
        valid_names=["train", "val"],
        callbacks=[lgb.early_stopping(40, verbose=False)],
    )

    def _eval(name: str, x, y) -> dict:
        if x is None or len(x) == 0:
            return {f"{name}_skipped": True}
        proba = booster.predict(x)
        pred = (proba >= 0.5).astype(int)
        out = {
            f"{name}_n": int(len(y)),
            f"{name}_accuracy": round(float(accuracy_score(y, pred)), 6),
            f"{name}_precision": round(float(precision_score(y, pred, zero_division=0)), 6),
            f"{name}_recall": round(float(recall_score(y, pred, zero_division=0)), 6),
        }
        if len(np.unique(y)) > 1:
            out[f"{name}_auc"] = round(float(roc_auc_score(y, proba)), 6)
            out[f"{name}_avg_precision"] = round(
                float(average_precision_score(y, proba)), 6
            )
        # Safety: among predicted removes, how many have unique_fail > 0
        if test_part is not None and name == "test" and "unique_fail_contribution" in test_part.columns:
            unsafe = int(
                (
                    (pred == 1)
                    & (test_part["unique_fail_contribution"].astype(int) > 0)
                ).sum()
            )
            out["test_unsafe_remove_predictions"] = unsafe
        return out

    metrics = {}
    metrics.update(_eval("train", x_train, y_train))
    metrics.update(_eval("val", x_val, y_val))
    metrics.update(_eval("test", x_test, y_test))

    artifacts = _PROJECT_ROOT / "ml" / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    model_path = artifacts / "removal_classifier.txt"
    booster.save_model(str(model_path))

    meta = {
        "model": "removal_classifier",
        "algorithm": "lightgbm_binary",
        "feature_columns": REMOVAL_FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "best_iteration": int(booster.best_iteration or 0),
        "metrics": metrics,
        "model_path": str(model_path.relative_to(_PROJECT_ROOT)),
    }
    meta_path = artifacts / "removal_classifier_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    train()


if __name__ == "__main__":
    main()
