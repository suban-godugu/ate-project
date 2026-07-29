"""Startup validation for required configuration."""

from __future__ import annotations

import logging

from app.core.config import Settings

logger = logging.getLogger("verilumen.config")

INSECURE_JWT = "change-me-in-production"
INSECURE_MINIO_SECRET = "minioadmin123"


def validate_settings(settings: Settings) -> None:
    errors: list[str] = []
    warnings: list[str] = []

    if not settings.database_url:
        errors.append("DATABASE_URL is required")
    if not settings.redis_url:
        errors.append("REDIS_URL is required")
    if not settings.minio_access_key or not settings.minio_secret_key:
        errors.append("MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required")
    if not settings.jwt_secret:
        errors.append("JWT_SECRET is required")

    if settings.environment == "production":
        if settings.jwt_secret == INSECURE_JWT:
            errors.append("JWT_SECRET must be changed in production")
        if settings.minio_secret_key == INSECURE_MINIO_SECRET:
            errors.append("MINIO_SECRET_KEY must be changed in production")
        if "changeme" in settings.database_url.lower():
            errors.append("DATABASE_URL appears to use a default password in production")
    else:
        if settings.jwt_secret == INSECURE_JWT:
            warnings.append("Using default JWT_SECRET — set JWT_SECRET before production")
        if settings.minio_secret_key == INSECURE_MINIO_SECRET:
            warnings.append("Using default MinIO credentials — rotate before production")

    for msg in warnings:
        logger.warning(msg)

    if errors:
        joined = "; ".join(errors)
        raise RuntimeError(f"Configuration validation failed: {joined}")
