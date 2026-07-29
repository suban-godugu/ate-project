"""Offline PA-ML-003-LOT training — never import from session request path."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Sequence

import numpy as np

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ml.contracts_003 import (
    DEFAULT_INVESTIGATION_THRESHOLD,
    FEATURE_SCHEMA_VERSION_003_LOT,
    GENERATED_BY_003_LOT,
    MODEL_FAMILY_003_LOT,
)
from ml.feature_builder_001_lot import (
    build_feature_schema_lot,
    build_lot_feature_rows_from_output_dir,
    matrix_from_rows,
)
from ml.root_cause_common import (
    _utc_now_iso,
    build_root_cause_pipeline,
    evaluate_classifier,
    labels_and_groups,
    write_model_bundle,
)
from ml.train.train_model_dir import resolve_training_model_dir
from sklearn.model_selection import GroupKFold


def train_pa_ml_003_lot(
    *,
    output_dir: str,
    workspace_dir: str,
    model_version: str = "v0.1.0",
    status: str = "experimental",
    investigation_threshold: float = DEFAULT_INVESTIGATION_THRESHOLD,
) -> str:
    bundle = build_lot_feature_rows_from_output_dir(output_dir, include_labels=True)
    matrix, feature_names, _unit_ids = matrix_from_rows(bundle)
    if not matrix:
        raise RuntimeError("No labeled LOT feature rows available for PA-ML-003 training.")
    x = np.asarray(matrix, dtype=np.float64)
    y, groups = labels_and_groups(bundle)
    if len(set(y.tolist())) < 2:
        raise RuntimeError("Need both PASS and FAIL labels to train PA-ML-003-LOT.")

    unique_groups = sorted(set(groups.tolist()))
    n_splits = min(5, len(unique_groups))
    metrics_folds: List[Dict[str, Any]] = []
    if n_splits >= 2:
        gkf = GroupKFold(n_splits=n_splits)
        for fold_index, (train_idx, test_idx) in enumerate(
            gkf.split(x, y, groups), start=1
        ):
            pipe = build_root_cause_pipeline()
            if len(set(y[train_idx].tolist())) < 2:
                continue
            pipe.fit(x[train_idx], y[train_idx])
            scores = pipe.predict_proba(x[test_idx])[:, 1]
            fold_metrics = evaluate_classifier(y[test_idx], scores)
            fold_metrics["fold"] = fold_index
            metrics_folds.append(fold_metrics)

    final = build_root_cause_pipeline()
    final.fit(x, y)
    train_scores = final.predict_proba(x)[:, 1]
    train_metrics = evaluate_classifier(y, train_scores)

    dim = int(bundle.get("embedding_dimension") or 128)
    schema = build_feature_schema_lot(dim)
    schema["feature_schema_version"] = FEATURE_SCHEMA_VERSION_003_LOT
    schema["feature_names"] = feature_names
    schema["grain"] = "pattern_x_lot"
    schema["label"] = "any_FAIL_in_pattern_x_lot_equals_1"

    model_dir = resolve_training_model_dir(
        workspace_dir=workspace_dir,
        model_family=MODEL_FAMILY_003_LOT,
        model_version=model_version,
    )
    card: Dict[str, Any] = {
        "model_family": MODEL_FAMILY_003_LOT,
        "model_version": model_version,
        "generated_by": GENERATED_BY_003_LOT,
        "status": status,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_003_LOT,
        "grain": "pattern_x_lot",
        "training_timestamp": _utc_now_iso(),
        "training_session_hash": bundle.get("session_hash"),
        "training_row_count": int(len(y)),
        "training_lots": unique_groups,
        "algorithm": "RandomForestClassifier",
        "hyperparameters": {
            "n_estimators": 200,
            "class_weight": "balanced",
            "random_state": 42,
            "scaler": "StandardScaler",
        },
        "investigation_threshold": investigation_threshold,
        "metrics": {
            "train": train_metrics,
            "group_kfold": metrics_folds,
        },
        "inference_latency_budget_ms": 5000,
        "notes": [
            "LOT-grain root-cause ranking; investigation priority for candidates only.",
            "Association-based priority — not a causal diagnosis.",
        ],
    }
    write_model_bundle(
        model_dir=model_dir,
        pipeline=final,
        schema=schema,
        card=card,
    )
    return model_dir


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Train PA-ML-003 Root-cause Ranking offline (LOT grain)"
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--workspace-dir", default=None)
    parser.add_argument("--model-version", default="v0.1.0")
    parser.add_argument(
        "--status",
        default="experimental",
        choices=("experimental", "production"),
    )
    parser.add_argument(
        "--investigation-threshold",
        type=float,
        default=DEFAULT_INVESTIGATION_THRESHOLD,
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    output_dir = os.path.abspath(args.output_dir)
    workspace_dir = os.path.abspath(
        args.workspace_dir or os.path.dirname(output_dir) or os.getcwd()
    )
    model_dir = train_pa_ml_003_lot(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        model_version=args.model_version,
        status=args.status,
        investigation_threshold=args.investigation_threshold,
    )
    print(f"Wrote model to {model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
