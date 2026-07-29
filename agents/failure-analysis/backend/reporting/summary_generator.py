"""Engineering and executive summary generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from analyzer import REVIEWER_FEEDBACK_RESPONSES, generate_failure_summary


def build_summaries(
    *,
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
    upload_meta: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Generate executive and engineering summaries from consolidated analysis."""
    legacy = generate_failure_summary([], analysis)
    now = datetime.now(timezone.utc).isoformat()

    executive = _build_executive_summary(analysis, legacy, module_outputs, upload_meta)
    engineering = _build_engineering_summary(analysis, module_outputs, config)
    trends = _build_failure_trend_summary(analysis, module_outputs)
    yield_summary = _build_yield_summary(analysis, module_outputs)
    top_modes = _build_top_failure_modes(analysis, module_outputs)
    lot_summary = _build_lot_summary(analysis, module_outputs)
    wafer_summary = _build_wafer_summary(analysis, module_outputs)
    die_summary = _build_die_summary(analysis, module_outputs)
    root_cause = _build_root_cause_summary(analysis, module_outputs)
    actions = _build_corrective_actions(analysis, module_outputs, legacy)
    observations = _build_engineering_observations(analysis, module_outputs)

    return {
        "metadata": {
            "generated_at": now,
            "report_title": config.get("report", {}).get("title", "Failure Analysis Report"),
            "customer_name": config.get("report", {}).get("customer_name", ""),
            "upload_id": upload_meta.get("upload_id"),
            "original_filename": upload_meta.get("original_filename"),
            "records_accepted": upload_meta.get("records_accepted", 0),
            "requirement": "FA-FR-010",
        },
        "executive_summary": executive,
        "engineering_summary": engineering,
        "failure_trend_summary": trends,
        "yield_summary": yield_summary,
        "top_failure_modes": top_modes,
        "lot_summary": lot_summary,
        "wafer_summary": wafer_summary,
        "die_summary": die_summary,
        "root_cause_summary": root_cause,
        "recommended_corrective_actions": actions,
        "engineering_observations": observations,
        "module_sections": {},
        "benchmark_summary": {},
        "engineering_recommendations": [],
        "engineering_insights": {},
        "traceability": {},
        "requirement_traceability": legacy.get("requirement_traceability", {}),
        "reviewer_feedback_responses": REVIEWER_FEEDBACK_RESPONSES,
    }


def _build_executive_summary(
    analysis: dict[str, Any],
    legacy: dict[str, Any],
    module_outputs: dict[str, Any],
    upload_meta: dict[str, Any],
) -> dict[str, Any]:
    core = legacy.get("executive_summary", {})
    summary = analysis.get("summary", {})
    root_cause = module_outputs.get("root_cause", {})
    top_prediction = (root_cause.get("predictions") or [{}])[0] if root_cause else {}

    return {
        **core,
        "upload_filename": upload_meta.get("original_filename"),
        "overall_yield_pct": _safe_yield(module_outputs, summary),
        "top_predicted_root_cause": top_prediction.get(
            "predicted_root_cause", top_prediction.get("predicted_fault_type", "N/A")
        ),
        "top_prediction_confidence": top_prediction.get("confidence_score"),
        "modules_analyzed": _modules_present(module_outputs),
        "headline": _executive_headline(summary, top_prediction),
    }


def _build_engineering_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    detection = analysis.get("detection", {})
    correlation = analysis.get("failure_pattern_correlation", {})
    classification = module_outputs.get("classification") or analysis.get(
        "fault_classification", {}
    )

    return {
        "total_failing_patterns": analysis.get("summary", {}).get("total_failing_patterns", 0),
        "detection_accuracy_pct": detection.get("detection_accuracy", {}).get("accuracy_pct"),
        "classified_fault_count": classification.get("total_classified_failures", 0),
        "recurring_pattern_count": analysis.get("summary", {}).get("recurring_pattern_count", 0),
        "high_risk_pattern_count": analysis.get("summary", {}).get("high_risk_pattern_count", 0),
        "correlation_report_size": len(correlation.get("correlation_report", [])),
        "die_profiles_analyzed": (
            module_outputs.get("die_analysis", {}).get("total_dies")
            or analysis.get("die_level_analysis", {}).get("total_dies", 0)
        ),
        "wafer_profiles_analyzed": (
            module_outputs.get("wafer_analysis", {}).get("total_wafers")
            or analysis.get("wafer_level_analysis", {}).get("total_wafers", 0)
        ),
        "sections_included": [
            k for k, enabled in config.get("sections", {}).items() if enabled
        ],
        "technical_highlights": legacy_technical_highlights(analysis, module_outputs),
    }


