from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, extra: dict[str, Any] | None = None) -> tuple[str, str, datetime]:
    jti = str(uuid4())
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_ttl_min)
    payload = {"sub": subject, "exp": expire, "type": "access", "jti": jti}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM), jti, expire


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    jti = str(uuid4())
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days)
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": jti}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM), jti, expire


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def safe_decode_token(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None
