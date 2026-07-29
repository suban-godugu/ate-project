"""Clustering algorithms for failure pattern grouping."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SKLEARN_AVAILABLE = False


def build_feature_matrix(
    failures: list[dict[str, Any]],
    *,
    pattern_index: dict[str, int],
) -> tuple[np.ndarray, list[str]]:
    """One row per failure occurrence with encoded categorical features."""
    rows: list[list[float]] = []
    pattern_ids: list[str] = []
    lot_index: dict[str, int] = {}
    wafer_index: dict[str, int] = {}
    lot_counter = 0
    wafer_counter = 0

    for row in failures:
        pid = str(row.get("pattern_id", "UNKNOWN"))
        pattern_ids.append(pid)
        lot = str(row.get("lot_id", ""))
        wafer = f"{row.get('lot_id', '')}|{row.get('wafer_id', '')}"
        if lot not in lot_index:
            lot_index[lot] = lot_counter
            lot_counter += 1
        if wafer not in wafer_index:
            wafer_index[wafer] = wafer_counter
            wafer_counter += 1
        rows.append(
            [
                float(pattern_index.get(pid, 0)),
                float(lot_index[lot]),
                float(wafer_index[wafer]),
                float(row.get("confidence", 0.0) or 0.0),
                1.0 if row.get("is_inferred") else 0.0,
            ]
        )
    return np.array(rows, dtype=float), pattern_ids


def run_clustering(
    failures: list[dict[str, Any]],
    *,
    dbscan_eps: float = 0.45,
    min_cluster_size: int = 2,
    contamination: float = 0.05,
) -> dict[str, Any]:
    """DBSCAN + KMeans fallback + IsolationForest anomaly flags."""
    if not failures:
        return {"clusters": [], "anomalies": [], "labels": []}
    if not SKLEARN_AVAILABLE:
        return _fallback_clustering(failures)

    pattern_index = {pid: idx for idx, pid in enumerate(sorted({str(r.get('pattern_id', '')) for r in failures}))}
    matrix, pattern_ids = build_feature_matrix(failures, pattern_index=pattern_index)
    if matrix.shape[0] < 2:
        return {
            "clusters": [{"cluster_id": 0, "pattern_ids": list(set(pattern_ids)), "size": len(pattern_ids)}],
            "anomalies": [],
            "labels": [0] * len(pattern_ids),
        }

    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    dbscan = DBSCAN(eps=dbscan_eps, min_samples=min_cluster_size)
    labels = dbscan.fit_predict(scaled)
    if (labels >= 0).sum() == 0:
        k = min(3, len(failures))
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(scaled)

    clusters = _summarize_clusters(pattern_ids, labels)
    anomalies: list[str] = []
    if len(scaled) >= 5:
        iso = IsolationForest(contamination=min(contamination, 0.49), random_state=42)
        preds = iso.fit_predict(scaled)
        anomalies = [pattern_ids[i] for i, p in enumerate(preds) if p == -1]

    return {"clusters": clusters, "anomalies": sorted(set(anomalies)), "labels": labels.tolist()}


def _summarize_clusters(pattern_ids: list[str], labels: np.ndarray) -> list[dict[str, Any]]:
    buckets: dict[int, list[str]] = {}
    for pid, label in zip(pattern_ids, labels):
        buckets.setdefault(int(label), []).append(pid)
    clusters: list[dict[str, Any]] = []
    for cluster_id, members in sorted(buckets.items()):
        unique = sorted(set(members))
        clusters.append(
            {
                "cluster_id": cluster_id,
                "pattern_ids": unique,
                "size": len(members),
                "dominant_pattern": max(set(members), key=members.count),
            }
        )
    clusters.sort(key=lambda c: c["size"], reverse=True)
    return clusters


def _fallback_clustering(failures: list[dict[str, Any]]) -> dict[str, Any]:
    by_pattern: dict[str, int] = {}
    for row in failures:
        pid = str(row.get("pattern_id", "UNKNOWN"))
        by_pattern[pid] = by_pattern.get(pid, 0) + 1
    clusters = [
        {"cluster_id": idx, "pattern_ids": [pid], "size": count, "dominant_pattern": pid}
        for idx, (pid, count) in enumerate(sorted(by_pattern.items(), key=lambda x: -x[1]))
    ]
    return {"clusters": clusters, "anomalies": [], "labels": list(range(len(failures)))}
