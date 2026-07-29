"""Hotspot detection for die-level spatial failures."""

from __future__ import annotations

from typing import Any


def detect_hotspots(
    density_report: dict[str, Any],
    *,
    threshold: float = 0.15,
    min_dies: int = 3,
) -> dict[str, Any]:
    """Identify high-density failure regions from the density grid."""
    grid = density_report.get("grid", [])
    hotspots = []

    for cell in grid:
        if cell.get("failure_count", 0) < min_dies:
            continue
        if cell.get("density", 0.0) < threshold:
            continue
        hotspots.append(
            {
                "hotspot_id": f"{cell['x']}_{cell['y']}",
                "x": cell["x"],
                "y": cell["y"],
                "density": cell["density"],
                "failure_count": cell["failure_count"],
                "die_count": cell["die_count"],
                "severity": _hotspot_severity(cell["density"], threshold),
            }
        )

    hotspots.sort(key=lambda h: (h["density"], h["failure_count"]), reverse=True)
    return {
        "hotspot_count": len(hotspots),
        "threshold": threshold,
        "min_dies": min_dies,
        "hotspots": hotspots[:50],
        "max_density": density_report.get("max_density", 0.0),
    }


def detect_ai_hotspots(
    die_points: list[dict[str, Any]],
    *,
    contamination: float = 0.05,
) -> dict[str, Any]:
    """Isolation Forest anomaly detection for spatial hotspots (AI-assisted)."""
    coords = [
        [float(p["x"]), float(p["y"])]
        for p in die_points
        if p.get("is_failing") and p.get("x") is not None and p.get("y") is not None
    ]
    if len(coords) < 5:
        return {"anomaly_count": 0, "anomalies": [], "method": "insufficient_data"}

    try:
        from sklearn.ensemble import IsolationForest
        import numpy as np

        model = IsolationForest(contamination=contamination, random_state=42)
        labels = model.fit_predict(np.array(coords))
        scores = model.decision_function(np.array(coords))

        anomalies = []
        failing_points = [
            p
            for p in die_points
            if p.get("is_failing") and p.get("x") is not None and p.get("y") is not None
        ]
        for idx, label in enumerate(labels):
            if label == -1:
                point = failing_points[idx]
                anomalies.append(
                    {
                        "die_id": point.get("die_id"),
                        "wafer_id": point.get("wafer_id"),
                        "x": point.get("x"),
                        "y": point.get("y"),
                        "anomaly_score": round(float(scores[idx]), 4),
                    }
                )

        anomalies.sort(key=lambda a: a["anomaly_score"])
        return {
            "anomaly_count": len(anomalies),
            "anomalies": anomalies[:50],
            "method": "isolation_forest",
            "contamination": contamination,
        }
    except ImportError:
        return {"anomaly_count": 0, "anomalies": [], "method": "unavailable"}


def _hotspot_severity(density: float, threshold: float) -> str:
    if density >= threshold * 3:
        return "critical"
    if density >= threshold * 2:
        return "high"
    if density >= threshold:
        return "medium"
    return "low"
