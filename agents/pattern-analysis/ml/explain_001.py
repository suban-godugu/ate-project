"""PA-ML-001 explainability helpers (coefficient-based top contributors)."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence


def top_contributors_from_coefficients(
    *,
    feature_names: Sequence[str],
    feature_values: Mapping[str, float],
    coefficients: Sequence[float],
    intercept: float = 0.0,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Rank features by |coef * value| contribution to the linear score.
    Deterministic secondary sort by feature name.
    """
    scored: List[Dict[str, Any]] = []
    for index, name in enumerate(feature_names):
        if index >= len(coefficients):
            break
        value = float(feature_values.get(name) or 0.0)
        coef = float(coefficients[index])
        contribution = coef * value
        scored.append(
            {
                "feature": name,
                "value": round(value, 6),
                "coefficient": round(coef, 6),
                "contribution": round(contribution, 6),
            }
        )
    scored.sort(key=lambda item: (-abs(float(item["contribution"])), str(item["feature"])))
    top = scored[: max(0, int(top_k))]
    # Intercept noted only when requested via empty features — keep payload lean.
    _ = intercept
    return top
