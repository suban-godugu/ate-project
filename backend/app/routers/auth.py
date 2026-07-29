from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import blacklist_jwt, cache_get, cache_set
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

SESSION_TTL = 24 * 3600  # spec: 24h refresh metadata cache


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token, _, _ = create_access_token(str(user.id), {"email": user.email, "name": user.name})
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(str(user.id))
    await cache_set(
        f"session:{user.id}",
        {"refresh_jti": refresh_jti, "exp": refresh_exp.isoformat()},
        ttl=SESSION_TTL,
    )
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
    session = await cache_get(f"session:{user_id}")
    if not session or session.get("revoked") or session.get("refresh_jti") != refresh_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    access_token, _, _ = create_access_token(str(user.id), {"email": user.email, "name": user.name})
    new_refresh, new_jti, refresh_exp = create_refresh_token(str(user.id))
    exp = payload.get("exp")
    if refresh_jti and exp:
        ttl = max(int(exp) - int(datetime.now(UTC).timestamp()), 60)
        await blacklist_jwt(str(refresh_jti), ttl)
    await cache_set(
        f"session:{user.id}",
        {"refresh_jti": new_jti, "exp": refresh_exp.isoformat()},
        ttl=SESSION_TTL,
    )
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    user: User = Depends(get_current_user),
):
    await cache_set(f"session:{user.id}", {"revoked": True}, ttl=SESSION_TTL)
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
