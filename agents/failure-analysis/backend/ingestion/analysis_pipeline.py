"""Dual STIL + tester-log dataset upload for dashboard Analyze workflow."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ingestion.dataset_service import DatasetIngestionService

logger = logging.getLogger(__name__)

LOG_EXTENSIONS = {".log", ".txt", ".stdf", ".std", ".dat", ".csv"}


class DatasetAnalysisOrchestrator:
    """Ingest one STIL + one-or-more tester logs as a single dataset."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.datasets = DatasetIngestionService(session)

    async def ingest_stil_and_logs(
        self,
        *,
        stil_file: UploadFile,
        log_files: list[UploadFile],
        dataset_name: str | None = None,
        created_by: str | None = None,
        async_process: bool = False,
    ) -> dict[str, Any]:
        stil_name = (stil_file.filename or "").lower()
        if not stil_name.endswith(".stil"):
            raise ValueError("stil_file must be a .stil file")
        if not log_files:
            raise ValueError("At least one tester log file is required")

        for log in log_files:
            name = (log.filename or "").lower()
            ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
            if ext and ext not in LOG_EXTENSIONS and not name.endswith(".stil"):
                # Allow unknown extensions that passed multipart; stil already validated.
                logger.warning("Accepting log candidate with extension %s: %s", ext, name)

        name = (dataset_name or "").strip() or f"ate_dataset_{uuid.uuid4().hex[:10]}"
        files = [stil_file, *log_files]
        relative_paths = [
            stil_file.filename or "input.stil",
            *[lf.filename or f"log_{i}.log" for i, lf in enumerate(log_files)],
        ]

        ingest = await self.datasets.create_dataset_from_files(
            name=name,
            files=files,
            relative_paths=relative_paths,
            async_process=async_process,
            created_by=created_by,
        )

        stil_upload_id = None
        log_upload_ids: list[str] = []
        for item in ingest.get("uploads") or []:
            filename = str(item.get("original_filename") or "").lower()
            upload_id = item.get("id")
            if not upload_id:
                continue
            if filename.endswith(".stil"):
                stil_upload_id = str(upload_id)
            else:
                log_upload_ids.append(str(upload_id))

        primary_upload_id = log_upload_ids[0] if log_upload_ids else stil_upload_id
        execution_id = str(uuid.uuid4())
        return {
            "execution_id": execution_id,
            "dataset_id": ingest["dataset_id"],
            "name": ingest.get("name") or name,
            "status": ingest.get("status") or "completed",
            "file_count": ingest.get("file_count") or len(files),
            "stil_count": ingest.get("stil_count") or (1 if stil_upload_id else 0),
            "log_count": ingest.get("log_count") or len(log_upload_ids),
            "stil_upload_id": stil_upload_id,
            "log_upload_ids": log_upload_ids,
            "primary_upload_id": primary_upload_id,
            "uploads": ingest.get("uploads") or [],
            "metrics": {
                "imported_files": ingest.get("file_count") or len(files),
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
            },
        }
