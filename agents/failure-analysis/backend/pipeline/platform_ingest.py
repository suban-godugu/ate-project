"""Persist platform unified_dataset into FA-FR-001 tables and run FA-FR-002…010.

Used by POST /api/v1/failure/run so Datasets / Patterns / Rates / … UI modules
have the same PostgreSQL rows as a native dashboard Analyze flow.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.config import PROCESSED_DIR, UPLOAD_DIR
from backend.database import SessionLocal
from backend.ingestion.ingestion_repository import IngestionRepository
from backend.pipeline.dataset_mapper import dataset_to_test_records
from evaluation.evaluation_repository import EvaluationRepository
from evaluation.upload_pipeline_runner import UploadPipelineRunner

logger = logging.getLogger("backend.pipeline.platform_ingest")
_pipeline_tasks: set[asyncio.Task[None]] = set()

AGENT_OUTPUT_HINT = Path(
    os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output")
)


def ensure_storage_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _records_from_dataset(dataset: dict[str, Any]) -> list[TestRecord]:
    out: list[TestRecord] = []
    seen: set[str] = set()
    for idx, raw in enumerate(dataset_to_test_records(dataset)):
        try:
            rec = TestRecord.from_dict(raw)
        except TypeError:
            continue
        base = rec.record_key or rec.build_record_key()
        key = f"{base}::{idx}"
        # Cap to DB String(512)
        if len(key) > 500:
            key = f"{hashlib.sha1(base.encode('utf-8')).hexdigest()}::{idx}"
        while key in seen:
            key = f"{key}x"
        seen.add(key)
        rec.record_key = key
        if rec.is_valid():
            out.append(rec)
    return out


async def persist_platform_dataset(
    session: AsyncSession,
    *,
    job_id: str,
    dataset: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create ingestion_datasets + uploads + test/normalized records for a platform job."""
    ensure_storage_dirs()
    repo = IngestionRepository(session)
    meta = metadata or {}
    file_name = str(meta.get("file_name") or f"platform-{job_id}.json")
    checksum = hashlib.sha256(
        f"platform:{job_id}:{file_name}:{len(dataset.get('records') or [])}".encode("utf-8")
    ).hexdigest()

    existing = await repo.find_by_checksum(checksum)
    if existing:
        if existing.status == "completed" and (existing.records_accepted or 0) > 0:
            return {
                "upload_id": existing.id,
                "dataset_id": existing.dataset_id,
                "records_accepted": int(existing.records_accepted or 0),
                "reused": True,
            }
        # Replace incomplete prior attempt for the same platform job checksum.
        await repo.mark_failed(
            existing,
            "incomplete platform ingest replaced",
            actor="platform",
        )
        await session.commit()

    records = _records_from_dataset(dataset)
    if not records:
        raise ValueError("unified dataset produced zero valid test records for FA ingest")

    name = str(meta.get("file_name") or meta.get("module") or f"Platform {job_id[:8]}")
    ds = await repo.create_dataset(
        name=name,
        source_root=str(AGENT_OUTPUT_HINT / job_id) if AGENT_OUTPUT_HINT else None,
        created_by="platform",
        metadata_json={
            "platform_job_id": job_id,
            "source": "verilumen_platform",
            **{k: v for k, v in meta.items() if isinstance(v, (str, int, float, bool))},
        },
    )

    stored_name = f"{job_id}_unified_dataset.json"
    # Platform markers live under agent output (not backend/storage/raw).
    out_dir = AGENT_OUTPUT_HINT / job_id / "failure"
    out_dir.mkdir(parents=True, exist_ok=True)
    stored_path = out_dir / stored_name
    try:
        if not stored_path.exists():
            stored_path.write_text(
                f'{{"job_id":"{job_id}","records":{len(records)},"input_root":"C:\\\\personal\\\\input all file\\\\{job_id}"}}\n',
                encoding="utf-8",
            )
    except OSError as exc:
        logger.warning("Could not write storage marker %s: %s", stored_path, exc)

    upload = await repo.create_upload(
        original_filename=file_name,
        stored_filename=stored_name,
        content_type="application/json",
        file_extension=".json",
        file_size_bytes=stored_path.stat().st_size if stored_path.exists() else len(records),
        checksum_sha256=checksum,
        dataset_id=ds.id,
        sanitized_filename=file_name,
        relative_path=stored_name,
        detected_mime="application/json",
        created_by="platform",
    )
    await repo.mark_processing(upload, actor="platform")
    # Keep batches small — dual write (test_records + normalized_records) blows PG param limits.
    await repo.save_records(upload.id, records, dataset_id=ds.id, batch_size=150)
    await repo.save_parser_metadata(
        upload.id,
        "platform_unified_dataset",
        {"job_id": job_id, "record_count": len(records), "mapper": "dataset_to_test_records"},
        parser_version="1.0",
    )
    await repo.mark_completed(
        upload,
        parser_id="platform_unified_dataset",
        records_accepted=len(records),
        records_quarantined=0,
        integrity_pct=100.0,
        validation_report={"source": "platform", "valid": True},
        processing_stats={"records": len(records), "job_id": job_id},
        actor="platform",
    )
    await repo.update_dataset_counts(
        ds,
        file_count=1,
        stil_count=1 if str(file_name).lower().endswith(".stil") else 0,
        log_count=0,
        status="completed",
        records_accepted=len(records),
        records_quarantined=0,
        mark_complete=True,
    )
    await repo.save_statistics(
        upload_id=upload.id,
        dataset_id=ds.id,
        upload_ms=0,
        validation_ms=0,
        parse_ms=0,
        normalize_ms=0,
        persist_ms=0,
        total_ms=0,
        records_parsed=len(records),
        records_accepted=len(records),
        records_quarantined=0,
        records_per_minute=0,
        file_size_bytes=upload.file_size_bytes,
        parser_id="platform_unified_dataset",
        success=True,
    )
    await repo.save_metadata(
        upload.id,
        {
            "platform_job_id": job_id,
            "ingested_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(records),
        },
    )
    await session.commit()
    return {
        "upload_id": upload.id,
        "dataset_id": ds.id,
        "records_accepted": len(records),
        "reused": False,
    }


