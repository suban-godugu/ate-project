"""Wafer-level statistical aggregation and yield analysis."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict
from typing import Any


def aggregate_wafer_data(
    spatial_map: list[dict[str, Any]],
    wafer_stats: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate per-wafer die data into wafer-level statistics."""
    by_wafer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in spatial_map:
        by_wafer[point.get("wafer_id", "UNKNOWN")].append(point)

    aggregated = []
    for wafer in wafer_stats:
        wafer_id = wafer["wafer_id"]
        points = by_wafer.get(wafer_id, [])
        pass_count = sum(1 for p in points if not p.get("is_failing"))
        fail_count = sum(1 for p in points if p.get("is_failing"))
        total = len(points) or wafer.get("total_dies_tested", 0)

        aggregated.append(
            {
                **wafer,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "die_points": len(points),
                "pass_fail_distribution": {
                    "pass": pass_count,
                    "fail": fail_count,
                    "pass_pct": round(100.0 * pass_count / total, 4) if total else 100.0,
                    "fail_pct": round(100.0 * fail_count / total, 4) if total else 0.0,
                },
            }
        )

    overall_yield = _overall_yield(aggregated)
    return {
        "wafer_statistics": aggregated,
        "wafer_count": len(aggregated),
        "overall_yield_pct": overall_yield,
        "yield_distribution": [
            {
                "wafer_id": w["wafer_id"],
                "lot_id": w["lot_id"],
                "yield_pct": w.get("yield_pct", 0.0),
                "failure_rate_pct": w.get("failure_rate_pct", 0.0),
            }
            for w in aggregated
        ],
    }


def compute_bin_distribution(
    wafer_stats: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate bin pareto across all wafers."""
    global_bins: Counter[str] = Counter()
    per_wafer: dict[str, list[dict[str, Any]]] = {}

    for wafer in wafer_stats:
        wafer_id = wafer["wafer_id"]
        pareto = wafer.get("bin_pareto", [])
        per_wafer[wafer_id] = pareto
        for row in pareto:
            global_bins[row["name"]] += row["count"]

    total = sum(global_bins.values()) or 1
    return {
        "global_bin_distribution": [
            {
                "bin": name,
                "count": count,
                "share_pct": round(100.0 * count / total, 2),
            }
            for name, count in global_bins.most_common(20)
        ],
        "per_wafer_bins": per_wafer,
    }


def compute_failure_density_per_wafer(
    spatial_map: list[dict[str, Any]],
    *,
    grid_resolution: int = 25,
) -> dict[str, Any]:
    """Grid-based failure density for each wafer."""
    by_wafer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in spatial_map:
        if point.get("x") is not None and point.get("y") is not None:
            by_wafer[point["wafer_id"]].append(point)

    densities: dict[str, Any] = {}
    for wafer_id, points in by_wafer.items():
        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        x_span = max(x_max - x_min, 1)
        y_span = max(y_max - y_min, 1)

        grid = []
        max_density = 0.0
        for i in range(grid_resolution):
            for j in range(grid_resolution):
                dies_in = fails_in = 0
                for p in points:
                    if (
                        x_min + i * x_span / grid_resolution
                        <= p["x"]
                        < x_min + (i + 1) * x_span / grid_resolution
                        and y_min + j * y_span / grid_resolution
                        <= p["y"]
                        < y_min + (j + 1) * y_span / grid_resolution
                    ):
                        dies_in += 1
                        if p.get("is_failing"):
                            fails_in += 1
                density = fails_in / dies_in if dies_in else 0.0
                max_density = max(max_density, density)
                grid.append(
                    {
                        "x": round(x_min + (i + 0.5) * x_span / grid_resolution, 3),
                        "y": round(y_min + (j + 0.5) * y_span / grid_resolution, 3),
                        "density": round(density, 4),
                        "failure_count": fails_in,
                    }
                )
        densities[wafer_id] = {
            "grid": grid,
            "max_density": round(max_density, 4),
            "die_count": len(points),
        }

    return densities


def _overall_yield(wafer_stats: list[dict[str, Any]]) -> float:
    total = sum(w.get("total_dies_tested", 0) for w in wafer_stats)
    failing = sum(w.get("failing_dies", 0) for w in wafer_stats)
    if total == 0:
        return 100.0
    return round(100.0 * (total - failing) / total, 4)
