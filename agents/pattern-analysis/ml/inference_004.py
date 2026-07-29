"""PA-ML-004 online inference — advisory pattern recommendations (log grain)."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Mapping, Optional

from ml.config import is_model_enabled, load_ml_config, model_version_for, resolve_ml_config_path
from ml.contracts_004 import (
    GENERATED_BY_004,
    MODEL_FAMILY_004,
    PATTERN_RECOMMENDATIONS_JSON,
    POLICY_VERSION_004,
)
from ml.execution_lookup import load_execution_results_by_log
from ml.inference_common import write_predictions_json
from ml.recommendation_common import (
    _session_hash_from_artifacts,
    build_recommendations,
    build_recommendations_payload,
    load_upstream_artifacts,
)
from ml.registry import resolve_usable_policy

logger = logging.getLogger(__name__)


def _run_recommendation_inference(
    *,
    output_dir: str,
    workspace_dir: str,
    config_path: Optional[str],
    model_family: str,
    generated_by: str,
    grain: str,
    artifact_filename: str,
    load_execution_results: Callable[[str], Dict[str, str]],
) -> Optional[str]:
    cfg_path = resolve_ml_config_path(workspace_dir, config_path)
    config = load_ml_config(cfg_path)
    if not is_model_enabled(config, model_family):
        logger.info("PA-ML-004 skipped: model %s disabled", model_family)
        return None

    model_dir, model_card, policy = resolve_usable_policy(
        workspace_dir, config, model_family
    )
    if model_dir is None or model_card is None or policy is None:
        logger.info("PA-ML-004 skipped: no usable policy for %s", model_family)
        return None

    policy_version = str(policy.get("policy_version") or "")
    if policy_version and policy_version != POLICY_VERSION_004:
        logger.warning(
            "PA-ML-004 skipped: policy version mismatch (model=%s, expected=%s)",
            policy_version,
            POLICY_VERSION_004,
        )
        return None

    failure_payload, anomaly_payload, root_cause_payload = load_upstream_artifacts(
        output_dir, grain=grain
    )
    if not any(payload is not None for payload in (failure_payload, anomaly_payload, root_cause_payload)):
        logger.info("PA-ML-004 skipped: no upstream ML artifacts for %s", grain)
        return None

    execution_results = load_execution_results(output_dir)
    recommendations: List[Dict[str, Any]] = build_recommendations(
        output_dir=output_dir,
        grain=grain,
        execution_results=execution_results,
        policy=policy,
    )
    if not recommendations:
        logger.info("PA-ML-004 skipped: no recommendation rows for %s", grain)
        return None

    payload = build_recommendations_payload(
        recommendations=recommendations,
        generated_by=generated_by,
        model_family=model_family,
        grain=grain,
        model_version=str(
            model_card.get("model_version") or model_version_for(config, model_family)
        ),
        policy_version=str(policy.get("policy_version") or POLICY_VERSION_004),
        session_hash=_session_hash_from_artifacts(
            failure_payload,
            anomaly_payload,
            root_cause_payload,
        ),
        status=model_card.get("status"),
    )
    out_path = os.path.join(output_dir, artifact_filename)
    write_predictions_json(out_path, payload)
    return out_path


def run_pa_ml_004_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """Non-fatal Layer-3 pattern recommendations (pattern × source_log grain)."""
    return _run_recommendation_inference(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        config_path=config_path,
        model_family=MODEL_FAMILY_004,
        generated_by=GENERATED_BY_004,
        grain="pattern_x_source_log",
        artifact_filename=PATTERN_RECOMMENDATIONS_JSON,
        load_execution_results=load_execution_results_by_log,
    )
