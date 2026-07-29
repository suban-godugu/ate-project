"""Heatmap generation separated from analytics engine."""

from __future__ import annotations

from typing import Any


def generate_die_heatmap(
    coordinate_map: dict[str, Any],
    density_report: dict[str, Any],
    *,
    hotspots: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build die heatmap and failure density map for visualization."""
    points = coordinate_map.get("mapped_points", [])
    scatter_pass = []
    scatter_fail = []

    for p in points:
        if p.get("x") is None or p.get("y") is None:
            continue
        entry = {
            "x": p["x"],
            "y": p["y"],
            "die_id": p.get("die_id"),
            "wafer_id": p.get("wafer_id"),
            "zone": p.get("zone"),
            "intensity": p.get("intensity", 1.0 if p.get("is_failing") else 0.0),
        }
        if p.get("is_failing"):
            scatter_fail.append(entry)
        else:
            scatter_pass.append(entry)

    density_grid = density_report.get("grid", [])
    bounds = density_report.get("bounds", {})

    return {
        "die_heatmap": {
            "passing_dies": scatter_pass,
            "failing_dies": scatter_fail,
            "centroid": coordinate_map.get("centroid"),
            "bounds": bounds,
        },
        "failure_density_map": {
            "grid": density_grid,
            "max_density": density_report.get("max_density", 0.0),
            "mean_density": density_report.get("mean_density", 0.0),
        },
        "hotspot_overlay": hotspots or [],
        "plotly_ready": {
            "scatter": {
                "pass": {
                    "x": [p["x"] for p in scatter_pass],
                    "y": [p["y"] for p in scatter_pass],
                    "mode": "markers",
                    "name": "pass",
                },
                "fail": {
                    "x": [p["x"] for p in scatter_fail],
                    "y": [p["y"] for p in scatter_fail],
                    "mode": "markers",
                    "name": "fail",
                },
            },
            "density_heatmap": {
                "x": [c["x"] for c in density_grid],
                "y": [c["y"] for c in density_grid],
                "z": [c["density"] for c in density_grid],
                "type": "heatmap",
            },
        },
        "matplotlib_ready": {
            "scatter_x": [p["x"] for p in scatter_fail],
            "scatter_y": [p["y"] for p in scatter_fail],
            "density_values": [c["density"] for c in density_grid],
        },
    }


def build_engineering_dashboard(
    *,
    heatmap: dict[str, Any],
    hotspots: dict[str, Any],
    clusters: dict[str, Any],
    yield_dist: dict[str, Any],
    spatial_stats: dict[str, Any],
    neighbor_report: dict[str, Any],
) -> dict[str, Any]:
    """Engineering-ready dashboard dataset."""
    return {
        "overall_yield_pct": yield_dist.get("overall_yield_pct", 0.0),
        "hotspot_count": hotspots.get("hotspot_count", 0),
        "cluster_count": clusters.get("cluster_count", 0),
        "edge_failures": spatial_stats.get("edge_failures", 0),
        "center_failures": spatial_stats.get("center_failures", 0),
        "neighbor_fail_rate": neighbor_report.get("neighbor_fail_rate", 0.0),
        "top_hotspots": hotspots.get("hotspots", [])[:10],
        "top_clusters": clusters.get("clusters", [])[:5],
        "wafer_yield_distribution": yield_dist.get("wafer_yield_distribution", []),
        "heatmap_summary": {
            "failing_die_points": len(heatmap.get("die_heatmap", {}).get("failing_dies", [])),
            "passing_die_points": len(heatmap.get("die_heatmap", {}).get("passing_dies", [])),
            "max_density": heatmap.get("failure_density_map", {}).get("max_density", 0.0),
        },
    }
