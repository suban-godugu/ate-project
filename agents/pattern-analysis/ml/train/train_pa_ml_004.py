"""Offline PA-ML-004 policy writer (log grain) — never import from session path."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Sequence

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from ml.contracts_004 import (
    DEFAULT_WEIGHTS,
    GENERATED_BY_004,
    MODEL_FAMILY_004,
    POLICY_VERSION_004,
    RECOMMENDATION_POLICY_JSON,
)

from ml.train.train_model_dir import resolve_training_model_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_policy() -> Dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION_004,
        "grain": "pattern_x_source_log",
        "weights": dict(DEFAULT_WEIGHTS),
        "tier_thresholds": {"high": 0.75, "medium": 0.5},
    }


def write_policy_bundle(
    *,
    model_dir: str,
    model_version: str,
    policy: Dict[str, Any],
    card: Dict[str, Any],
) -> None:
    os.makedirs(model_dir, exist_ok=True)
    with open(
        os.path.join(model_dir, RECOMMENDATION_POLICY_JSON), "w", encoding="utf-8"
    ) as handle:
        json.dump(policy, handle, indent=2, sort_keys=True)
    with open(os.path.join(model_dir, "model_card.json"), "w", encoding="utf-8") as handle:
        json.dump(card, handle, indent=2, sort_keys=True, allow_nan=False)


def train_pa_ml_004(
    *,
    output_dir: str,
    workspace_dir: str,
    model_version: str = "v0.1.0",
    status: str = "experimental",
) -> str:
    _ = output_dir
    policy = default_policy()
    model_dir = resolve_training_model_dir(
        workspace_dir=workspace_dir,
        model_family=MODEL_FAMILY_004,
        model_version=model_version,
    )
    card: Dict[str, Any] = {
        "model_family": MODEL_FAMILY_004,
        "model_version": model_version,
        "generated_by": GENERATED_BY_004,
        "status": status,
        "policy_version": POLICY_VERSION_004,
        "grain": "pattern_x_source_log",
        "algorithm": "FusionPolicy",
        "training_timestamp": _utc_now(),
        "hyperparameters": {"weights": policy["weights"]},
        "inference_latency_budget_ms": 2000,
        "notes": [
            "Fusion of PA-ML-001/002/003 advisory artifacts; no standalone classifier.",
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
        description="Write PA-ML-004 recommendation policy (log grain)"
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
    model_dir = train_pa_ml_004(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        model_version=args.model_version,
        status=args.status,
    )
    print(f"Wrote policy to {model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
