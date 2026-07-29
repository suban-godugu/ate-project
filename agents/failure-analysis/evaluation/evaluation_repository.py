"""Persistence for evaluation executions."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import EvaluationRun, ModelTrainingRun


class EvaluationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_run(self, report: dict[str, Any]) -> EvaluationRun:
        pass_fail = report.get("pass_fail_summary", {})
        training = report.get("latest_training") or {}
        run = EvaluationRun(
            id=str(report.get("execution_id")),
            status=str(report.get("status") or "completed"),
            processing_ms=float(report.get("processing_ms", 0.0)),
            datasets_evaluated=int(report.get("datasets_evaluated", 0)),
            pass_count=int(pass_fail.get("PASS", 0)),
            fail_count=int(pass_fail.get("FAIL", 0)),
            warning_count=int(pass_fail.get("WARNING", 0)),
            model_version=str(training.get("model_version") or ""),
            report_json=report,
            dashboard_json=report.get("dashboard", {}),
            export_paths=report.get("export_paths", {}),
        )
        self._session.add(run)
        await self._session.flush()

        if training.get("trained"):
            train_row = ModelTrainingRun(
                evaluation_run_id=run.id,
                model_name=str(training.get("model_name", "")),
                model_version=str(training.get("model_version", "")),
                validation_accuracy=float(training.get("validation_accuracy", 0.0)),
                sample_count=int(training.get("sample_count", 0)),
                artifact_path=str(training.get("model_path", "")),
                comparison_json=training.get("comparisons", []),
                metadata_json=training,
            )
            self._session.add(train_row)
            await self._session.flush()
        return run

    async def create_pending_run(
        self,
        execution_id: str,
        *,
        upload_id: str | None = None,
        dataset_id: str | None = None,
        dataset_name: str = "",
    ) -> EvaluationRun:
        run = EvaluationRun(
            id=execution_id,
            status="pending",
            report_json={
                "execution_id": execution_id,
                "upload_id": upload_id,
                "dataset_id": dataset_id,
                "dataset_name": dataset_name,
                "progress": 28,
                "current_step": "pattern_detection",
                "label": "Pattern Detection",
            },
            dashboard_json={},
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def mark_running(
        self,
        execution_id: str,
        *,
        upload_id: str | None = None,
        dataset_id: str | None = None,
    ) -> None:
        run = await self.get_run(execution_id)
        if run is None:
            return
        run.status = "running"
        meta = dict(run.report_json or {})
        meta.update(
            {
                "upload_id": upload_id or meta.get("upload_id"),
                "dataset_id": dataset_id or meta.get("dataset_id"),
                "current_step": "pattern_detection",
                "progress": 28,
                "label": "Pattern Detection",
            }
        )
        run.report_json = meta
        await self._session.flush()

    async def update_progress(
        self,
        execution_id: str,
        *,
        step: str,
        progress: int,
        label: str,
    ) -> None:
        run = await self.get_run(execution_id)
        if run is None:
            return
        meta = dict(run.report_json or {})
        meta.update({"current_step": step, "progress": progress, "label": label})
        run.report_json = meta
        if run.status in {"pending", "running"}:
            run.status = "running"
        await self._session.flush()

    async def complete_run(
        self,
        execution_id: str,
        payload: dict[str, Any],
        *,
        metrics: dict[str, Any],
        charts: dict[str, Any] | None = None,
    ) -> None:
        run = await self.get_run(execution_id)
        if run is None:
            return
        run.status = "completed"
        meta = dict(run.report_json or {})
        meta.update(payload)
        meta["metrics"] = metrics
        if charts is not None:
            meta["charts"] = charts
        meta["progress"] = 100
        meta["current_step"] = "completed"
        meta["label"] = "Completed"
        run.report_json = meta
        run.dashboard_json = {"metrics": metrics, "charts": charts or meta.get("charts", {})}
        await self._session.flush()

    async def fail_run(self, execution_id: str, error: str) -> None:
        run = await self.get_run(execution_id)
        if run is None:
            return
        run.status = "failed"
        meta = dict(run.report_json or {})
        meta["error"] = error
        meta["label"] = error
        run.report_json = meta
        await self._session.flush()

    async def get_status(self, execution_id: str) -> dict[str, Any] | None:
        run = await self.get_run(execution_id)
        if run is None:
            return None
        meta = run.report_json or {}
        dashboard = run.dashboard_json or {}
        metrics = meta.get("metrics") or dashboard.get("metrics")
        charts = meta.get("charts") or dashboard.get("charts")
        return {
            "execution_id": run.id,
            "dataset_id": meta.get("dataset_id"),
            "upload_id": meta.get("upload_id"),
            "status": run.status,
            "progress": int(meta.get("progress") or 0),
            "current_step": meta.get("current_step"),
            "label": meta.get("label"),
            "metrics": metrics,
            "charts": charts,
            "error": meta.get("error"),
            "processing_ms": float(run.processing_ms or meta.get("processing_time") or 0),
        }

    async def get_run(self, run_id: str) -> EvaluationRun | None:
        return await self._session.get(EvaluationRun, run_id)

    async def get_latest_or(self, run_id: str | None = None) -> EvaluationRun | None:
        if run_id:
            return await self.get_run(run_id)
        runs = await self.list_runs(limit=1)
        return runs[0] if runs else None

    async def list_runs(self, *, limit: int = 50) -> list[EvaluationRun]:
        stmt = (
            select(EvaluationRun)
            .order_by(EvaluationRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
