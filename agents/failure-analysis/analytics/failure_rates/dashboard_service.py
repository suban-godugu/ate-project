"""Dashboard-ready datasets separated from calculation engine."""

from __future__ import annotations

from typing import Any


def build_dashboard_dataset(report: dict[str, Any]) -> dict[str, Any]:
    """Visualization-ready payload for Plotly/Recharts frontends."""
    summary = report.get("summary", {})
    trend = report.get("trend_report", {})

    return {
        "overall_yield": {
            "yield_pct": summary.get("overall_yield_pct", 0.0),
            "failure_rate_pct": summary.get("overall_failure_rate_pct", 0.0),
            "tested": summary.get("total_dies_tested", 0),
            "failed": summary.get("total_failing_dies", 0),
        },
        "device_failure_rate": _top_entities(report.get("device_level", {}), "device"),
        "wafer_failure_rate": _top_entities(report.get("wafer_level", {}), "wafer"),
        "lot_failure_rate": _top_entities(report.get("lot_level", {}), "lot"),
        "product_failure_rate": _top_entities(report.get("product_level", {}), "product"),
        "tester_failure_rate": _top_entities(report.get("tester_level", {}), "tester"),
        "shift_failure_rate": _top_entities(report.get("shift_level", {}), "shift"),
        "production_yield": report.get("overall_manufacturing_yield", {}),
        "trend_graphs": {
            "time_series": trend.get("time_series", []),
            "worst_lots": trend.get("worst_lots", []),
            "worst_wafers": trend.get("worst_wafers", []),
            "trend_direction": trend.get("trend_direction", "unknown"),
        },
        "historical_comparison": trend.get("historical_comparison", []),
        "alerts": report.get("alerts", []),
        "statistics_by_level": {
            level: report.get(level, {}).get("statistics", {})
            for level in (
                "device_level",
                "die_level",
                "wafer_level",
                "lot_level",
                "product_level",
                "tester_level",
                "shift_level",
                "production_level",
            )
        },
        "plotly_ready": _plotly_series(report),
        "recharts_ready": _recharts_series(report),
    }


def _top_entities(level: dict[str, Any], label: str) -> list[dict[str, Any]]:
    entities = level.get("entities", level) if isinstance(level, dict) else {}
    if "entities" in level:
        entities = level["entities"]
    rows = []
    for key, stats in entities.items():
        rows.append(
            {
                f"{label}_id": key,
                "failure_rate_pct": stats.get("failure_rate_pct", 0.0),
                "yield_pct": stats.get("yield_percentage", stats.get("pass_rate_pct", 0.0)),
                "pass_count": stats.get("pass_count", 0),
                "fail_count": stats.get("fail_count", 0),
                "tested": stats.get("tested", 0),
            }
        )
    rows.sort(key=lambda r: r["failure_rate_pct"], reverse=True)
    return rows[:25]


def _plotly_series(report: dict[str, Any]) -> dict[str, Any]:
    trend = report.get("trend_report", {})
    return {
        "yield_trend": {
            "x": [p["window"] for p in trend.get("time_series", [])],
            "y": [p.get("yield_pct", 0.0) for p in trend.get("time_series", [])],
            "type": "scatter",
            "mode": "lines+markers",
        },
        "lot_bar": {
            "x": [p["lot_id"] for p in trend.get("worst_lots", [])],
            "y": [p.get("failure_rate_pct", 0.0) for p in trend.get("worst_lots", [])],
            "type": "bar",
        },
    }


def _recharts_series(report: dict[str, Any]) -> list[dict[str, Any]]:
    trend = report.get("trend_report", {})
    return [
        {
            "name": point.get("window", ""),
            "yield": point.get("yield_pct", 0.0),
            "failureRate": point.get("failure_rate_pct", 0.0),
        }
        for point in trend.get("time_series", [])
    ]