async def _run_modules_background(
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
            await session.commit()
            logger.info(
                "Platform FA modules completed execution_id=%s upload_id=%s",
                execution_id,
                upload_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Platform FA modules failed execution_id=%s: %s", execution_id, exc
            )
            try:
                await runner.repo.fail_run(execution_id, str(exc))
                await session.commit()
            except Exception:  # noqa: BLE001
                await session.rollback()


def schedule_module_pipeline(
    *,
    execution_id: str,
    upload_id: str,
    dataset_id: str | None,
    imported_files: int = 1,
    dataset_name: str = "",
) -> None:
    task = asyncio.create_task(
        _run_modules_background(
            execution_id, upload_id, dataset_id, imported_files, dataset_name
        )
    )
    _pipeline_tasks.add(task)
    task.add_done_callback(_pipeline_tasks.discard)


async def ingest_and_analyze_platform_dataset(
    *,
    job_id: str,
    dataset: dict[str, Any],
    metadata: dict[str, Any] | None = None,
    run_modules: bool = True,
    wait_for_modules: bool = False,
    force_modules: bool = False,
) -> dict[str, Any]:
    """Persist FA-FR-001 rows and kick FA-FR-002…010 (async by default)."""
    async with SessionLocal() as session:
        persisted = await persist_platform_dataset(
            session, job_id=job_id, dataset=dataset, metadata=metadata
        )
        upload_id = str(persisted["upload_id"])
        dataset_id = persisted.get("dataset_id")
        records_accepted = int(persisted.get("records_accepted") or 0)
        # evaluation_runs.id is VARCHAR(36) — keep UUID-length ids only.
        execution_id = job_id if len(job_id) <= 36 else str(uuid.uuid5(uuid.NAMESPACE_URL, f"fa:{job_id}"))
        if force_modules:
            execution_id = str(uuid.uuid4())

        if run_modules:
            eval_repo = EvaluationRepository(session)
            existing = await eval_repo.get_status(execution_id)
            status = (existing or {}).get("status") if existing else None
            if status == "completed" and not force_modules:
                persisted["execution_id"] = execution_id
                persisted["modules_status"] = "completed"
                return persisted
            if status != "running":
                if existing is None:
                    await eval_repo.create_pending_run(
                        execution_id,
                        upload_id=upload_id,
                        dataset_id=dataset_id,
                        dataset_name=str((metadata or {}).get("file_name") or job_id),
                    )
                await session.commit()
                if wait_for_modules:
                    runner = UploadPipelineRunner(session)
                    await runner.run(
                        execution_id=execution_id,
                        upload_id=upload_id,
                        dataset_id=dataset_id,
                        imported_files=max(records_accepted, 1),
                        dataset_name=str((metadata or {}).get("file_name") or job_id),
                    )
                    await session.commit()
                    status = "completed"
                else:
                    schedule_module_pipeline(
                        execution_id=execution_id,
                        upload_id=upload_id,
                        dataset_id=dataset_id,
                        imported_files=max(records_accepted, 1),
                        dataset_name=str((metadata or {}).get("file_name") or job_id),
                    )
                    status = "running"
            persisted["execution_id"] = execution_id
            persisted["modules_status"] = status or "running"
        return persisted
