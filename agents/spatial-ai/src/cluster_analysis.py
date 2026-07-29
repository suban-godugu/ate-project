"""
Spatial defect cluster detection for WaferVision-AI.

Pure post-processing over die extraction outputs (FAIL dies only).
Uses 8-connected component analysis (BFS). Does not invoke prediction,
Grad-CAM, or grid detection.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Mapping, Sequence

logger = logging.getLogger(__name__)

TOP_N_CLUSTERS = 20

# Severity score cutoffs (adaptive % scale — not absolute die counts).
_SEVERITY_LEVELS: tuple[tuple[float, str], ...] = (
    (0.50, "Very Low"),
    (1.50, "Low"),
    (3.00, "Medium"),
    (6.00, "High"),
)


class ClusterAnalysisError(Exception):
    """Raised when cluster analysis cannot be completed."""


def _is_fail(die: Mapping[str, Any]) -> bool:
    return str(die.get("status", "")).upper() == "FAIL"


def _is_good(die: Mapping[str, Any]) -> bool:
    return str(die.get("status", "")).upper() == "GOOD"


def severity_label(score: float) -> str:
    """Map severity_score to adaptive severity level."""
    for threshold, label in _SEVERITY_LEVELS:
        if score <= threshold:
            return label
    return "Critical"


def _die_key(die: Mapping[str, Any]) -> tuple[int, int]:
    return int(die["row"]), int(die["column"])


def _neighbor_keys(row: int, col: int) -> list[tuple[int, int]]:
    """8-connected neighbourhood."""
    out: list[tuple[int, int]] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            out.append((row + dr, col + dc))
    return out


def _connected_fail_components(
    fail_dies: Sequence[Mapping[str, Any]],
) -> list[list[Mapping[str, Any]]]:
    """BFS over FAIL dies using 8-connectivity on the die grid."""
    by_key = {_die_key(d): d for d in fail_dies}
    visited: set[tuple[int, int]] = set()
    components: list[list[Mapping[str, Any]]] = []

    for seed_key, seed_die in by_key.items():
        if seed_key in visited:
            continue
        queue: deque[tuple[int, int]] = deque([seed_key])
        visited.add(seed_key)
        members: list[Mapping[str, Any]] = []
        while queue:
            key = queue.popleft()
            members.append(by_key[key])
            r, c = key
            for nbr in _neighbor_keys(r, c):
                if nbr in by_key and nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
        components.append(members)

    return components


def _bbox_from_dies(
    members: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    xs: list[int] = []
    ys: list[int] = []
    for die in members:
        bbox = die.get("bbox")
        if isinstance(bbox, Mapping):
            xs.extend([int(bbox["x0"]), int(bbox["x1"])])
            ys.extend([int(bbox["y0"]), int(bbox["y1"])])
        else:
            xs.append(int(die["x"]))
            ys.append(int(die["y"]))
    return {
        "x1": int(min(xs)),
        "y1": int(min(ys)),
        "x2": int(max(xs)),
        "y2": int(max(ys)),
    }


def _point_in_bbox(x: float, y: float, box: Mapping[str, int]) -> bool:
    return box["x1"] <= x <= box["x2"] and box["y1"] <= y <= box["y2"]


def _build_cluster_record(
    members: Sequence[Mapping[str, Any]],
    all_dies: Sequence[Mapping[str, Any]],
    *,
    wafer_total_dies: int,
    wafer_fail_dies: int,
) -> dict[str, Any]:
    fail_count = len(members)
    rows = [int(d["row"]) for d in members]
    cols = [int(d["column"]) for d in members]
    cluster_area = max(1, (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1))

    box = _bbox_from_dies(members)
    good_in_box = 0
    fail_in_box = 0
    for die in all_dies:
        if not _point_in_bbox(float(die["x"]), float(die["y"]), box):
            continue
        if _is_good(die):
            good_in_box += 1
        elif _is_fail(die):
            fail_in_box += 1

    # Prefer FAIL member count for core metrics; bbox GOOD for context.
    cluster_fail_dies = fail_count
    good_dies = int(good_in_box)
    total_dies = int(good_in_box + fail_in_box)

    center_x = float(sum(int(d["x"]) for d in members) / fail_count)
    center_y = float(sum(int(d["y"]) for d in members) / fail_count)

    wafer_total = max(1, int(wafer_total_dies))
    wafer_fail = max(1, int(wafer_fail_dies)) if wafer_fail_dies > 0 else 1

    cluster_fail_percent = (cluster_fail_dies / wafer_total) * 100.0
    contribution_percent = (cluster_fail_dies / wafer_fail) * 100.0
    cluster_density = cluster_fail_dies / float(cluster_area)

    severity_score = (
        0.50 * cluster_fail_percent
        + 0.30 * cluster_density
        + 0.20 * contribution_percent
    )

    return {
        "cluster_id": "",  # assigned after sort
        "good_dies": good_dies,
        "fail_dies": int(cluster_fail_dies),
        "total_dies": total_dies if total_dies > 0 else int(cluster_fail_dies),
        "member_die_ids": [int(d["die_id"]) for d in members],
        "center_x": round(center_x, 4),
        "center_y": round(center_y, 4),
        "bounding_box": box,
        "cluster_area": int(cluster_area),
        "cluster_density": round(float(cluster_density), 6),
        "cluster_fail_percent": round(float(cluster_fail_percent), 4),
        "contribution_percent": round(float(contribution_percent), 4),
        "severity_score": round(float(severity_score), 4),
        "severity": severity_label(severity_score),
        "rank": 0,
    }


def _sort_key(cluster: Mapping[str, Any]) -> tuple[float, float, float, int, int]:
    return (
        -float(cluster["severity_score"]),
        -float(cluster["cluster_fail_percent"]),
        -float(cluster["cluster_density"]),
        -int(cluster["cluster_area"]),
        -int(cluster["fail_dies"]),
    )


def detect_defect_clusters(
    dies: Sequence[Mapping[str, Any]],
    yield_summary: Mapping[str, Any] | None = None,
    *,
    top_n: int = TOP_N_CLUSTERS,
) -> dict[str, Any]:
    """
    Detect FAIL-die clusters via 8-connected BFS and return top-N by severity.

    Args:
        dies: Die records from ``dice_analysis`` (statuses treated as SoT).
        yield_summary: Optional yield block; used for wafer totals when present.
        top_n: Maximum clusters to return after ranking.

    Returns:
        ``{"cluster_summary": {...}, "clusters": [...]}``
    """
    if not dies:
        raise ClusterAnalysisError("No dies available for cluster analysis.")

    if yield_summary:
        wafer_total = int(yield_summary.get("total_dies") or len(dies))
        wafer_fail = int(yield_summary.get("fail_dies") or 0)
    else:
        wafer_total = len(dies)
        wafer_fail = sum(1 for d in dies if _is_fail(d))

    if wafer_fail == 0:
        return {
            "cluster_summary": {
                "total_clusters_detected": 0,
                "displayed_clusters": 0,
                "critical_clusters": 0,
                "largest_cluster_fail_dies": 0,
                "highest_severity_score": 0.0,
            },
            "clusters": [],
        }

    fail_dies = [d for d in dies if _is_fail(d)]
    components = _connected_fail_components(fail_dies)

    all_clusters = [
        _build_cluster_record(
            members,
            dies,
            wafer_total_dies=wafer_total,
            wafer_fail_dies=wafer_fail,
        )
        for members in components
    ]
    all_clusters.sort(key=_sort_key)

    displayed = all_clusters[: max(0, int(top_n))]
    for index, cluster in enumerate(displayed, start=1):
        cluster["rank"] = index
        cluster["cluster_id"] = f"C{index:03d}"

    critical = sum(1 for c in displayed if c["severity"] == "Critical")
    largest = max((int(c["fail_dies"]) for c in all_clusters), default=0)
    highest = max((float(c["severity_score"]) for c in all_clusters), default=0.0)

    return {
        "cluster_summary": {
            "total_clusters_detected": len(all_clusters),
            "displayed_clusters": len(displayed),
            "critical_clusters": int(critical),
            "largest_cluster_fail_dies": int(largest),
            "highest_severity_score": round(float(highest), 4),
        },
        "clusters": displayed,
    }


def run_cluster_analysis(
    dies: Sequence[Mapping[str, Any]],
    yield_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Public entry used by the master pipeline."""
    return detect_defect_clusters(dies, yield_summary)


__all__ = [
    "ClusterAnalysisError",
    "TOP_N_CLUSTERS",
    "detect_defect_clusters",
    "run_cluster_analysis",
    "severity_label",
]
