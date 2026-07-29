"""Reusable deterministic statistical helpers."""

import math


def percentile_value(values: list[float], percentile: float) -> float:
    """Return a linearly interpolated dataset-relative percentile (0..100)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pct = max(0.0, min(100.0, percentile))
    rank = (len(ordered) - 1) * (pct / 100.0)
    low = int(math.floor(rank))
    high = int(math.ceil(rank))
    if low == high:
        return ordered[low]
    weight = rank - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight
