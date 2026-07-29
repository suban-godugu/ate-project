"""Edge and center failure analysis for wafers."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


def analyze_edge_center(
    spatial_map: list[dict[str, Any]],
    *,
    edge_radius_ratio: float = 0.67,
    center_radius_ratio: float = 0.34,
) -> dict[str, Any]:
    """Classify failing dies as edge, mid-radius, or center."""
    by_wafer: dict[str, list[dict[str, Any]]] = {}
    for point in spatial_map:
        if point.get("x") is None or point.get("y") is None:
            continue
        by_wafer.setdefault(point["wafer_id"], []).append(point)

    per_wafer = []
    global_zones: Counter[str] = Counter()

    for wafer_id, points in sorted(by_wafer.items()):
        coords = [(p["x"], p["y"]) for p in points]
        cx = sum(x for x, _ in coords) / len(coords)
        cy = sum(y for _, y in coords) / len(coords)
        max_r = max(math.sqrt((x - cx) ** 2 + (y - cy) ** 2) for x, y in coords) or 1.0

        zones: Counter[str] = Counter()
        for p in points:
            if not p.get("is_failing"):
                continue
            r = math.sqrt((p["x"] - cx) ** 2 + (p["y"] - cy) ** 2) / max_r
            if r < center_radius_ratio:
                zone = "center"
            elif r < edge_radius_ratio:
                zone = "mid_radius"
            else:
                zone = "edge"
            zones[zone] += 1
            global_zones[zone] += 1

        total_failing = sum(zones.values())
        per_wafer.append(
            {
                "wafer_id": wafer_id,
                "centroid": {"x": round(cx, 3), "y": round(cy, 3)},
                "edge_failures": zones.get("edge", 0),
                "center_failures": zones.get("center", 0),
                "mid_radius_failures": zones.get("mid_radius", 0),
                "dominant_zone": zones.most_common(1)[0][0] if zones else "none",
                "edge_pct": round(100.0 * zones.get("edge", 0) / total_failing, 2)
                if total_failing
                else 0.0,
                "center_pct": round(100.0 * zones.get("center", 0) / total_failing, 2)
                if total_failing
                else 0.0,
            }
        )

    return {
        "per_wafer": per_wafer,
        "global_edge_failures": global_zones.get("edge", 0),
        "global_center_failures": global_zones.get("center", 0),
        "global_mid_radius_failures": global_zones.get("mid_radius", 0),
    }


def detect_radial_defects(
    edge_center: dict[str, Any],
    *,
    edge_threshold_pct: float = 50.0,
) -> list[dict[str, Any]]:
    """Flag wafers with dominant edge or center radial patterns."""
    defects = []
    for wafer in edge_center.get("per_wafer", []):
        if wafer["edge_pct"] >= edge_threshold_pct:
            defects.append(
                {
                    "wafer_id": wafer["wafer_id"],
                    "defect_type": "edge_dominant",
                    "edge_pct": wafer["edge_pct"],
                    "message": f"Edge failures dominate at {wafer['edge_pct']:.1f}%",
                }
            )
        elif wafer["center_pct"] >= edge_threshold_pct:
            defects.append(
                {
                    "wafer_id": wafer["wafer_id"],
                    "defect_type": "center_dominant",
                    "center_pct": wafer["center_pct"],
                    "message": f"Center failures dominate at {wafer['center_pct']:.1f}%",
                }
            )
    return defects
