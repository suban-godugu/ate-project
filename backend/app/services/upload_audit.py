"""Upload and parser audit helpers — extends write_audit_log without duplicating it."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.uploads import UploadJob
from app.models.users import User
from app.services.audit_service import write_audit_log


def _job_meta(
    job: UploadJob,
    *,
    user: User | None = None,
    severity: str = "info",
    status: str | None = None,
    duration_ms: int | None = None,
    message: str | None = None,
    extra: dict | None = None,
) -> dict:
    meta = {
        "event_type": extra.get("event_type") if extra and "event_type" in extra else None,
        "severity": severity,
        "upload_job_id": str(job.id),
        "filename": job.file_name,
        "filesize": job.size_bytes,
        "status": status or (job.status.value if job.status else None),
        "module": job.module,
        "kind": job.kind.value if job.kind else None,
    }
    if duration_ms is not None:
        meta["duration_ms"] = duration_ms
    if message:
        meta["message"] = message
    if user:
        meta["username"] = user.name
    for key in ("lot", "wafer", "tester", "product"):
        if extra and extra.get(key):
            meta[key] = extra[key]
    if extra:
        meta.update({k: v for k, v in extra.items() if k not in ("event_type", "lot", "wafer", "tester", "product")})
    return meta


async def audit_upload_event(
    db: AsyncSession,
    *,
    user_id: UUID | str | None,
    action: str,
    job: UploadJob,
    user: User | None = None,
    severity: str = "info",
    status: str | None = None,
    duration_ms: int | None = None,
    message: str | None = None,
    extra: dict | None = None,
) -> None:
    meta = _job_meta(
        job,
        user=user,
        severity=severity,
        status=status,
        duration_ms=duration_ms,
        message=message,
        extra=extra,
    )
    meta["event_type"] = action
    await write_audit_log(
        db,
        user_id=user_id,
        action=action,
        entity_type="upload",
        entity_id=str(job.id),
        meta=meta,
    )
