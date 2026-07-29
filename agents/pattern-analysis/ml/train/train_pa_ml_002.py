"""Offline PA-ML-002 training (log grain) — never import from session request path."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Sequence

import numpy as np

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ml.anomaly_common import (
    anomaly_flags,
    build_anomaly_pipeline,
    feature_training_stats,
    raw_anomaly_scores,
    score_calibration_from_raw,
    write_model_bundle,
)
from ml.contracts_002 import (
    FEATURE_SCHEMA_VERSION_002,
    GENERATED_BY_002,
    MODEL_FAMILY_002,
)
from ml.feature_builder_001 import (
    build_feature_rows_from_output_dir,
    build_feature_schema,
    matrix_from_rows,
)
from ml.train.train_model_dir import resolve_training_model_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def train_pa_ml_002(
    *,
    output_dir: str,
    workspace_dir: str,
    model_version: str = "v0.1.0",
    status: str = "experimental",
    contamination: float = 0.01,
) -> str:
    bundle = build_feature_rows_from_output_dir(output_dir, include_labels=False)
    matrix, feature_names, _unit_ids = matrix_from_rows(bundle)
    if not matrix:
        raise RuntimeError("No feature rows available for PA-ML-002 training.")
    x = np.asarray(matrix, dtype=np.float64)

    pipeline = build_anomaly_pipeline(contamination=contamination)
    pipeline.fit(x)
    raw = raw_anomaly_scores(pipeline, x)
    calibration = score_calibration_from_raw(raw)
    flags = anomaly_flags(pipeline, x)

    dim = int(bundle.get("embedding_dimension") or 128)
    schema = build_feature_schema(dim)
    schema["feature_schema_version"] = FEATURE_SCHEMA_VERSION_002
    schema["feature_names"] = feature_names
    schema["grain"] = "pattern_x_source_log"
    schema["training_feature_stats"] = feature_training_stats(x, feature_names)

    model_dir = resolve_training_model_dir(
        workspace_dir=workspace_dir,
        model_family=MODEL_FAMILY_002,
        model_version=model_version,
    )
    card: Dict[str, Any] = {
        "model_family": MODEL_FAMILY_002,
        "model_version": model_version,
        "generated_by": GENERATED_BY_002,
        "status": status,
        "feature_schema_version": FEATURE_SCHEMA_VERSION_002,
        "grain": "pattern_x_source_log",
        "training_timestamp": _utc_now(),
        "training_session_hash": bundle.get("session_hash"),
        "training_row_count": int(len(x)),
        "algorithm": "IsolationForest",
        "hyperparameters": {
            "n_estimators": 200,
            "contamination": contamination,
            "scaler": "StandardScaler",
            "random_state": 42,
        },
        "metrics": {
            "train": {
                "anomaly_count": int(flags.sum()),
                "anomaly_rate": round(float(flags.mean()), 6),
            }
        },
        "score_calibration": calibration,
        "inference_latency_budget_ms": 5000,
        "notes": [
            "Unsupervised anomaly model; higher anomaly_score = more unusual.",
            "Forbidden outcome aggregates excluded from features.",
        ],
    }
    write_model_bundle(
        model_dir=model_dir,
        pipeline=pipeline,
        schema=schema,
        card=card,
    )
    return model_dir


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train PA-ML-002 Anomaly offline (log grain)")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--workspace-dir", default=None)
    parser.add_argument("--model-version", default="v0.1.0")
    parser.add_argument("--contamination", type=float, default=0.01)
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
    model_dir = train_pa_ml_002(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        model_version=args.model_version,
        status=args.status,
        contamination=args.contamination,
    )
    print(f"Wrote model to {model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
