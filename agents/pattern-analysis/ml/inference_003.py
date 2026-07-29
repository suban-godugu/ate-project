"""PA-ML-003 online inference — advisory root-cause rankings (log grain)."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Dict, List, Mapping, Optional

import joblib

from ml.config import is_model_enabled, load_ml_config, model_version_for, resolve_ml_config_path
from ml.contracts_003 import (
    DEFAULT_INVESTIGATION_THRESHOLD,
    FEATURE_SCHEMA_VERSION_003,
    GENERATED_BY_003,
    MODEL_FAMILY_003,
    ROOT_CAUSE_RANKINGS_JSON,
)
from ml.explain_003 import (
    evidence_categories,
    hypothesis_tags,
    top_contributors_from_importances,
)
from ml.execution_lookup import (
    load_execution_results_by_log,
    load_execution_results_by_lot,
)
from ml.inference_common import predict_scores, scaled_feature_values, write_predictions_json
from ml.registry import model_joblib_path, resolve_usable_model
from ml.root_cause_common import (
    advisory_index_log,
    build_chain_summaries,
    build_rankings_payload,
    feature_importances_from_model,
    investigation_score,
    is_candidate,
    scan_chain_by_pattern,
)

from ml.feature_builder_001 import build_feature_rows_from_output_dir, matrix_from_rows

logger = logging.getLogger(__name__)


def _run_root_cause_inference(
    *,
    output_dir: str,
    workspace_dir: str,
    config_path: Optional[str],
    model_family: str,
    feature_schema_version: str,
    generated_by: str,
    grain: str,
    artifact_filename: str,
    build_bundle: Callable[[str], Mapping[str, Any]],
    advisory_index: Callable[[str], tuple],
) -> Optional[str]:
    cfg_path = resolve_ml_config_path(workspace_dir, config_path)
    config = load_ml_config(cfg_path)
    if not is_model_enabled(config, model_family):
        logger.info("PA-ML-003 skipped: model %s disabled", model_family)
        return None

    model_dir, model_card, feature_schema = resolve_usable_model(
        workspace_dir, config, model_family
    )
    if model_dir is None or model_card is None or feature_schema is None:
        logger.info("PA-ML-003 skipped: no usable model for %s", model_family)
        return None

    schema_version = str(feature_schema.get("feature_schema_version") or "")
    if schema_version != feature_schema_version:
        logger.warning(
            "PA-ML-003 skipped: feature schema mismatch (model=%s, expected=%s)",
            schema_version,
            feature_schema_version,
        )
        return None

    expected_names = list(feature_schema.get("feature_names") or [])
    bundle = build_bundle(output_dir)
    if list(bundle.get("feature_names") or []) != expected_names:
        logger.warning("PA-ML-003 skipped: live feature names do not match model schema")
        return None

    matrix, names, _unit_ids = matrix_from_rows(bundle)
    if not matrix:
        logger.info("PA-ML-003 skipped: no feature rows")
        return None

    model = joblib.load(model_joblib_path(model_dir))
    importances = feature_importances_from_model(model)
    model_scores = predict_scores(model, matrix)
    threshold = float(
        model_card.get("investigation_threshold") or DEFAULT_INVESTIGATION_THRESHOLD
    )

    failure_scores, anomaly_flags = advisory_index(output_dir)
    chain_map = scan_chain_by_pattern(output_dir)
    if grain == "pattern_x_lot":
        execution_results = load_execution_results_by_lot(output_dir)
    else:
        execution_results = load_execution_results_by_log(output_dir)

    candidates: List[Dict[str, Any]] = []
    for index, row in enumerate(bundle.get("rows") or []):
        if not isinstance(row, Mapping):
            continue
        uid = str(row.get("unit_id") or "")
        features = row.get("features") if isinstance(row.get("features"), Mapping) else {}
        scaled = scaled_feature_values(model, names, features)
        actual_result = execution_results.get(uid, "")
        is_anomaly = int(anomaly_flags.get(uid, 0))
        base_score = float(model_scores[index])
        if not is_candidate(
            model_score=base_score,
            actual_result=actual_result,
            is_anomaly=is_anomaly,
            threshold=threshold,
        ):
            continue
        inv_score = investigation_score(
            model_score=base_score,
            failure_boost=failure_scores.get(uid, 0.0),
            is_anomaly=is_anomaly,
            actual_fail=str(actual_result).upper() == "FAIL",
        )
        contributors = top_contributors_from_importances(
            feature_names=names,
            feature_values=scaled,
            importances=importances,
            top_k=5,
        )
        pattern_id = str(row.get("pattern_id") or "")
        entry: Dict[str, Any] = {
            "unit_id": uid,
            "pattern_id": pattern_id,
            "scan_chain_id": chain_map.get(pattern_id, ""),
            "investigation_score": inv_score,
            "model_score": round(base_score, 6),
            "actual_result": actual_result,
            "hypothesis_tags": hypothesis_tags(
                feature_values=features,
                contributors=contributors,
                actual_result=actual_result,
                is_anomaly=is_anomaly,
            ),
            "top_contributors": contributors,
            "evidence_categories": evidence_categories(contributors),
        }
        for key in (
            "source_log",
            "source_log_relpath",
            "source_lot",
            "log_count_in_lot",
        ):
            if row.get(key) is not None:
                entry[key] = row.get(key)
        candidates.append(entry)

    candidates.sort(
        key=lambda item: (
            -float(item.get("investigation_score") or 0.0),
            str(item.get("unit_id") or ""),
        )
    )
    for rank, entry in enumerate(candidates, start=1):
        entry["investigation_rank"] = rank

    chain_summaries = build_chain_summaries(candidates)
    payload = build_rankings_payload(
        rankings=candidates,
        generated_by=generated_by,
        model_family=model_family,
        grain=grain,
        model_version=str(
            model_card.get("model_version") or model_version_for(config, model_family)
        ),
        feature_schema_version=feature_schema_version,
        session_hash=bundle.get("session_hash"),
        status=model_card.get("status"),
        chain_summaries=chain_summaries,
        investigation_threshold=threshold,
    )
    out_path = os.path.join(output_dir, artifact_filename)
    write_predictions_json(out_path, payload)
    return out_path


def run_pa_ml_003_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """Non-fatal Layer-3 root-cause ranking (pattern × source_log grain)."""
    return _run_root_cause_inference(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        config_path=config_path,
        model_family=MODEL_FAMILY_003,
        feature_schema_version=FEATURE_SCHEMA_VERSION_003,
        generated_by=GENERATED_BY_003,
        grain="pattern_x_source_log",
        artifact_filename=ROOT_CAUSE_RANKINGS_JSON,
        build_bundle=lambda path: build_feature_rows_from_output_dir(
            path, include_labels=False
        ),
        advisory_index=advisory_index_log,
    )
