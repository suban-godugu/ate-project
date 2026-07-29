from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.users import User
from app.schemas.common import AuditLogOut, AuditLogListResponse
from app.services.audit_query import list_audit_logs
from app.services.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID

    uid = UUID(user_id) if user_id else None
    rows, total = await list_audit_logs(
        db,
        viewer=user,
        page=page,
        page_size=page_size,
        user_id=uid,
        action=action,
        entity_type=entity_type,
        severity=severity,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    return AuditLogListResponse(
        items=[AuditLogOut(**r) for r in rows],
        page=page,
        page_size=page_size,
        total=total,
    )
