"""Dashboard dataset and visualization payloads (separated from report logic)."""

from __future__ import annotations

from typing import Any


def build_dashboard_dataset(
    summaries: dict[str, Any],
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    """Build Plotly-ready dashboard payloads."""
    charts = {
        "yield_by_lot": _yield_by_lot_chart(summaries),
        "failure_mode_pareto": _failure_mode_pareto(summaries),
        "wafer_yield_distribution": _wafer_yield_chart(module_outputs),
        "root_cause_confidence": _root_cause_confidence_chart(summaries),
        "correlation_heatmap": _correlation_heatmap(analysis, module_outputs),
    }

    return {
        "summary_cards": _summary_cards(summaries, analysis),
        "charts": charts,
        "tables": {
            "top_failure_modes": summaries.get("top_failure_modes", [])[:10],
            "lot_summary": summaries.get("lot_summary", [])[:10],
            "wafer_summary": summaries.get("wafer_summary", [])[:10],
            "corrective_actions": summaries.get("recommended_corrective_actions", [])[:10],
        },
        "metadata": summaries.get("metadata", {}),
    }


def _summary_cards(summaries: dict[str, Any], analysis: dict[str, Any]) -> list[dict[str, Any]]:
    exec_sum = summaries.get("executive_summary", {})
    summary = analysis.get("summary", {})
    return [
        {
            "label": "Dies Tested",
            "value": summary.get("total_dies_tested", 0),
            "format": "integer",
        },
        {
            "label": "Failing Dies",
            "value": summary.get("total_failing_dies", 0),
            "format": "integer",
        },
        {
            "label": "Overall Yield",
            "value": exec_sum.get("overall_yield_pct"),
            "format": "percent",
        },
        {
            "label": "Recurring Patterns",
            "value": summary.get("recurring_pattern_count", 0),
            "format": "integer",
        },
        {
            "label": "High-Risk Patterns",
            "value": summary.get("high_risk_pattern_count", 0),
            "format": "integer",
        },
        {
            "label": "Top Root Cause Confidence",
            "value": exec_sum.get("top_prediction_confidence"),
            "format": "decimal",
        },
    ]


def _yield_by_lot_chart(summaries: dict[str, Any]) -> dict[str, Any]:
    lots = summaries.get("lot_summary", [])
    labels = [str(row.get("lot_id", "")) for row in lots[:15]]
    rates = [
        round((1.0 - float(row.get("failure_rate", 0))) * 100, 2)
        for row in lots[:15]
    ]
    return {
        "type": "bar",
        "title": "Yield by Lot (%)",
        "plotly": {
            "data": [
                {
                    "type": "bar",
                    "x": labels,
                    "y": rates,
                    "name": "Yield %",
                }
            ],
            "layout": {"title": "Yield by Lot", "yaxis": {"title": "Yield %"}},
        },
    }


def _failure_mode_pareto(summaries: dict[str, Any]) -> dict[str, Any]:
    modes = summaries.get("top_failure_modes", [])[:10]
    labels = [str(m.get("fault_category", "")) for m in modes]
    counts = [int(m.get("count", 0)) for m in modes]
    return {
        "type": "bar",
        "title": "Top Failure Modes",
        "plotly": {
            "data": [{"type": "bar", "x": labels, "y": counts, "name": "Count"}],
            "layout": {"title": "Failure Mode Pareto"},
        },
    }


def _wafer_yield_chart(module_outputs: dict[str, Any]) -> dict[str, Any]:
    wafer = module_outputs.get("wafer_analysis", {})
    dist = wafer.get("yield_distribution", [])
    labels = [str(d.get("wafer_id", d.get("label", i))) for i, d in enumerate(dist[:20])]
    values = [float(d.get("yield_pct", d.get("yield", 0))) for d in dist[:20]]
    return {
        "type": "bar",
        "title": "Wafer Yield Distribution",
        "plotly": {
            "data": [{"type": "bar", "x": labels, "y": values, "name": "Yield %"}],
            "layout": {"title": "Wafer Yield Distribution"},
        },
    }


def _root_cause_confidence_chart(summaries: dict[str, Any]) -> dict[str, Any]:
    preds = summaries.get("root_cause_summary", {}).get("predictions", [])[:10]
    labels = [str(p.get("scan_chain_id", p.get("predicted_fault_type", ""))) for p in preds]
    scores = [float(p.get("confidence_score", 0)) for p in preds]
    return {
        "type": "bar",
        "title": "Root Cause Confidence",
        "plotly": {
            "data": [{"type": "bar", "x": labels, "y": scores, "name": "Confidence"}],
            "layout": {"title": "Root Cause Confidence Scores", "yaxis": {"range": [0, 1]}},
        },
    }


def _correlation_heatmap(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    correlation = module_outputs.get("correlation") or analysis.get(
        "failure_pattern_correlation", {}
    )
    matrix = correlation.get("correlation_matrix", {})
    if not matrix:
        report = correlation.get("correlation_report", [])[:8]
        labels = [str(r.get("pattern_id", "")) for r in report]
        z = [[float(r.get("correlation_score", 0))] for r in report]
        return {
            "type": "heatmap",
            "title": "Pattern Correlation Scores",
            "plotly": {
                "data": [
                    {
                        "type": "heatmap",
                        "x": ["score"],
                        "y": labels,
                        "z": z,
                        "colorscale": "RdYlGn",
                    }
                ],
                "layout": {"title": "Top Pattern Correlation"},
            },
        }

    keys = list(matrix.keys())[:10]
    z = [[float(matrix.get(a, {}).get(b, 0)) for b in keys] for a in keys]
    return {
        "type": "heatmap",
        "title": "Failure Correlation Matrix",
        "plotly": {
            "data": [{"type": "heatmap", "x": keys, "y": keys, "z": z}],
            "layout": {"title": "Correlation Matrix"},
        },
    }
