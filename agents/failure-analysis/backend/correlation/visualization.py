"""Visualization payloads for correlation matrix and network graphs."""

from __future__ import annotations

from typing import Any


def build_visualization(
    *,
    correlation_matrix: dict[str, Any],
    network: dict[str, Any],
    engineering_insights: list[str],
) -> dict[str, Any]:
    """Plotly/Recharts-ready visualization datasets."""
    pearson = correlation_matrix.get("pearson", {})
    matrix_heatmap = _heatmap_from_matrix(pearson)

    return {
        "correlation_heatmap": matrix_heatmap,
        "network_graph": {
            "nodes": network.get("nodes", []),
            "edges": network.get("edges", []),
            "layout": network.get("layout", {}),
        },
        "plotly_ready": {
            "heatmap": {
                "z": matrix_heatmap.get("values", []),
                "x": matrix_heatmap.get("columns", []),
                "y": matrix_heatmap.get("rows", []),
                "type": "heatmap",
            },
            "network": {
                "nodes": [
                    {
                        "id": n["id"],
                        "x": network.get("layout", {}).get(n["id"], {}).get("x", 0),
                        "y": network.get("layout", {}).get(n["id"], {}).get("y", 0),
                        "type": n.get("node_type"),
                    }
                    for n in network.get("nodes", [])
                ],
                "edges": network.get("edges", []),
            },
        },
        "recharts_ready": {
            "dimension_bars": [
                {"dimension": dim, "score": info.get("correlation_score", 0)}
                for dim, info in correlation_matrix.get("dimension_scores", {}).items()
            ],
        },
        "engineering_insights": engineering_insights,
    }


def _heatmap_from_matrix(matrix: dict[str, dict[str, float]]) -> dict[str, Any]:
    rows = sorted(matrix.keys())
    cols = sorted({c for row in matrix.values() for c in row.keys()}) or rows
    values = [[matrix.get(r, {}).get(c, 0.0) for c in cols] for r in rows]
    return {"rows": rows, "columns": cols, "values": values}
