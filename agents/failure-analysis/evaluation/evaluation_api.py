"""REST API for AI Evaluation, Validation & Model Training Framework."""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import SessionLocal, get_db
from evaluation.evaluation_repository import EvaluationRepository
from evaluation.evaluation_service import EvaluationService
from evaluation.upload_pipeline_runner import UploadPipelineRunner

router = APIRouter(prefix=f"{API_PREFIX}/evaluation", tags=["evaluation"])
logger = logging.getLogger(__name__)
_pipeline_tasks: set[asyncio.Task[None]] = set()


class EvaluationRunRequest(BaseModel):
    dataset_id: str | None = None
    upload_id: str | None = Field(
        default=None,
        description="Ingested upload id from FA-FR-001 for dashboard pipeline runs.",
    )
    execution_id: str | None = Field(
        default=None,
        description="Optional pre-assigned execution id from dataset upload.",
    )
    imported_files: int | None = Field(default=None, ge=1)
    dataset_name: str | None = None
    modules: list[str] | None = Field(
        default=None,
        description="Optional subset e.g. ['FA-FR-002','FA-FR-009']",
    )
    max_logs: int | None = Field(default=None, ge=1, le=5000)
    config_path: str | None = None
    async_execution: bool = Field(
        default=False,
        description="When true with upload_id, runs FA-FR-002..010 in background.",
    )


async def _run_upload_pipeline_background(
    execution_id: str,
    upload_id: str,
    dataset_id: str | None,
    imported_files: int,
    dataset_name: str,
) -> None:
    async with SessionLocal() as session:
        runner = UploadPipelineRunner(session)
        try:
            await runner.run(
                execution_id=execution_id,
                upload_id=upload_id,
                dataset_id=dataset_id,
                imported_files=imported_files,
                dataset_name=dataset_name,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Background upload pipeline failed execution_id=%s", execution_id
            )
            try:
                await runner.repo.fail_run(execution_id, str(exc))
                await session.commit()
            except Exception:
                logger.exception(
                    "Failed to persist pipeline failure execution_id=%s", execution_id
                )
                await session.rollback()


def _schedule_upload_pipeline(
    execution_id: str,
    upload_id: str,
    dataset_id: str | None,
    imported_files: int,
    dataset_name: str,
) -> None:
    task = asyncio.create_task(
        _run_upload_pipeline_background(
            execution_id,
            upload_id,
            dataset_id,
            imported_files,
            dataset_name,
        )
    )
    _pipeline_tasks.add(task)
    task.add_done_callback(_pipeline_tasks.discard)


@router.get("/datasets")
async def discover_datasets(
    config_path: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Automatically discover STIL/log/csv/json datasets under configured roots."""
    repo = EvaluationRepository(db)
    service = EvaluationService(repo, config_path=config_path)
    return await asyncio.to_thread(service.orchestrator.discover)


@router.post("/run")
async def run_evaluation(
    body: EvaluationRunRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute complete or partial FA-FR validation pipeline with AI evaluation."""
    repo = EvaluationRepository(db)

    if body.upload_id:
        execution_id = body.execution_id or str(uuid.uuid4())
        await repo.create_pending_run(
            execution_id,
            upload_id=body.upload_id,
            dataset_id=body.dataset_id,
            dataset_name=body.dataset_name or "",
        )
        await repo.mark_running(
            execution_id,
            upload_id=body.upload_id,
            dataset_id=body.dataset_id,
        )
        await db.commit()
        if body.async_execution:
            _schedule_upload_pipeline(
                execution_id,
                body.upload_id,
                body.dataset_id,
                int(body.imported_files or 1),
                body.dataset_name or "",
            )
            return {
                "execution_id": execution_id,
                "upload_id": body.upload_id,
                "dataset_id": body.dataset_id,
                "status": "running",
            }
        runner = UploadPipelineRunner(db)
        try:
            result = await runner.run(
                execution_id=execution_id,
                upload_id=body.upload_id,
                dataset_id=body.dataset_id,
                imported_files=int(body.imported_files or 1),
                dataset_name=body.dataset_name or "",
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        await db.commit()
        return result

    service = EvaluationService(repo, config_path=body.config_path)
    try:
        report = await asyncio.to_thread(
            service.orchestrator.run,
            dataset_id=body.dataset_id,
            modules=body.modules,
            max_logs=body.max_logs,
        )
        run = await service.repo.save_run(report)
        result = {
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
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return result


@router.get("/status/{execution_id}")
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Poll dashboard analysis execution progress and metrics."""
    repo = EvaluationRepository(db)
    status = await repo.get_status(execution_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return status


@router.get("")
async def list_evaluations(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = EvaluationRepository(db)
    runs = await repo.list_runs(limit=limit)
    return {
        "runs": [
            {
                "execution_id": run.id,
                "datasets_evaluated": run.datasets_evaluated,
                "pass_count": run.pass_count,
                "fail_count": run.fail_count,
                "warning_count": run.warning_count,
                "model_version": run.model_version,
                "processing_ms": run.processing_ms,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
    }


@router.get("/dashboard")
async def evaluation_dashboard(
    execution_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = EvaluationRepository(db)
    service = EvaluationService(repo)
    try:
        return await service.get_dashboard(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/report")
async def evaluation_report(
    execution_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = EvaluationRepository(db)
    service = EvaluationService(repo)
    try:
        return await service.get_report(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/download/{fmt}")
async def download_evaluation_export(
    fmt: str,
    execution_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    fmt = fmt.lower()
    if fmt not in {"pdf", "excel", "csv", "json"}:
        raise HTTPException(status_code=400, detail="Supported formats: pdf, excel, csv, json")
    repo = EvaluationRepository(db)
    run = await repo.get_run(execution_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
    path = (run.export_paths or {}).get(fmt)
    if not path or not Path(path).is_file():
        raise HTTPException(status_code=404, detail=f"Export not available for format={fmt}")
    media = {
        "pdf": "application/pdf",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "json": "application/json",
    }[fmt]
    suffix = {"pdf": ".pdf", "excel": ".xlsx", "csv": ".csv", "json": ".json"}[fmt]
    return FileResponse(
        path=path,
        media_type=media,
        filename=f"evaluation_{execution_id}{suffix}",
    )
