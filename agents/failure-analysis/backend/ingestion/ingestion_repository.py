"""Repository pattern for FA-FR-001 upload and dataset persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import case, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.ingestion.models_ingestion import (
    AuditLog,
    IngestionDataset,
    IngestionStatistics,
    NormalizedRecord,
    ParserMetadata,
    UploadHistory,
    ValidationResult,
)
from backend.models import TestRecordRow, Upload, UploadMetadata


class IngestionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_dataset(
        self,
        *,
        name: str,
        source_root: str | None = None,
        created_by: str | None = None,
        tenant_id: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> IngestionDataset:
        dataset = IngestionDataset(
            name=name,
            source_root=source_root,
            status="pending",
            created_by=created_by,
            tenant_id=tenant_id,
            metadata_json=metadata_json or {},
        )
        self._session.add(dataset)
        await self._session.flush()
        return dataset

    async def get_dataset(self, dataset_id: str) -> IngestionDataset | None:
        return await self._session.get(IngestionDataset, dataset_id)

    async def list_datasets(self, *, limit: int = 50, offset: int = 0) -> list[IngestionDataset]:
        stmt = (
            select(IngestionDataset)
            .order_by(IngestionDataset.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_dataset_counts(
        self,
        dataset: IngestionDataset,
        *,
        file_count: int,
        stil_count: int,
        log_count: int,
        status: str | None = None,
        records_accepted: int | None = None,
        records_quarantined: int | None = None,
        error_message: str | None = None,
        mark_complete: bool = False,
    ) -> IngestionDataset:
        dataset.file_count = file_count
        dataset.stil_count = stil_count
        dataset.log_count = log_count
        if status:
            dataset.status = status
        if records_accepted is not None:
            dataset.records_accepted = records_accepted
        if records_quarantined is not None:
            dataset.records_quarantined = records_quarantined
        if error_message is not None:
            dataset.error_message = error_message
        if mark_complete:
            dataset.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return dataset

    async def create_upload(
        self,
        *,
        original_filename: str,
        stored_filename: str,
        content_type: str,
        file_extension: str,
        file_size_bytes: int,
        checksum_sha256: str,
        dataset_id: str | None = None,
        sanitized_filename: str | None = None,
        relative_path: str | None = None,
        detected_mime: str | None = None,
        created_by: str | None = None,
        tenant_id: str | None = None,
    ) -> Upload:
        upload = Upload(
            dataset_id=dataset_id,
            original_filename=original_filename,
            sanitized_filename=sanitized_filename or original_filename,
            stored_filename=stored_filename,
            relative_path=relative_path,
            content_type=content_type,
            detected_mime=detected_mime,
            file_extension=file_extension,
            file_size_bytes=file_size_bytes,
            checksum_sha256=checksum_sha256,
            created_by=created_by,
            tenant_id=tenant_id,
            status="pending",
        )
        self._session.add(upload)
        await self._session.flush()
        await self.add_history(upload.id, None, "pending", "Upload created", created_by)
        await self.add_audit("upload", upload.id, "create", created_by, {"filename": original_filename})
        return upload

    async def get_upload(self, upload_id: str) -> Upload | None:
        return await self._session.get(Upload, upload_id)

    async def list_uploads(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        dataset_id: str | None = None,
        status: str | None = None,
    ) -> list[Upload]:
        stmt = select(Upload).order_by(Upload.created_at.desc()).limit(limit).offset(offset)
        if dataset_id:
            stmt = stmt.where(Upload.dataset_id == dataset_id)
        if status:
            stmt = stmt.where(Upload.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_checksum(self, checksum: str) -> Upload | None:
        stmt = (
            select(Upload)
            .where(Upload.checksum_sha256 == checksum, Upload.status != "failed")
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_history(
        self,
        upload_id: str,
        from_status: str | None,
        to_status: str,
        message: str | None = None,
        actor: str | None = None,
    ) -> None:
        self._session.add(
            UploadHistory(
                upload_id=upload_id,
                from_status=from_status,
                to_status=to_status,
                message=message,
                actor=actor,
            )
        )
        await self._session.flush()

    async def add_audit(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        actor: str | None = None,
        details: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> None:
        self._session.add(
            AuditLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                actor=actor,
                tenant_id=tenant_id,
                details=details or {},
            )
        )
        await self._session.flush()

    async def save_validation_issues(
        self,
        upload_id: str,
        issues: list[str],
        *,
        dataset_id: str | None = None,
        severity: str = "error",
        category: str = "file_validation",
        code: str = "VALIDATION",
    ) -> None:
        for issue in issues:
            self._session.add(
                ValidationResult(
                    upload_id=upload_id,
                    dataset_id=dataset_id,
                    severity=severity,
                    category=category,
                    code=code,
                    message=issue,
                    details={},
                )
            )
        await self._session.flush()

    async def save_parser_metadata(
        self,
        upload_id: str,
        parser_id: str,
        metadata: dict[str, Any],
        *,
        parser_version: str = "1.0",
    ) -> None:
        self._session.add(
            ParserMetadata(
                upload_id=upload_id,
                parser_id=parser_id,
                parser_version=parser_version,
                metadata_json=metadata,
            )
        )
        await self._session.flush()

    async def save_statistics(self, **kwargs: Any) -> IngestionStatistics:
        row = IngestionStatistics(**kwargs)
        self._session.add(row)
        await self._session.flush()
        return row

    async def mark_processing(self, upload: Upload, actor: str | None = None) -> Upload:
        previous = upload.status
        upload.status = "processing"
        await self._session.flush()
        await self.add_history(upload.id, previous, "processing", "Pipeline started", actor)
        return upload

    async def mark_completed(
        self,
        upload: Upload,
        *,
        parser_id: str | None,
        records_accepted: int,
        records_quarantined: int,
        integrity_pct: float,
        validation_report: dict[str, Any],
        processing_stats: dict[str, Any],
        actor: str | None = None,
    ) -> Upload:
        previous = upload.status
        upload.status = "completed"
        upload.parser_id = parser_id
        upload.records_accepted = records_accepted
        upload.records_quarantined = records_quarantined
        upload.integrity_pct = integrity_pct
        upload.validation_report = validation_report
        upload.processing_stats = processing_stats
        upload.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self.add_history(upload.id, previous, "completed", "Ingestion completed", actor)
        await self.add_audit("upload", upload.id, "complete", actor, processing_stats)
        return upload

    async def mark_failed(self, upload: Upload, error_message: str, actor: str | None = None) -> Upload:
        previous = upload.status
        upload.status = "failed"
        upload.error_message = error_message
        upload.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self.add_history(upload.id, previous, "failed", error_message, actor)
        await self.add_audit("upload", upload.id, "fail", actor, {"error": error_message})
        return upload

    async def save_metadata(self, upload_id: str, metadata: dict[str, Any]) -> UploadMetadata:
        row = UploadMetadata(upload_id=upload_id, metadata_json=metadata)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_metadata(self, upload_id: str) -> UploadMetadata | None:
        stmt = (
            select(UploadMetadata)
            .where(UploadMetadata.upload_id == upload_id)
            .order_by(UploadMetadata.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_records(
        self,
        upload_id: str,
        records: list[TestRecord],
        *,
        dataset_id: str | None = None,
        batch_size: int = 1000,
    ) -> int:
        legacy_rows: list[TestRecordRow] = []
        normalized_rows: list[NormalizedRecord] = []
        for record in records:
            key = record.record_key or record.build_record_key()
            payload = record.to_dict()
            legacy_rows.append(
                TestRecordRow(
                    upload_id=upload_id,
                    record_key=key,
                    lot_id=record.lot_id,
                    wafer_id=record.wafer_id,
                    die_id=record.die_id,
                    test_stage=record.test_stage,
                    tester_id=record.tester_id,
                    pass_fail=record.pass_fail,
                    timestamp=record.timestamp,
                    adapter_id=record.adapter_id,
                    payload=payload,
                )
            )
            normalized_rows.append(
                NormalizedRecord(
                    upload_id=upload_id,
                    dataset_id=dataset_id,
                    record_key=key,
                    lot_id=record.lot_id,
                    wafer_id=record.wafer_id,
                    die_id=record.die_id,
                    test_stage=record.test_stage,
                    tester_id=record.tester_id,
                    pass_fail=record.pass_fail,
                    timestamp=record.timestamp,
                    adapter_id=record.adapter_id,
                    payload=payload,
                )
            )
            if len(legacy_rows) >= batch_size:
                self._session.add_all(legacy_rows)
                self._session.add_all(normalized_rows)
                await self._session.flush()
                legacy_rows.clear()
                normalized_rows.clear()
        if legacy_rows:
            self._session.add_all(legacy_rows)
            self._session.add_all(normalized_rows)
            await self._session.flush()
        return len(records)

    async def list_normalized_records(
        self, upload_id: str, *, limit: int = 100, offset: int = 0
    ) -> list[NormalizedRecord]:
        stmt = (
            select(NormalizedRecord)
            .where(NormalizedRecord.upload_id == upload_id)
            .order_by(NormalizedRecord.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_validation_results(self, upload_id: str) -> list[ValidationResult]:
        stmt = (
            select(ValidationResult)
            .where(ValidationResult.upload_id == upload_id)
            .order_by(ValidationResult.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_history(self, upload_id: str) -> list[UploadHistory]:
        stmt = (
            select(UploadHistory)
            .where(UploadHistory.upload_id == upload_id)
            .order_by(UploadHistory.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def parser_statistics(self) -> list[dict[str, Any]]:
        stmt = (
            select(
                Upload.parser_id,
                func.count(Upload.id),
                func.coalesce(func.sum(Upload.records_accepted), 0),
                func.sum(case((Upload.status == "completed", 1), else_=0)),
            )
            .where(Upload.parser_id.is_not(None))
            .group_by(Upload.parser_id)
        )
        result = await self._session.execute(stmt)
        rows = []
        for parser_id, count, accepted, success in result.all():
            rows.append(
                {
                    "parser_id": parser_id,
                    "upload_count": int(count),
                    "records_accepted": int(accepted or 0),
                    "success_count": int(success or 0),
                }
            )
        return rows

    async def status_counts(self) -> dict[str, int]:
        stmt = select(Upload.status, func.count(Upload.id)).group_by(Upload.status)
        result = await self._session.execute(stmt)
        return {status: int(count) for status, count in result.all()}

    async def delete_upload(self, upload_id: str) -> bool:
        upload = await self.get_upload(upload_id)
        if upload is None:
            return False
        await self._session.execute(delete(NormalizedRecord).where(NormalizedRecord.upload_id == upload_id))
        await self._session.execute(delete(TestRecordRow).where(TestRecordRow.upload_id == upload_id))
        await self._session.execute(delete(UploadMetadata).where(UploadMetadata.upload_id == upload_id))
        await self._session.execute(delete(ValidationResult).where(ValidationResult.upload_id == upload_id))
        await self._session.execute(delete(ParserMetadata).where(ParserMetadata.upload_id == upload_id))
        await self._session.execute(delete(UploadHistory).where(UploadHistory.upload_id == upload_id))
        await self._session.execute(delete(IngestionStatistics).where(IngestionStatistics.upload_id == upload_id))
        await self._session.delete(upload)
        await self.add_audit("upload", upload_id, "delete", None, {})
        await self._session.flush()
        return True
