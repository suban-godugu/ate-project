"""Configuration validation tests."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.core.startup_validation import validate_settings


def test_development_allows_default_jwt():
    settings = Settings(environment="development", jwt_secret="change-me-in-production")
    validate_settings(settings)


def test_production_rejects_default_jwt():
    settings = Settings(environment="production", jwt_secret="change-me-in-production")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_settings(settings)


def test_production_rejects_default_minio_secret():
    settings = Settings(
        environment="production",
        jwt_secret="secure-production-secret-value",
        minio_secret_key="minioadmin123",
    )
    with pytest.raises(RuntimeError, match="MINIO"):
        validate_settings(settings)
