"""PA-ML-004 Pattern Recommendations contracts and constants."""
from __future__ import annotations

PATTERN_RECOMMENDATIONS_JSON = "PA-Analysis-Session_pattern_recommendations.json"
PATTERN_RECOMMENDATIONS_BY_LOT_JSON = (
    "PA-Analysis-Session_pattern_recommendations_by_lot.json"
)
GENERATED_BY_004 = "PA-ML-004"
GENERATED_BY_004_LOT = "PA-ML-004-LOT"
POLICY_VERSION_004 = "4.0"
MODEL_FAMILY_004 = "pa_ml_004"
MODEL_FAMILY_004_LOT = "pa_ml_004_lot"
RECOMMENDATION_POLICY_JSON = "recommendation_policy.json"

DEFAULT_WEIGHTS = {
    "w_failure": 0.35,
    "w_anomaly": 0.25,
    "w_rootcause": 0.30,
    "w_fail_obs": 0.10,
}
TIER_HIGH = 0.75
TIER_MEDIUM = 0.5
RECOMMENDATION_DISCLAIMER = (
    "Advisory prioritization only — not an engineering verdict."
)
