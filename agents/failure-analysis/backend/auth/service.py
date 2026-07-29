"""Auth service: login, refresh, logout, bootstrap admin."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.repository import (
    AuditRepository,
    NotificationRepository,
    TokenRepository,
    UserRepository,
)
from backend.auth.security import (
    ROLES,
    create_access_token,
    create_refresh_token_value,
    verify_password,
)
from backend.settings import get_settings


def serialize_user(user: Any) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "status": user.status,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = TokenRepository(db)
        self.audit = AuditRepository(db)
        self.notifications = NotificationRepository(db)

    async def ensure_bootstrap_admin(self) -> None:
        settings = get_settings()
        count = await self.users.count()
        if count > 0:
            return
        email = getattr(settings, "bootstrap_admin_email", "admin@verilumen.local")
        password = getattr(settings, "bootstrap_admin_password", "ChangeMe123!")
        await self.users.create(
            email=email,
            full_name="System Administrator",
            password=password,
            role="administrator",
        )
        await self.audit.add(
            action="bootstrap_admin",
            actor_email=email,
            details={"message": "Initial administrator created"},
        )
        await self.db.commit()

    async def login(
        self, email: str, password: str, *, ip_address: str | None = None
    ) -> dict[str, Any]:
        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            await self.audit.add(
                action="login_failed",
                actor_email=email,
                ip_address=ip_address,
                details={"reason": "invalid_credentials"},
            )
            await self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_credentials", "message": "Invalid email or password"},
            )
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "user_disabled", "message": "Account is disabled"},
            )

        settings = get_settings()
        access = create_access_token(
            user_id=user.id, email=user.email, role=user.role
        )
        refresh = create_refresh_token_value()
        await self.tokens.store(
            user_id=user.id,
            raw_token=refresh,
            days=getattr(settings, "jwt_refresh_days", 7),
        )
        await self.users.touch_login(user)
        await self.audit.add(
            action="login",
            actor_id=user.id,
            actor_email=user.email,
            ip_address=ip_address,
        )
        await self.notifications.create(
            title="Login successful",
            body=f"Signed in as {user.email}",
            category="info",
            user_id=user.id,
        )
        await self.db.commit()
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": getattr(settings, "jwt_access_minutes", 30) * 60,
            "user": serialize_user(user),
        }

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        row = await self.tokens.find_valid(refresh_token)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_refresh", "message": "Refresh token invalid or expired"},
            )
        user = await self.users.get_by_id(row.user_id)
        if user is None or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "user_disabled", "message": "User inactive"},
            )
        # Rotate refresh token
        await self.tokens.revoke(refresh_token)
        new_refresh = create_refresh_token_value()
        settings = get_settings()
        await self.tokens.store(
            user_id=user.id,
            raw_token=new_refresh,
            days=getattr(settings, "jwt_refresh_days", 7),
        )
        access = create_access_token(
            user_id=user.id, email=user.email, role=user.role
        )
        await self.db.commit()
        return {
            "access_token": access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
            "expires_in": getattr(settings, "jwt_access_minutes", 30) * 60,
            "user": serialize_user(user),
        }

    async def logout(
        self, refresh_token: str | None, user: dict[str, Any], *, ip_address: str | None = None
    ) -> None:
        if refresh_token:
            await self.tokens.revoke(refresh_token)
        await self.audit.add(
            action="logout",
            actor_id=user.get("id"),
            actor_email=user.get("email"),
            ip_address=ip_address,
        )
        await self.db.commit()

    async def create_user(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        role: str,
        actor: dict[str, Any],
    ) -> dict[str, Any]:
        if role not in ROLES:
            raise HTTPException(status_code=422, detail={"code": "invalid_role", "message": f"Role must be one of {ROLES}"})
        existing = await self.users.get_by_email(email)
        if existing:
            raise HTTPException(status_code=409, detail={"code": "email_exists", "message": "Email already registered"})
        user = await self.users.create(
            email=email, full_name=full_name, password=password, role=role
        )
        await self.audit.add(
            action="user_created",
            actor_id=actor.get("id"),
            actor_email=actor.get("email"),
            resource_type="user",
            resource_id=user.id,
            details={"email": email, "role": role},
        )
        await self.db.commit()
        return serialize_user(user)
