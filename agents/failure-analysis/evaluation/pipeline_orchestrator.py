"""End-to-end evaluation orchestrator (independent of FA business engines)."""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from evaluation.ai_metrics import (
    compute_classification_metrics,
    engineering_score,
    recommendation_accuracy,
    similarity_accuracy,
)
from evaluation.benchmark_engine import BenchmarkEngine
from evaluation.dataset_discovery import DatasetDiscoveryEngine, load_evaluation_config
from evaluation.domain import DatasetBundle
from evaluation.module_runners import ModuleRunner, select_logs
from evaluation.report_generator import EvaluationReportGenerator
from evaluation.structured_logging import EvaluationLogger
from evaluation.training_pipeline import (
    ModelTrainingPipeline,
    extract_labels_from_csv,
    extract_labels_from_die_logs,
)
from evaluation.validation_engine import ValidationEngine
from evaluation.dashboard_data import build_evaluation_dashboard


class EvaluationOrchestrator:
    """
    Dataset discovery → FA pipeline → validation → AI metrics → training →
    benchmarks → engineering reports / dashboard.
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        self.config = load_evaluation_config(config_path)
        self.config_path = config_path
        self.discovery = DatasetDiscoveryEngine(config_path=config_path)
        self.validator = ValidationEngine(config=self.config)
        exec_cfg = self.config.get("execution", {})
        self.max_logs = int(exec_cfg.get("max_logs_per_dataset", 30))
        self.max_stil_bytes = int(exec_cfg.get("max_stil_bytes_for_full_parse", 50_000_000))
        self.default_modules = list(
            exec_cfg.get(
                "modules",
                [f"FA-FR-{i:03d}" for i in range(1, 11)],
            )
        )
        train_cfg = self.config.get("training", {})
        self.training = ModelTrainingPipeline(
            model_store_dir=Path(train_cfg.get("model_store_dir", "backend/storage/models")),
            test_size=float(train_cfg.get("test_size", 0.2)),
            validation_size=float(train_cfg.get("validation_size", 0.1)),
            random_state=int(train_cfg.get("random_state", 42)),
            min_labelled_samples=int(train_cfg.get("min_labelled_samples", 20)),
        )
        self.training_enabled = bool(train_cfg.get("enabled", True))
        self.labelled_csv_globs = list(train_cfg.get("labelled_csv_globs", []))
        report_cfg = self.config.get("reporting", {})
        self.reporter = EvaluationReportGenerator(
            output_dir=Path(report_cfg.get("output_dir", "backend/storage/evaluation_reports")),
            formats=list(report_cfg.get("formats", ["json", "csv", "excel", "pdf"])),
        )
        log_cfg = self.config.get("logging", {})
        self.log_dir = Path(log_cfg.get("log_dir", "backend/storage/evaluation_logs"))
        self.log_level = str(log_cfg.get("level", "INFO"))
        self.targets_ms = {
            str(k): float(v) for k, v in self.config.get("performance_targets_ms", {}).items()
        }

    def discover(self) -> dict[str, Any]:
        inventory = self.discovery.discover()
        return inventory.to_dict()

    def run(
        self,
        *,
        dataset_id: str | None = None,
        modules: list[str] | None = None,
        max_logs: int | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        execution_id = str(uuid.uuid4())
        inventory = self.discovery.discover()
        bundles = inventory.bundles
        if dataset_id:
            bundles = [b for b in bundles if b.dataset_id == dataset_id or b.scale_token == dataset_id]
            if not bundles:
                raise ValueError(f"Dataset not found: {dataset_id}")

        # Prefer concrete scale bundles over unmatched
        bundles = [b for b in bundles if b.scale_token != "unmatched"] or bundles
        selected_modules = modules or self.default_modules
        limit = self.max_logs if max_logs is None else max_logs

        dataset_results: list[dict[str, Any]] = []
        for bundle in bundles:
            dataset_results.append(
                self._evaluate_bundle(
                    bundle=bundle,
                    modules=selected_modules,
                    max_logs=limit,
                    execution_id=execution_id,
                    inventory_warnings=inventory.warnings,
                )
            )

        overall = self._aggregate(dataset_results, inventory.to_dict(), execution_id)
        overall["processing_ms"] = round((time.perf_counter() - start) * 1000, 3)
        overall["export_paths"] = self.reporter.generate(overall)
        overall["dashboard"] = build_evaluation_dashboard(overall)
        return overall

    def run_module(
        self,
        module: str,
        *,
        dataset_id: str | None = None,
        max_logs: int | None = None,
    ) -> dict[str, Any]:
        return self.run(
            dataset_id=dataset_id,
            modules=[module],
            max_logs=max_logs,
        )

    def _evaluate_bundle(
        self,
        *,
        bundle: DatasetBundle,
        modules: list[str],
        max_logs: int,
        execution_id: str,
        inventory_warnings: list[str],
    ) -> dict[str, Any]:
        elog = EvaluationLogger(
            log_dir=self.log_dir,
            level=self.log_level,
            execution_id=execution_id,
            dataset_name=bundle.dataset_id,
        )
        bench = BenchmarkEngine()
        runner = ModuleRunner(bench)
        module_outputs: dict[str, Any] = {}
        raw_reports: dict[str, Any] = {}

        logs = select_logs(bundle.preferred_logs, max_logs)
        if not logs and not bundle.stil_paths:
            elog.log(
                module="discovery",
                status="WARNING",
                message="No logs or STIL available for bundle; skipping execution.",
            )
            return {
                "dataset": bundle.to_dict(),
                "module_outputs": {},
                "validation": [],
                "warnings": bundle.warnings + ["Empty dataset bundle"],
                "ai_evaluation": {},
                "training": {"trained": False, "reason": "No data"},
                "benchmark": bench.summarize(targets_ms=self.targets_ms),
                "execution_logs": elog.history(),
            }

        # FA-FR-001
        if "FA-FR-001" in modules:
            ingest = runner.ingest_dataset(
                stil_path=bundle.primary_stil,
                log_paths=logs,
                max_stil_bytes=self.max_stil_bytes,
            )
            module_outputs["FA-FR-001"] = {
                k: v for k, v in ingest.items() if k not in {"test_records", "die_logs"}
            }
            raw_reports["FA-FR-001"] = ingest
            elog.log(
                module="FA-FR-001",
                status="PASS" if ingest.get("record_count", 0) else "FAIL",
                duration_ms=float(ingest.get("duration_ms", 0)),
                message=f"records={ingest.get('record_count')}",
            )
            die_logs = ingest.get("die_logs", [])
            test_records = ingest.get("test_records", [])
        else:
            # Still need data for downstream modules
            ingest = runner.ingest_dataset(
                stil_path=bundle.primary_stil,
                log_paths=logs,
                max_stil_bytes=self.max_stil_bytes,
            )
            die_logs = ingest.get("die_logs", [])
            test_records = ingest.get("test_records", [])

        if not die_logs:
            validation = self.validator.validate_all(module_outputs)
            return {
                "dataset": bundle.to_dict(),
                "module_outputs": module_outputs,
                "validation": [v.to_dict() for v in validation],
                "warnings": bundle.warnings + inventory_warnings + ["No die logs parsed"],
                "ai_evaluation": {},
                "training": {"trained": False, "reason": "No die logs"},
                "benchmark": bench.summarize(targets_ms=self.targets_ms),
                "execution_logs": elog.history(),
            }

        module_map = {
            "FA-FR-002": lambda: runner.run_fr002(die_logs, test_records),
            "FA-FR-003": lambda: runner.run_fr003(die_logs, test_records),
            "FA-FR-004": lambda: runner.run_fr004(die_logs, test_records),
            "FA-FR-005": lambda: runner.run_fr005(die_logs, test_records),
            "FA-FR-006": lambda: runner.run_fr006(die_logs, test_records),
            "FA-FR-007": lambda: runner.run_fr007(die_logs, test_records),
            "FA-FR-008": lambda: runner.run_fr008(die_logs, test_records),
            "FA-FR-009": lambda: runner.run_fr009(die_logs, test_records),
        }

        for module, fn in module_map.items():
            if module not in modules:
                continue
            try:
                result = fn()
                raw_reports[module] = result.get("report", result)
                module_outputs[module] = {
                    k: v for k, v in result.items() if k != "report" and k != "detected"
                }
                elog.log(
                    module=module,
                    status="PASS",
                    duration_ms=float(result.get("duration_ms", 0)),
                    message="completed",
                )
            except Exception as exc:
                module_outputs[module] = {
                    "requirement": module,
                    "error": str(exc),
                    "duration_ms": 0.0,
                }
                elog.log(
                    module=module,
                    status="FAIL",
                    message="exception during module execution",
                    exception=str(exc),
                )

        if "FA-FR-010" in modules:
            try:
                upload_meta = {
                    "upload_id": f"eval-{bundle.dataset_id}",
                    "original_filename": bundle.dataset_id,
                    "records_accepted": len(test_records),
                }
                # Map module outputs into reporting-friendly shapes
                mapped = {
                    "root_cause": raw_reports.get("FA-FR-009", {}),
                    "die": raw_reports.get("FA-FR-007", {}),
                    "wafer": raw_reports.get("FA-FR-008", {}),
                    "classification": raw_reports.get("FA-FR-004", {}),
                }
                result = runner.run_fr010(
                    die_logs,
                    test_records,
                    upload_meta=upload_meta,
                    module_outputs=mapped,
                )
                raw_reports["FA-FR-010"] = result.get("report", result)
                module_outputs["FA-FR-010"] = {
                    k: v for k, v in result.items() if k != "report"
                }
                elog.log(
                    module="FA-FR-010",
                    status="PASS",
                    duration_ms=float(result.get("duration_ms", 0)),
                    message="report generated",
                )
            except Exception as exc:
                module_outputs["FA-FR-010"] = {
                    "requirement": "FA-FR-010",
                    "error": str(exc),
                }
                elog.log(
                    module="FA-FR-010",
                    status="FAIL",
                    exception=str(exc),
                    message="report generation failed",
                )

        validation = self.validator.validate_all(module_outputs)
        ai_eval = self._ai_evaluate(module_outputs, raw_reports, die_logs)
        training = self._train_if_possible(die_logs, bundle)

        for item in validation:
            elog.log(
                module=f"validate:{item.module}",
                status=item.status.value,
                duration_ms=item.duration_ms,
                message=item.explanation,
            )

        return {
            "dataset": bundle.to_dict(),
            "logs_evaluated": len(logs),
            "module_outputs": module_outputs,
            "validation": [v.to_dict() for v in validation],
            "warnings": bundle.warnings + inventory_warnings,
            "ai_evaluation": ai_eval,
            "training": training,
            "benchmark": bench.summarize(targets_ms=self.targets_ms),
            "execution_logs": elog.history(),
        }

    def _ai_evaluate(
        self,
        module_outputs: dict[str, Any],
        raw_reports: dict[str, Any],
        die_logs: list[Any],
    ) -> dict[str, Any]:
        y_true: list[str] = []
        y_pred: list[str] = []
        confidences: list[float] = []

        class_report = raw_reports.get("FA-FR-004", {})
        if isinstance(class_report, dict):
            classified_dies = {
                str(f.get("die_id", "")) for f in class_report.get("classified_faults", [])
            }
            for die in die_logs:
                die_id = str(getattr(die, "die_id", ""))
                header = getattr(die, "header_fields", {}) or {}
                source = str(getattr(die, "source_path", "")).lower()
                raw_label = (
                    header.get("DIE_LABEL")
                    or header.get("DEFECT_TYPE")
                    or ("FAIL" if "fail_die" in source else "PASS" if "good_die" in source else "")
                )
                if not raw_label:
                    continue
                truth = str(raw_label).upper()
                # Normalize binary labels for pass/fail scoring when taxonomy differs
                if truth in {"FAIL", "PASS"}:
                    pred = "FAIL" if die_id in classified_dies or getattr(die, "is_failing_die", False) else "PASS"
                    y_true.append(truth)
                    y_pred.append(pred)
                    confidences.append(1.0 if truth == pred else 0.3)
                else:
                    # Defect-type labels: compare against dominant die classification when available
                    die_classes = [
                        f
                        for f in class_report.get("classified_faults", [])
                        if str(f.get("die_id", "")) == die_id
                    ]
                    if die_classes:
                        pred = str(die_classes[0].get("fault_category", "Unknown"))
                        conf = float(die_classes[0].get("classification_confidence", 0.5))
                    else:
                        pred = "Unknown"
                        conf = 0.2
                    y_true.append(truth)
                    y_pred.append(pred)
                    confidences.append(conf)

        # Fallback: pass/fail prediction vs die failing flag
        if not y_true:
            for die in die_logs:
                truth = "FAIL" if getattr(die, "is_failing_die", False) else "PASS"
                pred = "FAIL" if getattr(die, "failing_patterns", None) else "PASS"
                y_true.append(truth)
                y_pred.append(pred)
                confidences.append(1.0 if truth == pred else 0.4)

        metrics = compute_classification_metrics(y_true, y_pred, confidences=confidences)
        metrics["engineering_score"] = engineering_score(metrics)

        root = module_outputs.get("FA-FR-009", {})
        root_report = raw_reports.get("FA-FR-009", {})
        similar = (
            root_report.get("similar_historical_cases", [])
            if isinstance(root_report, dict)
            else []
        )
        recommendations = (
            root_report.get("engineering_recommendations", [])
            if isinstance(root_report, dict)
            else []
        )
        metrics["similarity_accuracy"] = similarity_accuracy(
            retrieved_relevant=sum(1 for c in similar if c.get("similarity_score", 0) >= 0.35),
            retrieved_total=max(len(similar), 1),
        )
        metrics["recommendation_accuracy"] = recommendation_accuracy(recommendations)
        metrics["prediction_confidence"] = float(root.get("average_confidence", 0.0))
        return metrics

    def _train_if_possible(self, die_logs: list[Any], bundle: DatasetBundle) -> dict[str, Any]:
        if not self.training_enabled:
            return {"trained": False, "reason": "Training disabled in config"}

        rows = extract_labels_from_die_logs(die_logs)
        for tabular in bundle.tabular_paths:
            if tabular.suffix.lower() != ".csv":
                continue
            try:
                rows.extend(extract_labels_from_csv(tabular))
            except Exception:
                continue

        # Also search labelled CSV globs under tabular parents / roots
        for root in self.discovery.search_roots:
            for pattern in self.labelled_csv_globs:
                for csv_path in root.glob(pattern):
                    if not csv_path.is_file():
                        continue
                    try:
                        rows.extend(extract_labels_from_csv(csv_path))
                    except Exception:
                        continue

        try:
            return self.training.train_from_labelled_rows(rows)
        except Exception as exc:
            return {
                "trained": False,
                "reason": f"Training failed: {exc}",
                "sample_count": len(rows),
            }

    def _aggregate(
        self,
        dataset_results: list[dict[str, Any]],
        inventory: dict[str, Any],
        execution_id: str,
    ) -> dict[str, Any]:
        pass_fail = {"PASS": 0, "FAIL": 0, "WARNING": 0, "SKIPPED": 0}
        for result in dataset_results:
            for item in result.get("validation", []):
                status = item.get("status", "WARNING")
                pass_fail[status] = pass_fail.get(status, 0) + 1

        return {
            "requirement": "EVAL-FRAMEWORK",
            "execution_id": execution_id,
            "inventory": inventory,
            "dataset_results": dataset_results,
            "pass_fail_summary": pass_fail,
            "datasets_evaluated": len(dataset_results),
            "latest_training": next(
                (
                    r.get("training")
                    for r in dataset_results
                    if r.get("training", {}).get("trained")
                ),
                dataset_results[0].get("training") if dataset_results else {},
            ),
        }
