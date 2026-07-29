import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import cache_delete, cache_delete_pattern
from app.models.analytics import Alert
from app.models.core import Lot, Wafer
from app.models.users import User
from app.schemas.common import AlertCreate, AlertUpdate
from app.services.deps import format_relative_time


async def invalidate_alert_caches() -> None:
    await cache_delete_pattern("dash:alerts:*")
    await cache_delete_pattern("notif:*")
    await cache_delete("search:index:v1")


def _alert_row(a: Alert, lots: dict, wafers: dict, users: dict) -> dict[str, Any]:
    return {
        "id": str(a.id),
        "sourceModule": a.source_module,
        "lotId": lots.get(a.lot_id, ""),
        "waferId": wafers.get(a.wafer_id, ""),
        "severity": a.severity,
        "description": a.description or a.title or "",
        "status": a.status,
        "assignedEngineer": users.get(a.assigned_user_id, "Unassigned"),
        "createdTime": format_relative_time(a.created_at),
    }


async def _lookup_refs(db: AsyncSession, alerts: list[Alert]) -> tuple[dict, dict, dict]:
    lot_ids = {a.lot_id for a in alerts if a.lot_id}
    wafer_ids = {a.wafer_id for a in alerts if a.wafer_id}
    user_ids = {a.assigned_user_id for a in alerts if a.assigned_user_id}
    lots, wafers, users = {}, {}, {}
    if lot_ids:
        res = await db.execute(select(Lot).where(Lot.id.in_(lot_ids)))
        lots = {l.id: l.lot_code.upper() for l in res.scalars().all()}
    if wafer_ids:
        res = await db.execute(select(Wafer).where(Wafer.id.in_(wafer_ids)))
        wafers = {
            w.id: w.wafer_code.replace("wafer-", "W-").replace("Wafer-", "W-")
            for w in res.scalars().all()
        }
    if user_ids:
        res = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = {u.id: u.name for u in res.scalars().all()}
    return lots, wafers, users


async def create_alert(db: AsyncSession, body: AlertCreate) -> dict[str, Any]:
    alert = Alert(
        source_module=body.source_module,
        severity=body.severity,
        status=body.status,
        title=body.title,
        description=body.description,
        lot_id=uuid.UUID(body.lot_id) if body.lot_id else None,
        wafer_id=uuid.UUID(body.wafer_id) if body.wafer_id else None,
        assigned_user_id=uuid.UUID(body.assigned_user_id) if body.assigned_user_id else None,
    )
    db.add(alert)
    await db.flush()
    lots, wafers, users = await _lookup_refs(db, [alert])
    await invalidate_alert_caches()
    return _alert_row(alert, lots, wafers, users)


async def update_alert(db: AsyncSession, alert_id: str, body: AlertUpdate) -> dict[str, Any]:
    result = await db.execute(select(Alert).where(Alert.id == uuid.UUID(alert_id)))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if body.severity is not None:
        alert.severity = body.severity
    if body.status is not None:
        alert.status = body.status
    if body.title is not None:
        alert.title = body.title
    if body.description is not None:
        alert.description = body.description
    if body.assigned_user_id is not None:
        alert.assigned_user_id = uuid.UUID(body.assigned_user_id) if body.assigned_user_id else None
    await db.flush()
    lots, wafers, users = await _lookup_refs(db, [alert])
    await invalidate_alert_caches()
    return _alert_row(alert, lots, wafers, users)


async def delete_alert(db: AsyncSession, alert_id: str) -> None:
    result = await db.execute(select(Alert).where(Alert.id == uuid.UUID(alert_id)))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.execute(delete(Alert).where(Alert.id == uuid.UUID(alert_id)))
    await invalidate_alert_caches()
