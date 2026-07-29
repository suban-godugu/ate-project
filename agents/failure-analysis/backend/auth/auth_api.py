"""Auth, users, audit, settings, notifications, and system health APIs."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.repository import (
    AuditRepository,
    NotificationRepository,
    SettingsRepository,
    UserRepository,
)
from backend.auth.security import (
    ROLES,
    AdminUser,
    CurrentUser,
    EngineerUser,
    require_capability,
)
from backend.auth.service import AuthService, serialize_user
from backend.config import API_PREFIX
from backend.database import get_db
from backend.settings import get_settings

router = APIRouter(prefix=f"{API_PREFIX}", tags=["auth"])


# ── Schemas ──────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class CreateUserRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="viewer")


class UpdateUserRequest(BaseModel):
    full_name: str | None = None
    role: str | None = None
    status: str | None = None


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class SettingsPayload(BaseModel):
    backend_url: str | None = None
    polling_interval_ms: int | None = Field(default=None, ge=1000, le=60_000)
    theme: str | None = None
    notification_preferences: dict[str, Any] | None = None
    export_preferences: dict[str, Any] | None = None
    analysis_defaults: dict[str, Any] | None = None


# ── Auth ─────────────────────────────────────────────────────────────────


@router.post("/auth/login")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    svc = AuthService(db)
    await svc.ensure_bootstrap_admin()
    ip = request.client.host if request.client else None
    return await svc.login(body.email, body.password, ip_address=ip)


@router.post("/auth/refresh")
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await AuthService(db).refresh(body.refresh_token)


@router.post("/auth/logout")
async def logout(
    body: LogoutRequest,
    request: Request,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    ip = request.client.host if request.client else None
    await AuthService(db).logout(body.refresh_token, user, ip_address=ip)
    return {"status": "ok"}


@router.get("/auth/me")
async def me(user: CurrentUser) -> dict[str, Any]:
    return {"user": user}


# ── Users (Administrator) ────────────────────────────────────────────────


@router.get("/users")
async def list_users(
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    require_capability("user_management", admin["role"])
    users = await UserRepository(db).list_users(limit=limit)
    return {"users": [serialize_user(u) for u in users], "roles": list(ROLES)}


@router.post("/users", status_code=201)
async def create_user(
    body: CreateUserRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    require_capability("user_management", admin["role"])
    user = await AuthService(db).create_user(
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        role=body.role,
        actor=admin,
    )
    return {"user": user}


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    require_capability("user_management", admin["role"])
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
    if body.role and body.role not in ROLES:
        raise HTTPException(status_code=422, detail={"code": "invalid_role", "message": "Invalid role"})
    await repo.update_user(
        user,
        full_name=body.full_name,
        role=body.role,
        status=body.status,
    )
    await AuditRepository(db).add(
        action="user_updated",
        actor_id=admin["id"],
        actor_email=admin["email"],
        resource_type="user",
        resource_id=user_id,
        details=body.model_dump(exclude_none=True),
    )
    await db.commit()
    return {"user": serialize_user(user)}


@router.post("/users/{user_id}/disable")
async def disable_user(
    user_id: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    require_capability("user_management", admin["role"])
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
    await repo.update_user(user, status="disabled")
    await AuditRepository(db).add(
        action="user_disabled",
        actor_id=admin["id"],
        actor_email=admin["email"],
        resource_type="user",
        resource_id=user_id,
    )
    await db.commit()
    return {"user": serialize_user(user)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    require_capability("user_management", admin["role"])
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail={"code": "self_delete", "message": "Cannot delete yourself"})
    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
    await db.delete(user)
    await AuditRepository(db).add(
        action="user_deleted",
        actor_id=admin["id"],
        actor_email=admin["email"],
        resource_type="user",
        resource_id=user_id,
    )
    await db.commit()
    return {"status": "deleted"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: str,
    body: ResetPasswordRequest,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    require_capability("user_management", admin["role"])
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
    await repo.set_password(user, body.password)
    await AuditRepository(db).add(
        action="password_reset",
        actor_id=admin["id"],
        actor_email=admin["email"],
        resource_type="user",
        resource_id=user_id,
    )
    await db.commit()
    return {"status": "ok"}


# ── Audit ────────────────────────────────────────────────────────────────


@router.get("/audit")
async def list_audit(
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
    search: str | None = None,
    action: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    require_capability("audit_logs", admin["role"])
    events = await AuditRepository(db).list_events(
        search=search, action=action, limit=limit
    )
    return {
        "events": [
            {
                "id": e.id,
                "action": e.action,
                "actor_id": e.actor_id,
                "actor_email": e.actor_email,
                "resource_type": e.resource_type,
                "resource_id": e.resource_id,
                "details": e.details,
                "ip_address": e.ip_address,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }


# ── Settings ─────────────────────────────────────────────────────────────


DEFAULT_SETTINGS = {
    "backend_url": "",
    "polling_interval_ms": 2000,
    "theme": "enterprise-dark",
    "notification_preferences": {
        "analysis_completed": True,
        "analysis_failed": True,
        "report_ready": True,
        "system_warning": True,
    },
    "export_preferences": {"default_format": "pdf"},
    "analysis_defaults": {"async_execution": True},
}


@router.get("/settings")
async def get_settings_api(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    stored = await SettingsRepository(db).get("app")
    return {"settings": {**DEFAULT_SETTINGS, **stored}}


@router.put("/settings")
async def put_settings(
    body: SettingsPayload,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    require_capability("settings", admin["role"])
    repo = SettingsRepository(db)
    current = await repo.get("app")
    merged = {**DEFAULT_SETTINGS, **current, **body.model_dump(exclude_none=True)}
    saved = await repo.upsert("app", merged, updated_by=admin["email"])
    await AuditRepository(db).add(
        action="settings_changed",
        actor_id=admin["id"],
        actor_email=admin["email"],
        resource_type="settings",
        details=body.model_dump(exclude_none=True),
    )
    await db.commit()
    return {"settings": saved}


# ── Notifications ────────────────────────────────────────────────────────


@router.get("/notifications")
async def list_notifications(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    repo = NotificationRepository(db)
    items = await repo.list_for_user(user["id"])
    unread = await repo.unread_count(user["id"])
    return {
        "unread_count": unread,
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "body": n.body,
                "category": n.category,
                "read": n.read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in items
        ],
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await NotificationRepository(db).mark_read(notification_id, user["id"])
    await db.commit()
    return {"status": "ok"}


# ── System Health ────────────────────────────────────────────────────────


@router.get("/system/health")
async def system_health(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    start = time.perf_counter()
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    storage_status = "ok" if upload_dir.exists() else "missing"
    storage_bytes = 0
    file_count = 0
    if upload_dir.exists():
        for p in upload_dir.rglob("*"):
            if p.is_file():
                file_count += 1
                try:
                    storage_bytes += p.stat().st_size
                except OSError:
                    pass

    cpu = mem = disk = None
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.05)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage(str(upload_dir if upload_dir.exists() else Path.cwd())).percent
    except Exception:
        pass

    last_analysis = None
    queue_size = 0
    try:
        from backend.models import EvaluationRun  # type: ignore

        result = await db.execute(
            select(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(1)
        )
        run = result.scalar_one_or_none()
        if run:
            last_analysis = {
                "execution_id": getattr(run, "id", None),
                "status": getattr(run, "status", None),
                "created_at": run.created_at.isoformat() if getattr(run, "created_at", None) else None,
            }
    except Exception:
        pass

    response_ms = round((time.perf_counter() - start) * 1000, 2)
    return {
        "backend_status": "ok",
        "database_status": db_status,
        "storage_status": storage_status,
        "cpu_usage": cpu,
        "memory_usage": mem,
        "disk_usage": disk,
        "api_response_time_ms": response_ms,
        "last_successful_analysis": last_analysis,
        "queue_size": queue_size,
        "storage_bytes": storage_bytes,
        "uploaded_file_count": file_count,
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ── Storage / file management ────────────────────────────────────────────


@router.get("/storage/files")
async def list_storage_files(
    user: EngineerUser,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """List uploaded files from ingestion uploads table when available."""
    files: list[dict[str, Any]] = []
    try:
        from backend.models import Upload

        result = await db.execute(
            select(Upload).order_by(Upload.created_at.desc()).limit(limit)
        )
        for row in result.scalars().all():
            files.append(
                {
                    "id": row.id,
                    "filename": getattr(row, "original_filename", None)
                    or getattr(row, "filename", None)
                    or row.id,
                    "size_bytes": getattr(row, "size_bytes", None)
                    or getattr(row, "file_size_bytes", 0)
                    or 0,
                    "uploaded_at": row.created_at.isoformat() if row.created_at else None,
                    "owner": getattr(row, "created_by", None)
                    or getattr(row, "uploaded_by", None),
                    "status": getattr(row, "status", "unknown"),
                    "dataset_id": getattr(row, "dataset_id", None),
                }
            )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"code": "storage_error", "message": str(exc)},
        ) from exc
    return {"files": files, "total": len(files)}


@router.post("/storage/files/{upload_id}/archive")
async def archive_file(
    upload_id: str,
    user: EngineerUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await AuditRepository(db).add(
        action="file_archived",
        actor_id=user["id"],
        actor_email=user["email"],
        resource_type="upload",
        resource_id=upload_id,
    )
    await db.commit()
    return {"status": "archived", "upload_id": upload_id}


@router.delete("/storage/files/{upload_id}")
async def delete_storage_file(
    upload_id: str,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    try:
        from backend.models import Upload

        row = await db.get(Upload, upload_id)
        if row:
            await db.delete(row)
    except Exception:
        pass
    await AuditRepository(db).add(
        action="file_deleted",
        actor_id=admin["id"],
        actor_email=admin["email"],
        resource_type="upload",
        resource_id=upload_id,
    )
    await db.commit()
    return {"status": "deleted"}
