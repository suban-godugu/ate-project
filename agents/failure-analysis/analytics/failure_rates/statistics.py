"""Statistical metrics for failure rate datasets."""

from __future__ import annotations

import math
import statistics
from typing import Any


def compute_statistics(rates: list[float]) -> dict[str, Any]:
    """Mean, median, stdev, and sigma level for a rate sample."""
    if not rates:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "sigma_level": 0.0,
            "min": 0.0,
            "max": 0.0,
        }
    mean = statistics.mean(rates)
    median = statistics.median(rates)
    std_dev = statistics.pstdev(rates) if len(rates) > 1 else 0.0
    sigma_level = round(mean / std_dev, 4) if std_dev > 0 else float("inf")
    if math.isinf(sigma_level):
        sigma_level = 99.0
    return {
        "count": len(rates),
        "mean": round(mean, 6),
        "median": round(median, 6),
        "std_dev": round(std_dev, 6),
        "sigma_level": sigma_level,
        "min": round(min(rates), 6),
        "max": round(max(rates), 6),
    }


def bucket_summary(tested: int, failed: int) -> dict[str, Any]:
    passing = tested - failed
    failure_pct = round(100.0 * failed / tested, 6) if tested else 0.0
    yield_pct = round(100.0 - failure_pct, 6)
    return {
        "pass_count": passing,
        "fail_count": failed,
        "tested": tested,
        "failure_percentage": failure_pct,
        "yield_percentage": yield_pct,
        "failure_rate_pct": failure_pct,
        "pass_rate_pct": yield_pct,
    }


def attach_statistics(level_data: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rates = [float(row.get("failure_rate_pct", 0.0)) for row in level_data.values()]
    return {
        "entities": level_data,
        "statistics": compute_statistics(rates),
    }
