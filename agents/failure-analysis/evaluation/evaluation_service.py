"""Service layer for the evaluation framework."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from evaluation.evaluation_repository import EvaluationRepository
from evaluation.pipeline_orchestrator import EvaluationOrchestrator


class EvaluationService:
    def __init__(
        self,
        repo: EvaluationRepository,
        *,
        config_path: Path | str | None = None,
    ) -> None:
        self.repo = repo
        self.orchestrator = EvaluationOrchestrator(config_path=config_path)

    async def discover(self) -> dict[str, Any]:
        return self.orchestrator.discover()

    async def run_evaluation(
        self,
        *,
        dataset_id: str | None = None,
        modules: list[str] | None = None,
        max_logs: int | None = None,
    ) -> dict[str, Any]:
        report = self.orchestrator.run(
            dataset_id=dataset_id,
            modules=modules,
            max_logs=max_logs,
        )
        run = await self.repo.save_run(report)
        return {
            "execution_id": run.id,
            "processing_ms": report["processing_ms"],
            "datasets_evaluated": report["datasets_evaluated"],
            "pass_fail_summary": report["pass_fail_summary"],
            "inventory": report["inventory"],
            "dataset_results": report["dataset_results"],
            "latest_training": report.get("latest_training"),
            "dashboard": report.get("dashboard"),
            "export_paths": report.get("export_paths"),
        }

    async def get_dashboard(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No evaluation runs found")
        return {
            "execution_id": run.id,
            "dashboard": run.dashboard_json,
            "pass_fail_summary": {
                "PASS": run.pass_count,
                "FAIL": run.fail_count,
                "WARNING": run.warning_count,
            },
            "model_version": run.model_version,
        }

    async def get_report(self, run_id: str | None = None) -> dict[str, Any]:
        run = await self.repo.get_latest_or(run_id)
        if run is None:
            raise ValueError("No evaluation runs found")
        return {
            "execution_id": run.id,
            "report": run.report_json,
            "export_paths": run.export_paths,
        }
