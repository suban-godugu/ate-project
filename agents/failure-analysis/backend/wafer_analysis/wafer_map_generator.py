"""Wafer map generation separated from analytics engine."""

from __future__ import annotations

from typing import Any


def generate_wafer_maps(
    spatial_map: list[dict[str, Any]],
    density_by_wafer: dict[str, Any],
    *,
    hotspots: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate per-wafer heatmaps and pass/fail maps."""
    by_wafer: dict[str, dict[str, list]] = {}
    for point in spatial_map:
        wafer_id = point.get("wafer_id", "UNKNOWN")
        bucket = by_wafer.setdefault(wafer_id, {"pass": [], "fail": []})
        entry = {
            "x": point.get("x"),
            "y": point.get("y"),
            "die_id": point.get("die_id"),
            "intensity": point.get("intensity", 0.0),
        }
        if point.get("is_failing"):
            bucket["fail"].append(entry)
        else:
            bucket["pass"].append(entry)

    wafer_maps = []
    for wafer_id, buckets in sorted(by_wafer.items()):
        density = density_by_wafer.get(wafer_id, {})
        wafer_maps.append(
            {
                "wafer_id": wafer_id,
                "pass_dies": buckets["pass"],
                "fail_dies": buckets["fail"],
                "density_grid": density.get("grid", []),
                "max_density": density.get("max_density", 0.0),
                "hotspots": (hotspots or {}).get("per_wafer", {}).get(wafer_id, []),
            }
        )

    return {
        "wafer_maps": wafer_maps,
        "wafer_count": len(wafer_maps),
        "plotly_ready": _plotly_payload(wafer_maps),
        "matplotlib_ready": {
            "wafers": [
                {
                    "wafer_id": m["wafer_id"],
                    "fail_x": [p["x"] for p in m["fail_dies"] if p["x"] is not None],
                    "fail_y": [p["y"] for p in m["fail_dies"] if p["y"] is not None],
                }
                for m in wafer_maps
            ]
        },
    }


def build_engineering_dashboard(
    *,
    aggregation: dict[str, Any],
    edge_center: dict[str, Any],
    radial: dict[str, Any],
    hotspots: dict[str, Any],
    clusters: dict[str, Any],
    bin_dist: dict[str, Any],
    anomalies: dict[str, Any],
    legacy_alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Engineering-ready wafer dashboard dataset."""
    wafers = aggregation.get("wafer_statistics", [])
    worst = sorted(wafers, key=lambda w: w.get("failure_rate_pct", 0), reverse=True)[:5]

    return {
        "overall_yield_pct": aggregation.get("overall_yield_pct", 100.0),
        "wafer_count": aggregation.get("wafer_count", 0),
        "outlier_wafer_count": sum(1 for w in wafers if w.get("is_outlier")),
        "hotspot_count": hotspots.get("hotspot_count", 0),
        "cluster_count": clusters.get("cluster_count", 0),
        "anomaly_count": anomalies.get("anomaly_count", 0),
        "edge_failures": edge_center.get("global_edge_failures", 0),
        "center_failures": edge_center.get("global_center_failures", 0),
        "yield_distribution": aggregation.get("yield_distribution", []),
        "worst_wafers": worst,
        "top_hotspots": hotspots.get("top_hotspots", [])[:10],
        "top_clusters": clusters.get("top_clusters", [])[:5],
        "bin_distribution": bin_dist.get("global_bin_distribution", [])[:10],
        "alerts": legacy_alerts[:15],
        "radial_summary": [
            {"wafer_id": r["wafer_id"], "pattern": r["pattern"]}
            for r in radial.get("per_wafer", [])[:10]
        ],
    }


def _plotly_payload(wafer_maps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plots = []
    for wm in wafer_maps[:10]:
        plots.append(
            {
                "wafer_id": wm["wafer_id"],
                "scatter": {
                    "pass": {
                        "x": [p["x"] for p in wm["pass_dies"] if p["x"] is not None],
                        "y": [p["y"] for p in wm["pass_dies"] if p["y"] is not None],
                    },
                    "fail": {
                        "x": [p["x"] for p in wm["fail_dies"] if p["x"] is not None],
                        "y": [p["y"] for p in wm["fail_dies"] if p["y"] is not None],
                    },
                },
                "density": {
                    "x": [c["x"] for c in wm["density_grid"]],
                    "y": [c["y"] for c in wm["density_grid"]],
                    "z": [c["density"] for c in wm["density_grid"]],
                },
            }
        )
    return plots
