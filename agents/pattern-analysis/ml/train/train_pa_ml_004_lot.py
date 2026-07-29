"""Offline PA-ML-004-LOT policy writer — never import from session path."""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, Sequence

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ml.contracts_004 import (
    GENERATED_BY_004_LOT,
    MODEL_FAMILY_004_LOT,
    POLICY_VERSION_004,
)
from ml.train.train_pa_ml_004 import default_policy, write_policy_bundle, _utc_now
from ml.train.train_model_dir import resolve_training_model_dir


def train_pa_ml_004_lot(
    *,
    output_dir: str,
    workspace_dir: str,
    model_version: str = "v0.1.0",
    status: str = "experimental",
) -> str:
    _ = output_dir
    policy = default_policy()
    policy["grain"] = "pattern_x_lot"
    model_dir = resolve_training_model_dir(
        workspace_dir=workspace_dir,
        model_family=MODEL_FAMILY_004_LOT,
        model_version=model_version,
    )
    card: Dict[str, Any] = {
        "model_family": MODEL_FAMILY_004_LOT,
        "model_version": model_version,
        "generated_by": GENERATED_BY_004_LOT,
        "status": status,
        "policy_version": POLICY_VERSION_004,
        "grain": "pattern_x_lot",
        "algorithm": "FusionPolicy",
        "training_timestamp": _utc_now(),
        "hyperparameters": {"weights": policy["weights"]},
        "inference_latency_budget_ms": 2000,
        "notes": [
            "LOT-grain fusion of PA-ML-001/002/003 advisory artifacts.",
            "Advisory prioritization only — not an engineering verdict.",
        ],
    }
    write_policy_bundle(
        model_dir=model_dir,
        model_version=model_version,
        policy=policy,
        card=card,
    )
    return model_dir


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write PA-ML-004 recommendation policy (LOT grain)"
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--workspace-dir", default=None)
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
    model_dir = train_pa_ml_004_lot(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        model_version=args.model_version,
        status=args.status,
    )
    print(f"Wrote policy to {model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
