"""PA-ML-001 online inference — advisory predictions only (log grain)."""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence

import joblib

from ml.config import is_model_enabled, load_ml_config, resolve_ml_config_path
from ml.contracts import (
    FAILURE_PREDICTIONS_JSON,
    FEATURE_SCHEMA_VERSION,
    GENERATED_BY,
    MODEL_FAMILY,
)
from ml.explain_001 import top_contributors_from_coefficients
from ml.feature_builder_001 import build_feature_rows_from_output_dir, matrix_from_rows
from ml.inference_common import (
    coefficients_from_model,
    predict_scores,
    scaled_feature_values,
    write_predictions_json,
)
from ml.registry import model_joblib_path, resolve_usable_model

logger = logging.getLogger(__name__)


def run_pa_ml_001_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """
    Non-fatal Layer-3 inference (pattern × source_log grain).

    Returns path to predictions file, or None when skipped.
    Never mutates L1 session artifacts.
    """
    cfg_path = resolve_ml_config_path(workspace_dir, config_path)
    config = load_ml_config(cfg_path)
    if not is_model_enabled(config, MODEL_FAMILY):
        logger.info("PA-ML-001 skipped: model %s disabled", MODEL_FAMILY)
        return None

    model_dir, model_card, feature_schema = resolve_usable_model(
        workspace_dir,
        config,
        MODEL_FAMILY,
    )
    if model_dir is None or model_card is None or feature_schema is None:
        logger.info(
            "PA-ML-001 skipped: no usable model for %s",
            MODEL_FAMILY,
        )
        return None

    schema_version = str(feature_schema.get("feature_schema_version") or "")
    if schema_version != FEATURE_SCHEMA_VERSION:
        logger.warning(
            "PA-ML-001 skipped: feature schema mismatch (model=%s, expected=%s)",
            schema_version,
            FEATURE_SCHEMA_VERSION,
        )
        return None

    expected_names = list(feature_schema.get("feature_names") or [])
    bundle = build_feature_rows_from_output_dir(output_dir, include_labels=False)
    if list(bundle.get("feature_names") or []) != expected_names:
        logger.warning("PA-ML-001 skipped: live feature names do not match model schema")
        return None

    matrix, names, _unit_ids = matrix_from_rows(bundle)
    if not matrix:
        logger.info("PA-ML-001 skipped: no feature rows")
        return None

    model = joblib.load(model_joblib_path(model_dir))
    coefficients, intercept = coefficients_from_model(model)
    scores = predict_scores(model, matrix)

    predictions: List[Dict[str, Any]] = []
    rows = bundle.get("rows") or []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        score = float(scores[index])
        features = row.get("features") if isinstance(row.get("features"), Mapping) else {}
        scaled_features = scaled_feature_values(model, names, features)
        predictions.append(
            {
                "unit_id": row.get("unit_id"),
                "pattern_id": row.get("pattern_id"),
                "source_log": row.get("source_log"),
                "source_log_relpath": row.get("source_log_relpath"),
                "source_lot": row.get("source_lot"),
                "score": round(score, 6),
                "label_pred": int(score >= 0.5),
                "top_contributors": top_contributors_from_coefficients(
                    feature_names=names,
                    feature_values=scaled_features,
                    coefficients=coefficients,
                    intercept=intercept,
                    top_k=5,
                ),
            }
        )

    predictions.sort(
        key=lambda item: (
            -float(item.get("score") or 0.0),
            str(item.get("unit_id") or ""),
        )
    )

    payload = {
        "generated_by": GENERATED_BY,
        "model_family": MODEL_FAMILY,
        "grain": "pattern_x_source_log",
        "model_version": str(model_card.get("model_version") or config.model_version),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "session_hash": bundle.get("session_hash"),
        "status": model_card.get("status"),
        "prediction_count": len(predictions),
        "predictions": predictions,
    }
    out_path = os.path.join(output_dir, FAILURE_PREDICTIONS_JSON)
    write_predictions_json(out_path, payload)
    return out_path
