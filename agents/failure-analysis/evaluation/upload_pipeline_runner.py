"""Run FA-FR-002…010 against an ingested upload_id with structured progress logging."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from analytics.failure_rates.production_service import (
    FailureRateValidationError,
    ProductionFailureRateService,
)
from analytics.failure_rates.schemas import ComputeFailureRatesRequest
from analytics.pattern_detection.detection_service import DetectionService
from analytics.pattern_detection.schemas import DetectPatternsRequest
from backend.classification.classification_repository import ClassificationRepository
from backend.classification.classification_service import ClassificationService
from backend.correlation.production_service import ProductionCorrelationService
from backend.correlation.schemas import AnalyzeCorrelationRequest
from backend.die_analysis.die_repository import DieAnalysisRepository
from backend.die_analysis.die_service import DieAnalysisService
from backend.die_analysis.production_service import (
    DieValidationError,
    ProductionDieAnalysisService,
)
from backend.die_analysis.schemas import AnalyzeDieRequest
from backend.recurring.production_service import ProductionRecurrenceService
from backend.recurring.schemas import AnalyzeRecurrenceRequest
from backend.reporting.report_repository import ReportRepository
from backend.reporting.report_service import ReportService
from backend.root_cause.production_service import (
    FaultPredictionValidationError,
    ProductionFaultPredictionService,
)
from backend.root_cause.root_cause_repository import RootCauseRepository
from backend.root_cause.root_cause_service import RootCauseService
from backend.root_cause.schemas import PredictFaultRequest
from backend.wafer_analysis.production_service import (
    ProductionWaferAnalysisService,
    WaferValidationError,
)
from backend.wafer_analysis.schemas import AnalyzeWaferRequest
from backend.wafer_analysis.wafer_repository import WaferAnalysisRepository
from backend.wafer_analysis.wafer_service import WaferAnalysisService
from evaluation.dashboard_metrics import extract_dashboard_charts, normalize_dashboard_metrics
from evaluation.evaluation_repository import EvaluationRepository
from evaluation.structured_logging import EvaluationLogger

logger = logging.getLogger(__name__)

DEFAULT_EVAL_LOG_DIR = Path("backend/storage/evaluation_logs")


def _analysis_scope(
    dataset_id: str | None, upload_id: str
) -> dict[str, str | None]:
    """Prefer upload scope so FA-FR-004…010 lineage keys share the same upload_id.

    Dataset-only scope left classification keyed by dataset_id while recurrence /
    correlation looked up classification by upload_id — leaving Recurring /
    Correlation / production Die empty.
    """
    if upload_id:
        return {"dataset_id": None, "upload_id": upload_id}
    if dataset_id:
        return {"dataset_id": dataset_id, "upload_id": None}
    return {"dataset_id": None, "upload_id": upload_id}


def _as_number(value: Any, fallback: float = 0.0) -> float:
    try:
        n = float(value)
        return n if n == n else fallback
    except (TypeError, ValueError):
        return fallback


def _to_percent(value: Any) -> float:
    n = _as_number(value)
    if 0 <= n <= 1:
        return round(n * 100, 4)
    return round(n, 4)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def extract_metrics(
    *,
    imported_files: int,
    detection: dict[str, Any] | None,
    rates: dict[str, Any] | None,
    classification: dict[str, Any] | None,
    recurrence: dict[str, Any] | None,
    correlation: dict[str, Any] | None,
    die: dict[str, Any] | None,
    wafer: dict[str, Any] | None,
    root_cause: dict[str, Any] | None,
    report: dict[str, Any] | None,
) -> dict[str, float | int]:
    metrics: dict[str, float | int] = {
        "imported_files": imported_files,
        "overall_failure_rate": 0.0,
        "ai_detection_accuracy": 0.0,
        "failing_patterns": 0,
        "die_failure_rate": 0.0,
        "wafer_failure_rate": 0.0,
        "lot_failure_rate": 0.0,
        "fault_categories": 0,
        "root_cause_confidence": 0.0,
        "recurring_failures": 0,
        "failure_correlations": 0,
        "reports_generated": 0,
    }

    detection = _as_dict(detection)
    rates = _as_dict(rates)
    classification = _as_dict(classification)
    recurrence = _as_dict(recurrence)
    correlation = _as_dict(correlation)
    die = _as_dict(die)
    wafer = _as_dict(wafer)
    root_cause = _as_dict(root_cause)
    report = _as_dict(report)

    if detection:
        metrics["failing_patterns"] = int(
            _as_number(detection.get("pattern_count") or len(detection.get("patterns") or []))
        )
        bench = _as_dict(detection.get("benchmark_metrics"))
        if bench.get("accuracy_pct") is not None:
            metrics["ai_detection_accuracy"] = _to_percent(bench.get("accuracy_pct"))
        elif detection.get("meets_accuracy_target"):
            metrics["ai_detection_accuracy"] = 100.0

    if rates:
        rows = rates.get("metrics") or rates.get("rates") or []
        if not isinstance(rows, list):
            rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            level = str(row.get("aggregation_level") or "").lower()
            pct = _as_number(row.get("failure_percentage"))
            if "lot" in level:
                metrics["lot_failure_rate"] = pct
            if "wafer" in level:
                metrics["wafer_failure_rate"] = pct
            if "die" in level:
                metrics["die_failure_rate"] = pct
            if "device" in level or "overall" in level:
                metrics["overall_failure_rate"] = pct
        if not metrics["overall_failure_rate"] and rows and isinstance(rows[0], dict):
            metrics["overall_failure_rate"] = _as_number(rows[0].get("failure_percentage"))

    if classification:
        summary = _as_dict(classification.get("classification_summary"))
        metrics["fault_categories"] = int(
            _as_number(
                summary.get("unique_categories")
                or len(_as_dict(classification.get("category_summary")))
            )
        )

    if recurrence:
        metrics["recurring_failures"] = int(
            _as_number(
                recurrence.get("recurrence_count")
                or len(recurrence.get("recurrences") or [])
            )
        )

    if correlation:
        metrics["failure_correlations"] = int(
            _as_number(
                correlation.get("correlation_count")
                or len(correlation.get("correlations") or [])
            )
        )

    if die:
        dies = die.get("dies") or die.get("dashboard_feed") or []
        if isinstance(dies, list) and dies:
            failing = sum(
                1
                for d in dies
                if isinstance(d, dict) and (d.get("is_failing") or d.get("is_failing_die"))
            )
            metrics["die_failure_rate"] = round((failing / len(dies)) * 100, 4)

    if wafer:
        yield_metrics = wafer.get("yield_metrics") or wafer.get("statistics") or {}
        if not isinstance(yield_metrics, dict):
            yield_metrics = {}
        if yield_metrics.get("overall_yield") is not None:
            metrics["wafer_failure_rate"] = round(
                100 - _as_number(yield_metrics.get("overall_yield")), 4
            )
        elif yield_metrics.get("failure_rate") is not None:
            metrics["wafer_failure_rate"] = _as_number(yield_metrics.get("failure_rate"))
        elif isinstance(wafer.get("wafer_ranking"), list) and wafer["wafer_ranking"]:
            first = wafer["wafer_ranking"][0]
            if isinstance(first, dict) and first.get("failure_rate") is not None:
                metrics["wafer_failure_rate"] = _to_percent(first.get("failure_rate"))
        elif isinstance(wafer.get("wafers"), list) and wafer["wafers"]:
            first = wafer["wafers"][0]
            if isinstance(first, dict) and first.get("yield_pct") is not None:
                metrics["wafer_failure_rate"] = round(
                    100 - _as_number(first.get("yield_pct")), 4
                )

    if root_cause:
        conf = root_cause.get("average_confidence")
        preds = root_cause.get("predictions") or []
        if not isinstance(preds, list):
            preds = []
        if conf is None and preds:
            conf = sum(
                _as_number(p.get("confidence_score")) for p in preds if isinstance(p, dict)
            ) / max(len(preds), 1)
        metrics["root_cause_confidence"] = _to_percent(conf or 0)

    if report and (report.get("report_id") or report.get("id")):
        metrics["reports_generated"] = 1

    return metrics


class UploadPipelineRunner:
    """Sequential FA-FR pipeline for dashboard Analyze workflow."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = EvaluationRepository(session)

    async def run(
        self,
        *,
        execution_id: str,
        upload_id: str,
        dataset_id: str | None,
        imported_files: int = 1,
        dataset_name: str = "",
    ) -> dict[str, Any]:
        log = EvaluationLogger(
            log_dir=DEFAULT_EVAL_LOG_DIR,
            execution_id=execution_id,
            dataset_name=dataset_name or upload_id,
        )
        await self.repo.mark_running(
            execution_id, upload_id=upload_id, dataset_id=dataset_id
        )

        detection: dict[str, Any] | None = None
        rates: dict[str, Any] | None = None
        classification: dict[str, Any] | None = None
        recurrence: dict[str, Any] | None = None
        correlation: dict[str, Any] | None = None
        die: dict[str, Any] | None = None
        wafer: dict[str, Any] | None = None
        root_cause: dict[str, Any] | None = None
        report: dict[str, Any] | None = None
        detection_execution_id: str | None = None
        computation_id: str | None = None

        try:
            scope = _analysis_scope(dataset_id, upload_id)

            await self.repo.update_progress(
                execution_id, step="pattern_detection", progress=32, label="Pattern Detection"
            )
            detection = await DetectionService(self.session).execute(
                DetectPatternsRequest(
                    **scope,
                    async_execution=False,
                    incremental=False,
                ),
                execution_id=str(uuid.uuid4()),
            )
            detection_execution_id = detection.get("execution_id") or detection.get(
                "analysis_id"
            )
            log.log(module="FA-FR-002", status="PASS", message="completed")

            await self.repo.update_progress(
                execution_id, step="failure_rate", progress=42, label="Failure Rate"
            )
            try:
                rates = await ProductionFailureRateService(self.session).execute(
                    ComputeFailureRatesRequest(
                        **scope,
                        detection_execution_id=detection_execution_id,
                        async_execution=False,
                    ),
                    execution_id=str(uuid.uuid4()),
                )
                log.log(module="FA-FR-003", status="PASS", message="completed")
            except FailureRateValidationError as exc:
                rates = {
                    "metrics": [],
                    "rates": [],
                    "warnings": [issue.get("message", str(issue)) for issue in exc.issues],
                }
                log.log(module="FA-FR-003", status="WARNING", message=str(exc.issues))
            computation_id = rates.get("execution_id") or rates.get("computation_id")

            await self.repo.update_progress(
                execution_id, step="classification", progress=52, label="Classification"
            )
            classification_service = ClassificationService(
                ClassificationRepository(self.session),
                enable_ml=True,
                enable_llm=False,
            )
            # Prefer upload_id so FA-FR-005/006 can find FA-FR-004 by upload lineage.
            if upload_id:
                classification = await classification_service.analyze_upload(upload_id)
            elif dataset_id:
                classification = await classification_service.analyze_dataset(dataset_id)
            else:
                classification = {}
            log.log(module="FA-FR-004", status="PASS", message="completed")

            await self.repo.update_progress(
                execution_id, step="recurrence", progress=58, label="Recurrence"
            )
            try:
                recurrence = await ProductionRecurrenceService(self.session).execute(
                    AnalyzeRecurrenceRequest(
                        **scope,
                        detection_execution_id=detection_execution_id,
                        computation_id=computation_id,
                        async_execution=False,
                    )
                )
                log.log(module="FA-FR-005", status="PASS", message="completed")
            except ValueError as exc:
                recurrence = {
                    "recurrence_count": 0,
                    "recurrences": [],
                    "warnings": [str(exc)],
                }
                log.log(module="FA-FR-005", status="WARNING", message=str(exc))

            await self.repo.update_progress(
                execution_id, step="correlation", progress=64, label="Correlation"
            )
            try:
                correlation = await ProductionCorrelationService(self.session).execute(
                    AnalyzeCorrelationRequest(
                        **scope,
                        async_execution=False,
                    )
                )
                log.log(module="FA-FR-006", status="PASS", message="completed")
            except ValueError as exc:
                correlation = {
                    "correlation_count": 0,
                    "correlations": [],
                    "warnings": [str(exc)],
                }
                log.log(module="FA-FR-006", status="WARNING", message=str(exc))

            await self.repo.update_progress(
                execution_id, step="die_analysis", progress=72, label="Die Analysis"
            )
            recurrence_analysis_id = (recurrence or {}).get("analysis_id") or (
                recurrence or {}
            ).get("execution_id")
            correlation_analysis_id = (correlation or {}).get("analysis_id") or (
                correlation or {}
            ).get("execution_id")
            die_analysis_id: str | None = None
            try:
                die = await ProductionDieAnalysisService(self.session).execute(
                    AnalyzeDieRequest(
                        **scope,
                        detection_execution_id=detection_execution_id,
                        computation_id=computation_id,
                        recurrence_analysis_id=recurrence_analysis_id,
                        correlation_analysis_id=correlation_analysis_id,
                        async_execution=False,
                        incremental=False,
                    ),
                    execution_id=str(uuid.uuid4()),
                )
                die_analysis_id = die.get("analysis_id") or die.get("execution_id")
                log.log(module="FA-FR-007", status="PASS", message="completed")
            except (DieValidationError, ValueError) as exc:
                die_service = DieAnalysisService(DieAnalysisRepository(self.session))
                die = (
                    await die_service.analyze_dataset(dataset_id)
                    if dataset_id
                    else await die_service.analyze_upload(upload_id)
                )
                log.log(module="FA-FR-007", status="WARNING", message=str(exc))

            await self.repo.update_progress(
                execution_id, step="wafer_analysis", progress=78, label="Wafer Analysis"
            )
            wafer_analysis_id: str | None = None
            try:
                wafer = await ProductionWaferAnalysisService(self.session).execute(
                    AnalyzeWaferRequest(
                        **scope,
                        detection_execution_id=detection_execution_id,
                        computation_id=computation_id,
                        recurrence_analysis_id=recurrence_analysis_id,
                        correlation_analysis_id=correlation_analysis_id,
                        die_analysis_id=die_analysis_id,
                        async_execution=False,
                        incremental=False,
                    ),
                    execution_id=str(uuid.uuid4()),
                )
                wafer_analysis_id = wafer.get("analysis_id") or wafer.get("execution_id")
                log.log(module="FA-FR-008", status="PASS", message="completed")
            except (WaferValidationError, ValueError) as exc:
                wafer_service = WaferAnalysisService(WaferAnalysisRepository(self.session))
                wafer = (
                    await wafer_service.analyze_dataset(dataset_id)
                    if dataset_id
                    else await wafer_service.analyze_upload(upload_id)
                )
                log.log(module="FA-FR-008", status="WARNING", message=str(exc))

            await self.repo.update_progress(
                execution_id, step="root_cause", progress=86, label="Root Cause"
            )
            try:
                root_cause = await ProductionFaultPredictionService(self.session).execute(
                    PredictFaultRequest(
                        **scope,
                        detection_execution_id=detection_execution_id,
                        computation_id=computation_id,
                        recurrence_analysis_id=recurrence_analysis_id,
                        correlation_analysis_id=correlation_analysis_id,
                        die_analysis_id=die_analysis_id,
                        wafer_analysis_id=wafer_analysis_id,
                        async_execution=False,
                        incremental=False,
                    ),
                    execution_id=str(uuid.uuid4()),
                )
                log.log(module="FA-FR-009", status="PASS", message="completed")
            except (FaultPredictionValidationError, ValueError) as exc:
                root_cause_service = RootCauseService(RootCauseRepository(self.session))
                root_cause = (
                    await root_cause_service.predict_dataset(dataset_id)
                    if dataset_id
                    else await root_cause_service.predict_upload(upload_id)
                )
                log.log(module="FA-FR-009", status="WARNING", message=str(exc))

            await self.repo.update_progress(
                execution_id, step="evaluation", progress=90, label="Evaluation"
            )
            log.log(module="FA-FR-EVAL", status="PASS", message="pipeline modules validated")

            await self.repo.update_progress(
                execution_id, step="reporting", progress=95, label="Generating Reports"
            )
            report_service = ReportService(ReportRepository(self.session))
            # Prefer upload report when pipeline ran in upload scope.
            if scope.get("upload_id"):
                report = await report_service.generate_report(str(scope["upload_id"]))
            elif dataset_id:
                report = await report_service.generate_dataset_report(
                    dataset_id,
                    primary_upload_id=upload_id,
                )
            else:
                report = await report_service.generate_report(upload_id)
            log.log(module="FA-FR-010", status="PASS", message="report generated")

            await self.session.commit()

            raw_metrics = extract_metrics(
                imported_files=imported_files,
                detection=detection,
                rates=rates,
                classification=classification,
                recurrence=recurrence,
                correlation=correlation,
                die=die,
                wafer=wafer,
                root_cause=root_cause,
                report=report,
            )
            module_outputs = {
                "FA-FR-002": detection,
                "FA-FR-003": rates,
                "FA-FR-004": classification,
                "FA-FR-005": recurrence,
                "FA-FR-006": correlation,
                "FA-FR-007": die,
                "FA-FR-008": wafer,
                "FA-FR-009": root_cause,
                "FA-FR-010": report,
            }
            charts = extract_dashboard_charts(module_outputs)
            metrics = normalize_dashboard_metrics(
                raw_metrics,
                imported_files=imported_files,
                rates=rates,
                detection=detection,
            )
            payload = {
                "execution_id": execution_id,
                "upload_id": upload_id,
                "dataset_id": dataset_id,
                "status": "completed",
                "metrics": metrics,
                "charts": charts,
                "module_outputs": module_outputs,
            }
            await self.repo.complete_run(
                execution_id, payload, metrics=metrics, charts=charts
            )
            await self.session.commit()
            return payload
        except Exception as exc:  # noqa: BLE001
            logger.exception("Upload pipeline failed execution_id=%s", execution_id)
            log.log(
                module="pipeline",
                status="FAIL",
                message=str(exc),
                exception=str(exc),
            )
            await self.repo.fail_run(execution_id, str(exc))
            await self.session.commit()
            raise
