"""PA-ML-002-LOT online inference — advisory anomaly scores (pattern × LOT grain)."""
from __future__ import annotations

import logging
from typing import Optional

from ml.contracts_002 import (
    ANOMALY_SCORES_BY_LOT_JSON,
    FEATURE_SCHEMA_VERSION_002_LOT,
    GENERATED_BY_002_LOT,
    MODEL_FAMILY_002_LOT,
)
from ml.feature_builder_001_lot import build_lot_feature_rows_from_output_dir
from ml.inference_002 import _run_anomaly_inference

logger = logging.getLogger(__name__)


def run_pa_ml_002_lot_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """Non-fatal Layer-3 anomaly inference (pattern × LOT grain)."""
    return _run_anomaly_inference(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        config_path=config_path,
        model_family=MODEL_FAMILY_002_LOT,
        feature_schema_version=FEATURE_SCHEMA_VERSION_002_LOT,
        generated_by=GENERATED_BY_002_LOT,
        grain="pattern_x_lot",
        artifact_filename=ANOMALY_SCORES_BY_LOT_JSON,
        build_bundle=lambda path: build_lot_feature_rows_from_output_dir(
            path, include_labels=False
        ),
    )
