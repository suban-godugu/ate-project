from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import blacklist_jwt, get_redis, prefix_key
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    safe_decode_token,
    verify_password,
)
from app.models.users import User
from app.schemas.common import LoginRequest, RefreshRequest, TokenResponse, UserOut
from app.services.audit_service import write_audit_log
from app.services.deps import get_current_user, security

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_TTL = 24 * 3600  # refresh metadata cache
# Demo / shared account: allow many browsers on alex@verilumen.ai at once.
MAX_CONCURRENT_SESSIONS = 20


def _sessions_key(user_id: str) -> str:
    return prefix_key(f"sessions:{user_id}")


async def _register_refresh_session(user_id: str, refresh_jti: str) -> None:
    """Track up to MAX_CONCURRENT_SESSIONS refresh tokens per user (newest kept)."""
    client = await get_redis()
    key = _sessions_key(user_id)
    now = datetime.now(UTC).timestamp()
    await client.zadd(key, {refresh_jti: now})
    # Drop oldest when over the cap (rank 0 = lowest score = oldest).
    count = await client.zcard(key)
    if count > MAX_CONCURRENT_SESSIONS:
        overflow = count - MAX_CONCURRENT_SESSIONS
        await client.zremrangebyrank(key, 0, overflow - 1)
    await client.expire(key, SESSION_TTL)


async def _refresh_session_valid(user_id: str, refresh_jti: str) -> bool:
    client = await get_redis()
    score = await client.zscore(_sessions_key(user_id), refresh_jti)
    return score is not None


async def _rotate_refresh_session(user_id: str, old_jti: str, new_jti: str) -> None:
    client = await get_redis()
    key = _sessions_key(user_id)
    await client.zrem(key, old_jti)
    await _register_refresh_session(user_id, new_jti)


async def _revoke_refresh_session(user_id: str, refresh_jti: str | None) -> None:
    if not refresh_jti:
        return
    client = await get_redis()
    await client.zrem(_sessions_key(user_id), refresh_jti)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, _, _ = create_access_token(str(user.id), {"email": user.email, "name": user.name})
    refresh_token, refresh_jti, _ = create_refresh_token(str(user.id))
    await _register_refresh_session(str(user.id), refresh_jti)
    await write_audit_log(db, user_id=user.id, action="login", entity_type="user", entity_id=str(user.id))
    await db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = safe_decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user_id = payload.get("sub")
    refresh_jti = payload.get("jti")
    if not user_id or not refresh_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    if not await _refresh_session_valid(str(user_id), str(refresh_jti)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token, _, _ = create_access_token(str(user.id), {"email": user.email, "name": user.name})
    new_refresh, new_jti, _ = create_refresh_token(str(user.id))
    exp = payload.get("exp")
    if refresh_jti and exp:
        ttl = max(int(exp) - int(datetime.now(UTC).timestamp()), 60)
        await blacklist_jwt(str(refresh_jti), ttl)
    await _rotate_refresh_session(str(user.id), str(refresh_jti), new_jti)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user: User = Depends(get_current_user),
):
    # Only revoke this browser's access token — do not kick other demo sessions.
    if credentials:
        payload = safe_decode_token(credentials.credentials)
        if payload and payload.get("jti"):
            exp = payload.get("exp")
            if exp:
                ttl = max(int(exp) - int(datetime.now(UTC).timestamp()), 60)
            else:
                ttl = 15 * 60
            await blacklist_jwt(str(payload["jti"]), ttl)
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role,
        department=user.department,
    )
