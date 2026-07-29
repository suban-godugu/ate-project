"""JWT helpers, password hashing, and RBAC dependencies."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.settings import get_settings

ROLES = ("administrator", "engineer", "operator", "viewer")
ROLE_RANK = {r: i for i, r in enumerate(ROLES)}

CAPABILITIES: dict[str, str] = {
    "user_management": "administrator",
    "settings": "administrator",
    "audit_logs": "administrator",
    "upload": "engineer",
    "run_analysis": "engineer",
    "view_reports": "engineer",
    "view_dashboard": "operator",
    "monitor_analysis": "operator",
    "read_dashboard": "viewer",
}

_bearer = HTTPBearer(auto_error=False)


def _secret() -> str:
    settings = get_settings()
    return getattr(settings, "jwt_secret", None) or "dev-only-change-me-jwt-secret-32b!"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000)
    return f"pbkdf2_sha256$120000${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, rounds_s, salt, expected = password_hash.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(rounds_s)
        )
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    *,
    user_id: str,
    email: str,
    role: str,
    expires_minutes: int | None = None,
) -> str:
    settings = get_settings()
    minutes = expires_minutes or getattr(settings, "jwt_access_minutes", 30)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=minutes)).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "token_expired", "message": "Access token expired"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid access token"},
        ) from exc


def role_at_least(user_role: str, required: str) -> bool:
    return ROLE_RANK.get(user_role, 99) <= ROLE_RANK.get(required, 99)


def require_capability(capability: str, user_role: str) -> None:
    required = CAPABILITIES.get(capability, "administrator")
    if not role_at_least(user_role, required):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "forbidden",
                "message": f"Role '{user_role}' cannot perform '{capability}'",
            },
        )


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    settings = get_settings()
    auth_required = getattr(settings, "auth_required", True)

    if credentials is None:
        if not auth_required:
            return {
                "id": "anonymous",
                "email": "anonymous@local",
                "role": "administrator",
                "full_name": "Anonymous",
                "status": "active",
            }
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Authentication required"},
        )

    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Expected access token"},
        )

    from backend.auth.repository import UserRepository

    user = await UserRepository(db).get_by_id(str(payload["sub"]))
    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "user_disabled", "message": "User inactive or not found"},
        )
    request.state.user = user
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "status": user.status,
    }


def require_roles(*roles: str):
    async def _dep(user: Annotated[dict[str, Any], Depends(get_current_user)]) -> dict[str, Any]:
        if not any(role_at_least(user["role"], r) for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "Insufficient role"},
            )
        return user

    return _dep


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
AdminUser = Annotated[dict[str, Any], Depends(require_roles("administrator"))]
EngineerUser = Annotated[dict[str, Any], Depends(require_roles("engineer"))]
OperatorUser = Annotated[dict[str, Any], Depends(require_roles("operator"))]
