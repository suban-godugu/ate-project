"""FastAPI routes for FA-FR-001 Semiconductor Test Data Ingestion Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import API_PREFIX
from backend.database import get_db
from backend.ingestion.analysis_pipeline import DatasetAnalysisOrchestrator
from backend.ingestion.dataset_service import DatasetIngestionService
from backend.ingestion.ingestion_repository import IngestionRepository
from backend.ingestion.schemas import (
    AsyncUploadAccepted,
    DatasetCreateResponse,
    DatasetSummary,
    IngestionStatsSummary,
    ParserStat,
    UploadResponse,
    UploadSummary,
)
from backend.ingestion.tasks import enqueue_upload_processing
from backend.ingestion.upload_service import UploadService
from evaluation.data_roots import primary_dataset_root

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{API_PREFIX}", tags=["ingestion"])


def _upload_summary(item) -> dict[str, Any]:
    return {
        "id": item.id,
        "dataset_id": getattr(item, "dataset_id", None),
        "original_filename": item.original_filename,
        "status": item.status,
        "parser_id": item.parser_id,
        "records_accepted": item.records_accepted,
        "records_quarantined": item.records_quarantined,
        "integrity_pct": item.integrity_pct,
        "file_size_bytes": item.file_size_bytes,
        "checksum_sha256": item.checksum_sha256,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "error_message": item.error_message,
    }


@router.post(
    "/uploads",
    response_model=UploadResponse | AsyncUploadAccepted,
    summary="Upload a single semiconductor tester file",
)
async def create_upload(
    file: UploadFile = File(...),
    allow_duplicate: bool = Query(False),
    async_process: bool = Query(False),
    dataset_id: str | None = Query(None),
    relative_path: str | None = Query(None),
    created_by: str | None = Query(None, description="RBAC actor id (optional)"),
    db: AsyncSession = Depends(get_db),
):
    """Upload, validate, parse, normalize, and persist a tester output file."""
    service = UploadService(db)
    if async_process:
        try:
            stored_path, checksum, size = await service.save_raw_upload(file)
        except ValueError as exc:
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        repo = IngestionRepository(db)
        upload = await repo.create_upload(
            original_filename=file.filename or "upload.bin",
            stored_filename=stored_path.name,
            content_type=file.content_type or "application/octet-stream",
            file_extension=stored_path.suffix.lower(),
            file_size_bytes=size,
            checksum_sha256=checksum,
            dataset_id=dataset_id,
            relative_path=relative_path,
            created_by=created_by,
        )
        await db.commit()
        task_id = enqueue_upload_processing(upload.id)
        return {
            "upload_id": upload.id,
            "dataset_id": dataset_id,
            "status": "queued",
            "message": "Upload accepted; processing asynchronously",
            "task_id": task_id,
        }

    result = await service.process_upload(
        upload_file=file,
        allow_duplicate=allow_duplicate,
        dataset_id=dataset_id,
        relative_path=relative_path,
        created_by=created_by,
    )
    if result.get("duplicate"):
        raise HTTPException(status_code=409, detail=result)
    if result.get("upload", {}).get("status") == "failed":
        raise HTTPException(status_code=422, detail=result)
    return result


@router.get("/uploads", summary="List upload history")
async def list_uploads(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    dataset_id: str | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    repo = IngestionRepository(db)
    uploads = await repo.list_uploads(
        limit=limit, offset=offset, dataset_id=dataset_id, status=status
    )
    return {
        "total_returned": len(uploads),
        "uploads": [_upload_summary(item) for item in uploads],
    }


@router.get("/uploads/{upload_id}", summary="Get upload detail + validation report")
async def get_upload(upload_id: str, db: AsyncSession = Depends(get_db)):
    repo = IngestionRepository(db)
    upload = await repo.get_upload(upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    history = await repo.list_history(upload_id)
    issues = await repo.list_validation_results(upload_id)
    return {
        "upload": {
            **_upload_summary(upload),
            "stored_filename": upload.stored_filename,
            "relative_path": upload.relative_path,
            "detected_mime": upload.detected_mime,
            "validation_report": upload.validation_report,
            "processing_statistics": upload.processing_stats,
        },
        "history": [
            {
                "from_status": h.from_status,
                "to_status": h.to_status,
                "message": h.message,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in history
        ],
        "validation_results": [
            {
                "severity": v.severity,
                "category": v.category,
                "code": v.code,
                "message": v.message,
                "details": v.details,
            }
            for v in issues
        ],
    }


@router.get("/uploads/{upload_id}/metadata")
async def get_upload_metadata(upload_id: str, db: AsyncSession = Depends(get_db)):
    repo = IngestionRepository(db)
    upload = await repo.get_upload(upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    metadata = await repo.get_metadata(upload_id)
    if metadata is None:
        raise HTTPException(status_code=404, detail="Metadata not generated yet")
    return {"upload_id": upload_id, "metadata": metadata.metadata_json}


@router.get("/uploads/{upload_id}/records", summary="Retrieve normalized records")
async def get_normalized_records(
    upload_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = IngestionRepository(db)
    upload = await repo.get_upload(upload_id)
    if upload is None:
        raise HTTPException(status_code=404, detail="Upload not found")
    rows = await repo.list_normalized_records(upload_id, limit=limit, offset=offset)
    return {
        "upload_id": upload_id,
        "total_returned": len(rows),
        "records": [
            {
                "id": r.id,
                "record_key": r.record_key,
                "lot_id": r.lot_id,
                "wafer_id": r.wafer_id,
                "die_id": r.die_id,
                "test_stage": r.test_stage,
                "pass_fail": r.pass_fail,
                "adapter_id": r.adapter_id,
                "payload": r.payload,
            }
            for r in rows
        ],
    }


@router.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: str, db: AsyncSession = Depends(get_db)):
    repo = IngestionRepository(db)
    deleted = await repo.delete_upload(upload_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Upload not found")
    await db.commit()
    return {"deleted": True, "upload_id": upload_id}


@router.post(
    "/datasets/upload",
    summary="Upload a folder / multi-file dataset (STIL + logs)",
)
async def upload_dataset(
    name: str | None = Form(None),
    dataset_name: str | None = Form(None),
    files: list[UploadFile] = File(default=[]),
    relative_paths: list[str] | None = Form(None),
    stil_file: UploadFile | None = File(None),
    tester_logs: list[UploadFile] = File(default=[]),
    created_by: str | None = Form(None),
    async_process: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept browser folder uploads or explicit STIL + tester log bundle.

    Dual-input mode: ``stil_file`` + ``tester_logs[]`` + optional ``dataset_name``.
    Legacy mode: ``name`` + ``files[]`` (+ optional ``relative_paths``).
    """
    logger.info(
        "[UPLOAD_DEBUG] upload_dataset handler START name=%s dataset_name=%s stil_file=%s "
        "tester_logs_count=%d files_count=%d async_process=%s created_by=%s",
        name,
        dataset_name,
        stil_file.filename if stil_file is not None else None,
        len(tester_logs),
        len(files),
        async_process,
        created_by,
    )
    logger.info(
        "[UPLOAD_DEBUG] POST /datasets/upload REACHED "
        "stil_file=%s tester_logs_count=%d files_count=%d "
        "dataset_name=%s name=%s async_process=%s created_by=%s",
        stil_file.filename if stil_file is not None else None,
        len(tester_logs),
        len(files),
        dataset_name,
        name,
        async_process,
        created_by,
    )
    if stil_file is not None:
        if not tester_logs:
            raise HTTPException(status_code=422, detail="At least one tester log is required")
        try:
            orchestrator = DatasetAnalysisOrchestrator(db)
            return await orchestrator.ingest_stil_and_logs(
                stil_file=stil_file,
                log_files=tester_logs,
                dataset_name=dataset_name or name,
                created_by=created_by,
                async_process=async_process,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    resolved_name = (dataset_name or name or "").strip()
    if not resolved_name:
        raise HTTPException(status_code=422, detail="dataset_name or name is required")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    service = DatasetIngestionService(db)
    try:
        ingest = await service.create_dataset_from_files(
            name=resolved_name,
            files=files,
            relative_paths=relative_paths,
            async_process=async_process,
            created_by=created_by,
        )
    except Exception:
        logger.exception(
            "[UPLOAD_DEBUG] upload_dataset create_dataset_from_files FAILED "
            "resolved_name=%s files_count=%d async_process=%s created_by=%s",
            resolved_name,
            len(files),
            async_process,
            created_by,
        )
        raise
    execution_id = str(uuid.uuid4())
    primary_upload_id = None
    for item in ingest.get("uploads") or []:
        filename = str(item.get("original_filename") or "").lower()
        if not filename.endswith(".stil") and item.get("id"):
            primary_upload_id = str(item["id"])
            break
    if primary_upload_id is None and ingest.get("uploads"):
        primary_upload_id = str(ingest["uploads"][0].get("id") or "")
    return {
        **ingest,
        "execution_id": execution_id,
        "primary_upload_id": primary_upload_id,
    }


@router.post(
    "/datasets/analyze",
    summary="Upload STIL + tester logs and prepare dataset for full FA analysis",
)
async def analyze_dataset_bundle(
    stil_file: UploadFile = File(..., description="Required .stil pattern file"),
    log_files: list[UploadFile] = File(..., description="One or more tester log files"),
    dataset_name: str | None = Form(None),
    created_by: str | None = Form(None),
    async_process: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    """
    Dual-input ingestion for the ATE dashboard Analyze workflow.

    Requires exactly one STIL file and one-or-more tester logs (.log/.txt/.stdf/…).
    Returns dataset_id + primary_upload_id so the client can run FA-FR-002…010.
    """
    try:
        orchestrator = DatasetAnalysisOrchestrator(db)
        return await orchestrator.ingest_stil_and_logs(
            stil_file=stil_file,
            log_files=log_files,
            dataset_name=dataset_name,
            created_by=created_by,
            async_process=async_process,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


class ServerScanRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=512)
    root: str | None = Field(
        default=None,
        description="Optional server path. Defaults to configured Verilumen / DATASET_ROOT.",
    )
    created_by: str | None = None


@router.post("/datasets/scan", summary="Recursively scan a trusted server dataset root")
async def scan_server_dataset(body: ServerScanRequest, db: AsyncSession = Depends(get_db)):
    logger.info(
        "[DATASET_DEBUG] POST /datasets/scan START name=%s root=%s created_by=%s",
        body.name,
        body.root,
        body.created_by,
    )
    root = Path(body.root).expanduser() if body.root else primary_dataset_root()
    if root is None:
        raise HTTPException(
            status_code=400,
            detail="No dataset root configured. Set DATASET_ROOT or provide body.root",
        )
    # Prevent arbitrary filesystem traversal outside known roots for safety.
    allowed = primary_dataset_root()
    resolved = root.resolve()
    if allowed is not None and allowed.resolve() not in resolved.parents and resolved != allowed.resolve():
        # allow exact root or children of primary dataset root
        if not str(resolved).startswith(str(allowed.resolve())):
            raise HTTPException(status_code=403, detail="Scan root is outside allowed dataset roots")
    service = DatasetIngestionService(db)
    try:
        result = await service.ingest_server_folder(
            name=body.name, root_path=resolved, created_by=body.created_by
        )
        logger.info(
            "[DATASET_DEBUG] POST /datasets/scan END dataset_id=%s status=%s",
            result.get("dataset_id"),
            result.get("status"),
        )
        return result
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        logger.exception(
            "[DATASET_DEBUG] POST /datasets/scan FAILED name=%s resolved_root=%s",
            body.name,
            str(resolved),
        )
        raise


@router.get("/datasets", summary="List ingestion datasets")
async def list_datasets(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = IngestionRepository(db)
    logger.info("[DATASET_DEBUG] GET /datasets START limit=%d offset=%d", limit, offset)
    try:
        datasets = await repo.list_datasets(limit=limit, offset=offset)
    except Exception:
        logger.exception(
            "[DATASET_DEBUG] GET /datasets FAILED limit=%d offset=%d",
            limit,
            offset,
        )
        raise
    return {
        "datasets": [
            DatasetSummary(
                id=d.id,
                name=d.name,
                status=d.status,
                file_count=d.file_count,
                stil_count=d.stil_count,
                log_count=d.log_count,
                records_accepted=d.records_accepted,
                records_quarantined=d.records_quarantined,
                created_at=d.created_at.isoformat() if d.created_at else None,
                completed_at=d.completed_at.isoformat() if d.completed_at else None,
                error_message=d.error_message,
            ).model_dump()
            for d in datasets
        ]
    }


@router.get("/datasets/{dataset_id}", summary="Dataset explorer detail")
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    repo = IngestionRepository(db)
    logger.info("[DATASET_DEBUG] GET /datasets/%s START", dataset_id)
    try:
        dataset = await repo.get_dataset(dataset_id)
    except Exception:
        logger.exception(
            "[DATASET_DEBUG] GET /datasets/%s FAILED (get_dataset)", dataset_id
        )
        raise
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    try:
        uploads = await repo.list_uploads(limit=200, dataset_id=dataset_id)
    except Exception:
        logger.exception(
            "[DATASET_DEBUG] GET /datasets/%s FAILED (list_uploads)", dataset_id
        )
        raise
    return {
        "dataset": DatasetSummary(
            id=dataset.id,
            name=dataset.name,
            status=dataset.status,
            file_count=dataset.file_count,
            stil_count=dataset.stil_count,
            log_count=dataset.log_count,
            records_accepted=dataset.records_accepted,
            records_quarantined=dataset.records_quarantined,
            created_at=dataset.created_at.isoformat() if dataset.created_at else None,
            completed_at=dataset.completed_at.isoformat() if dataset.completed_at else None,
            error_message=dataset.error_message,
        ).model_dump(),
        "uploads": [_upload_summary(u) for u in uploads],
    }


@router.get("/ingestion/statistics", response_model=IngestionStatsSummary)
async def ingestion_statistics(db: AsyncSession = Depends(get_db)):
    repo = IngestionRepository(db)
    counts = await repo.status_counts()
    parsers = await repo.parser_statistics()
    uploads = await repo.list_uploads(limit=200)
    total_accepted = sum(u.records_accepted for u in uploads)
    return IngestionStatsSummary(
        total_uploads=sum(counts.values()),
        completed=counts.get("completed", 0),
        failed=counts.get("failed", 0),
        queued=counts.get("pending", 0) + counts.get("queued", 0),
        processing=counts.get("processing", 0),
        total_records_accepted=total_accepted,
        by_parser=[ParserStat(**p) for p in parsers],
    )
