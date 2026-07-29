"""Run failure analysis across multiple LOT directories in one batch."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from analyzer import analyze_failures
from ingestor import ingest_logs
from main import build_report, configure_logging, export_dashboard_data, export_report
from stdf_ingestor import ingest_stdf, stdf_result_to_dict
from stil_ingestor import ingest_stil_file, stil_result_to_dict, validate_stil_against_logs
from evaluation.data_roots import default_stil_file, primary_dataset_root

BASE = primary_dataset_root()
if BASE is None:
    raise SystemExit(
        "Dataset root not found. Set DATASET_ROOT or EVALUATION_DATA_ROOTS, "
        "or place data under ~/Desktop/verilumen labs"
    )
LOT_DIRS = sorted(
    p.name
    for p in BASE.iterdir()
    if p.is_dir() and p.name.startswith("LOT_") and any(p.glob("*.log"))
)
STIL_FILE = default_stil_file(BASE) or (BASE / "Production_SCAN_stuck_at_Full.stil")
REPORT_PATH = Path("failure_analysis_report.json")
DASHBOARD_PATH = Path("dashboard_data.json")


def main() -> int:
    configure_logging(verbose=False)
    logger = logging.getLogger("multi_lot_run")

    die_logs = []
    ingestion_errors: list[dict] = []
    lot_stats: list[tuple[str, int, int]] = []
    for lot in LOT_DIRS:
        lot_path = BASE / lot
        logs, errs = ingest_logs(lot_path, recursive=False)
        die_logs.extend(logs)
        ingestion_errors.extend(errs)
        failing = sum(1 for d in logs if d.is_failing_die)
        lot_stats.append((lot, len(logs), failing))
        logger.info("Lot %s: %d log(s) ingested, %d failing die(s)", lot, len(logs), failing)

    if not die_logs:
        logger.error("No logs were successfully ingested.")
        return 1

    stdf_result = ingest_stdf(BASE, die_logs)
    stdf_info = stdf_result_to_dict(stdf_result)

    stil_result = ingest_stil_file(STIL_FILE)
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

    analysis = analyze_failures(die_logs)
    report = build_report(
        BASE,
        die_logs,
        analysis,
        ingestion_errors,
        stdf_info,
        stil_info,
        cross_validation,
    )
    export_report(report, REPORT_PATH)
    export_dashboard_data(analysis, DASHBOARD_PATH)

    summary = analysis["summary"]
    det = analysis["detection"]["detection_accuracy"]
    exec_summary = analysis["failure_summary"]["executive_summary"]

    print("=== FULL FAILURE ANALYSIS (ALL LOTS) ===")
    print(f"Lots processed     : {len(LOT_DIRS)}")
    print(f"Log files ingested : {len(die_logs)}")
    print(f"Failing dies       : {summary['total_failing_dies']}/{summary['total_dies_tested']}")
    print(f"Die failure rate   : {summary['overall_die_failure_rate'] * 100:.2f}%")
    print(f"Failing patterns   : {summary['total_failing_patterns']}")
    print(f"Recurring patterns : {summary['recurring_pattern_count']}")
    print(f"Detection accuracy : {det['accuracy_pct']}% (meets={det['meets_threshold']})")
    print(f"Fault-type preds   : {summary.get('fault_type_prediction_count', summary.get('root_cause_prediction_count', 0))}")
    print(f"Top fault category : {exec_summary['top_fault_category']}")
    print("--- Per-lot breakdown ---")
    for lot, total, failing in lot_stats:
        rate = (failing / total * 100) if total else 0
        print(f"  {lot}: {failing}/{total} failing dies ({rate:.0f}%)")
    print(f"Report written     : {REPORT_PATH.resolve()}")
    print(f"Dashboard written  : {DASHBOARD_PATH.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
