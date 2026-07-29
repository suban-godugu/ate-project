from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.request_context import get_request_id
from app.models.users import AuditLog


async def write_audit_log(
    db: AsyncSession,
    *,
    user_id: UUID | str | None,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    meta: dict | None = None,
) -> None:
    uid = UUID(str(user_id)) if user_id else None
    merged_meta = dict(meta or {})
    rid = get_request_id()
    if rid:
        merged_meta["request_id"] = rid
    db.add(
        AuditLog(
            user_id=uid,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            meta=merged_meta,
        )
    )
