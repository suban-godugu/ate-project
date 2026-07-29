"""Hotspot detection for wafer-level failures."""

from __future__ import annotations

from typing import Any


def detect_wafer_hotspots(
    density_by_wafer: dict[str, Any],
    *,
    threshold: float = 0.15,
    min_dies: int = 3,
) -> dict[str, Any]:
    """Detect hotspot regions per wafer from density grids."""
    all_hotspots: list[dict[str, Any]] = []
    per_wafer: dict[str, list[dict[str, Any]]] = {}

    for wafer_id, report in density_by_wafer.items():
        hotspots = []
        for cell in report.get("grid", []):
            if cell.get("failure_count", 0) < min_dies:
                continue
            if cell.get("density", 0.0) < threshold:
                continue
            hotspot = {
                "wafer_id": wafer_id,
                "x": cell["x"],
                "y": cell["y"],
                "density": cell["density"],
                "failure_count": cell["failure_count"],
                "severity": _severity(cell["density"], threshold),
            }
            hotspots.append(hotspot)
            all_hotspots.append(hotspot)

        hotspots.sort(key=lambda h: h["density"], reverse=True)
        per_wafer[wafer_id] = hotspots[:20]

    all_hotspots.sort(key=lambda h: (h["density"], h["failure_count"]), reverse=True)
    return {
        "hotspot_count": len(all_hotspots),
        "threshold": threshold,
        "per_wafer": per_wafer,
        "top_hotspots": all_hotspots[:50],
    }


def detect_ai_wafer_anomalies(
    spatial_map: list[dict[str, Any]],
    wafer_stats: list[dict[str, Any]],
    *,
    contamination: float = 0.05,
) -> dict[str, Any]:
    """Isolation Forest anomaly detection on wafer yield metrics."""
    if len(wafer_stats) < 3:
        return {"anomaly_count": 0, "anomalies": [], "method": "insufficient_data"}

    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np

        features = []
        wafer_ids = []
        for w in wafer_stats:
            features.append(
                [
                    w.get("failure_rate_pct", 0.0),
                    w.get("failing_dies", 0),
                    1.0 if w.get("is_outlier") else 0.0,
                ]
            )
            wafer_ids.append(w["wafer_id"])

        model = IsolationForest(contamination=contamination, random_state=42)
        labels = model.fit_predict(np.array(features))
        scores = model.decision_function(np.array(features))

        anomalies = []
        for idx, label in enumerate(labels):
            if label == -1:
                anomalies.append(
                    {
                        "wafer_id": wafer_ids[idx],
                        "anomaly_score": round(float(scores[idx]), 4),
                        "failure_rate_pct": wafer_stats[idx].get("failure_rate_pct"),
                    }
                )
        return {
            "anomaly_count": len(anomalies),
            "anomalies": anomalies,
            "method": "isolation_forest",
        }
    except ImportError:
        outliers = [w for w in wafer_stats if w.get("is_outlier")]
        return {
            "anomaly_count": len(outliers),
            "anomalies": [
                {"wafer_id": w["wafer_id"], "reason": w.get("outlier_reason", "")}
                for w in outliers
            ],
            "method": "statistical_outlier",
        }


def _severity(density: float, threshold: float) -> str:
    if density >= threshold * 3:
        return "critical"
    if density >= threshold * 2:
        return "high"
    return "medium"
