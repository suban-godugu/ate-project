"""Async upload and ingestion pipeline orchestration for FA-FR-001."""

from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import PROCESSED_DIR, UPLOAD_DIR
from backend.ingestion.ingestion_repository import IngestionRepository
from backend.ingestion.metadata_service import build_upload_metadata
from backend.ingestion.normalization import normalize_records, records_to_payload
from backend.ingestion.parser_factory import ParserFactory
from backend.ingestion.security import detect_mime, safe_relative_path, sanitize_filename
from backend.ingestion.validation import sha256_file, validate_records, validate_upload_file

logger = logging.getLogger(__name__)


class UploadService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        parser_factory: ParserFactory | None = None,
    ) -> None:
        self._repo = IngestionRepository(session)
        self._factory = parser_factory or ParserFactory()
        self._session = session

    async def save_raw_upload(
        self,
        upload_file: UploadFile,
        *,
        max_bytes: int | None = None,
    ) -> tuple[Path, str, int]:
        from backend.config import MAX_UPLOAD_BYTES

        limit = max_bytes or MAX_UPLOAD_BYTES
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        original = sanitize_filename(upload_file.filename or "upload.bin")
        suffix = Path(original).suffix.lower()
        stored_name = f"{uuid.uuid4().hex}{suffix}"
        dest = UPLOAD_DIR / stored_name
        size = 0
        digest = __import__("hashlib").sha256()
        with dest.open("wb") as handle:
            while chunk := await upload_file.read(1024 * 1024):
                size += len(chunk)
                if size > limit:
                    handle.close()
                    dest.unlink(missing_ok=True)
                    raise ValueError(f"File exceeds max size ({limit} bytes)")
                digest.update(chunk)
                handle.write(chunk)
        return dest, digest.hexdigest(), size

    async def process_upload(
        self,
        *,
        upload_file: UploadFile,
        allow_duplicate: bool = False,
        dataset_id: str | None = None,
        relative_path: str | None = None,
        created_by: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        original_name = upload_file.filename or "upload.bin"
        sanitized = sanitize_filename(original_name)
        rel = safe_relative_path(relative_path)
        try:
            stored_path, checksum, size = await self.save_raw_upload(upload_file)
        except ValueError as exc:
            return {
                "duplicate": False,
                "upload": {
                    "id": "",
                    "original_filename": original_name,
                    "status": "failed",
                    "error_message": str(exc),
                    "records_accepted": 0,
                    "records_quarantined": 0,
                    "integrity_pct": 0.0,
                },
                "validation_report": {"issues": [str(exc)]},
                "processing_statistics": {},
                "parsed_dataset_preview": [],
            }

        upload_ms = (time.perf_counter() - start) * 1000
        mime = detect_mime(stored_path, upload_file.content_type)

        v_start = time.perf_counter()
        file_validation = validate_upload_file(
            stored_path, size_bytes=size, content_type=upload_file.content_type
        )
        validation_ms = (time.perf_counter() - v_start) * 1000

        if not file_validation["valid"]:
            upload = await self._repo.create_upload(
                original_filename=original_name,
                sanitized_filename=sanitized,
                stored_filename=stored_path.name,
                content_type=upload_file.content_type or "application/octet-stream",
                detected_mime=mime,
                file_extension=stored_path.suffix.lower(),
                file_size_bytes=size,
                checksum_sha256=checksum,
                dataset_id=dataset_id,
                relative_path=rel,
                created_by=created_by,
                tenant_id=tenant_id,
            )
            await self._repo.save_validation_issues(
                upload.id, file_validation["issues"], dataset_id=dataset_id
            )
            await self._repo.mark_failed(upload, "; ".join(file_validation["issues"]), created_by)
            await self._session.commit()
            return self._response(upload, parsed_dataset=[], duplicate=False)

        if not allow_duplicate:
            existing = await self._repo.find_by_checksum(checksum)
            if existing is not None:
                stored_path.unlink(missing_ok=True)
                return {
                    "duplicate": True,
                    "existing_upload_id": existing.id,
                    "message": "Duplicate upload detected (checksum match)",
                    "upload": self._serialize_upload(existing),
                }

        upload = await self._repo.create_upload(
            original_filename=original_name,
            sanitized_filename=sanitized,
            stored_filename=stored_path.name,
            content_type=upload_file.content_type or "application/octet-stream",
            detected_mime=mime,
            file_extension=stored_path.suffix.lower(),
            file_size_bytes=size,
            checksum_sha256=checksum,
            dataset_id=dataset_id,
            relative_path=rel,
            created_by=created_by,
            tenant_id=tenant_id,
        )
        await self._repo.mark_processing(upload, created_by)
        await self._session.commit()

        try:
            return await self._run_pipeline(
                upload.id,
                stored_path,
                original_name,
                checksum,
                start,
                upload_ms=upload_ms,
                validation_ms=validation_ms,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Upload processing failed for %s", upload.id)
            await self._repo.mark_failed(upload, str(exc), created_by)
            await self._session.commit()
            return self._response(upload, parsed_dataset=[], duplicate=False)

    async def process_local_path(
        self,
        path: Path,
        *,
        dataset_id: str | None = None,
        relative_path: str | None = None,
        created_by: str | None = None,
        tenant_id: str | None = None,
        allow_duplicate: bool = False,
    ) -> dict[str, Any]:
        """Ingest an already-available local file (server-side folder scan)."""
        start = time.perf_counter()
        if not path.is_file():
            raise FileNotFoundError(path)
        size = path.stat().st_size
        checksum = sha256_file(path)
        original_name = path.name
        sanitized = sanitize_filename(original_name)
        rel = safe_relative_path(relative_path)
        mime = detect_mime(path, None)

        file_validation = validate_upload_file(path, size_bytes=size, content_type=None)
        if not file_validation["valid"]:
            # Copy into upload storage for auditability
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            stored_name = f"{uuid.uuid4().hex}{path.suffix.lower()}"
            stored_path = UPLOAD_DIR / stored_name
            stored_path.write_bytes(path.read_bytes())
            upload = await self._repo.create_upload(
                original_filename=original_name,
                sanitized_filename=sanitized,
                stored_filename=stored_path.name,
                content_type="application/octet-stream",
                detected_mime=mime,
                file_extension=path.suffix.lower(),
                file_size_bytes=size,
                checksum_sha256=checksum,
                dataset_id=dataset_id,
                relative_path=rel,
                created_by=created_by,
                tenant_id=tenant_id,
            )
            await self._repo.save_validation_issues(
                upload.id, file_validation["issues"], dataset_id=dataset_id
            )
            await self._repo.mark_failed(upload, "; ".join(file_validation["issues"]), created_by)
            await self._session.commit()
            return self._response(upload, parsed_dataset=[], duplicate=False)

        if not allow_duplicate:
            existing = await self._repo.find_by_checksum(checksum)
            if existing is not None:
                return {
                    "duplicate": True,
                    "existing_upload_id": existing.id,
                    "message": "Duplicate upload detected (checksum match)",
                    "upload": self._serialize_upload(existing),
                }

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid.uuid4().hex}{path.suffix.lower()}"
        stored_path = UPLOAD_DIR / stored_name
        stored_path.write_bytes(path.read_bytes())

        upload = await self._repo.create_upload(
            original_filename=original_name,
            sanitized_filename=sanitized,
            stored_filename=stored_path.name,
            content_type="application/octet-stream",
            detected_mime=mime,
            file_extension=path.suffix.lower(),
            file_size_bytes=size,
            checksum_sha256=checksum,
            dataset_id=dataset_id,
            relative_path=rel,
            created_by=created_by,
            tenant_id=tenant_id,
        )
        await self._repo.mark_processing(upload, created_by)
        await self._session.commit()
        return await self._run_pipeline(
            upload.id, stored_path, original_name, checksum, start, upload_ms=0, validation_ms=0
        )

    async def process_existing_upload(self, upload_id: str) -> dict[str, Any]:
        upload = await self._repo.get_upload(upload_id)
        if upload is None:
            raise FileNotFoundError(f"Upload not found: {upload_id}")
        stored_path = UPLOAD_DIR / upload.stored_filename
        if not stored_path.is_file():
            await self._repo.mark_failed(upload, f"Stored file missing: {stored_path.name}")
            await self._session.commit()
            raise FileNotFoundError(stored_path)

        file_validation = validate_upload_file(
            stored_path,
            size_bytes=upload.file_size_bytes,
            content_type=upload.content_type,
        )
        if not file_validation["valid"]:
            await self._repo.save_validation_issues(upload.id, file_validation["issues"])
            await self._repo.mark_failed(upload, "; ".join(file_validation["issues"]))
            await self._session.commit()
            return self._response(upload, parsed_dataset=[], duplicate=False)

        start = time.perf_counter()
        await self._repo.mark_processing(upload)
        await self._session.commit()
        return await self._run_pipeline(
            upload.id,
            stored_path,
            upload.original_filename,
            upload.checksum_sha256,
            start,
        )

    async def _run_pipeline(
        self,
        upload_id: str,
        stored_path: Path,
        original_name: str,
        checksum: str,
        start: float,
        *,
        upload_ms: float = 0.0,
        validation_ms: float = 0.0,
    ) -> dict[str, Any]:
        upload = await self._repo.get_upload(upload_id)
        if upload is None:
            raise FileNotFoundError(upload_id)

        p_start = time.perf_counter()
        parse_result, parser_id = self._factory.parse(stored_path)
        parse_ms = (time.perf_counter() - p_start) * 1000

        n_start = time.perf_counter()
        normalized = normalize_records(parse_result.records)
        accepted, quarantined, duplicate_count = validate_records(normalized)
        normalize_ms = (time.perf_counter() - n_start) * 1000

        fatal_parse = bool(parse_result.errors) and parser_id is None
        zero_accept_non_stil = (
            len(accepted) == 0
            and parser_id not in {None, "stil_v1"}
            and stored_path.suffix.lower() != ".stil"
        )
        stil_failed = parser_id == "stil_v1" and any(
            "validation failed" in (e.get("error") or "").lower() for e in parse_result.errors
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        records_per_minute = (
            round(len(normalized) / max(elapsed_ms / 60000, 1e-6), 2) if normalized else 0.0
        )

        validation_report = {
            "file_validation": validate_upload_file(
                stored_path, size_bytes=stored_path.stat().st_size, content_type=upload.content_type
            ),
            "parse_errors": parse_result.errors,
            "quarantined_count": len(quarantined),
            "quarantine_sample": quarantined[:10],
            "duplicate_records_skipped": duplicate_count,
            "mandatory_fields_enforced": True,
            "parser_metadata_keys": list((parse_result.metadata or {}).keys()),
        }
        processing_stats = {
            "elapsed_ms": elapsed_ms,
            "upload_ms": round(upload_ms, 2),
            "validation_ms": round(validation_ms, 2),
            "parse_ms": round(parse_ms, 2),
            "normalize_ms": round(normalize_ms, 2),
            "records_parsed": len(normalized),
            "records_accepted": len(accepted),
            "records_per_minute": records_per_minute,
            "parser_id": parser_id,
        }

        if fatal_parse or stil_failed or zero_accept_non_stil:
            issues = [e.get("error", "parse error") for e in parse_result.errors] or [
                "No valid records produced"
            ]
            await self._repo.save_validation_issues(
                upload.id, issues, dataset_id=upload.dataset_id, category="parser"
            )
            await self._repo.mark_failed(upload, "; ".join(issues))
            await self._repo.save_statistics(
                upload_id=upload.id,
                dataset_id=upload.dataset_id,
                upload_ms=upload_ms,
                validation_ms=validation_ms,
                parse_ms=parse_ms,
                normalize_ms=normalize_ms,
                persist_ms=0,
                total_ms=elapsed_ms,
                records_parsed=len(normalized),
                records_accepted=0,
                records_quarantined=len(quarantined) + duplicate_count,
                records_per_minute=0,
                file_size_bytes=upload.file_size_bytes,
                parser_id=parser_id,
                success=False,
            )
            await self._session.commit()
            return self._response(upload, parsed_dataset=[], duplicate=False)

        persist_start = time.perf_counter()
        total = len(accepted) + len(quarantined) + duplicate_count
        integrity = round(100.0 * len(accepted) / total, 4) if total else 100.0

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        processed_path = PROCESSED_DIR / f"{upload_id}.json"
        processed_path.write_text(
            json.dumps(records_to_payload(accepted), indent=2),
            encoding="utf-8",
        )

        await self._repo.save_records(upload_id, accepted, dataset_id=upload.dataset_id)
        if parse_result.metadata:
            await self._repo.save_parser_metadata(
                upload_id, parser_id or "unknown", parse_result.metadata
            )
        if quarantined:
            await self._repo.save_validation_issues(
                upload_id,
                [f"Quarantined record missing fields: {q}" for q in quarantined[:20]],
                dataset_id=upload.dataset_id,
                severity="warning",
                category="quarantine",
                code="MANDATORY_FIELDS",
            )

        metadata = build_upload_metadata(
            upload_id=upload_id,
            original_filename=original_name,
            stored_path=stored_path,
            parser_id=parser_id,
            checksum=checksum,
            records=accepted,
            validation_report=validation_report,
            processing_stats=processing_stats,
        )
        await self._repo.save_metadata(upload_id, metadata)
        persist_ms = (time.perf_counter() - persist_start) * 1000
        processing_stats["persist_ms"] = round(persist_ms, 2)

        await self._repo.mark_completed(
            upload,
            parser_id=parser_id,
            records_accepted=len(accepted),
            records_quarantined=len(quarantined) + duplicate_count,
            integrity_pct=integrity,
            validation_report=validation_report,
            processing_stats=processing_stats,
        )
        await self._repo.save_statistics(
            upload_id=upload.id,
            dataset_id=upload.dataset_id,
            upload_ms=upload_ms,
            validation_ms=validation_ms,
            parse_ms=parse_ms,
            normalize_ms=normalize_ms,
            persist_ms=persist_ms,
            total_ms=elapsed_ms,
            records_parsed=len(normalized),
            records_accepted=len(accepted),
            records_quarantined=len(quarantined) + duplicate_count,
            records_per_minute=records_per_minute,
            file_size_bytes=upload.file_size_bytes,
            parser_id=parser_id,
            success=True,
        )
        await self._session.commit()

        return self._response(
            upload,
            parsed_dataset=records_to_payload(accepted)[:100],
            duplicate=False,
            metadata=metadata,
        )

    def _serialize_upload(self, upload) -> dict[str, Any]:
        return {
            "id": upload.id,
            "dataset_id": upload.dataset_id,
            "original_filename": upload.original_filename,
            "status": upload.status,
            "parser_id": upload.parser_id,
            "file_size_bytes": upload.file_size_bytes,
            "checksum_sha256": upload.checksum_sha256,
            "records_accepted": upload.records_accepted,
            "records_quarantined": upload.records_quarantined,
            "integrity_pct": upload.integrity_pct,
            "created_at": upload.created_at.isoformat() if upload.created_at else None,
            "completed_at": upload.completed_at.isoformat() if upload.completed_at else None,
            "error_message": upload.error_message,
        }

    def _response(
        self,
        upload,
        *,
        parsed_dataset: list[dict[str, Any]],
        duplicate: bool,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "duplicate": duplicate,
            "upload": self._serialize_upload(upload),
            "parsed_dataset_preview": parsed_dataset,
            "validation_report": upload.validation_report,
            "processing_statistics": upload.processing_stats,
            "metadata": metadata,
        }
