"""Template-driven section assembly for FA-FR-010."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_SECTIONS: dict[str, bool] = {
    "executive_summary": True,
    "engineering_summary": True,
    "fa_fr_001_ingestion": True,
    "fa_fr_002_patterns": True,
    "fa_fr_003_failure_rates": True,
    "fa_fr_004_classification": True,
    "fa_fr_005_recurrence": True,
    "fa_fr_006_correlation": True,
    "fa_fr_007_die_analysis": True,
    "fa_fr_008_wafer_analysis": True,
    "fa_fr_009_fault_prediction": True,
    "engineering_insights": True,
    "benchmark_summary": True,
    "recommendations": True,
    "failure_trend_summary": True,
    "yield_summary": True,
    "top_failure_modes": True,
    "root_cause_summary": True,
    "corrective_actions": True,
}

BUILTIN_TEMPLATES: list[dict[str, Any]] = [
    {
        "template_key": "enterprise_full",
        "name": "Enterprise Full Report",
        "version": "1.0",
        "description": "Complete FA-FR-001..009 consolidated engineering report",
        "sections_json": DEFAULT_SECTIONS,
        "is_default": True,
    },
    {
        "template_key": "executive_brief",
        "name": "Executive Brief",
        "version": "1.0",
        "description": "Condensed executive and benchmark summary",
        "sections_json": {
            **{k: False for k in DEFAULT_SECTIONS},
            "executive_summary": True,
            "benchmark_summary": True,
            "recommendations": True,
            "fa_fr_009_fault_prediction": True,
        },
        "is_default": False,
    },
]


def merge_template_sections(
    template_sections: dict[str, Any] | None,
    config_sections: dict[str, Any] | None,
) -> dict[str, bool]:
    merged = dict(DEFAULT_SECTIONS)
    if template_sections:
        for key, value in template_sections.items():
            merged[key] = bool(value)
    if config_sections:
        for key, value in config_sections.items():
            if key in merged:
                merged[key] = bool(value)
    return merged


def build_module_sections(
    *,
    module_outputs: dict[str, Any],
    upstream: dict[str, Any],
    enabled_sections: dict[str, bool],
) -> dict[str, Any]:
    sections: dict[str, Any] = {}
    if enabled_sections.get("fa_fr_001_ingestion"):
        sections["fa_fr_001_ingestion"] = {
            "requirement": "FA-FR-001",
            "status": upstream.get("ingestion", {}).get("status", "unknown"),
            "records_accepted": upstream.get("ingestion", {}).get("records_accepted", 0),
            "integrity_pct": upstream.get("ingestion", {}).get("integrity_pct", 0.0),
            "source_id": upstream.get("ingestion", {}).get("source_id"),
        }
    if enabled_sections.get("fa_fr_002_patterns"):
        patterns = module_outputs.get("patterns") or module_outputs.get("pattern_detection") or {}
        sections["fa_fr_002_patterns"] = {
            "requirement": "FA-FR-002",
            "analysis_id": upstream.get("detection", {}).get("analysis_id"),
            "pattern_count": patterns.get("unique_patterns")
            or patterns.get("failure_count", 0),
            "pattern_ranking": (patterns.get("pattern_ranking") or [])[:20],
            "benchmark_metrics": upstream.get("detection", {}).get("benchmark_metrics", {}),
        }
    if enabled_sections.get("fa_fr_003_failure_rates"):
        rates = module_outputs.get("failure_rates", {})
        sections["fa_fr_003_failure_rates"] = {
            "requirement": "FA-FR-003",
            "computation_id": upstream.get("computation", {}).get("computation_id"),
            "metrics": rates.get("failure_rate_metrics", rates.get("metrics", []))[:20],
            "trend_analysis": rates.get("trend_analysis", []),
            "benchmark_metrics": upstream.get("computation", {}).get("benchmark_metrics", {}),
        }
    if enabled_sections.get("fa_fr_004_classification"):
        classification = module_outputs.get("classification", {})
        sections["fa_fr_004_classification"] = {
            "requirement": "FA-FR-004",
            "execution_id": upstream.get("classification", {}).get("execution_id"),
            "total_classified": classification.get("total_classified_failures", 0),
            "distribution": classification.get("fault_distribution", []),
            "severity_breakdown": classification.get("severity_breakdown", {}),
        }
    if enabled_sections.get("fa_fr_005_recurrence"):
        recurring = module_outputs.get("recurring", {})
        sections["fa_fr_005_recurrence"] = {
            "requirement": "FA-FR-005",
            "analysis_id": upstream.get("recurrence", {}).get("analysis_id"),
            "recurring_failures": (
                recurring.get("recurring_failure_list")
                or recurring.get("recurrence_events", [])
            )[:20],
            "classification_summary": recurring.get("classification_summary", {}),
        }
    if enabled_sections.get("fa_fr_006_correlation"):
        correlation = module_outputs.get("correlation", {})
        sections["fa_fr_006_correlation"] = {
            "requirement": "FA-FR-006",
            "analysis_id": upstream.get("correlation", {}).get("analysis_id"),
            "correlations": (
                correlation.get("correlation_report")
                or correlation.get("top_failing_patterns", [])
            )[:20],
            "benchmark_metrics": correlation.get("benchmark_metrics", {}),
        }
    if enabled_sections.get("fa_fr_007_die_analysis"):
        die = module_outputs.get("die_analysis", {})
        sections["fa_fr_007_die_analysis"] = {
            "requirement": "FA-FR-007",
            "analysis_id": upstream.get("die_analysis", {}).get("analysis_id"),
            "total_dies": die.get("total_dies", 0),
            "failing_dies": die.get("failing_dies", 0),
            "hotspot_count": die.get("hotspot_count", 0),
            "die_profiles": (die.get("die_profiles") or die.get("dashboard_feed", []))[:20],
        }
    if enabled_sections.get("fa_fr_008_wafer_analysis"):
        wafer = module_outputs.get("wafer_analysis", {})
        sections["fa_fr_008_wafer_analysis"] = {
            "requirement": "FA-FR-008",
            "analysis_id": upstream.get("wafer_analysis", {}).get("analysis_id"),
            "total_wafers": wafer.get("total_wafers", 0),
            "overall_yield_pct": wafer.get("overall_yield_pct", 0.0),
            "wafer_statistics": (
                wafer.get("wafer_statistics") or wafer.get("dashboard_feed", [])
            )[:20],
        }
    if enabled_sections.get("fa_fr_009_fault_prediction"):
        root_cause = module_outputs.get("root_cause", {})
        sections["fa_fr_009_fault_prediction"] = {
            "requirement": "FA-FR-009",
            "execution_id": upstream.get("fault_prediction", {}).get("execution_id"),
            "predictions": (root_cause.get("predictions") or [])[:20],
            "average_confidence": root_cause.get("average_confidence", 0.0),
            "disclaimer": root_cause.get(
                "disclaimer",
                "Predictions are probable fault types only.",
            ),
        }
    return sections


def apply_template_to_summaries(
    summaries: dict[str, Any],
    *,
    module_sections: dict[str, Any],
    enabled_sections: dict[str, bool],
    recommendations: list[dict[str, Any]],
    benchmark_summary: dict[str, Any],
    traceability: dict[str, Any],
) -> dict[str, Any]:
    output = deepcopy(summaries)
    output["module_sections"] = module_sections
    output["enabled_sections"] = enabled_sections
    if enabled_sections.get("benchmark_summary"):
        output["benchmark_summary"] = benchmark_summary
    if enabled_sections.get("recommendations"):
        output["engineering_recommendations"] = recommendations
    if enabled_sections.get("engineering_insights"):
        output["engineering_insights"] = {
            "observations": summaries.get("engineering_observations", []),
            "technical_highlights": summaries.get("engineering_summary", {}).get(
                "technical_highlights", {}
            ),
            "ai_assisted_notes": _ai_insights(module_sections),
        }
    output["traceability"] = traceability
    return output


def _ai_insights(module_sections: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    prediction = module_sections.get("fa_fr_009_fault_prediction", {})
    preds = prediction.get("predictions") or []
    if preds:
        top = preds[0]
        notes.append(
            "Top predicted fault type "
            f"{top.get('predicted_fault_type', 'unknown')} "
            f"with confidence {top.get('confidence_score', 0.0)}."
        )
    correlation = module_sections.get("fa_fr_006_correlation", {})
    corrs = correlation.get("correlations") or []
    if corrs:
        notes.append(
            f"Strongest correlation observed for pattern {corrs[0].get('pattern_id', 'N/A')}."
        )
    return notes
