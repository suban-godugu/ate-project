"""Failure Analysis Agent — orchestrates ingestion, analysis, and reporting."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from analyzer import analyze_failures
from ingestion_service import export_ingestion_report, ingest_directory
from ingestor import ingest_logs
from pattern_detection import load_pattern_manifest
from stdf_ingestor import ingest_stdf, stdf_result_to_dict
from stil_ingestor import (
    ingest_stil_file,
    stil_result_to_dict,
    validate_stil_against_logs,
)
from evaluation.data_roots import default_stil_file, primary_dataset_root

_resolved_root = primary_dataset_root()
DEFAULT_LOG_DIR = _resolved_root or Path(".")
DEFAULT_STIL_FILE = default_stil_file(_resolved_root) or Path("Production_SCAN_stuck_at_Full.stil")
DEFAULT_REPORT_PATH = Path("failure_analysis_report.json")
DEFAULT_DASHBOARD_PATH = Path("dashboard_data.json")
DEFAULT_INGESTION_REPORT_PATH = Path("ingestion_report.json")
DEFAULT_RATE_AGGREGATES_PATH = Path("data/failure_rate_aggregates.json")
DEFAULT_PATTERN_MANIFEST = Path("config/pattern_manifest.yaml")
DEFAULT_FAULT_TAXONOMY = Path("config/fault_taxonomy.yaml")
RECURRING_FAILURES_REPORT_LIMIT = 100
CORRELATION_REPORT_LIMIT = 50
ROOT_CAUSE_REPORT_LIMIT = 50
DIE_DASHBOARD_LIMIT = 135
WAFER_DASHBOARD_LIMIT = 130


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def build_report(
    log_dir: Path,
    die_logs: list,
    analysis: dict,
    ingestion_errors: list[dict],
    stdf_info: dict,
    stil_info: dict,
    cross_validation: dict,
    ingestion_report: dict | None = None,
    *,
    include_all_failures: bool = False,
) -> dict:
    correlation = analysis["failure_pattern_correlation"]
    die_level = analysis["die_level_analysis"]
    wafer_level = analysis["wafer_level_analysis"]
    root_causes = analysis.get("fault_type_predictions") or analysis["root_cause_predictions"]
    failure_summary = analysis["failure_summary"]

    ingestion_ok = (
        stdf_info.get("validation_passed")
        and stil_info.get("validation_passed")
        and not ingestion_errors
    )
    traceability = failure_summary["requirement_traceability"]
    traceability["FA-FR-001"] = {
        "description": "Ingest STDF, STIL, and tester logs with validation",
        "acceptance_criteria": "STDF and tester logs imported successfully with validation.",
        "status": "MET" if ingestion_ok else "PARTIAL",
        "evidence": (
            f"{len(die_logs)} tester logs; "
            f"STDF records: {stdf_info.get('stdf_records_count', 0)}; "
            f"STIL patterns: {stil_info.get('metadata', {}).get('pattern_count_verified', 0)}; "
            f"STIL chains: {stil_info.get('scan_chain_count', 0)}; "
            f"cross-validation: {cross_validation.get('passed')}"
        ),
    }
    fr_entries = [v for k, v in traceability.items() if k.startswith("FA-FR")]
    met_count = sum(1 for v in fr_entries if v.get("status") == "MET")
    traceability["_acceptance_overview"] = {
        "all_criteria_met": met_count == len(fr_entries),
        "met_count": met_count,
        "total_requirements": len(fr_entries),
    }

    analysis_payload = {
        "summary": analysis["summary"],
        "detection": analysis["detection"],
        "failure_summary": failure_summary,
        "failure_rates": analysis["failure_rates"],
        "fault_classification": {
            "predefined_categories": analysis["fault_classification"][
                "predefined_categories"
            ],
            "category_definitions": analysis["fault_classification"][
                "category_definitions"
            ],
            "classification_method": analysis["fault_classification"][
                "classification_method"
            ],
            "classification_thresholds": analysis["fault_classification"][
                "classification_thresholds"
            ],
            "total_classified_failures": analysis["fault_classification"][
                "total_classified_failures"
            ],
            "category_summary": analysis["fault_classification"]["category_summary"],
            "source_fail_type_counts": analysis["fault_classification"][
                "source_fail_type_counts"
            ],
            "method_counts": analysis["fault_classification"].get("method_counts", {}),
            "die_classifications": analysis["fault_classification"].get("die_classifications", []),
            "ml_enabled": analysis["fault_classification"].get("ml_enabled", False),
        },
        "recurring_failures": {
            "min_lots_threshold": analysis["recurring_failures"]["min_lots_threshold"],
            "recurring_definition": analysis["recurring_failures"][
                "recurring_definition"
            ],
            "total_unique_failing_patterns": analysis["recurring_failures"][
                "total_unique_failing_patterns"
            ],
            "recurring_pattern_count": analysis["recurring_failures"][
                "recurring_pattern_count"
            ],
            "non_recurring_pattern_count": analysis["recurring_failures"][
                "non_recurring_pattern_count"
            ],
            "recurring_failures": analysis["recurring_failures"]["recurring_failures"][
                :RECURRING_FAILURES_REPORT_LIMIT
            ],
            "signature_summary": analysis["recurring_failures"].get("signature_summary", {}),
            "recurrence_events": analysis["recurring_failures"].get("recurrence_events", [])[
                :RECURRING_FAILURES_REPORT_LIMIT
            ],
            "entity_index": analysis["recurring_failures"].get("entity_index", {}),
            "min_entities_threshold": analysis["recurring_failures"].get(
                "min_entities_threshold"
            ),
            "failure_share_threshold": analysis["recurring_failures"].get(
                "failure_share_threshold"
            ),
            "note": (
                f"Showing top {RECURRING_FAILURES_REPORT_LIMIT} recurring patterns "
                "ranked by lot spread. Use --include-all-failures for the full list."
            ),
        },
        "failure_pattern_correlation": {
            "baseline_failure_rate": correlation["baseline_failure_rate"],
            "ranking_method": correlation.get("ranking_method", ""),
            "weights": correlation.get("weights", {}),
            "high_risk_threshold": correlation.get("high_risk_threshold"),
            "top_failing_patterns": correlation["top_failing_patterns"],
            "engineering_recommendations": correlation["engineering_recommendations"],
            "correlation_report": correlation["correlation_report"][
                :CORRELATION_REPORT_LIMIT
            ],
            "correlation_report_total": len(correlation["correlation_report"]),
            "downstream_export": correlation.get("downstream_export", {}),
            "note": (
                f"Showing top {CORRELATION_REPORT_LIMIT} of "
                f"{len(correlation['correlation_report'])} correlated patterns."
            ),
        },
        "die_level_analysis": {
            "purpose": die_level["purpose"],
            "differentiator_vs_fa_fr_003": die_level["differentiator_vs_fa_fr_003"],
            "total_dies": die_level["total_dies"],
            "failing_dies": die_level["failing_dies"],
            "dashboard_feed": die_level["dashboard_feed"][:DIE_DASHBOARD_LIMIT],
        },
        "wafer_level_analysis": {
            "purpose": wafer_level["purpose"],
            "differentiator_vs_fa_fr_003": wafer_level["differentiator_vs_fa_fr_003"],
            "total_wafers": wafer_level["total_wafers"],
            "wafer_ranking": wafer_level["wafer_ranking"],
            "heatmap_data": wafer_level["heatmap_data"][:WAFER_DASHBOARD_LIMIT],
            "spatial_map": wafer_level["spatial_map"][:WAFER_DASHBOARD_LIMIT],
            "alerts": wafer_level["alerts"],
            "dashboard_feed": wafer_level["dashboard_feed"][:WAFER_DASHBOARD_LIMIT],
        },
        "fault_type_predictions": {
            "phase": root_causes["phase"],
            "phase_description": root_causes["phase_description"],
            "total_predictions": root_causes["total_predictions"],
            "ranked_hypothesis_queue": root_causes["ranked_hypothesis_queue"],
            "predictions": root_causes["predictions"][:ROOT_CAUSE_REPORT_LIMIT],
        },
        "root_cause_predictions": {
            "phase": root_causes["phase"],
            "phase_description": root_causes["phase_description"],
            "total_predictions": root_causes["total_predictions"],
            "ranked_hypothesis_queue": root_causes["ranked_hypothesis_queue"],
            "predictions": root_causes["predictions"][:ROOT_CAUSE_REPORT_LIMIT],
            "note": "Deprecated alias; see fault_type_predictions (client FR-009 rename).",
        },
    }

    if include_all_failures:
        analysis_payload["failing_patterns"] = analysis["failing_patterns"]
        analysis_payload["fault_classification"]["classified_failures"] = analysis[
            "fault_classification"
        ]["classified_failures"]
        analysis_payload["recurring_failures"]["recurring_failures"] = analysis[
            "recurring_failures"
        ]["recurring_failures"]
        analysis_payload["recurring_failures"].pop("note", None)
        analysis_payload["failure_pattern_correlation"]["correlation_report"] = (
            correlation["correlation_report"]
        )
        analysis_payload["die_level_analysis"]["dashboard_feed"] = die_level[
            "dashboard_feed"
        ]
        analysis_payload["wafer_level_analysis"]["dashboard_feed"] = wafer_level[
            "dashboard_feed"
        ]
        analysis_payload["root_cause_predictions"]["predictions"] = root_causes[
            "predictions"
        ]
    else:
        analysis_payload["failing_patterns_summary"] = {
            "total_failing_pattern_occurrences": analysis["summary"][
                "total_failing_patterns"
            ],
            "note": (
                "Full per-occurrence failing pattern list omitted from the default "
                "report. Re-run with --include-all-failures for complete export."
            ),
        }

    return {
        "report_metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_directory": str(log_dir),
            "agent": "Failure Analysis Agent — Scan Chain",
            "requirements": {
                "FA-FR-001": "Ingest STDF, STIL, and tester logs with validation (ASCII/custom formats)",
                "FA-FR-002": "Detect failing patterns (100% completeness)",
                "FA-FR-003": "Calculate failure rates at device, lot, wafer, pattern level",
                "FA-FR-004": "Classify fault types into predefined categories",
                "FA-FR-005": "Identify recurring failures across lots",
                "FA-FR-006": "Generate failure-to-pattern correlation report",
                "FA-FR-007": "Analyze die-level failures for dashboard",
                "FA-FR-008": "Analyze wafer-level failures for dashboard",
                "FA-FR-009": "Predict probable fault types with confidence score",
                "FA-FR-010": "Generate failure summary report automatically",
            },
        },
        "ingestion": {
            "tester_logs": {
                "files_discovered": len(die_logs) + len(ingestion_errors),
                "files_parsed_successfully": len(die_logs),
                "files_failed": len(ingestion_errors),
                "errors": ingestion_errors,
            },
            "adapter_pipeline": ingestion_report,
            "stdf": stdf_info,
            "stil": stil_info,
            "cross_validation": cross_validation,
        },
        "analysis": analysis_payload,
    }


def export_dashboard_data(analysis: dict, output_path: Path) -> None:
    """Export compact dashboard feed for FA-FR-007 and FA-FR-008 UI integration."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "die_level_dashboard": analysis["die_level_analysis"]["dashboard_feed"],
        "die_spatial_ai_handoff": analysis["die_level_analysis"].get("spatial_ai_handoff", []),
        "wafer_level_dashboard": analysis["wafer_level_analysis"]["dashboard_feed"],
        "wafer_heatmap": analysis["wafer_level_analysis"]["heatmap_data"],
        "wafer_spatial_map": analysis["wafer_level_analysis"]["spatial_map"],
        "wafer_alerts": analysis["wafer_level_analysis"]["alerts"],
        "wafer_outlier_count": analysis["wafer_level_analysis"].get("outlier_wafer_count", 0),
        "lot_sequence_trends": analysis["wafer_level_analysis"].get("lot_sequence_trends", []),
        "top_correlated_patterns": analysis["failure_pattern_correlation"][
            "top_failing_patterns"
        ],
        "executive_summary": analysis["failure_summary"]["executive_summary"],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def export_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    logging.getLogger(__name__).info("Report written to %s", output_path.resolve())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Failure Analysis Agent for ATE scan chain tester logs."
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_LOG_DIR,
        help="Root directory containing tester .log files (searched recursively).",
    )
    parser.add_argument(
        "--stil-file",
        type=Path,
        default=DEFAULT_STIL_FILE,
        help="Path to STIL scan test file (ATPG pattern definition).",
    )
    parser.add_argument(
        "--stdf-dir",
        type=Path,
        default=None,
        help="Optional directory to search for STDF files (defaults to --log-dir).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_REPORT_PATH,
        help="Path for the JSON failure analysis report.",
    )
    parser.add_argument(
        "--dashboard-output",
        type=Path,
        default=DEFAULT_DASHBOARD_PATH,
        help="Path for dashboard-ready JSON feed.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search sub-directories of --log-dir for .log files (default: top-level only).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    parser.add_argument(
        "--include-all-failures",
        action="store_true",
        help="Include full failure, correlation, and prediction lists in the report.",
    )
    parser.add_argument(
        "--use-adapter-ingestion",
        action="store_true",
        help="Use FA-FR-001 plugin adapter pipeline (STDF + YAML ASCII + CSV).",
    )
    parser.add_argument(
        "--ingestion-report",
        type=Path,
        default=DEFAULT_INGESTION_REPORT_PATH,
        help="Path for adapter ingestion report JSON.",
    )
    parser.add_argument(
        "--pattern-manifest",
        type=Path,
        default=DEFAULT_PATTERN_MANIFEST,
        help="YAML pattern manifest for FA-FR-002 inference fallback.",
    )
    parser.add_argument(
        "--fault-taxonomy",
        type=Path,
        default=DEFAULT_FAULT_TAXONOMY,
        help="YAML fault taxonomy for FA-FR-004 rule + ML classification.",
    )
    parser.add_argument(
        "--persist-rates",
        type=Path,
        default=None,
        help="Persist FA-FR-003 rate aggregates to JSON (default when --use-adapter-ingestion).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    logger = logging.getLogger(__name__)

    log_dir = args.log_dir
    stdf_dir = args.stdf_dir or log_dir
    if not log_dir.is_dir():
        logger.error("Log directory not found: %s", log_dir)
        return 1

    logger.info("Starting Failure Analysis Agent")
    logger.info("Reading tester logs from: %s", log_dir.resolve())
    logger.info("Searching STDF files in: %s", stdf_dir.resolve())

    die_logs: list = []
    ingestion_errors: list[dict] = []
    ingestion_report_dict: dict | None = None
    test_records: list = []

    if args.use_adapter_ingestion:
        logger.info("Using plugin adapter ingestion pipeline (FA-FR-001 Phase 1)")
        test_records, die_logs, ingestion_report = ingest_directory(
            log_dir, recursive=args.recursive, use_legacy_fallback=True
        )
        ingestion_report_dict = ingestion_report.to_dict()
        ingestion_errors = ingestion_report.errors
        export_ingestion_report(ingestion_report, args.ingestion_report)
        logger.info(
            "Adapter ingestion: %d records, %.2f%% integrity",
            ingestion_report.records_accepted,
            ingestion_report.integrity_pct,
        )
    else:
        die_logs, ingestion_errors = ingest_logs(log_dir, recursive=args.recursive)

    if not die_logs:
        logger.error("No logs were successfully ingested.")
        return 1

    stdf_result = ingest_stdf(stdf_dir, die_logs)
    stdf_info = stdf_result_to_dict(stdf_result)

    stil_info: dict = {"validation_passed": False, "errors": ["STIL file not provided"]}
    cross_validation: dict = {"passed": False, "notes": []}
    if args.stil_file and args.stil_file.is_file():
        logger.info("Ingesting STIL file: %s", args.stil_file.resolve())
        stil_result = ingest_stil_file(args.stil_file)
        stil_info = stil_result_to_dict(stil_result)

        die_pattern_count = die_logs[0].declared_patterns if die_logs else 0
        log_scan_chains: set[str] = set()
        for die in die_logs:
            for pattern in die.failing_patterns[:100]:
                if pattern.scan_chain_id:
                    log_scan_chains.add(pattern.scan_chain_id)

        stil_passed, stil_notes = validate_stil_against_logs(
            stil_result, die_pattern_count, log_scan_chains
        )
        cross_validation = {
            "passed": stil_passed and stdf_info.get("validation_passed", False),
            "stil_log_validation": stil_passed,
            "stdf_validation": stdf_info.get("validation_passed", False),
            "notes": stil_notes + stdf_info.get("validation_notes", []),
        }
        stil_info["cross_validation_notes"] = stil_notes
    else:
        logger.warning("STIL file not found at %s — skipping STIL ingestion", args.stil_file)

    manifest = load_pattern_manifest(args.pattern_manifest)
    persist_rates = args.persist_rates
    if persist_rates is None and args.use_adapter_ingestion:
        persist_rates = DEFAULT_RATE_AGGREGATES_PATH

    analysis = analyze_failures(
        die_logs,
        test_records=test_records or None,
        manifest=manifest,
        taxonomy_path=args.fault_taxonomy,
        persist_rates_path=persist_rates,
    )
    report = build_report(
        log_dir,
        die_logs,
        analysis,
        ingestion_errors,
        stdf_info,
        stil_info,
        cross_validation,
        ingestion_report_dict,
        include_all_failures=args.include_all_failures,
    )
    export_report(report, args.output)
    export_dashboard_data(analysis, args.dashboard_output)

    summary = analysis["summary"]
    exec_summary = analysis["failure_summary"]["executive_summary"]
    logger.info("Ingested %d tester log file(s)", len(die_logs))
    logger.info("STDF validation passed: %s", stdf_info["validation_passed"])
    logger.info("STIL validation passed: %s", stil_info.get("validation_passed"))
    logger.info("Cross-validation passed: %s", cross_validation.get("passed"))
    logger.info("Detected %d failing pattern occurrence(s)", summary["total_failing_patterns"])
    det_acc = analysis["detection"]["detection_accuracy"]
    logger.info(
        "Detection accuracy: %.2f%% (threshold %.0f%%, meets=%s)",
        det_acc["accuracy_pct"],
        det_acc.get("threshold", 1.0) * 100,
        det_acc["meets_threshold"],
    )
    logger.info("Overall die failure rate: %.2f%%", summary["overall_die_failure_rate"] * 100)
    logger.info("Classified %d faults", summary["total_classified_faults"])
    logger.info("Recurring patterns: %d", summary["recurring_pattern_count"])
    logger.info("High-risk correlated patterns: %d", summary["high_risk_pattern_count"])
    logger.info(
        "Fault-type predictions: %d",
        summary.get("fault_type_prediction_count", summary["root_cause_prediction_count"]),
    )
    logger.info("Wafer alerts: %d", len(analysis["wafer_level_analysis"]["alerts"]))
    logger.info("Top fault category: %s", exec_summary["top_fault_category"])
    logger.info("Dashboard data written to %s", args.dashboard_output.resolve())
    logger.info("Failure analysis complete.")

    all_ok = (
        not ingestion_errors
        and stdf_info["validation_passed"]
        and stil_info.get("validation_passed", False)
    )
    return 0 if all_ok else 2


if __name__ == "__main__":
    sys.exit(main())
