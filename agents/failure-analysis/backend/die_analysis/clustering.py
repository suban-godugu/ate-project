"""DBSCAN spatial clustering for die failures."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from sklearn.cluster import DBSCAN

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SKLEARN_AVAILABLE = False


def cluster_die_failures(
    die_points: list[dict[str, Any]],
    *,
    eps: float = 2.5,
    min_samples: int = 3,
) -> dict[str, Any]:
    """Detect spatial clusters of failing dies using DBSCAN."""
    failing = [
        p
        for p in die_points
        if p.get("is_failing") and p.get("x") is not None and p.get("y") is not None
    ]
    if not failing or not SKLEARN_AVAILABLE:
        return {
            "cluster_count": 0,
            "noise_count": len(failing),
            "clusters": [],
            "method": "unavailable" if not SKLEARN_AVAILABLE else "insufficient_data",
        }

    coords = np.array([[float(p["x"]), float(p["y"])] for p in failing])
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(coords)

    clusters: dict[int, list[dict[str, Any]]] = {}
    noise = 0
    for idx, label in enumerate(labels):
        label_int = int(label)
        if label_int == -1:
            noise += 1
            continue
        clusters.setdefault(label_int, []).append(failing[idx])

    cluster_rows = []
    for cluster_id, members in sorted(clusters.items()):
        xs = [m["x"] for m in members]
        ys = [m["y"] for m in members]
        cluster_rows.append(
            {
                "cluster_id": cluster_id,
                "member_count": len(members),
                "centroid": {
                    "x": round(sum(xs) / len(xs), 3),
                    "y": round(sum(ys) / len(ys), 3),
                },
                "dies": [
                    {
                        "die_id": m.get("die_id"),
                        "wafer_id": m.get("wafer_id"),
                        "x": m.get("x"),
                        "y": m.get("y"),
                    }
                    for m in members[:20]
                ],
            }
        )

    cluster_rows.sort(key=lambda c: c["member_count"], reverse=True)
    return {
        "cluster_count": len(cluster_rows),
        "noise_count": noise,
        "clusters": cluster_rows,
        "method": "dbscan",
        "eps": eps,
        "min_samples": min_samples,
    }
