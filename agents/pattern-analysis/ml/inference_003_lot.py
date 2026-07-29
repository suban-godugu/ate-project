"""PA-ML-003-LOT online inference — advisory root-cause rankings (pattern × LOT grain)."""
from __future__ import annotations

import logging
from typing import Optional

from ml.contracts_003 import (
    FEATURE_SCHEMA_VERSION_003_LOT,
    GENERATED_BY_003_LOT,
    MODEL_FAMILY_003_LOT,
    ROOT_CAUSE_RANKINGS_BY_LOT_JSON,
)
from ml.feature_builder_001_lot import build_lot_feature_rows_from_output_dir
from ml.inference_003 import _run_root_cause_inference
from ml.root_cause_common import advisory_index_lot

logger = logging.getLogger(__name__)


def run_pa_ml_003_lot_inference(
    output_dir: str,
    workspace_dir: str,
    *,
    config_path: Optional[str] = None,
) -> Optional[str]:
    """Non-fatal Layer-3 root-cause ranking (pattern × LOT grain)."""
    return _run_root_cause_inference(
        output_dir=output_dir,
        workspace_dir=workspace_dir,
        config_path=config_path,
        model_family=MODEL_FAMILY_003_LOT,
        feature_schema_version=FEATURE_SCHEMA_VERSION_003_LOT,
        generated_by=GENERATED_BY_003_LOT,
        grain="pattern_x_lot",
        artifact_filename=ROOT_CAUSE_RANKINGS_BY_LOT_JSON,
        build_bundle=lambda path: build_lot_feature_rows_from_output_dir(
            path, include_labels=False
        ),
        advisory_index=advisory_index_lot,
    )
