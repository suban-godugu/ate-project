"""Radial failure distribution analysis for wafers."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


def analyze_radial_distribution(
    spatial_map: list[dict[str, Any]],
    *,
    radial_bins: int = 8,
) -> dict[str, Any]:
    """Bin failing dies by normalized radial distance from wafer center."""
    by_wafer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in spatial_map:
        if point.get("x") is not None and point.get("y") is not None:
            by_wafer[point["wafer_id"]].append(point)

    per_wafer = []
    for wafer_id, points in sorted(by_wafer.items()):
        coords = [(p["x"], p["y"]) for p in points]
        cx = sum(x for x, _ in coords) / len(coords)
        cy = sum(y for _, y in coords) / len(coords)
        max_r = max(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for x, y in coords) or 1.0

        bins = [0] * radial_bins
        total_failing = 0
        for p in points:
            if not p.get("is_failing"):
                continue
            r_norm = math.sqrt((p["x"] - cx) ** 2 + (p["y"] - cy) ** 2) / max_r
            bin_idx = min(int(r_norm * radial_bins), radial_bins - 1)
            bins[bin_idx] += 1
            total_failing += 1

        radial_profile = [
            {
                "ring": i,
                "radius_min": round(i / radial_bins, 3),
                "radius_max": round((i + 1) / radial_bins, 3),
                "failure_count": bins[i],
                "failure_pct": round(100.0 * bins[i] / total_failing, 2) if total_failing else 0.0,
            }
            for i in range(radial_bins)
        ]

        peak_ring = max(range(radial_bins), key=lambda i: bins[i]) if total_failing else 0
        per_wafer.append(
            {
                "wafer_id": wafer_id,
                "centroid": {"x": round(cx, 3), "y": round(cy, 3)},
                "total_failing": total_failing,
                "radial_profile": radial_profile,
                "peak_ring": peak_ring,
                "pattern": _radial_pattern(radial_profile),
            }
        )

    return {
        "radial_bins": radial_bins,
        "per_wafer": per_wafer,
    }


def _radial_pattern(profile: list[dict[str, Any]]) -> str:
    if not profile:
        return "unknown"
    outer = sum(p["failure_count"] for p in profile[-2:])
    inner = sum(p["failure_count"] for p in profile[:2])
    total = sum(p["failure_count"] for p in profile)
    if total == 0:
        return "none"
    if outer > inner * 2:
        return "edge_ring"
    if inner > outer * 2:
        return "center_ring"
    return "uniform"
