"""
Engineering zone analysis for WaferVision-AI.

Partitions dies into Center / Edge / four quadrants using wafer_geometry.
Pure post-processing — does not alter die statuses or earlier pipeline outputs.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Mapping, Sequence

logger = logging.getLogger(__name__)

ZONE_NAMES: tuple[str, ...] = (
    "Center",
    "Edge",
    "Upper Left",
    "Upper Right",
    "Lower Left",
    "Lower Right",
)

# Radial thresholds relative to wafer radius (adaptive to auto/manual grids).
CENTER_RADIUS_RATIO = 0.50
EDGE_RADIUS_RATIO = 0.85


class ZoneAnalysisError(Exception):
    """Raised when zone analysis cannot be completed."""


def _is_fail(die: Mapping[str, Any]) -> bool:
    return str(die.get("status", "")).upper() == "FAIL"


def _is_good(die: Mapping[str, Any]) -> bool:
    return str(die.get("status", "")).upper() == "GOOD"


def _defect_density_label(fail_percent: float) -> str:
    if fail_percent > 5.0:
        return "High"
    if fail_percent > 2.0:
        return "Medium"
    return "Low"


def _zone_status(fail_percent: float) -> str:
    if fail_percent <= 2.0:
        return "Normal"
    if fail_percent <= 5.0:
        return "Warning"
    return "Critical"


def assign_die_zone(
    die: Mapping[str, Any],
    geometry: Mapping[str, Any],
) -> str:
    """
    Exclusive zone assignment for one die.

    Priority: Center → Edge → quadrant (image coords: y increases downward).
    """
    cx = float(geometry["center_x"])
    cy = float(geometry["center_y"])
    radius = float(geometry["radius"])
    if radius <= 0:
        raise ZoneAnalysisError("wafer_geometry.radius must be positive.")

    x = float(die["x"])
    y = float(die["y"])
    dx = x - cx
    dy = y - cy
    r = math.hypot(dx, dy)

    if r <= CENTER_RADIUS_RATIO * radius:
        return "Center"
    if r >= EDGE_RADIUS_RATIO * radius:
        return "Edge"

    # Quadrants (Upper = smaller y in image coordinates)
    if dx < 0 and dy < 0:
        return "Upper Left"
    if dx >= 0 and dy < 0:
        return "Upper Right"
    if dx < 0 and dy >= 0:
        return "Lower Left"
    return "Lower Right"


def _zone_boundary_polygon(
    zone: str,
    geometry: Mapping[str, Any],
    *,
    segments: int = 48,
) -> list[dict[str, float]]:
    """Approximate polygonal boundary for UI highlighting."""
    cx = float(geometry["center_x"])
    cy = float(geometry["center_y"])
    radius = float(geometry["radius"])
    r_center = CENTER_RADIUS_RATIO * radius
    r_edge = EDGE_RADIUS_RATIO * radius

    def arc(r: float, a0: float, a1: float) -> list[dict[str, float]]:
        pts: list[dict[str, float]] = []
        for i in range(segments + 1):
            t = a0 + (a1 - a0) * (i / segments)
            pts.append(
                {
                    "x": round(cx + r * math.cos(t), 4),
                    "y": round(cy + r * math.sin(t), 4),
                }
            )
        return pts

    # Image space: 0=right, π/2=down in standard math with y-down screen coords
    # Use math angles relative to +x; upper half is negative y → angle ≈ -π/2.
    if zone == "Center":
        return arc(r_center, 0.0, 2.0 * math.pi)

    if zone == "Edge":
        outer = arc(radius, 0.0, 2.0 * math.pi)
        inner = list(reversed(arc(r_edge, 0.0, 2.0 * math.pi)))
        return outer + inner

    # Quadrant wedges between center ring and edge ring.
    angles = {
        "Upper Left": (math.pi, 1.5 * math.pi),
        "Upper Right": (1.5 * math.pi, 2.0 * math.pi),
        "Lower Right": (0.0, 0.5 * math.pi),
        "Lower Left": (0.5 * math.pi, math.pi),
    }
    a0, a1 = angles[zone]
    outer = arc(r_edge, a0, a1)
    inner = list(reversed(arc(r_center, a0, a1)))
    return outer + inner


def analyze_engineering_zones(
    dies: Sequence[Mapping[str, Any]],
    wafer_geometry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """
    Compute per-zone yield / fail metrics and rank by fail severity.

    Args:
        dies: Die records from the pipeline (GOOD/FAIL as SoT).
        wafer_geometry: ``center_x``, ``center_y``, ``radius``.

    Returns:
        Sorted list of zone dictionaries.
    """
    if not dies:
        raise ZoneAnalysisError("No dies available for zone analysis.")
    if not wafer_geometry:
        raise ZoneAnalysisError("wafer_geometry is required for zone analysis.")

    required = ("center_x", "center_y", "radius")
    missing = [k for k in required if k not in wafer_geometry]
    if missing:
        raise ZoneAnalysisError(
            f"wafer_geometry missing required keys: {', '.join(missing)}"
        )

    buckets: dict[str, list[Mapping[str, Any]]] = {name: [] for name in ZONE_NAMES}
    for die in dies:
        zone = assign_die_zone(die, wafer_geometry)
        buckets[zone].append(die)

    records: list[dict[str, Any]] = []
    for zone in ZONE_NAMES:
        members = buckets[zone]
        total = len(members)
        good = sum(1 for d in members if _is_good(d))
        fail = sum(1 for d in members if _is_fail(d))
        if total > 0:
            yield_percent = (good / total) * 100.0
            fail_percent = (fail / total) * 100.0
        else:
            yield_percent = 0.0
            fail_percent = 0.0

        records.append(
            {
                "zone": zone,
                "good_dies": int(good),
                "fail_dies": int(fail),
                "total_dies": int(total),
                "yield_percent": round(float(yield_percent), 4),
                "fail_percent": round(float(fail_percent), 4),
                "defect_density": _defect_density_label(fail_percent),
                "rank": 0,
                "status": _zone_status(fail_percent),
                "zone_boundary": _zone_boundary_polygon(zone, wafer_geometry),
            }
        )

    records.sort(
        key=lambda z: (
            -float(z["fail_percent"]),
            # Density tie-break: High > Medium > Low
            -{"High": 3, "Medium": 2, "Low": 1}.get(str(z["defect_density"]), 0),
            -int(z["fail_dies"]),
        )
    )
    for index, zone in enumerate(records, start=1):
        zone["rank"] = index

    return records


def run_zone_analysis(
    dies: Sequence[Mapping[str, Any]],
    wafer_geometry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Public entry used by the master pipeline."""
    return analyze_engineering_zones(dies, wafer_geometry)


__all__ = [
    "ZoneAnalysisError",
    "ZONE_NAMES",
    "CENTER_RADIUS_RATIO",
    "EDGE_RADIUS_RATIO",
    "assign_die_zone",
    "analyze_engineering_zones",
    "run_zone_analysis",
]
