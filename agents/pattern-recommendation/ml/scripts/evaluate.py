"""Evaluate trained ML artifacts vs heuristic baselines."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import lightgbm as lgb
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ml.features.schema import ORDERING_FEATURE_COLUMNS, REMOVAL_FEATURE_COLUMNS
from ml.scripts.train_ordering import _early_fail_mass, _ndcg_at_k


def _split_mask(frame: pd.DataFrame, split: str) -> pd.Series:
    if "split" in frame.columns:
        return frame["split"] == split
    if "split_x" in frame.columns:
        return frame["split_x"] == split
    if "split_y" in frame.columns:
        return frame["split_y"] == split
    return pd.Series([True] * len(frame), index=frame.index)


def main() -> None:
    data_dir = _PROJECT_ROOT / "ml" / "data"
    artifacts = _PROJECT_ROOT / "ml" / "artifacts"
    features = pd.read_csv(data_dir / "pattern_features.csv")
    removal_labels = pd.read_csv(data_dir / "removal_labels.csv")
    ordering_labels = pd.read_csv(data_dir / "ordering_relevance.csv")

    report: dict = {"splits": features["split"].value_counts().to_dict()}

    removal_model = artifacts / "removal_classifier.txt"
    if removal_model.exists():
        booster = lgb.Booster(model_file=str(removal_model))
        merged = removal_labels[["pattern_id", "label", "unique_fail_contribution"]].merge(
            features,
            on="pattern_id",
            how="inner",
            suffixes=("_label", ""),
        )
        test = merged[merged["split"] == "test"]
        if test.empty:
            test = merged
        x = test[REMOVAL_FEATURE_COLUMNS].astype(float)
        y = test["label"].astype(int).to_numpy()
        proba = booster.predict(x)
        pred = (proba >= 0.5).astype(int)
        unique = test["unique_fail_contribution"].astype(int).to_numpy()
        safe_pred = pred.copy()
        safe_pred[unique > 0] = 0
        tp = int(((safe_pred == 1) & (y == 1)).sum())
        fp = int(((safe_pred == 1) & (y == 0)).sum())
        report["removal"] = {
            "n": int(len(test)),
            "precision_safe": round(tp / (tp + fp), 6) if (tp + fp) else 0.0,
            "unsafe_before_filter": int(((pred == 1) & (unique > 0)).sum()),
            "unsafe_after_filter": int(((safe_pred == 1) & (unique > 0)).sum()),
        }

    ordering_model = artifacts / "ordering_ranker.txt"
    if ordering_model.exists():
        booster = lgb.Booster(model_file=str(ordering_model))
        label_keep = ["pattern_id", "relevance", "group_id"]
        merged = ordering_labels[label_keep].merge(
            features,
            on="pattern_id",
            how="inner",
        )
        test = merged[merged["split"] == "test"]
        if test.empty:
            test = merged
        x = test[ORDERING_FEATURE_COLUMNS].astype(float)
        scores = booster.predict(x)
        relevance = test["relevance"].to_numpy(dtype=float)
        failed = test["failed_log_count"].to_numpy(dtype=float)
        heur = test["heuristic_order_score"].to_numpy(dtype=float)
        report["ordering"] = {
            "n": int(len(test)),
            "ndcg50_ml": round(_ndcg_at_k(relevance, scores, 50), 6),
            "ndcg50_heuristic": round(_ndcg_at_k(relevance, heur, 50), 6),
            "early_fail_mass_top50_ml": round(_early_fail_mass(failed, scores, 50), 6),
            "early_fail_mass_top50_heuristic": round(
                _early_fail_mass(failed, heur, 50), 6
            ),
        }

    out = artifacts / "evaluation_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
