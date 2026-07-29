"""PA-ML-002 online inference — advisory anomaly scores (log grain)."""
from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Mapping, Optional

import joblib
import numpy as np

from ml.anomaly_common import (
    anomaly_flags,
    calibrate_scores,
    raw_anomaly_scores,
    scaled_feature_row,
)
from ml.config import is_model_enabled, load_ml_config, model_version_for, resolve_ml_config_path
from ml.contracts_002 import (
    ANOMALY_SCORES_JSON,
    FEATURE_SCHEMA_VERSION_002,
    GENERATED_BY_002,
    MODEL_FAMILY_002,
)
from ml.explain_002 import top_contributors_from_deviation
from ml.feature_builder_001 import build_feature_rows_from_output_dir, matrix_from_rows
from ml.inference_common import write_predictions_json
from ml.registry import model_joblib_path, resolve_usable_model

logger = logging.getLogger(__name__)


def _run_anomaly_inference(
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
) -> Optional[str]:
    cfg_path = resolve_ml_config_path(workspace_dir, config_path)
    config = load_ml_config(cfg_path)
    if not is_model_enabled(config, model_family):
        logger.info("PA-ML-002 skipped: model %s disabled", model_family)
        return None

    model_dir, model_card, feature_schema = resolve_usable_model(
        workspace_dir, config, model_family
    )
    if model_dir is None or model_card is None or feature_schema is None:
        logger.info("PA-ML-002 skipped: no usable model for %s", model_family)
        return None

    schema_version = str(feature_schema.get("feature_schema_version") or "")
    if schema_version != feature_schema_version:
        logger.warning(
            "PA-ML-002 skipped: feature schema mismatch (model=%s, expected=%s)",
            schema_version,
            feature_schema_version,
        )
        return None

    expected_names = list(feature_schema.get("feature_names") or [])
    bundle = build_bundle(output_dir)
    if list(bundle.get("feature_names") or []) != expected_names:
        logger.warning("PA-ML-002 skipped: live feature names do not match model schema")
        return None

    matrix, names, _unit_ids = matrix_from_rows(bundle)
    if not matrix:
        logger.info("PA-ML-002 skipped: no feature rows")
        return None

    model = joblib.load(model_joblib_path(model_dir))
    x = np.asarray(matrix, dtype=np.float64)
    raw = raw_anomaly_scores(model, x)
    calibration = model_card.get("score_calibration") or {}
    scores = calibrate_scores(raw, calibration)
    flags = anomaly_flags(model, x)
    training_stats = feature_schema.get("training_feature_stats") or {}

    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(bundle.get("rows") or []):
        if not isinstance(row, Mapping):
            continue
        features = row.get("features") if isinstance(row.get("features"), Mapping) else {}
        scaled = scaled_feature_row(model, names, features)
        entry: Dict[str, Any] = {
            "unit_id": row.get("unit_id"),
            "pattern_id": row.get("pattern_id"),
            "anomaly_score": round(float(scores[index]), 6),
            "is_anomaly": int(flags[index]),
            "top_contributors": top_contributors_from_deviation(
                feature_names=names,
                feature_values=scaled,
                training_stats=training_stats,
                top_k=5,
            ),
        }
        for key in (
            "source_log",
            "source_log_relpath",
            "source_lot",
            "log_count_in_lot",
        ):
            if row.get(key) is not None:
                entry[key] = row.get(key)
        rows.append(entry)

    rows.sort(
        key=lambda item: (
            -float(item.get("anomaly_score") or 0.0),
            str(item.get("unit_id") or ""),
        )
    )

    payload = {
        "generated_by": generated_by,
        "model_family": model_family,
        "grain": grain,
        "model_version": str(
            model_card.get("model_version") or model_version_for(config, model_family)
        ),
        "feature_schema_version": feature_schema_version,
        "session_hash": bundle.get("session_hash"),
        "status": model_card.get("status"),
        "score_count": len(rows),
        "anomaly_count": int(sum(int(r.get("is_anomaly") or 0) for r in rows)),
        "scores": rows,
    }
    out_path = os.path.join(output_dir, artifact_filename)
    write_predictions_json(out_path, payload)
    return out_path


def run_pa_ml_002_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """Non-fatal Layer-3 anomaly inference (pattern × source_log grain)."""
    return _run_anomaly_inference(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        config_path=config_path,
        model_family=MODEL_FAMILY_002,
        feature_schema_version=FEATURE_SCHEMA_VERSION_002,
        generated_by=GENERATED_BY_002,
        grain="pattern_x_source_log",
        artifact_filename=ANOMALY_SCORES_JSON,
        build_bundle=lambda path: build_feature_rows_from_output_dir(
            path, include_labels=False
        ),
    )
