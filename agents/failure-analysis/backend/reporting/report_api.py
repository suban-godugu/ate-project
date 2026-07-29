"""REST API for FA-FR-010 failure summary & engineering reporting."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.reporting.production_engine import ReportHandoffGateError
from backend.reporting.production_repository import ProductionReportingRepository
from backend.reporting.production_service import (
    ProductionReportingService,
    ReportValidationError,
)
from backend.reporting.report_repository import ReportRepository
from backend.reporting.report_service import ReportService
from backend.reporting.schemas import ExportReportRequest, GenerateReportRequest
from backend.reporting.security import reporting_access_context, reporting_rate_limit
from backend.reporting.tasks import (
    run_report_export_background,
    run_report_generation_background,
)

router = APIRouter(
    prefix=f"{API_PREFIX}/reports",
    tags=["reporting"],
    dependencies=[Depends(reporting_access_context)],
)


class LegacyGenerateReportRequest(BaseModel):
    """Backward-compatible request body for legacy upload-only generation."""

    upload_id: str
    config_path: str | None = None


def _structured_error(status_code: int, code: str, message: str, issues: list | None = None):
    detail: dict[str, Any] = {"code": code, "message": message}
    if issues:
        detail["issues"] = issues
    raise HTTPException(status_code=status_code, detail=detail)


@router.post("/generate")
async def generate_report(
    body: GenerateReportRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(reporting_access_context),
    _rate_limit: None = Depends(reporting_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate comprehensive engineering report from validated upstream analytics."""
    legacy_explicit = "legacy" in body.model_fields_set
    use_legacy = body.legacy or (
        not legacy_explicit
        and body.upload_id is not None
        and body.dataset_id is None
        and body.template_key is None
        and not body.async_execution
    )
    if use_legacy:
        repo = ReportRepository(db)
        service = ReportService(repo, config_path=body.config_path)
        try:
            result = await service.generate_report(body.upload_id or "")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        await db.commit()
        return result

    report_id = str(uuid.uuid4())
    effective = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective.async_execution:
        config = await ProductionReportingRepository(db).get_template(
            effective.template_key
        )
        await ProductionReportingRepository(db).create_audit(
            report_id=report_id,
            action="generate",
            status="queued",
            actor=effective.actor,
            dataset_id=effective.dataset_id,
            upload_id=effective.upload_id,
            template_id=config.id,
            details={"async": True, "requirement": "FA-FR-010"},
        )
        await db.commit()
        background_tasks.add_task(
            run_report_generation_background,
            effective.model_dump(),
            report_id,
        )
        return {
            "report_id": report_id,
            "status": "queued",
            "upload_id": effective.upload_id,
            "dataset_id": effective.dataset_id,
            "template_key": config.template_key,
        }

    service = ProductionReportingService(db)
    try:
        result = await service.execute(effective, report_id=report_id)
    except ReportHandoffGateError as exc:
        _structured_error(422, "REPORT_UPSTREAM_GATE_FAILED", str(exc), exc.issues)
    except ReportValidationError as exc:
        _structured_error(422, "REPORT_VALIDATION_FAILED", str(exc), exc.issues)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return result


@router.get("")
async def list_reports(
    limit: int = Query(50, ge=1, le=200),
    include_legacy: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    prod_repo = ProductionReportingRepository(db)
    production = await prod_repo.list_reports(limit=limit)
    items = [
        {
            "report_id": row.id,
            "report_name": row.report_name,
            "upload_id": row.upload_id,
            "dataset_id": row.dataset_id,
            "status": row.status,
            "completeness_score": row.completeness_score,
            "consistency_score": row.consistency_score,
            "processing_ms": row.processing_ms,
            "legacy": False,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in production
    ]
    if include_legacy:
        legacy_repo = ReportRepository(db)
        legacy_runs = await legacy_repo.list_runs(limit=limit)
        seen = {item["report_id"] for item in items}
        for run in legacy_runs:
            if run.id in seen:
                continue
            items.append(
                {
                    "report_id": run.id,
                    "report_name": "Legacy Engineering Report",
                    "upload_id": run.upload_id,
                    "dataset_id": None,
                    "status": run.status,
                    "total_dies": run.total_dies,
                    "failing_dies": run.failing_dies,
                    "overall_yield_pct": run.overall_yield_pct,
                    "processing_ms": run.processing_ms,
                    "legacy": True,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                }
            )
    return {"reports": items[:limit]}


@router.get("/history")
async def report_history(
    report_id: str | None = Query(default=None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    rows = await ProductionReportingRepository(db).list_history(
        report_id=report_id,
        limit=limit,
    )
    return {
        "history": [
            {
                "history_id": row.id,
                "report_id": row.report_id,
                "version": row.version,
                "change_reason": row.change_reason,
                "actor": row.actor,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    templates = await ProductionReportingRepository(db).list_templates()
    return {
        "templates": [
            {
                "template_id": row.id,
                "template_key": row.template_key,
                "name": row.name,
                "version": row.version,
                "description": row.description,
                "sections": row.sections_json,
                "is_default": row.is_default,
            }
            for row in templates
        ]
    }


@router.post("/export")
async def export_report(
    body: ExportReportRequest,
    background_tasks: BackgroundTasks,
    access: dict[str, str] = Depends(reporting_access_context),
    _rate_limit: None = Depends(reporting_rate_limit),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    export_id = str(uuid.uuid4())
    effective = body.model_copy(update={"actor": body.actor or access["actor"]})
    if effective.async_execution:
        await ProductionReportingRepository(db).create_audit(
            report_id=effective.report_id,
            action="export",
            status="queued",
            actor=effective.actor,
            export_format=effective.format,
        )
        await db.commit()
        background_tasks.add_task(
            run_report_export_background,
            effective.model_dump(),
            export_id,
        )
        return {
            "export_id": export_id,
            "report_id": effective.report_id,
            "format": effective.format,
            "status": "queued",
        }

    service = ProductionReportingService(db)
    try:
        return await service.export(effective, export_id=export_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/download/pdf")
async def download_pdf(
    report_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    return await _download_export(db, report_id, "pdf", "application/pdf", ".pdf")


@router.get("/download/excel")
async def download_excel(
    report_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    return await _download_export(
        db,
        report_id,
        "excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    )


@router.get("/download/json")
async def download_json(
    report_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    return await _download_export(db, report_id, "json", "application/json", ".json")


@router.get("/download/html")
async def download_html(
    report_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    return await _download_export(db, report_id, "html", "text/html", ".html")


@router.get("/download/csv")
async def download_csv(
    report_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    return await _download_export(db, report_id, "csv", "text/csv", ".csv")


@router.get("/{report_id}")
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    service = ProductionReportingService(db)
    try:
        return await service.get_report_detail(report_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


async def _download_export(
    db: AsyncSession,
    report_id: str,
    fmt: str,
    media_type: str,
    suffix: str,
) -> FileResponse:
    prod = await ProductionReportingRepository(db).get_report(report_id)
    if prod is not None:
        export_paths = prod.report_json.get("export_paths", {})
        path_str = export_paths.get(fmt) or export_paths.get(
            {"excel": "xlsx"}.get(fmt, fmt)
        )
        if path_str:
            return FileResponse(
                path=path_str,
                media_type=media_type,
                filename=f"failure_report_{report_id}{suffix}",
            )

    repo = ReportRepository(db)
    service = ReportService(repo)
    try:
        path = await service.get_export_path(report_id, fmt)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path=path,
        media_type=media_type,
        filename=f"failure_report_{report_id}{suffix}",
    )
