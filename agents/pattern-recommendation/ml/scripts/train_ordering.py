"""Train LightGBM LambdaMART ordering ranker."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from ml.features.schema import ORDERING_FEATURE_COLUMNS


def _ndcg_at_k(relevance: np.ndarray, scores: np.ndarray, k: int = 50) -> float:
    order = np.argsort(-scores)
    rel = relevance[order][:k]
    if rel.size == 0:
        return 0.0
    discounts = 1.0 / np.log2(np.arange(2, rel.size + 2))
    dcg = float(np.sum((2**rel - 1.0) * discounts))
    ideal = np.sort(relevance)[::-1][:k]
    idcg = float(np.sum((2**ideal - 1.0) * (1.0 / np.log2(np.arange(2, ideal.size + 2)))))
    return float(dcg / idcg) if idcg > 0 else 0.0


def _early_fail_mass(failed_logs: np.ndarray, scores: np.ndarray, k: int = 50) -> float:
    order = np.argsort(-scores)
    top = failed_logs[order][:k]
    total = float(failed_logs.sum()) or 1.0
    return float(top.sum() / total)


def _prepare_split(features: pd.DataFrame, labels: pd.DataFrame, split: str):
    merged = labels.merge(features, on="pattern_id", how="inner", suffixes=("", "_f"))
    # Prefer label split if present; else feature split
    split_col = "split" if "split" in merged.columns else "split_f"
    part = merged[merged[split_col] == split].copy()
    if part.empty:
        return None
    part = part.sort_values(["group_id", "pattern_id"])
    return part


def train() -> dict:
    data_dir = _PROJECT_ROOT / "ml" / "data"
    features = pd.read_csv(data_dir / "pattern_features.csv")
    labels = pd.read_csv(data_dir / "ordering_relevance.csv")

    train_df = _prepare_split(features, labels, "train")
    val_df = _prepare_split(features, labels, "val")
    test_df = _prepare_split(features, labels, "test")

    if train_df is None or train_df.empty:
        raise RuntimeError("No training rows for ordering ranker")
    if val_df is None or val_df.empty:
        val_df = train_df
    if test_df is None or test_df.empty:
        test_df = val_df

    def _dataset(frame: pd.DataFrame) -> lgb.Dataset:
        x = frame[ORDERING_FEATURE_COLUMNS].astype(float)
        y = frame["relevance"].astype(int)
        group = frame.groupby("group_id", sort=False).size().tolist()
        return lgb.Dataset(
            x,
            label=y,
            group=group,
            feature_name=ORDERING_FEATURE_COLUMNS,
            free_raw_data=False,
        )

    train_set = _dataset(train_df)
    val_set = _dataset(val_df)

    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "eval_at": [10, 50],
        "learning_rate": 0.05,
        "num_leaves": 31,
        "min_data_in_leaf": 5,
        "feature_fraction": 0.9,
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

    def _eval(name: str, frame: pd.DataFrame) -> dict:
        x = frame[ORDERING_FEATURE_COLUMNS].astype(float)
        scores = booster.predict(x)
        relevance = frame["relevance"].to_numpy(dtype=float)
        failed = frame["failed_log_count"].to_numpy(dtype=float)
        heur = frame["heuristic_order_score"].to_numpy(dtype=float)
        return {
            f"{name}_n": int(len(frame)),
            f"{name}_ndcg50_ml": round(_ndcg_at_k(relevance, scores, 50), 6),
            f"{name}_ndcg50_heuristic": round(_ndcg_at_k(relevance, heur, 50), 6),
            f"{name}_early_fail_mass_top50_ml": round(
                _early_fail_mass(failed, scores, 50), 6
            ),
            f"{name}_early_fail_mass_top50_heuristic": round(
                _early_fail_mass(failed, heur, 50), 6
            ),
        }

    metrics = {}
    metrics.update(_eval("train", train_df))
    metrics.update(_eval("val", val_df))
    metrics.update(_eval("test", test_df))

    artifacts = _PROJECT_ROOT / "ml" / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    model_path = artifacts / "ordering_ranker.txt"
    booster.save_model(str(model_path))

    meta = {
        "model": "ordering_ranker",
        "algorithm": "lightgbm_lambdarank",
        "feature_columns": ORDERING_FEATURE_COLUMNS,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "best_iteration": int(booster.best_iteration or 0),
        "metrics": metrics,
        "model_path": str(model_path.relative_to(_PROJECT_ROOT)),
    }
    meta_path = artifacts / "ordering_ranker_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return meta


def main() -> None:
    train()


if __name__ == "__main__":
    main()
