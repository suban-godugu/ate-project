"""Dataset / recursive folder ingestion orchestrator."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import ALLOWED_EXTENSIONS
from backend.ingestion.ingestion_repository import IngestionRepository
from backend.ingestion.security import safe_relative_path, sanitize_filename
from backend.ingestion.tasks import enqueue_upload_processing
from backend.ingestion.upload_service import UploadService

logger = logging.getLogger(__name__)

LOG_EXTENSIONS = {".log", ".txt", ".dat"}
STIL_EXTENSIONS = {".stil"}


class DatasetIngestionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = IngestionRepository(session)
        self._uploads = UploadService(session)

    async def create_dataset_from_files(
        self,
        *,
        name: str,
        files: list[UploadFile],
        relative_paths: list[str] | None = None,
        async_process: bool = True,
        created_by: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        logger.info(
            "[UPLOAD_DEBUG] create_dataset_from_files ENTRY "
            "name=%s file_count=%d async_process=%s created_by=%s tenant_id=%s",
            name,
            len(files),
            async_process,
            created_by,
            tenant_id,
        )
        for idx, f in enumerate(files):
            logger.info(
                "[UPLOAD_DEBUG] create_dataset_from_files queued file[%d] filename=%s content_type=%s",
                idx,
                f.filename,
                f.content_type,
            )
        try:
            logger.info("[UPLOAD_DEBUG] before create_dataset DB write name=%s", name)
            dataset = await self._repo.create_dataset(
                name=name,
                created_by=created_by,
                tenant_id=tenant_id,
                metadata_json={"source": "multipart_folder"},
            )
            await self._session.commit()
            logger.info(
                "[UPLOAD_DEBUG] after create_dataset DB write dataset_id=%s",
                dataset.id,
            )

            upload_summaries: list[dict[str, Any]] = []
            stil_count = 0
            log_count = 0

            for index, upload_file in enumerate(files):
                rel = None
                if relative_paths and index < len(relative_paths):
                    rel = safe_relative_path(relative_paths[index])
                filename = sanitize_filename(upload_file.filename or f"file_{index}")
                ext = Path(filename).suffix.lower()
                logger.info(
                    "[UPLOAD_DEBUG] before reading file index=%d filename=%s ext=%s relative_path=%s",
                    index,
                    filename,
                    ext,
                    rel,
                )
                if ext not in ALLOWED_EXTENSIONS:
                    logger.warning("Skipping unsupported file in dataset: %s", filename)
                    continue
                if ext in STIL_EXTENSIONS:
                    stil_count += 1
                if ext in LOG_EXTENSIONS:
                    log_count += 1

                if async_process:
                    stored_path, checksum, size = await self._uploads.save_raw_upload(upload_file)
                    logger.info(
                        "[UPLOAD_DEBUG] after reading file index=%d filename=%s size_bytes=%d stored_path=%s checksum_prefix=%s",
                        index,
                        filename,
                        size,
                        stored_path,
                        checksum[:12],
                    )
                    logger.info(
                        "[UPLOAD_DEBUG] before create_upload DB write index=%d filename=%s",
                        index,
                        filename,
                    )
                    upload = await self._repo.create_upload(
                        original_filename=filename,
                        sanitized_filename=filename,
                        stored_filename=stored_path.name,
                        content_type=upload_file.content_type or "application/octet-stream",
                        file_extension=ext,
                        file_size_bytes=size,
                        checksum_sha256=checksum,
                        dataset_id=dataset.id,
                        relative_path=rel,
                        created_by=created_by,
                        tenant_id=tenant_id,
                    )
                    await self._session.commit()
                    logger.info(
                        "[UPLOAD_DEBUG] after create_upload DB write index=%d upload_id=%s",
                        index,
                        upload.id,
                    )
                    enqueue_upload_processing(upload.id)
                    upload_summaries.append(
                        {
                            "id": upload.id,
                            "original_filename": filename,
                            "status": "queued",
                            "dataset_id": dataset.id,
                            "records_accepted": 0,
                            "records_quarantined": 0,
                            "integrity_pct": 0.0,
                        }
                    )
                else:
                    logger.info(
                        "[UPLOAD_DEBUG] before process_upload (sync) index=%d filename=%s",
                        index,
                        filename,
                    )
                    # Dataset membership requires per-dataset upload rows even when the
                    # same tester artifact is re-ingested (checksum dedupe is per file upload API).
                    result = await self._uploads.process_upload(
                        upload_file=upload_file,
                        allow_duplicate=True,
                        dataset_id=dataset.id,
                        relative_path=rel,
                        created_by=created_by,
                        tenant_id=tenant_id,
                    )
                    logger.info(
                        "[UPLOAD_DEBUG] after process_upload (sync) index=%d upload_id=%s",
                        index,
                        (result.get("upload") or {}).get("id"),
                    )
                    upload = result.get("upload") or {}
                    if upload.get("id"):
                        upload_summaries.append(upload)

            logger.info(
                "[UPLOAD_DEBUG] before update_dataset_counts DB write dataset_id=%s upload_count=%d",
                dataset.id,
                len(upload_summaries),
            )
            await self._repo.update_dataset_counts(
                dataset,
                file_count=len(upload_summaries),
                stil_count=stil_count,
                log_count=log_count,
                status="processing" if async_process else "completed",
                mark_complete=not async_process,
            )
            await self._repo.add_audit(
                "dataset",
                dataset.id,
                "create",
                created_by,
                {"file_count": len(upload_summaries), "stil_count": stil_count, "log_count": log_count},
                tenant_id=tenant_id,
            )
            await self._session.commit()
            logger.info(
                "[UPLOAD_DEBUG] after final DB commit dataset_id=%s status=%s",
                dataset.id,
                dataset.status,
            )

            payload = {
                "dataset_id": dataset.id,
                "name": dataset.name,
                "status": dataset.status,
                "file_count": len(upload_summaries),
                "stil_count": stil_count,
                "log_count": log_count,
                "uploads": upload_summaries,
            }
            logger.info(
                "[UPLOAD_DEBUG] create_dataset_from_files RETURN dataset_id=%s file_count=%d stil_count=%d log_count=%d",
                payload["dataset_id"],
                payload["file_count"],
                payload["stil_count"],
                payload["log_count"],
            )
            logger.info(
                "[UPLOAD_DEBUG] create_dataset_from_files END dataset_id=%s status=%s",
                dataset.id,
                dataset.status,
            )
            return payload
        except Exception:
            logger.exception(
                "[UPLOAD_DEBUG] create_dataset_from_files FAILED name=%s file_count=%d",
                name,
                len(files),
            )
            raise

    async def ingest_server_folder(
        self,
        *,
        name: str,
        root_path: Path,
        async_process: bool = False,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """Scan a trusted server-side directory recursively (not client-supplied arbitrary paths)."""
        if not root_path.is_dir():
            raise FileNotFoundError(f"Dataset root not found: {root_path}")

        dataset = await self._repo.create_dataset(
            name=name,
            source_root=str(root_path.resolve()),
            created_by=created_by,
            metadata_json={"source": "server_scan"},
        )
        await self._session.commit()

        files = [
            p
            for p in sorted(root_path.rglob("*"))
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
        ]
        stil_count = sum(1 for p in files if p.suffix.lower() in STIL_EXTENSIONS)
        log_count = sum(1 for p in files if p.suffix.lower() in LOG_EXTENSIONS)

        summaries: list[dict[str, Any]] = []
        for path in files:
            rel = str(path.relative_to(root_path)).replace("\\", "/")
            result = await self._uploads.process_local_path(
                path,
                dataset_id=dataset.id,
                relative_path=rel,
                created_by=created_by,
            )
            summaries.append(result.get("upload", {}))

        accepted = sum(int(s.get("records_accepted") or 0) for s in summaries)
        quarantined = sum(int(s.get("records_quarantined") or 0) for s in summaries)
        await self._repo.update_dataset_counts(
            dataset,
            file_count=len(summaries),
            stil_count=stil_count,
            log_count=log_count,
            status="completed",
            records_accepted=accepted,
            records_quarantined=quarantined,
            mark_complete=True,
        )
        await self._session.commit()
        return {
            "dataset_id": dataset.id,
            "name": dataset.name,
            "status": "completed",
            "file_count": len(summaries),
            "stil_count": stil_count,
            "log_count": log_count,
            "uploads": summaries,
        }
