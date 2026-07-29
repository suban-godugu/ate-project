"""DBSCAN cluster detection for wafer-level failures."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np

try:
    from sklearn.cluster import DBSCAN

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SKLEARN_AVAILABLE = False


def detect_wafer_clusters(
    spatial_map: list[dict[str, Any]],
    *,
    eps: float = 2.5,
    min_samples: int = 3,
) -> dict[str, Any]:
    """Detect failure clusters per wafer using DBSCAN."""
    by_wafer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in spatial_map:
        if point.get("is_failing") and point.get("x") is not None and point.get("y") is not None:
            by_wafer[point["wafer_id"]].append(point)

    all_clusters: list[dict[str, Any]] = []
    per_wafer: dict[str, list[dict[str, Any]]] = {}

    for wafer_id, points in sorted(by_wafer.items()):
        if not SKLEARN_AVAILABLE or len(points) < min_samples:
            per_wafer[wafer_id] = []
            continue

        coords = np.array([[float(p["x"]), float(p["y"])] for p in points])
        labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(coords)

        clusters: dict[int, list[dict[str, Any]]] = defaultdict(list)
        noise = 0
        for idx, label in enumerate(labels):
            if int(label) == -1:
                noise += 1
            else:
                clusters[int(label)].append(points[idx])

        wafer_clusters = []
        for cluster_id, members in sorted(clusters.items()):
            xs = [m["x"] for m in members]
            ys = [m["y"] for m in members]
            row = {
                "wafer_id": wafer_id,
                "cluster_id": cluster_id,
                "member_count": len(members),
                "centroid": {"x": round(sum(xs) / len(xs), 3), "y": round(sum(ys) / len(ys), 3)},
                "dies": [
                    {"die_id": m["die_id"], "x": m["x"], "y": m["y"]} for m in members[:15]
                ],
            }
            wafer_clusters.append(row)
            all_clusters.append(row)

        wafer_clusters.sort(key=lambda c: c["member_count"], reverse=True)
        per_wafer[wafer_id] = wafer_clusters

    all_clusters.sort(key=lambda c: c["member_count"], reverse=True)
    return {
        "cluster_count": len(all_clusters),
        "per_wafer": per_wafer,
        "top_clusters": all_clusters[:30],
        "method": "dbscan" if SKLEARN_AVAILABLE else "unavailable",
        "eps": eps,
        "min_samples": min_samples,
    }