def legacy_technical_highlights(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    correlation = analysis.get("failure_pattern_correlation", {})
    root_cause = module_outputs.get("root_cause", analysis.get("fault_type_predictions", {}))
    return {
        "top_correlated_patterns": correlation.get("top_failing_patterns", [])[:5],
        "top_recurring_patterns": analysis.get("recurring_failures", {}).get(
            "recurring_failures", []
        )[:5],
        "top_root_cause_predictions": (root_cause.get("predictions") or [])[:5],
        "wafer_alerts": (
            module_outputs.get("wafer_analysis", {}).get("legacy_report", {}).get("alerts")
            or analysis.get("wafer_level_analysis", {}).get("alerts", [])
        )[:10],
    }


def _build_failure_trend_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    wafer_mod = module_outputs.get("wafer_analysis", {})
    trends = wafer_mod.get("legacy_report", {}).get("lot_sequence_trends", [])
    if not trends:
        trends = analysis.get("wafer_level_analysis", {}).get("lot_sequence_trends", [])

    recurring = module_outputs.get("recurring") or analysis.get("recurring_failures", {})
    return {
        "lot_sequence_trends": trends[:20],
        "recurring_failures": recurring.get("recurring_failures", [])[:10],
        "trend_narrative": _trend_narrative(trends, recurring),
    }


def _build_yield_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    rates = module_outputs.get("failure_rates") or analysis.get("failure_rates", {})
    engine = rates.get("engine", rates) if isinstance(rates, dict) else {}
    wafer_mod = module_outputs.get("wafer_analysis", {})

    return {
        "overall_die_failure_rate": analysis.get("summary", {}).get("overall_die_failure_rate"),
        "overall_yield_pct": wafer_mod.get("overall_yield_pct")
        or _invert_rate(analysis.get("summary", {}).get("overall_die_failure_rate")),
        "device_level": rates.get("device_level", engine.get("device_level", {})),
        "lot_level": rates.get("lot_level", engine.get("lot_level", {})),
        "wafer_level": rates.get("wafer_level", engine.get("wafer_level", {})),
        "pattern_level": rates.get("pattern_level", engine.get("pattern_level", {})),
        "yield_distribution": wafer_mod.get("yield_distribution", []),
    }


def _build_top_failure_modes(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> list[dict[str, Any]]:
    classification = module_outputs.get("classification") or analysis.get(
        "fault_classification", {}
    )
    category_summary = classification.get("category_summary", {})
    modes: list[dict[str, Any]] = []
    for category, stats in sorted(
        category_summary.items(),
        key=lambda kv: kv[1].get("count", 0) if isinstance(kv[1], dict) else 0,
        reverse=True,
    ):
        if isinstance(stats, dict):
            modes.append({"fault_category": category, **stats})
        else:
            modes.append({"fault_category": category, "count": stats})
    if not modes:
        for row in analysis.get("failure_pattern_correlation", {}).get(
            "top_failing_patterns", []
        )[:10]:
            modes.append(
                {
                    "fault_category": row.get("pattern_id", "UNKNOWN"),
                    "count": row.get("failure_count", 0),
                    "source": "correlation",
                }
            )
    return modes[:15]


def _build_lot_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> list[dict[str, Any]]:
    rates = module_outputs.get("failure_rates") or analysis.get("failure_rates", {})
    lot_level = rates.get("lot_level", rates.get("engine", {}).get("lot_level", {}))
    rows: list[dict[str, Any]] = []
    for lot_id, stats in sorted(lot_level.items()):
        if isinstance(stats, dict):
            rows.append({"lot_id": lot_id, **stats})
    return rows[:50]


def _build_wafer_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> list[dict[str, Any]]:
    wafer_mod = module_outputs.get("wafer_analysis", {})
    stats = (
        wafer_mod.get("wafer_statistics")
        or wafer_mod.get("dashboard_feed")
        or wafer_mod.get("engineering_dashboard", {}).get("wafer_statistics")
        or []
    )
    if stats:
        return stats[:50]

    rates = module_outputs.get("failure_rates") or analysis.get("failure_rates", {})
    wafer_level = rates.get("wafer_level", rates.get("engine", {}).get("wafer_level", {}))
    rows: list[dict[str, Any]] = []
    for wafer_id, row in sorted(wafer_level.items()):
        if isinstance(row, dict):
            rows.append({"wafer_id": wafer_id, **row})
    return rows[:50]


def _build_die_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    die_mod = module_outputs.get("die_analysis", {})
    die_legacy = analysis.get("die_level_analysis", {})
    # Production FA-FR-007 uses die_profiles / dashboard_feed with is_failing;
    # legacy uses engineering_dashboard / dashboard_feed with is_failing_die.
    dashboard = (
        die_mod.get("die_profiles")
        or die_mod.get("dashboard_feed")
        or die_mod.get("engineering_dashboard")
        or die_legacy.get("dashboard_feed")
        or []
    )
    if not isinstance(dashboard, list):
        dashboard = []

    def _is_failing(row: dict[str, Any]) -> bool:
        if "is_failing" in row:
            return bool(row.get("is_failing"))
        if "is_failing_die" in row:
            return bool(row.get("is_failing_die"))
        disposition = row.get("disposition")
        return disposition not in (None, "RELEASE")

    failing_rows = [row for row in dashboard if isinstance(row, dict) and _is_failing(row)]
    total_dies = int(die_mod.get("total_dies") or die_legacy.get("total_dies") or len(dashboard) or 0)
    failing_dies = int(die_mod.get("failing_dies") or die_legacy.get("failing_dies") or len(failing_rows))
    yield_pct = die_mod.get("overall_yield_pct")
    if yield_pct is None and total_dies:
        yield_pct = round((1.0 - (failing_dies / total_dies)) * 100.0, 2)
    ranked = sorted(
        failing_rows,
        key=lambda row: (
            float(row.get("health_score", 1.0) if row.get("health_score") is not None else 1.0),
            -int(row.get("failure_count") or 0),
        ),
    )
    return {
        "total_dies": total_dies,
        "failing_dies": failing_dies,
        "overall_yield_pct": yield_pct,
        "hotspot_count": die_mod.get("hotspot_count", 0),
        "cluster_count": die_mod.get("cluster_count", 0),
        "top_failing_dies": ranked[:20],
    }


def _build_root_cause_summary(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> dict[str, Any]:
    root_cause = module_outputs.get("root_cause")
    if root_cause:
        return {
            "total_predictions": root_cause.get("total_predictions", 0),
            "average_confidence": root_cause.get("average_confidence"),
            "predictions": (root_cause.get("predictions") or [])[:10],
            "ranked_hypothesis_queue": root_cause.get("ranked_hypothesis_queue", [])[:10],
            "similar_historical_cases": root_cause.get("similar_historical_cases", [])[:5],
            "root_cause_report": root_cause.get("root_cause_report", {}),
        }

    legacy = analysis.get("fault_type_predictions", analysis.get("root_cause_predictions", {}))
    return {
        "total_predictions": legacy.get("total_predictions", 0),
        "predictions": legacy.get("predictions", [])[:10],
        "ranked_hypothesis_queue": legacy.get("ranked_hypothesis_queue", [])[:10],
        "phase_description": legacy.get("phase_description", ""),
    }


def _build_corrective_actions(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
    legacy: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    for rec in module_outputs.get("root_cause", {}).get("engineering_recommendations", []):
        actions.append({**rec, "source": "root_cause"})

    for rec in analysis.get("failure_pattern_correlation", {}).get(
        "engineering_recommendations", []
    ):
        if isinstance(rec, str):
            actions.append({"action": rec, "priority": "MEDIUM", "source": "correlation"})
        elif isinstance(rec, dict):
            actions.append({**rec, "source": "correlation"})

    for rec in legacy.get("recommended_actions", []):
        if isinstance(rec, str):
            actions.append({"action": rec, "priority": "MEDIUM", "source": "legacy"})

    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for action in actions:
        key = str(action.get("action", action))
        if key in seen:
            continue
        seen.add(key)
        unique.append(action)
    return unique[:25]


def _build_engineering_observations(
    analysis: dict[str, Any],
    module_outputs: dict[str, Any],
) -> list[str]:
    observations: list[str] = []

    det = analysis.get("detection", {}).get("detection_accuracy", {})
    if det.get("meets_threshold"):
        observations.append(
            f"Pattern detection met completeness target ({det.get('accuracy_pct', 0):.1f}%)."
        )

    recurring_count = analysis.get("summary", {}).get("recurring_pattern_count", 0)
    if recurring_count:
        observations.append(
            f"{recurring_count} recurring failure pattern(s) span multiple lots — investigate process drift."
        )

    wafer_mod = module_outputs.get("wafer_analysis", {})
    outliers = wafer_mod.get("outlier_wafer_count", 0)
    if outliers:
        observations.append(f"{outliers} wafer outlier(s) detected versus lot siblings.")

    die_mod = module_outputs.get("die_analysis", {})
    if die_mod.get("hotspot_count", 0) > 0:
        observations.append(
            f"Die-level analysis identified {die_mod['hotspot_count']} spatial hotspot region(s)."
        )

    rc = module_outputs.get("root_cause", {})
    high_conf = sum(
        1 for p in rc.get("predictions", []) if p.get("confidence_score", 0) >= 0.75
    )
    if high_conf:
        observations.append(
            f"{high_conf} high-confidence root cause prediction(s) available for prioritized FA."
        )

    if not observations:
        observations.append("No critical anomalies beyond baseline failure statistics.")

    return observations


def _executive_headline(summary: dict[str, Any], top_prediction: dict[str, Any]) -> str:
    rate = summary.get("overall_die_failure_rate", 0)
    failing = summary.get("total_failing_dies", 0)
    total = summary.get("total_dies_tested", 0)
    root = top_prediction.get("predicted_root_cause", top_prediction.get("predicted_fault_type"))
    if root and root != "N/A":
        return (
            f"{failing}/{total} dies failing ({rate * 100:.1f}%); "
            f"leading hypothesis: {root}."
        )
    return f"{failing}/{total} dies failing ({rate * 100:.1f}% die failure rate)."


def _modules_present(module_outputs: dict[str, Any]) -> list[str]:
    return sorted(k for k, v in module_outputs.items() if v)


def _safe_yield(module_outputs: dict[str, Any], summary: dict[str, Any]) -> float | None:
    wafer = module_outputs.get("wafer_analysis", {})
    if wafer.get("overall_yield_pct") is not None:
        return float(wafer["overall_yield_pct"])
    rate = summary.get("overall_die_failure_rate")
    return _invert_rate(rate)


def _invert_rate(rate: float | None) -> float | None:
    if rate is None:
        return None
    return round((1.0 - float(rate)) * 100, 2)


def _trend_narrative(trends: list[Any], recurring: dict[str, Any]) -> str:
    parts: list[str] = []
    if trends:
        parts.append(f"Lot/wafer sequence trends captured for {len(trends)} data point(s).")
    rec_count = recurring.get("recurring_pattern_count", len(recurring.get("recurring_failures", [])))
    if rec_count:
        parts.append(f"{rec_count} recurring signature(s) indicate systematic failure modes.")
    return " ".join(parts) if parts else "Insufficient trend data for narrative summary."
