"""PA-ML-002 explainability — deviation from training distribution."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence


def top_contributors_from_deviation(
    *,
    feature_names: Sequence[str],
    feature_values: Mapping[str, float],
    training_stats: Mapping[str, Mapping[str, float]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Rank features by |z-score| vs training mean/std.
    Deterministic secondary sort by feature name.
    """
    scored: List[Dict[str, Any]] = []
    for name in feature_names:
        value = float(feature_values.get(name) or 0.0)
        stats = training_stats.get(name) or {}
        mean = float(stats.get("mean") or 0.0)
        std = float(stats.get("std") or 0.0)
        if std <= 1e-12:
            z_score = 0.0
        else:
            z_score = (value - mean) / std
        scored.append(
            {
                "feature": name,
                "value": round(value, 6),
                "training_mean": round(mean, 6),
                "z_score": round(z_score, 6),
                "contribution": round(abs(z_score), 6),
            }
        )
    scored.sort(
        key=lambda item: (-float(item["contribution"]), str(item["feature"]))
    )
    return scored[: max(0, int(top_k))]
