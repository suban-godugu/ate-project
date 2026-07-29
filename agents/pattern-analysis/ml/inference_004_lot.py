"""PA-ML-004-LOT online inference — advisory pattern recommendations (pattern × LOT)."""
from __future__ import annotations

import logging
from typing import Optional

from ml.contracts_004 import (
    GENERATED_BY_004_LOT,
    MODEL_FAMILY_004_LOT,
    PATTERN_RECOMMENDATIONS_BY_LOT_JSON,
)
from ml.execution_lookup import load_execution_results_by_lot
from ml.inference_004 import _run_recommendation_inference

logger = logging.getLogger(__name__)


def run_pa_ml_004_lot_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """Non-fatal Layer-3 pattern recommendations (pattern × LOT grain)."""
    return _run_recommendation_inference(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        config_path=config_path,
        model_family=MODEL_FAMILY_004_LOT,
        generated_by=GENERATED_BY_004_LOT,
        grain="pattern_x_lot",
        artifact_filename=PATTERN_RECOMMENDATIONS_BY_LOT_JSON,
        load_execution_results=load_execution_results_by_lot,
    )
