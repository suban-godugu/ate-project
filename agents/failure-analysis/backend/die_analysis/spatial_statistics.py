"""Spatial statistics for die-level failure analytics."""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from typing import Any


def map_coordinates(die_points: list[dict[str, Any]]) -> dict[str, Any]:
    """Map die X/Y positions and classify edge vs center failures."""
    mapped = []
    coords = [(p["x"], p["y"]) for p in die_points if p.get("x") is not None and p.get("y") is not None]
    centroid = _centroid(coords)
    max_radius = _max_radius(coords, centroid) if coords else 1.0

    for point in die_points:
        x, y = point.get("x"), point.get("y")
        zone = "unknown"
        radius_ratio = None
        if x is not None and y is not None and centroid:
            cx, cy = centroid
            radius = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            radius_ratio = round(radius / max_radius, 4) if max_radius else 0.0
            if radius_ratio < 0.34:
                zone = "center"
            elif radius_ratio < 0.67:
                zone = "mid_radius"
            else:
                zone = "edge"

        mapped.append({**point, "zone": zone, "radius_ratio": radius_ratio})

    failing = [p for p in mapped if p.get("is_failing")]
    zone_counts = Counter(p.get("zone", "unknown") for p in failing)

    return {
        "mapped_points": mapped,
        "centroid": {"x": centroid[0], "y": centroid[1]} if centroid else None,
        "max_radius": round(max_radius, 4),
        "edge_failures": zone_counts.get("edge", 0),
        "center_failures": zone_counts.get("center", 0),
        "mid_radius_failures": zone_counts.get("mid_radius", 0),
        "total_with_coordinates": len(coords),
    }


def compute_failure_density(
    die_points: list[dict[str, Any]],
    *,
    grid_resolution: int = 20,
) -> dict[str, Any]:
    """Grid-based failure density across wafer coordinates."""
    coords = [
        (p["x"], p["y"])
        for p in die_points
        if p.get("x") is not None and p.get("y") is not None
    ]
    if not coords:
        return {"grid": [], "max_density": 0.0, "mean_density": 0.0}

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    x_span = max(x_max - x_min, 1)
    y_span = max(y_max - y_min, 1)

    failing_set = {
        (p["x"], p["y"])
        for p in die_points
        if p.get("is_failing") and p.get("x") is not None and p.get("y") is not None
    }

    grid: list[dict[str, Any]] = []
    densities: list[float] = []
    for i in range(grid_resolution):
        for j in range(grid_resolution):
            cell_x = x_min + (i + 0.5) * x_span / grid_resolution
            cell_y = y_min + (j + 0.5) * y_span / grid_resolution
            dies_in_cell = sum(
                1
                for x, y in coords
                if x_min + i * x_span / grid_resolution <= x < x_min + (i + 1) * x_span / grid_resolution
                and y_min + j * y_span / grid_resolution <= y < y_min + (j + 1) * y_span / grid_resolution
            )
            fails_in_cell = sum(
                1
                for x, y in failing_set
                if x_min + i * x_span / grid_resolution <= x < x_min + (i + 1) * x_span / grid_resolution
                and y_min + j * y_span / grid_resolution <= y < y_min + (j + 1) * y_span / grid_resolution
            )
            density = fails_in_cell / dies_in_cell if dies_in_cell else 0.0
            densities.append(density)
            grid.append(
                {
                    "x": round(cell_x, 3),
                    "y": round(cell_y, 3),
                    "die_count": dies_in_cell,
                    "failure_count": fails_in_cell,
                    "density": round(density, 4),
                }
            )

    return {
        "grid": grid,
        "max_density": round(max(densities), 4) if densities else 0.0,
        "mean_density": round(statistics.mean(densities), 4) if densities else 0.0,
        "bounds": {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max},
    }


