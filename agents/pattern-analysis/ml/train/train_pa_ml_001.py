"""Offline PA-ML-001 training — never import from session request path."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Sequence, Tuple

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Allow `python -m ml.train.train_pa_ml_001` from repo root.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ml.contracts import FEATURE_SCHEMA_VERSION, GENERATED_BY, MODEL_FAMILY
from ml.feature_builder_001 import (
    build_feature_rows_from_output_dir,
    build_feature_schema,
    matrix_from_rows,
)
from ml.train.train_model_dir import resolve_training_model_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _labels_and_groups(bundle: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
    labels: List[int] = []
    groups: List[str] = []
    for row in bundle.get("rows") or []:
        labels.append(int(row["label"]))
        groups.append(str(row.get("source_lot") or "Ungrouped"))
    return np.asarray(labels, dtype=np.int64), np.asarray(groups)


def _safe_metric(fn, y_true, y_score_or_pred, **kwargs):
    try:
        value = float(fn(y_true, y_score_or_pred, **kwargs))
    except Exception:
        return None
    if np.isnan(value) or np.isinf(value):
        return None
    return value


def _evaluate(y_true: np.ndarray, y_score: np.ndarray) -> Dict[str, Any]:
    y_pred = (y_score >= 0.5).astype(int)
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    positives = int((y_true == 1).sum())
    fnr = (fn / positives) if positives else None
    return {
        "precision": _safe_metric(precision_score, y_true, y_pred, zero_division=0),
        "recall": _safe_metric(recall_score, y_true, y_pred, zero_division=0),
        "f1": _safe_metric(f1_score, y_true, y_pred, zero_division=0),
        "roc_auc": _safe_metric(roc_auc_score, y_true, y_score),
        "pr_auc": _safe_metric(average_precision_score, y_true, y_score),
        "brier": _safe_metric(brier_score_loss, y_true, y_score),
        "fnr": fnr,
        "positive_count": positives,
        "negative_count": int((y_true == 0).sum()),
    }


def train_pa_ml_001(
    *,
    output_dir: str,
    workspace_dir: str,
    model_version: str = "v0.1.0",
    status: str = "experimental",
) -> str:
    bundle = build_feature_rows_from_output_dir(output_dir, include_labels=True)
    matrix, feature_names, _unit_ids = matrix_from_rows(bundle)
    if not matrix:
        raise RuntimeError("No labeled feature rows available for training.")
    x = np.asarray(matrix, dtype=np.float64)
    y, groups = _labels_and_groups(bundle)
    if len(set(y.tolist())) < 2:
        raise RuntimeError("Need both PASS and FAIL labels to train PA-ML-001.")

    unique_groups = sorted(set(groups.tolist()))
    n_splits = min(5, len(unique_groups))
    metrics_folds: List[Dict[str, Any]] = []
    if n_splits >= 2:
        gkf = GroupKFold(n_splits=n_splits)
        for fold_index, (train_idx, test_idx) in enumerate(
            gkf.split(x, y, groups), start=1
        ):
            pipe = Pipeline(
                steps=[
                    ("scaler", StandardScaler()),
                    (
                        "clf",
                        LogisticRegression(
                            max_iter=2000,
                            class_weight="balanced",
                            solver="lbfgs",
                        ),
                    ),
                ]
            )
            if len(set(y[train_idx].tolist())) < 2:
                continue
            pipe.fit(x[train_idx], y[train_idx])
            scores = pipe.predict_proba(x[test_idx])[:, 1]
            fold_metrics = _evaluate(y[test_idx], scores)
            fold_metrics["fold"] = fold_index
            metrics_folds.append(fold_metrics)

    final = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    solver="lbfgs",
                ),
            ),
        ]
    )
    final.fit(x, y)
    train_scores = final.predict_proba(x)[:, 1]
    train_metrics = _evaluate(y, train_scores)

    model_dir = resolve_training_model_dir(
        workspace_dir=workspace_dir,
        model_family=MODEL_FAMILY,
        model_version=model_version,
    )
    os.makedirs(model_dir, exist_ok=True)
    joblib.dump(final, os.path.join(model_dir, "model.joblib"))

    dim = int(bundle.get("embedding_dimension") or 128)
    schema = build_feature_schema(dim)
    schema["feature_names"] = feature_names
    with open(
        os.path.join(model_dir, "feature_schema.json"), "w", encoding="utf-8"
    ) as handle:
        json.dump(schema, handle, indent=2, sort_keys=True)

    card = {
        "model_family": MODEL_FAMILY,
        "model_version": model_version,
        "generated_by": GENERATED_BY,
        "status": status,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "training_timestamp": _utc_now(),
        "training_session_hash": bundle.get("session_hash"),
        "training_row_count": int(len(y)),
        "training_lots": unique_groups,
        "algorithm": "LogisticRegression",
        "hyperparameters": {
            "max_iter": 2000,
            "class_weight": "balanced",
            "solver": "lbfgs",
            "scaler": "StandardScaler",
        },
        "metrics": {
            "train": train_metrics,
            "group_kfold": metrics_folds,
        },
        "inference_latency_budget_ms": 5000,
        "notes": [
            "Experimental model trained offline from Analysis Session artifacts.",
            "Label = latest_result FAIL=1; forbidden outcome aggregates excluded from features.",
        ],
    }
    with open(os.path.join(model_dir, "model_card.json"), "w", encoding="utf-8") as handle:
        json.dump(card, handle, indent=2, sort_keys=True, allow_nan=False)
    return model_dir


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train PA-ML-001 Failure Risk offline")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory containing PA-Analysis-Session_*.json artifacts",
    )
    parser.add_argument(
        "--workspace-dir",
        default=None,
        help="Repo/workspace root for models/ (default: parent of output-dir or cwd)",
    )
    parser.add_argument("--model-version", default="v0.1.0")
    parser.add_argument(
        "--status",
        default="experimental",
        choices=("experimental", "production"),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    output_dir = os.path.abspath(args.output_dir)
    workspace_dir = os.path.abspath(
        args.workspace_dir or os.path.dirname(output_dir) or os.getcwd()
    )
    model_dir = train_pa_ml_001(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        model_version=args.model_version,
        status=args.status,
    )
    print(f"Wrote model to {model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
