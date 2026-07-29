"""In-process runners that invoke existing FA-FR engines without modifying them."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adapters.registry import default_registry
from adapters.schema import TestRecord
from evaluation.benchmark_engine import BenchmarkEngine
from stil_ingestor import ingest_stil_file


class ModuleRunner:
    """Strategy-style runners for FA-FR-001..010 against in-memory datasets."""

    def __init__(self, benchmark: BenchmarkEngine) -> None:
        self.benchmark = benchmark
        self.registry = default_registry()

    def ingest_dataset(
        self,
        *,
        stil_path: Path | None,
        log_paths: list[Path],
        max_stil_bytes: int,
    ) -> dict[str, Any]:
        stil_info: dict[str, Any] = {}
        if stil_path and stil_path.is_file():
            size = stil_path.stat().st_size
            if size <= max_stil_bytes:

                def _parse_stil() -> Any:
                    return ingest_stil_file(stil_path)

                stil_result, sample = self.benchmark.measure("parsing", _parse_stil)
                stil_info = {
                    "stil_path": str(stil_path),
                    "pattern_count": stil_result.metadata.total_patterns
                    or stil_result.pattern_count_verified,
                    "stil_validation_passed": stil_result.validation_passed,
                    "stil_notes": stil_result.validation_notes,
                    "scan_chain_count": len(stil_result.scan_chains),
                    "file_size_bytes": stil_result.file_size_bytes,
                    "duration_ms": sample.duration_ms,
                }
            else:
                stil_info = {
                    "stil_path": str(stil_path),
                    "pattern_count": None,
                    "stil_validation_passed": True,
                    "stil_notes": [
                        f"STIL size {size} exceeds parse threshold {max_stil_bytes}; "
                        "metadata-only deferred (warning)."
                    ],
                    "file_size_bytes": size,
                    "duration_ms": 0.0,
                    "skipped_full_parse": True,
                }

        records: list[TestRecord] = []
        parse_errors: list[str] = []

        def _parse_logs() -> list[TestRecord]:
            parsed: list[TestRecord] = []
            for path in log_paths:
                adapter = self.registry.resolve(path)
                if adapter is None:
                    parse_errors.append(f"No adapter for {path}")
                    continue
                result = adapter.parse(path)
                parsed.extend(result.records)
                for err in result.errors:
                    parse_errors.append(str(err))
            return parsed

        records, log_sample = self.benchmark.measure("upload", _parse_logs)
        pattern_ids: set[str] = set()
        for rec in records:
            pattern_ids.update(rec.failing_patterns or [])

        from adapters.bridge import test_records_to_die_logs

        die_logs = test_records_to_die_logs(records)
        stil_pattern_count = stil_info.get("pattern_count")
        pattern_count = len(pattern_ids) or (
            int(stil_pattern_count) if stil_pattern_count is not None else 0
        )
        payload = {
            **stil_info,
            "requirement": "FA-FR-001",
            "record_count": len(records),
            "die_count": len(die_logs),
            "pattern_count": pattern_count,
            "parse_errors": parse_errors,
            "duration_ms": log_sample.duration_ms + float(stil_info.get("duration_ms") or 0),
            "test_records": records,
            "die_logs": die_logs,
        }
        return payload

    def run_fr002(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from analyzer import detect_failing_patterns, measure_detection_accuracy

        def _run() -> dict[str, Any]:
            detected = detect_failing_patterns(die_logs, test_records=test_records)
            accuracy = measure_detection_accuracy(die_logs, detected)
            return {
                "requirement": "FA-FR-002",
                "detected_count": len(detected),
                "detection_accuracy": accuracy,
                "accuracy_pct": accuracy.get("accuracy_pct", 0.0),
                "false_positives": accuracy.get("false_positives"),
                "false_negatives": accuracy.get("false_negatives"),
                "detected": detected,
            }

        result, sample = self.benchmark.measure("pattern_detection", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr003(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from failure_rate_engine import compute_failure_rates

        def _run() -> dict[str, Any]:
            rates = compute_failure_rates(die_logs, test_records=test_records)
            levels = [k for k in ("device_level", "lot_level", "wafer_level", "pattern_level") if rates.get(k)]
            return {
                "requirement": "FA-FR-003",
                "levels_present": levels,
                "rates": rates,
            }

        result, sample = self.benchmark.measure("failure_rates", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr004(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from backend.classification.classification_engine import ClassificationEngine

        def _run() -> dict[str, Any]:
            report = ClassificationEngine().analyze(
                die_logs=die_logs, test_records=test_records
            )
            faults = report.get("classified_faults", [])
            confidences = [
                float(f.get("classification_confidence", 0.0)) for f in faults
            ]
            methods = dict(report.get("method_counts", {}))
            if not methods:
                for fault in faults:
                    method = str(fault.get("method", "unknown"))
                    methods[method] = methods.get(method, 0) + 1
            summary = report.get("classification_summary", {})
            return {
                "requirement": "FA-FR-004",
                "total_faults": int(
                    report.get("total_classified_failures", len(faults))
                ),
                "average_confidence": (
                    sum(confidences) / len(confidences) if confidences else 0.0
                ),
                "unique_categories": summary.get("unique_categories")
                or len(report.get("category_summary", {})),
                "methods": methods,
                "report": report,
            }

        result, sample = self.benchmark.measure("classification", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr005(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from backend.recurring.recurring_engine import RecurringEngine

        def _run() -> dict[str, Any]:
            report = RecurringEngine().analyze(
                die_logs=die_logs, test_records=test_records
            )
            recurring_list = report.get(
                "recurring_failure_list",
                report.get("recurrence_events", []),
            )
            similarity = report.get("similarity_report", {})
            return {
                "requirement": "FA-FR-005",
                "executed": True,
                "recurring_count": len(recurring_list),
                "frequency_summary": report.get("frequency_distribution"),
                "similarity_pairs": (
                    similarity.get("pair_count")
                    if isinstance(similarity, dict)
                    else None
                ),
                "report": report,
            }

        result, sample = self.benchmark.measure("recurring", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr006(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from backend.correlation.correlation_engine import CorrelationEngine

        def _run() -> dict[str, Any]:
            report = CorrelationEngine().analyze(
                die_logs=die_logs, test_records=test_records
            )
            corr = report.get("correlation_report", report.get("legacy_report", {}))
            rows = corr if isinstance(corr, list) else corr.get("correlation_report", [])
            return {
                "requirement": "FA-FR-006",
                "correlation_rows": len(rows),
                "has_matrix": bool(report.get("correlation_matrix")),
                "report": report,
            }

        result, sample = self.benchmark.measure("correlation", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr007(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from backend.die_analysis.die_engine import DieAnalysisEngine

        def _run() -> dict[str, Any]:
            report = DieAnalysisEngine().analyze(
                die_logs=die_logs, test_records=test_records
            )
            return {
                "requirement": "FA-FR-007",
                "total_dies": report.get("total_dies", 0),
                "hotspot_count": report.get("hotspot_analysis", {}).get("hotspot_count"),
                "has_heatmap": bool(report.get("die_heatmap") or report.get("heatmap")),
                "report": report,
            }

        result, sample = self.benchmark.measure("die_analysis", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr008(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from backend.wafer_analysis.wafer_engine import WaferAnalysisEngine

        def _run() -> dict[str, Any]:
            report = WaferAnalysisEngine().analyze(
                die_logs=die_logs, test_records=test_records
            )
            return {
                "requirement": "FA-FR-008",
                "total_wafers": report.get("total_wafers", 0),
                "has_heatmap": bool(report.get("wafer_heatmap")),
                "has_clusters": bool(report.get("cluster_report", {}).get("cluster_count", 0)),
                "has_edge_center": bool(report.get("edge_center_analysis")),
                "has_radial": bool(report.get("radial_failure_analysis")),
                "report": report,
            }

        result, sample = self.benchmark.measure("wafer_analysis", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr009(self, die_logs: list[Any], test_records: list[TestRecord]) -> dict[str, Any]:
        from backend.root_cause.root_cause_engine import RootCauseEngine

        def _run() -> dict[str, Any]:
            report = RootCauseEngine().predict(
                die_logs=die_logs, test_records=test_records
            )
            return {
                "requirement": "FA-FR-009",
                "total_predictions": report.get("total_predictions", 0),
                "average_confidence": report.get("average_confidence", 0.0),
                "has_historical_cases": bool(report.get("similar_historical_cases")),
                "has_recommendations": bool(report.get("engineering_recommendations")),
                "report": report,
            }

        result, sample = self.benchmark.measure("root_cause", _run)
        result["duration_ms"] = sample.duration_ms
        return result

    def run_fr010(
        self,
        die_logs: list[Any],
        test_records: list[TestRecord],
        *,
        upload_meta: dict[str, Any],
        module_outputs: dict[str, Any],
    ) -> dict[str, Any]:
        from backend.reporting.report_engine import ReportEngine

        def _run() -> dict[str, Any]:
            report = ReportEngine().generate(
                die_logs=die_logs,
                test_records=test_records,
                upload_meta=upload_meta,
                module_outputs=module_outputs,
            )
            exports = report.get("export_paths", {})
            return {
                "requirement": "FA-FR-010",
                "has_executive_summary": bool(report.get("executive_report")),
                "has_engineering_summary": bool(report.get("engineering_report")),
                "has_dashboard": bool(report.get("dashboard_dataset")),
                "exports": {
                    "pdf": bool(exports.get("pdf")),
                    "excel": bool(exports.get("excel")),
                    "json": bool(exports.get("json")),
                },
                "report": report,
            }

        result, sample = self.benchmark.measure("report_generation", _run)
        result["duration_ms"] = sample.duration_ms
        return result


def select_logs(paths: list[Path], max_logs: int) -> list[Path]:
    if max_logs <= 0 or len(paths) <= max_logs:
        return paths
    # Prefer diversity across lots: round-robin by parent folder
    by_parent: dict[str, list[Path]] = {}
    for path in paths:
        by_parent.setdefault(path.parent.name, []).append(path)
    selected: list[Path] = []
    parents = list(by_parent.keys())
    idx = 0
    while len(selected) < max_logs and parents:
        parent = parents[idx % len(parents)]
        bucket = by_parent[parent]
        if bucket:
            selected.append(bucket.pop(0))
        if not bucket:
            parents.remove(parent)
            if not parents:
                break
            idx = idx % len(parents)
            continue
        idx += 1
    return selected