def neighbor_analysis(
    die_points: list[dict[str, Any]],
    *,
    k: int = 5,
) -> dict[str, Any]:
    """KDTree neighbor analysis for failing die clusters."""
    points = [
        (float(p["x"]), float(p["y"]))
        for p in die_points
        if p.get("x") is not None and p.get("y") is not None
    ]
    failing_flags = [
        bool(p.get("is_failing"))
        for p in die_points
        if p.get("x") is not None and p.get("y") is not None
    ]

    if len(points) < k + 1:
        return {"neighbor_fail_rate": 0.0, "high_neighbor_dies": [], "method": "insufficient_data"}

    try:
        from scipy.spatial import KDTree

        tree = KDTree(points)
        high_neighbor: list[dict[str, Any]] = []
        neighbor_rates: list[float] = []

        for idx, point in enumerate(points):
            _, indices = tree.query(point, k=min(k + 1, len(points)))
            neighbor_idxs = [int(i) for i in indices if int(i) != idx][:k]
            if not neighbor_idxs:
                continue
            fail_neighbors = sum(1 for ni in neighbor_idxs if failing_flags[ni])
            rate = fail_neighbors / len(neighbor_idxs)
            neighbor_rates.append(rate)
            if failing_flags[idx] and rate >= 0.5:
                high_neighbor.append(
                    {
                        "x": point[0],
                        "y": point[1],
                        "neighbor_failure_rate": round(rate, 4),
                    }
                )

        return {
            "neighbor_fail_rate": round(statistics.mean(neighbor_rates), 4) if neighbor_rates else 0.0,
            "high_neighbor_dies": high_neighbor[:50],
            "k": k,
            "method": "kdtree",
        }
    except ImportError:
        return {"neighbor_fail_rate": 0.0, "high_neighbor_dies": [], "method": "unavailable"}


def pattern_density_by_zone(
    die_profiles: list[dict[str, Any]],
    coordinate_map: dict[str, Any],
) -> dict[str, Any]:
    """Pattern density breakdown by spatial zone."""
    zone_patterns: dict[str, Counter[str]] = defaultdict(Counter)
    point_lookup = {
        (p.get("die_id"), p.get("wafer_id")): p.get("zone", "unknown")
        for p in coordinate_map.get("mapped_points", [])
    }

    for profile in die_profiles:
        if not profile.get("is_failing_die"):
            continue
        zone = point_lookup.get((profile.get("die_id"), profile.get("wafer_id")), "unknown")
        for pattern in profile.get("failing_patterns", []):
            zone_patterns[zone][pattern] += 1

    return {
        zone: [{"pattern_id": p, "count": c} for p, c in counter.most_common(10)]
        for zone, counter in zone_patterns.items()
    }


def yield_distribution(die_profiles: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-wafer and overall yield distribution."""
    by_wafer: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "failing": 0})
    for profile in die_profiles:
        wafer = profile.get("wafer_id", "UNKNOWN")
        by_wafer[wafer]["total"] += 1
        if profile.get("is_failing_die"):
            by_wafer[wafer]["failing"] += 1

    wafers = []
    for wafer_id, counts in sorted(by_wafer.items()):
        total = counts["total"]
        failing = counts["failing"]
        yield_pct = round(100.0 * (total - failing) / total, 4) if total else 100.0
        wafers.append(
            {
                "wafer_id": wafer_id,
                "total_dies": total,
                "failing_dies": failing,
                "yield_pct": yield_pct,
            }
        )

    total_dies = sum(w["total_dies"] for w in wafers)
    total_failing = sum(w["failing_dies"] for w in wafers)
    overall_yield = round(100.0 * (total_dies - total_failing) / total_dies, 4) if total_dies else 100.0

    return {
        "overall_yield_pct": overall_yield,
        "wafer_yield_distribution": wafers,
        "wafer_count": len(wafers),
    }


def _centroid(coords: list[tuple[int | float, int | float]]) -> tuple[float, float] | None:
    if not coords:
        return None
    return (sum(x for x, _ in coords) / len(coords), sum(y for _, y in coords) / len(coords))


def _max_radius(
    coords: list[tuple[int | float, int | float]],
    centroid: tuple[float, float],
) -> float:
    cx, cy = centroid
    return max(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for x, y in coords) or 1.0
