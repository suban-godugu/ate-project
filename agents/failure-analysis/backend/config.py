"""Backend configuration — compatibility facade over Pydantic Settings."""

from __future__ import annotations

from pathlib import Path

from backend.settings import ROOT_DIR, BACKEND_DIR, DatabaseConfigurationError, get_settings

_settings = get_settings()

DATABASE_URL: str = _settings.resolved_database_url()
DATABASE_HOST: str = _settings.database_host
DATABASE_PORT: int = _settings.database_port
DATABASE_NAME: str = _settings.database_name
DATABASE_USER: str = _settings.database_user

REDIS_URL: str = _settings.redis_url
CELERY_ENABLED: bool = _settings.celery_enabled

UPLOAD_DIR: Path = Path(_settings.upload_dir)
PROCESSED_DIR: Path = Path(_settings.processed_dir)
ADAPTER_CONFIG_DIR: Path = Path(_settings.adapter_config_dir)

MAX_UPLOAD_BYTES: int = _settings.max_upload_bytes
ALLOWED_EXTENSIONS = {
    ".stil",
    ".stdf",
    ".std",
    ".log",
    ".txt",
    ".dat",
    ".csv",
    ".xml",
    ".json",
}

API_PREFIX: str = _settings.api_prefix

__all__ = [
    "ROOT_DIR",
    "BACKEND_DIR",
    "DATABASE_URL",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "REDIS_URL",
    "CELERY_ENABLED",
    "UPLOAD_DIR",
    "PROCESSED_DIR",
    "ADAPTER_CONFIG_DIR",
    "MAX_UPLOAD_BYTES",
    "ALLOWED_EXTENSIONS",
    "API_PREFIX",
    "DatabaseConfigurationError",
    "get_settings",
]
