"""Audit log retrieval with role-based filtering."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import AuditLog, User


async def list_audit_logs(
    db: AsyncSession,
    *,
    viewer: User,
    page: int = 1,
    page_size: int = 20,
    user_id: UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> tuple[list[dict], int]:
    def _apply_filters(stmt):
        role = (viewer.role or "engineer").lower()
        if role == "admin":
            if user_id:
                stmt = stmt.where(AuditLog.user_id == user_id)
        elif role != "viewer":
            stmt = stmt.where(AuditLog.user_id == viewer.id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)
        if severity:
            stmt = stmt.where(AuditLog.meta["severity"].astext == severity)
        if date_from:
            stmt = stmt.where(AuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(AuditLog.created_at <= date_to)
        if search:
            pattern = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    AuditLog.action.ilike(pattern),
                    AuditLog.entity_type.ilike(pattern),
                    AuditLog.entity_id.ilike(pattern),
                    AuditLog.meta["message"].astext.ilike(pattern),
                    AuditLog.meta["filename"].astext.ilike(pattern),
                )
            )
        return stmt

    count_stmt = _apply_filters(select(func.count(AuditLog.id)))
    total = (await db.execute(count_stmt)).scalar() or 0

    query = _apply_filters(select(AuditLog, User.name).outerjoin(User, AuditLog.user_id == User.id))
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size))
    rows = []
    for log, username in result.all():
        meta = log.meta or {}
        rows.append(
            {
                "id": str(log.id),
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "user_id": str(log.user_id) if log.user_id else None,
                "username": username or meta.get("username"),
                "severity": meta.get("severity", "info"),
                "status": meta.get("status"),
                "message": meta.get("message"),
                "upload_job_id": meta.get("upload_job_id"),
                "filename": meta.get("filename"),
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "meta": meta,
            }
        )
    return rows, total
