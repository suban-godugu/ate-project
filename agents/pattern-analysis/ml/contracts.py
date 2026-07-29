"""PA-ML-001 contracts and constants."""
from __future__ import annotations

FAILURE_PREDICTIONS_JSON = "PA-Analysis-Session_failure_predictions.json"
FAILURE_PREDICTIONS_BY_LOT_JSON = (
    "PA-Analysis-Session_failure_predictions_by_lot.json"
)
GENERATED_BY = "PA-ML-001"
GENERATED_BY_LOT = "PA-ML-001-LOT"
FEATURE_SCHEMA_VERSION = "1.0"
FEATURE_SCHEMA_VERSION_LOT = "1.0"
MODEL_FAMILY = "pa_ml_001"
MODEL_FAMILY_LOT = "pa_ml_001_lot"

FORBIDDEN_FEATURE_NAMES = frozenset(
    {
        "pass_count",
        "fail_count",
        "history",
        "latest_result",
        "label",
        "y",
    }
)

# Scalar feature names (embeddings are emb_0 .. emb_{dim-1})
SCALAR_FEATURE_NAMES = (
    "toggle_coverage_pct",
    "toggle_density_pct",
    "toggle_count",
    "cluster_id_code",
    "similarity_to_centroid",
    "redundancy_neighbor_count",
    "redundancy_max_raw_similarity",
    "redundancy_max_confidence",
)

LOT_SCALAR_FEATURE_NAMES = SCALAR_FEATURE_NAMES + ("log_count_in_lot",)

DEFAULT_EMBEDDING_DIM = 128
