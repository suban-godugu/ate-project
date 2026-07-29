"""Shared ML feature column definitions."""

from __future__ import annotations

SEVERITY_MAP = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}

# Columns used by both removal classifier and ordering ranker at inference.
# Note: unique_fail_contribution is used only as a hard safety filter, not a model input
# (it defines the removal label). failed_log_count is excluded from the ranker inputs
# because it directly defines ordering relevance.
SHARED_FEATURE_COLUMNS: list[str] = [
    "fail_rate",
    "severity_code",
    "mean_toggle_coverage",
    "mean_toggle_density",
    "mean_toggle_count",
    "coverage_percent",
    "failed_chain_count",
    "total_executions",
    "fail_executions",
    "similarity_to_representative",
    "cluster_size",
    "is_representative",
    "redundant_flag",
    "normalized_unique_fail_contribution",
    "normalized_toggle_coverage",
    "heuristic_removal_priority",
    "heuristic_order_score",
]

    # Also exclude normalized_unique from removal model — still label-adjacent.
REMOVAL_FEATURE_COLUMNS = [
    c
    for c in SHARED_FEATURE_COLUMNS + ["failed_log_count"]
    if c not in {"normalized_unique_fail_contribution"}
]
ORDERING_FEATURE_COLUMNS = SHARED_FEATURE_COLUMNS.copy()
FEATURE_COLUMNS = SHARED_FEATURE_COLUMNS + ["failed_log_count", "unique_fail_contribution"]
