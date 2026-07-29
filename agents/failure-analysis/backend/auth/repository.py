"""Persistence helpers for auth domain."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.models import (
    AppSetting,
    Notification,
    RefreshToken,
    SystemAuditEvent,
    User,
)
from backend.auth.security import hash_password, hash_token


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: str) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email.lower()))
        return result.scalar_one_or_none()

    async def list_users(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        role: str = "viewer",
    ) -> User:
        user = User(
            email=email.lower().strip(),
            full_name=full_name.strip(),
            password_hash=hash_password(password),
            role=role,
            status="active",
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user: User, **fields: Any) -> User:
        for key, value in fields.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return user

    async def set_password(self, user: User, password: str) -> None:
        user.password_hash = hash_password(password)
        user.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def touch_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(User))
        return int(result.scalar_one())


class TokenRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def store(self, *, user_id: str, raw_token: str, days: int = 7) -> RefreshToken:
        row = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(days=days),
        )
        self.db.add(row)
        await self.db.flush()
        return row

    async def find_valid(self, raw_token: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(raw_token),
                RefreshToken.revoked.is_(False),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return None
        return row

    async def revoke(self, raw_token: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(raw_token))
            .values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
            .values(revoked=True)
        )


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add(
        self,
        *,
        action: str,
        actor_id: str | None = None,
        actor_email: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> SystemAuditEvent:
        event = SystemAuditEvent(
            action=action,
            actor_id=actor_id,
            actor_email=actor_email,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_events(
        self,
        *,
        search: str | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SystemAuditEvent]:
        stmt = select(SystemAuditEvent).order_by(SystemAuditEvent.created_at.desc())
        if action:
            stmt = stmt.where(SystemAuditEvent.action == action)
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    SystemAuditEvent.actor_email.ilike(like),
                    SystemAuditEvent.action.ilike(like),
                    SystemAuditEvent.resource_type.ilike(like),
                )
            )
        result = await self.db.execute(stmt.offset(offset).limit(limit))
        return list(result.scalars().all())


class SettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, key: str = "app") -> dict:
        result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        return row.value if row else {}

    async def upsert(self, key: str, value: dict, updated_by: str | None = None) -> dict:
        result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        row = result.scalar_one_or_none()
        if row is None:
            row = AppSetting(key=key, value=value, updated_by=updated_by)
            self.db.add(row)
        else:
            row.value = value
            row.updated_by = updated_by
            row.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return row.value


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        *,
        title: str,
        body: str = "",
        category: str = "info",
        user_id: str | None = None,
    ) -> Notification:
        n = Notification(title=title, body=body, category=category, user_id=user_id)
        self.db.add(n)
        await self.db.flush()
        return n

    async def list_for_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(
                or_(Notification.user_id == user_id, Notification.user_id.is_(None))
            )
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def unread_count(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.read.is_(False),
                or_(Notification.user_id == user_id, Notification.user_id.is_(None)),
            )
        )
        return int(result.scalar_one())

    async def mark_read(self, notification_id: str, user_id: str) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.id == notification_id)
            .values(read=True)
        )
