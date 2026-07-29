"""PA-ML-003 explainability — feature-importance contributors and hypothesis tags."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

TOGGLE_FEATURES = frozenset(
    {"toggle_coverage_pct", "toggle_density_pct", "toggle_count"}
)
CLUSTER_FEATURES = frozenset({"cluster_id_code", "similarity_to_centroid"})
REDUNDANCY_FEATURES = frozenset(
    {
        "redundancy_neighbor_count",
        "redundancy_max_raw_similarity",
        "redundancy_max_confidence",
    }
)


def _category_for_feature(name: str) -> str:
    if name in TOGGLE_FEATURES:
        return "toggle"
    if name in CLUSTER_FEATURES:
        return "cluster"
    if name in REDUNDANCY_FEATURES:
        return "redundancy"
    if name.startswith("emb_"):
        return "embedding"
    return "other"


def top_contributors_from_importances(
    *,
    feature_names: Sequence[str],
    feature_values: Mapping[str, float],
    importances: Sequence[float],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Rank features by |importance * value| contribution."""
    scored: List[Dict[str, Any]] = []
    for index, name in enumerate(feature_names):
        if index >= len(importances):
            break
        value = float(feature_values.get(name) or 0.0)
        importance = float(importances[index])
        contribution = importance * abs(value)
        scored.append(
            {
                "feature": name,
                "value": round(value, 6),
                "importance": round(importance, 6),
                "contribution": round(contribution, 6),
            }
        )
    scored.sort(
        key=lambda item: (-float(item["contribution"]), str(item["feature"]))
    )
    return scored[: max(0, int(top_k))]


def evidence_categories(
    contributors: Sequence[Mapping[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {
        "toggle": [],
        "cluster": [],
        "redundancy": [],
        "embedding": [],
        "other": [],
    }
    for item in contributors:
        category = _category_for_feature(str(item.get("feature") or ""))
        grouped[category].append(dict(item))
    return {key: value for key, value in grouped.items() if value}


def hypothesis_tags(
    *,
    feature_values: Mapping[str, float],
    contributors: Sequence[Mapping[str, Any]],
    actual_result: str = "",
    is_anomaly: int = 0,
) -> List[str]:
    tags: List[str] = []
    coverage = float(feature_values.get("toggle_coverage_pct") or 0.0)
    similarity = float(feature_values.get("similarity_to_centroid") or 0.0)
    if coverage < 30.0:
        tags.append("low_toggle_coverage")
    if similarity < 0.85:
        tags.append("cluster_outlier")
    if int(is_anomaly or 0) == 1:
        tags.append("anomaly_flagged")
    if str(actual_result or "").upper() == "FAIL":
        tags.append("observed_fail")
    top_names = {str(item.get("feature") or "") for item in contributors[:3]}
    if any(name.startswith("emb_") for name in top_names):
        tags.append("embedding_deviation")
    if any(name in REDUNDANCY_FEATURES for name in top_names):
        tags.append("redundancy_signal")
    return sorted(set(tags))
