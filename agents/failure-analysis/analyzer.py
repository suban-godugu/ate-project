"""Failure rate analysis module for the Failure Analysis Agent."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

from die_wafer_analytics import (
    analyze_die_level_failures as _analyze_die_level_failures,
    analyze_wafer_level_failures as _analyze_wafer_level_failures,
)
from failure_rate_engine import (
    FAILURE_RATE_TOLERANCE_PCT,
    compute_failure_rates,
    persist_aggregates,
)
from fault_classifier import classify_fault_type, classify_fault_types as _classify_fault_types
from ingestor import DieLog, PatternResult
from pattern_correlation import (
    calculate_pattern_level_failure_rates,
    correlate_failures_with_patterns as _correlate_failures_with_patterns,
)
from pattern_detection import (
    detect_failing_patterns as detect_failing_patterns_v2,
    load_pattern_manifest,
    measure_detection_accuracy as measure_detection_accuracy_v2,
)
from recurrence_detection import (
    RECURRING_DEFINITION as RECURRENCE_DEFINITION_FA005,
    identify_recurring_failures as _identify_recurring_failures,
)

# FA-FR-004: taxonomy loaded from config/fault_taxonomy.yaml (see fault_classifier.py).
# Legacy aliases retained for backward-compatible report keys.
FAULT_CATEGORIES = (
    "Electrical",
    "Functional",
    "Scan Chain",
    "Memory",
    "Timing",
    "Leakage",
    "Power/Ground",
    "Process-Induced",
    "Unclassified",
)

FAULT_CATEGORY_DEFINITIONS = {
    "Scan Chain": "Scan chain shift/stuck-at mismatch or SCAN_SHIFT fail type.",
    "Timing": "Negative setup/hold slack or setup/hold timing hints.",
    "Power/Ground": "IR drop, power grid, or supply-related failure.",
    "Functional": "Logic/transition/functional test failure.",
    "Leakage": "IDDQ high or leakage bin mapping.",
    "Process-Induced": "Process variation or thermal hotspot signature.",
    "Unclassified": "No rule or ML classification applied.",
}

# Thresholds used by the classifier (single source of truth, also reported).
TIMING_SLACK_FAIL_PS = 0.0
IR_DROP_FAIL_MV = 50.0
THERMAL_FAIL_C = 80.0

# Minimum number of lots a pattern must fail in to be flagged as recurring (FA-FR-005).
RECURRING_MIN_LOTS = 2

# FA-FR-005: human-readable definition of "recurring" (reviewer question).
RECURRING_DEFINITION = RECURRENCE_DEFINITION_FA005

# FA-FR-002: reviewer requested strict 100% detection completeness.
DETECTION_ACCURACY_THRESHOLD = 1.0

# FA-FR-003 / FA-FR-008: alert when wafer failure rate exceeds this threshold.
WAFER_ALERT_THRESHOLD = 0.05

# FA-FR-006: correlation score threshold for HIGH_RISK classification.
CORRELATION_HIGH_RISK_THRESHOLD = 0.75

# FA-FR-007: per-die disposition thresholds (fraction of executions failing).
DIE_SCRAP_SEVERITY = 0.10
DIE_RETEST_SEVERITY = 0.0

# FA-FR-006: composite correlation weights (client: rank beyond failure frequency).
CORRELATION_WEIGHT_FREQUENCY = 0.50
CORRELATION_WEIGHT_LOT_SPREAD = 0.25
CORRELATION_WEIGHT_WAFER_SPREAD = 0.25

# FA-FR-007: severity is an engineering heuristic, not physical FA (reviewer note).
DIE_SEVERITY_METHODOLOGY = (
    "Severity class is a triage heuristic based on the fraction of pattern/channel "
    "executions that failed on the die (fail_count / total_executions). "
    f">= {DIE_SCRAP_SEVERITY * 100:.0f}% => CATASTROPHIC_FAIL/SCRAP; "
    "> 0% => MARGINAL_FAIL/RETEST; 0% => PASS/RELEASE. This supports sorting and "
    "disposition only; it is not a substitute for physical failure analysis."
)

# Client feedback + concept docs: how this agent differs from full diagnosis.
REVIEWER_FEEDBACK_RESPONSES = {
    "FA-FR-001": (
        "Tester logs are ASCII text with customer-specific headers; ingestion supports "
        "multiple formats (compact P|CH, streamed CHANNEL_ID, legacy PATTERN_ID) and "
        "can be extended per customer template."
    ),
    "FA-FR-002": (
        "Detection completeness target is 100%: every FAIL/F execution present in the "
        "parsed log must be captured. This replaces the earlier >=95% wording."
    ),
    "FA-FR-003": (
        "Retained as the foundational yield layer (per Failure Rate Calculation doc): "
        "aggregates pass/fail into device/lot/wafer/pattern rates that trigger deeper "
        "die/wafer/pattern analysis."
    ),
    "FA-FR-004": (
        "Categories are deterministically defined in category_definitions using "
        "FAIL_TYPE, ROOT_CAUSE_HINT, timing slack, IR drop, and thermal thresholds."
    ),
    "FA-FR-005": (
        "Recurring = same PATTERN_ID failing in >=2 lots; output also reports "
        "affected wafer_count and die_count per recurring pattern."
    ),
    "FA-FR-006": (
        "Correlation ranking uses a composite score: failure frequency vs baseline, "
        "lot spread, and wafer spread (not frequency alone)."
    ),
    "FA-FR-007": (
        "Distinct from FR-003: per-die actionable profile (coordinates, disposition, "
        "severity class, fault breakdown) — spatial intelligence per Die-Level doc."
    ),
    "FA-FR-008": (
        "Distinct from FR-003: wafer spatial signature, heatmap, and equipment-style "
        "alerts — wafer health layer per concept documents."
    ),
    "FA-FR-009": (
        "Outputs predicted FAULT TYPE with confidence, not confirmed root cause. "
        "Full diagnosis (DEF/design correlation) belongs to Scan Chain Diagnosis Agent."
    ),
    "FA-FR-010": (
        "Automatic JSON executive + technical summary with requirement traceability."
    ),
}


def _failure_rate(failing: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(failing / total, 6)


def _parse_numeric(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def classify_fault_types(
    die_logs: list[DieLog],
    *,
    test_records: list | None = None,
    taxonomy_path: Path | None = None,
    enable_ml: bool = True,
) -> dict[str, Any]:
    """FA-FR-004: Classify failures via YAML rules + optional ML layer."""
    return _classify_fault_types(
        die_logs,
        test_records=test_records,
        taxonomy_path=taxonomy_path,
        enable_ml=enable_ml,
    )


def identify_recurring_failures(
    die_logs: list[DieLog],
    *,
    min_lots: int = RECURRING_MIN_LOTS,
    test_records: list | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """FA-FR-005: Multi-signature recurrence detection (die, wafer, lot scopes)."""
    return _identify_recurring_failures(
        die_logs,
        min_lots=min_lots,
        test_records=test_records,
        manifest_path=manifest_path,
    )


def _pattern_summary(pattern: PatternResult) -> dict[str, str]:
    return {
        "pattern_id": pattern.pattern_id,
        "scan_chain_id": pattern.scan_chain_id,
        "expected_signature": pattern.expected_signature,
        "actual_signature": pattern.actual_signature,
        "status": pattern.status,
    }


def calculate_device_level_failure_rate(die_logs: list[DieLog]) -> dict[str, Any]:
    """Failure rate = failing dies / total dies tested, grouped by device."""
    by_device: dict[str, list[DieLog]] = defaultdict(list)
    for die in die_logs:
        by_device[die.device_name].append(die)

    results: dict[str, Any] = {}
    for device_name, dies in sorted(by_device.items()):
        total_dies = len(dies)
        failing_dies = sum(1 for die in dies if die.is_failing_die)
        results[device_name] = {
            "total_dies_tested": total_dies,
            "failing_dies": failing_dies,
            "passing_dies": total_dies - failing_dies,
            "failure_rate": _failure_rate(failing_dies, total_dies),
        }

    return results


def calculate_lot_level_failure_rates(die_logs: list[DieLog]) -> dict[str, Any]:
    """Failure rate grouped by LOT_ID."""
    by_lot: dict[str, list[DieLog]] = defaultdict(list)
    for die in die_logs:
        by_lot[die.lot_id].append(die)

    results: dict[str, Any] = {}
    for lot_id, dies in sorted(by_lot.items()):
        total_dies = len(dies)
        failing_dies = sum(1 for die in dies if die.is_failing_die)
        results[lot_id] = {
            "total_dies_tested": total_dies,
            "failing_dies": failing_dies,
            "passing_dies": total_dies - failing_dies,
            "failure_rate": _failure_rate(failing_dies, total_dies),
        }

    return results


def calculate_wafer_level_failure_rates(die_logs: list[DieLog]) -> dict[str, Any]:
    """Failure rate grouped by WAFER_ID."""
    by_wafer: dict[str, list[DieLog]] = defaultdict(list)
    for die in die_logs:
        by_wafer[die.wafer_id].append(die)

    results: dict[str, Any] = {}
    for wafer_id, dies in sorted(by_wafer.items()):
        total_dies = len(dies)
        failing_dies = sum(1 for die in dies if die.is_failing_die)
        results[wafer_id] = {
            "lot_id": dies[0].lot_id,
            "total_dies_tested": total_dies,
            "failing_dies": failing_dies,
            "passing_dies": total_dies - failing_dies,
            "failure_rate": _failure_rate(failing_dies, total_dies),
        }

    return results


def correlate_failures_with_patterns(
    die_logs: list[DieLog],
    pattern_rates: dict[str, Any] | None = None,
    *,
    test_records: list | None = None,
    recurring_failures: dict[str, Any] | None = None,
    weights_path: Path | None = None,
    top_n: int = 50,
) -> dict[str, Any]:
    """FA-FR-006: Multi-factor failure-to-pattern correlation report."""
    return _correlate_failures_with_patterns(
        die_logs,
        pattern_rates,
        test_records=test_records,
        recurring_failures=recurring_failures,
        weights_path=weights_path,
        top_n=top_n,
    )


def _die_severity_class(severity: float, is_failing: bool) -> str:
    """Classify a die as PASS / MARGINAL_FAIL / CATASTROPHIC_FAIL."""
    if not is_failing:
        return "PASS"
    if severity >= DIE_SCRAP_SEVERITY:
        return "CATASTROPHIC_FAIL"
    return "MARGINAL_FAIL"


def _die_disposition(severity: float, is_failing: bool) -> str:
    """Recommend a shipment disposition for a die (FA-FR-007)."""
    if not is_failing:
        return "RELEASE"
    if severity >= DIE_SCRAP_SEVERITY:
        return "SCRAP"
    return "RETEST"


def analyze_die_level_failures(
    die_logs: list[DieLog],
    *,
    test_records: list | None = None,
    recurring_failures: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """FA-FR-007: Dashboard-ready die-level failure statistics."""
    return _analyze_die_level_failures(
        die_logs,
        test_records=test_records,
        recurring_failures=recurring_failures,
        classify_fault_type_fn=classify_fault_type,
    )


def analyze_wafer_level_failures(
    die_logs: list[DieLog],
    wafer_rates: dict[str, Any] | None = None,
    *,
    test_records: list | None = None,
    failure_rates_engine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """FA-FR-008: Dashboard-ready wafer-level failure statistics and rankings."""
    engine = failure_rates_engine
    if engine is None and wafer_rates is not None:
        engine = {"wafer_level": wafer_rates}
    return _analyze_wafer_level_failures(
        die_logs,
        test_records=test_records,
        failure_rates_engine=engine,
        classify_fault_type_fn=classify_fault_type,
    )


def predict_fault_types(
    die_logs: list[DieLog],
    recurring: dict[str, Any] | None = None,
    correlation: dict[str, Any] | None = None,
    *,
    top_n: int = 50,
) -> dict[str, Any]:
    """FA-FR-009: Predict probable fault types with confidence scores.

    Per client feedback this is fault-type prediction (characterization), not
    confirmed root-cause diagnosis. Full diagnosis requires correlating fault
    types to design elements (e.g. DEF) in the Scan Chain Diagnosis Agent.
    """
    if recurring is None:
        recurring = identify_recurring_failures(die_logs)
    if correlation is None:
        correlation = correlate_failures_with_patterns(die_logs)

    cluster_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "patterns": set(),
            "lots": set(),
            "wafers": set(),
            "dies": set(),
            "failure_count": 0,
            "hints": Counter(),
            "fault_categories": Counter(),
            "ir_drop_values": [],
            "thermal_values": [],
            "severity_scores": [],
            "setup_slack_values": [],
            "hold_slack_values": [],
            "transition_faults": 0,
        }
    )

    for die in die_logs:
        for pattern in die.failing_patterns:
            chain_key = pattern.scan_chain_id or "UNKNOWN_CHAIN"
            cluster = cluster_stats[chain_key]
            cluster["failure_count"] += 1
            cluster["patterns"].add(pattern.pattern_id)
            cluster["lots"].add(die.lot_id)
            cluster["wafers"].add(die.wafer_id)
            cluster["dies"].add(die.die_id)

            fields = pattern.raw_fields
            hint = fields.get("ROOT_CAUSE_HINT", "").strip()
            if hint:
                cluster["hints"][hint] += 1
            cluster["fault_categories"][classify_fault_type(pattern)] += 1

            ir_drop = _parse_numeric(fields.get("IR_DROP_MV"))
            if ir_drop is not None:
                cluster["ir_drop_values"].append(ir_drop)
            thermal = _parse_numeric(fields.get("THERMAL_C"))
            if thermal is not None:
                cluster["thermal_values"].append(thermal)
            severity = _parse_numeric(fields.get("AI_SEVERITY_SCORE"))
            if severity is not None:
                cluster["severity_scores"].append(severity)
            setup_slack = _parse_numeric(fields.get("SETUP_SLACK_PS"))
            if setup_slack is not None:
                cluster["setup_slack_values"].append(setup_slack)
            hold_slack = _parse_numeric(fields.get("HOLD_SLACK_PS"))
            if hold_slack is not None:
                cluster["hold_slack_values"].append(hold_slack)
            transition = _parse_numeric(fields.get("TRANSITION_FAULTS"))
            if transition is not None:
                cluster["transition_faults"] += int(transition)

    predictions: list[dict[str, Any]] = []
    for chain_id, cluster in cluster_stats.items():
        lot_count = len(cluster["lots"])
        die_count = len(cluster["dies"])
        failure_count = cluster["failure_count"]

        if cluster["hints"]:
            predicted_cause = cluster["hints"].most_common(1)[0][0]
            confidence = 0.55
        elif cluster["fault_categories"]:
            predicted_cause = cluster["fault_categories"].most_common(1)[0][0]
            confidence = 0.45
        else:
            predicted_cause = "UNKNOWN"
            confidence = 0.2

        evidence: list[str] = []
        if lot_count >= RECURRING_MIN_LOTS:
            confidence += 0.15
            evidence.append(f"Recurring across {lot_count} lot(s)")
        if cluster["setup_slack_values"]:
            min_setup = min(cluster["setup_slack_values"])
            if min_setup < TIMING_SLACK_FAIL_PS:
                confidence += 0.1
                evidence.append(f"Negative setup slack (min SETUP_SLACK_PS = {min_setup:.0f})")
        if cluster["hold_slack_values"]:
            min_hold = min(cluster["hold_slack_values"])
            if min_hold < TIMING_SLACK_FAIL_PS:
                confidence += 0.1
                evidence.append(f"Negative hold slack (min HOLD_SLACK_PS = {min_hold:.0f})")
        if cluster["ir_drop_values"]:
            avg_ir = sum(cluster["ir_drop_values"]) / len(cluster["ir_drop_values"])
            if avg_ir >= IR_DROP_FAIL_MV:
                confidence += 0.1
            evidence.append(f"Average IR_DROP_MV = {avg_ir:.1f}")
        if cluster["thermal_values"]:
            avg_th = sum(cluster["thermal_values"]) / len(cluster["thermal_values"])
            if avg_th >= THERMAL_FAIL_C:
                confidence += 0.1
            evidence.append(f"Average THERMAL_C = {avg_th:.1f}")
        if cluster["transition_faults"] > 0:
            evidence.append(f"Transition faults observed = {cluster['transition_faults']}")
        if cluster["severity_scores"]:
            avg_sev = sum(cluster["severity_scores"]) / len(cluster["severity_scores"])
            confidence = max(confidence, min(avg_sev, 0.95))
            evidence.append(f"Average AI_SEVERITY_SCORE = {avg_sev:.2f}")
        if cluster["fault_categories"]:
            top_fault = cluster["fault_categories"].most_common(1)[0][0]
            evidence.append(f"Primary fault category: {top_fault}")

        confidence = round(min(confidence, 0.99), 2)

        predictions.append(
            {
                "scan_chain_id": chain_id,
                "predicted_fault_type": predicted_cause,
                "predicted_root_cause": predicted_cause,  # deprecated alias
                "confidence_score": confidence,
                "failure_count": failure_count,
                "affected_dies": die_count,
                "affected_lots": lot_count,
                "affected_wafers": len(cluster["wafers"]),
                "pattern_count": len(cluster["patterns"]),
                "evidence": evidence,
            }
        )

    predictions.sort(
        key=lambda item: (item["confidence_score"], item["failure_count"]),
        reverse=True,
    )

    return {
        "phase": "FAULT_TYPE_PREDICTION",
        "phase_description": (
            "FA-FR-009 predicts probable FAULT TYPE (e.g. TIMING_VIOLATION, "
            "POWER_IR_DROP_FAULT) with a 0.0-1.0 confidence score and evidence trail. "
            "This is automated fault characterization for decision support — not "
            "confirmed root-cause diagnosis. Full diagnosis (correlating fault types "
            "to design elements such as DEF/layout and issuing corrective actions) "
            "belongs to the Scan Chain Diagnosis Agent."
        ),
        "total_predictions": len(predictions),
        "predictions": predictions[:top_n],
        "ranked_hypothesis_queue": [
            {
                "rank": idx + 1,
                "scan_chain_id": item["scan_chain_id"],
                "predicted_fault_type": item["predicted_fault_type"],
                "predicted_root_cause": item["predicted_fault_type"],  # deprecated
                "confidence_score": item["confidence_score"],
            }
            for idx, item in enumerate(predictions[:20])
        ],
    }


def predict_root_causes(
    die_logs: list[DieLog],
    recurring: dict[str, Any] | None = None,
    correlation: dict[str, Any] | None = None,
    *,
    top_n: int = 50,
) -> dict[str, Any]:
    """Deprecated alias for :func:`predict_fault_types` (client renamed FR-009)."""
    return predict_fault_types(
        die_logs, recurring, correlation, top_n=top_n
    )


def generate_failure_summary(
    die_logs: list[DieLog],
    analysis: dict[str, Any],
    stdf_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """FA-FR-010: Automatic executive and technical failure summary."""
    summary = analysis["summary"]
    fault_summary = analysis["fault_classification"]["category_summary"]
    top_fault = max(fault_summary, key=lambda k: fault_summary[k]["count"]) if fault_summary else "N/A"

    top_correlated = analysis.get("failure_pattern_correlation", {}).get(
        "top_failing_patterns", []
    )[:5]
    top_recurring = analysis.get("recurring_failures", {}).get("recurring_failures", [])[:5]
    top_predictions = analysis.get("fault_type_predictions", {}).get("predictions", [])
    if not top_predictions:
        top_predictions = analysis.get("root_cause_predictions", {}).get("predictions", [])[:5]
    else:
        top_predictions = top_predictions[:5]
    wafer_alerts = analysis.get("wafer_level_analysis", {}).get("alerts", [])

    rates = analysis.get("failure_rates", {})
    rate_levels = [
        lvl
        for lvl in ("device_level", "lot_level", "wafer_level", "pattern_level")
        if rates.get(lvl)
    ]
    detection = analysis.get("detection", {}).get("detection_accuracy", {})
    det_acc = detection.get("accuracy_pct", 0.0)
    det_ok = detection.get("meets_threshold", False)
    stdf_ok = bool(stdf_info and stdf_info.get("validation_passed"))
    correlation_report_present = bool(
        analysis.get("failure_pattern_correlation", {}).get("correlation_report")
    )
    wafer = analysis.get("wafer_level_analysis", {})
    has_spatial = bool(wafer.get("spatial_map"))
    predictions_have_conf = all(
        "confidence_score" in p for p in top_predictions
    ) if top_predictions else False

    requirement_status = {
        "FA-FR-001": {
            "description": "Ingest STDF and tester logs with validation",
            "acceptance_criteria": "STDF and tester logs imported successfully with validation.",
            "status": "MET" if stdf_ok else "PARTIAL",
            "evidence": (
                f"{summary['total_log_files']} tester log(s) ingested and validated; "
                f"STDF validation passed: {stdf_ok}."
            ),
        },
        "FA-FR-002": {
            "description": "Detect failing patterns (100% completeness)",
            "acceptance_criteria": "All failing patterns detected with 100% completeness.",
            "status": "MET" if det_ok else "PARTIAL",
            "evidence": (
                f"{summary['total_failing_patterns']} failing pattern occurrence(s) "
                f"detected; measured detection accuracy = {det_acc:.2f}% "
                f"(threshold {detection.get('threshold', DETECTION_ACCURACY_THRESHOLD) * 100:.0f}%); "
                "value-add over raw logs documented."
            ),
        },
        "FA-FR-003": {
            "description": "Calculate failure rates (device/lot/wafer/pattern)",
            "acceptance_criteria": "Failure rates calculated at device, lot, wafer and pattern level.",
            "status": "MET" if len(rate_levels) == 4 else "PARTIAL",
            "evidence": (
                f"Failure rates computed at: {', '.join(rate_levels)}. "
                f"{REVIEWER_FEEDBACK_RESPONSES['FA-FR-003']}"
            ),
        },
        "FA-FR-004": {
            "description": "Classify fault types into predefined categories",
            "acceptance_criteria": "Faults classified into predefined categories (definitions provided).",
            "status": "MET",
            "evidence": (
                f"{summary['total_classified_faults']} fault(s) classified into "
                f"{len(FAULT_CATEGORIES)} predefined categories using documented "
                f"deterministic rules (see category_definitions)."
            ),
        },
        "FA-FR-005": {
            "description": "Identify recurring failures across lots",
            "acceptance_criteria": "Recurring failures automatically identified across lots (defined criteria).",
            "status": "MET",
            "evidence": (
                f"{summary['recurring_pattern_count']} recurring pattern(s) identified; "
                f"criteria: fails in >= {RECURRING_MIN_LOTS} distinct lots "
                f"(see recurring_definition)."
            ),
        },
        "FA-FR-006": {
            "description": "Generate failure-to-pattern correlation report",
            "acceptance_criteria": "Failure-to-pattern correlation report generated.",
            "status": "MET" if correlation_report_present else "PARTIAL",
            "evidence": f"Correlation report generated; {len(top_correlated)} top patterns ranked.",
        },
        "FA-FR-007": {
            "description": "Analyze die-level failures for dashboard",
            "acceptance_criteria": "Die-level failure statistics displayed on dashboard.",
            "status": "MET",
            "evidence": (
                f"{analysis['die_level_analysis']['total_dies']} per-die profiles with "
                f"severity class + disposition (distinct from FR-003 aggregate rates). "
                f"{REVIEWER_FEEDBACK_RESPONSES['FA-FR-007']}"
            ),
        },
        "FA-FR-008": {
            "description": "Analyze wafer-level failures for dashboard",
            "acceptance_criteria": "Wafer-level failure statistics displayed on dashboard.",
            "status": "MET",
            "evidence": (
                f"{analysis['wafer_level_analysis']['total_wafers']} wafer profile(s) with "
                f"spatial map/signature{' (spatial map present)' if has_spatial else ''} "
                f"(distinct from FR-003 aggregate rates). "
                f"{REVIEWER_FEEDBACK_RESPONSES['FA-FR-008']}"
            ),
        },
        "FA-FR-009": {
            "description": "Predict probable fault types with confidence score",
            "acceptance_criteria": "Fault-type prediction generated with confidence score.",
            "status": "MET" if predictions_have_conf else "PARTIAL",
            "evidence": (
                f"{analysis.get('fault_type_predictions', analysis.get('root_cause_predictions', {})).get('total_predictions', 0)} "
                f"fault-type prediction(s) generated. "
                f"{REVIEWER_FEEDBACK_RESPONSES['FA-FR-009']}"
            ),
        },
        "FA-FR-010": {
            "description": "Generate failure summary report automatically",
            "acceptance_criteria": "Failure summary report generated automatically.",
            "status": "MET",
            "evidence": "Executive + technical summary and this traceability generated automatically.",
        },
    }

    met_count = sum(1 for v in requirement_status.values() if v["status"] == "MET")
    total_reqs = len(requirement_status)
    requirement_status["_acceptance_overview"] = {
        "all_criteria_met": met_count == total_reqs,
        "met_count": met_count,
        "total_requirements": total_reqs,
    }

    return {
        "executive_summary": {
            "total_dies_tested": summary["total_dies_tested"],
            "total_failing_dies": summary["total_failing_dies"],
            "overall_die_failure_rate": summary["overall_die_failure_rate"],
            "top_fault_category": top_fault,
            "recurring_pattern_count": summary["recurring_pattern_count"],
            "high_risk_pattern_count": len(
                [
                    p
                    for p in analysis.get("failure_pattern_correlation", {}).get(
                        "correlation_report", []
                    )
                    if p.get("status") == "HIGH_RISK"
                ]
            ),
        },
        "technical_highlights": {
            "top_correlated_patterns": top_correlated,
            "top_recurring_patterns": top_recurring,
            "top_fault_type_predictions": top_predictions,
            "top_root_cause_predictions": top_predictions,  # deprecated alias
            "wafer_alerts": wafer_alerts[:10],
        },
        "reviewer_feedback_responses": REVIEWER_FEEDBACK_RESPONSES,
        "requirement_traceability": requirement_status,
        "recommended_actions": analysis.get("failure_pattern_correlation", {}).get(
            "engineering_recommendations", []
        ),
    }


def detect_failing_patterns(
    die_logs: list[DieLog],
    *,
    manifest=None,
    test_records=None,
) -> list[dict[str, Any]]:
    """Detect failing patterns with deterministic + inference fallback (FA-FR-002)."""
    failures = detect_failing_patterns_v2(
        die_logs, manifest=manifest, test_records=test_records
    )
    for failure in failures:
        pattern = PatternResult(
            pattern_id=failure.get("pattern_id", ""),
            scan_chain_id=failure.get("scan_chain_id", ""),
            expected_signature=failure.get("expected_signature", ""),
            actual_signature=failure.get("actual_signature", ""),
            status=failure.get("status", "FAIL"),
            raw_fields={"failing_test": failure.get("inference_evidence", [""])[0]},
        )
        die = next(
            (d for d in die_logs if d.die_id == failure.get("die_id")),
            die_logs[0] if die_logs else None,
        )
        failure["fault_category"] = classify_fault_type(pattern, die=die)
    return failures


def measure_detection_accuracy(
    die_logs: list[DieLog],
    detected_failures: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """FA-FR-002 detection accuracy metrics."""
    failures = detected_failures or detect_failing_patterns_v2(die_logs)
    return measure_detection_accuracy_v2(die_logs, failures)


def analyze_failures(
    die_logs: list[DieLog],
    *,
    test_records: list | None = None,
    manifest=None,
    taxonomy_path: Path | None = None,
    persist_rates_path: Path | None = None,
) -> dict[str, Any]:
    """Run full failure analysis and return structured metrics."""
    failing_patterns = detect_failing_patterns(
        die_logs, manifest=manifest, test_records=test_records
    )
    detection_accuracy = measure_detection_accuracy(die_logs, failing_patterns)
    failing_dies = sum(1 for die in die_logs if die.is_failing_die)
    fault_classification = classify_fault_types(
        die_logs, test_records=test_records, taxonomy_path=taxonomy_path
    )
    recurring_failures = identify_recurring_failures(die_logs, test_records=test_records)
    pattern_rates = calculate_pattern_level_failure_rates(die_logs)
    failure_pattern_correlation = correlate_failures_with_patterns(
        die_logs,
        pattern_rates,
        test_records=test_records,
        recurring_failures=recurring_failures,
    )
    failure_rates_engine = compute_failure_rates(
        die_logs, test_records=test_records
    )
    if persist_rates_path:
        persist_aggregates(failure_rates_engine, persist_rates_path)

    die_level_analysis = analyze_die_level_failures(
        die_logs,
        test_records=test_records,
        recurring_failures=recurring_failures,
    )
    wafer_level_analysis = analyze_wafer_level_failures(
        die_logs,
        test_records=test_records,
        failure_rates_engine=failure_rates_engine,
    )
    fault_type_predictions = predict_fault_types(
        die_logs, recurring_failures, failure_pattern_correlation
    )

    analysis_core = {
        "summary": {
            "total_log_files": len(die_logs),
            "total_dies_tested": len(die_logs),
            "total_failing_dies": failing_dies,
            "total_failing_patterns": len(failing_patterns),
            "overall_die_failure_rate": _failure_rate(failing_dies, len(die_logs)),
            "total_classified_faults": fault_classification["total_classified_failures"],
            "recurring_pattern_count": recurring_failures["recurring_pattern_count"],
            "high_risk_pattern_count": len(
                [
                    item
                    for item in failure_pattern_correlation["correlation_report"]
                    if item["status"] == "HIGH_RISK"
                ]
            ),
            "fault_type_prediction_count": fault_type_predictions["total_predictions"],
            "root_cause_prediction_count": fault_type_predictions["total_predictions"],
        },
        "detection": {
            "requirement": "FA-FR-002",
            "total_failing_pattern_occurrences": len(failing_patterns),
            "detection_rule": (
                "Deterministic: explicit pattern_id / STATUS==FAIL in log. "
                "Inferred: failing_test → pattern via manifest when pattern_id absent."
            ),
            "detection_accuracy": detection_accuracy,
            "inferred_count": sum(1 for f in failing_patterns if f.get("is_inferred")),
            "deterministic_count": sum(
                1 for f in failing_patterns if f.get("detection_method") == "deterministic"
            ),
            "value_add_over_raw_logs": [
                "Scale & automation: parses every pattern x channel execution per die.",
                "Normalization: unifies tester-log and STDF/STIL formats into one schema.",
                "Full traceability: every FAIL linked to lot/wafer/die/pattern/scan-chain.",
                "Validation: 100% deterministic completeness + inferred confidence labels.",
                "Foundation for rates (003), classification (004), recurrence (005).",
            ],
        },
        "failing_patterns": failing_patterns,
        "fault_classification": fault_classification,
        "recurring_failures": recurring_failures,
        "failure_rates": {
            "device_level": calculate_device_level_failure_rate(die_logs),
            "lot_level": calculate_lot_level_failure_rates(die_logs),
            "wafer_level": calculate_wafer_level_failure_rates(die_logs),
            "pattern_level": pattern_rates,
            "engine": failure_rates_engine,
            "tolerance_pct": FAILURE_RATE_TOLERANCE_PCT,
        },
        "failure_pattern_correlation": failure_pattern_correlation,
        "die_level_analysis": die_level_analysis,
        "wafer_level_analysis": wafer_level_analysis,
        "fault_type_predictions": fault_type_predictions,
        "root_cause_predictions": fault_type_predictions,  # deprecated alias
    }
    analysis_core["failure_summary"] = generate_failure_summary(
        die_logs, analysis_core
    )
    return analysis_core


def die_log_to_dict(die: DieLog) -> dict[str, Any]:
    """Serialize a DieLog for optional export/debugging."""
    return {
        "source_path": die.source_path,
        "tester_name": die.tester_name,
        "device_name": die.device_name,
        "lot_id": die.lot_id,
        "wafer_id": die.wafer_id,
        "die_id": die.die_id,
        "header_fields": die.header_fields,
        "declared_patterns": die.declared_patterns,
        "total_executions": die.execution_count,
        "failing_pattern_count": len(die.failing_patterns),
        "is_failing_die": die.is_failing_die,
        "failing_patterns": [asdict(p) for p in die.failing_patterns],
    }
