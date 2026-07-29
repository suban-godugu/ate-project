"""DBSCAN clustering for recurring failure signatures."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SKLEARN_AVAILABLE = False


def cluster_recurring_failures(
    failure_rows: list[dict[str, Any]],
    *,
    eps: float = 0.45,
    min_samples: int = 2,
) -> dict[str, Any]:
    """Cluster failure occurrences to surface recurring signature groups."""
    if not failure_rows or not SKLEARN_AVAILABLE:
        return {
            "cluster_count": 0,
            "noise_count": len(failure_rows),
            "clusters": [],
            "method": "unavailable" if not SKLEARN_AVAILABLE else "insufficient_data",
        }

    matrix, row_keys, encoders = _build_matrix(failure_rows)
    if matrix.shape[0] < min_samples:
        return {
            "cluster_count": 0,
            "noise_count": len(failure_rows),
            "clusters": [],
            "method": "insufficient_data",
        }

    scaled = StandardScaler().fit_transform(matrix)
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(scaled)

    clusters: dict[int, list[str]] = {}
    for idx, label in enumerate(labels):
        clusters.setdefault(int(label), []).append(row_keys[idx])

    cluster_rows = []
    for label, members in sorted(clusters.items()):
        if label == -1:
            continue
        cluster_rows.append(
            {
                "cluster_id": label,
                "member_count": len(members),
                "members": members[:20],
                "is_recurring": len(members) >= min_samples,
            }
        )

    cluster_rows.sort(key=lambda c: c["member_count"], reverse=True)
    noise = len(clusters.get(-1, []))
    return {
        "cluster_count": len(cluster_rows),
        "noise_count": noise,
        "clusters": cluster_rows,
        "method": "dbscan",
        "eps": eps,
        "min_samples": min_samples,
        "encoders": {k: len(v) for k, v in encoders.items()},
    }


def _build_matrix(
    failure_rows: list[dict[str, Any]],
) -> tuple[np.ndarray, list[str], dict[str, dict[str, int]]]:
    encoders: dict[str, dict[str, int]] = {
        "pattern": {},
        "lot": {},
        "wafer": {},
        "device": {},
        "product": {},
        "tester": {},
    }
    rows: list[list[float]] = []
    keys: list[str] = []

    for row in failure_rows:
        keys.append(
            f"{row.get('lot_id')}|{row.get('wafer_id')}|{row.get('die_id')}|"
            f"{row.get('pattern_id')}"
        )
        rows.append(
            [
                float(_encode(encoders["pattern"], row.get("pattern_id", ""))),
                float(_encode(encoders["lot"], row.get("lot_id", ""))),
                float(_encode(encoders["wafer"], row.get("wafer_id", ""))),
                float(_encode(encoders["device"], row.get("device_id", ""))),
                float(_encode(encoders["product"], row.get("product_id", ""))),
                float(_encode(encoders["tester"], row.get("tester_id", ""))),
            ]
        )

    return np.array(rows, dtype=float), keys, encoders


def _encode(table: dict[str, int], value: str) -> int:
    key = str(value or "UNKNOWN")
    if key not in table:
        table[key] = len(table)
    return table[key]
