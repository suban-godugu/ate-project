"""Application settings loaded from environment / .env via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent


class DatabaseConfigurationError(Exception):
    """Raised when database settings are missing, invalid, or use a forbidden dialect."""


class Settings(BaseSettings):
    """Central configuration for the Failure Analysis Agent backend."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # PostgreSQL
    database_host: str = Field(default="localhost", alias="DATABASE_HOST")
    database_port: int = Field(default=5432, alias="DATABASE_PORT")
    database_name: str = Field(default="failure_analysis_db", alias="DATABASE_NAME")
    database_user: str = Field(default="postgres", alias="DATABASE_USER")
    database_password: str = Field(default="", alias="DATABASE_PASSWORD")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Connection pool
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")

    # App / infra
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    celery_enabled: bool = Field(default=False, alias="CELERY_ENABLED")
    upload_dir: Path = Field(default=BACKEND_DIR / "storage" / "raw", alias="UPLOAD_DIR")
    processed_dir: Path = Field(
        default=BACKEND_DIR / "storage" / "processed", alias="PROCESSED_DIR"
    )
    adapter_config_dir: Path = Field(
        default=ROOT_DIR / "config" / "adapters", alias="ADAPTER_CONFIG_DIR"
    )
    max_upload_bytes: int = Field(
        default=5 * 1024 * 1024 * 1024, alias="MAX_UPLOAD_BYTES"
    )
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    # Dataset discovery (optional). Prefer DATASET_ROOT over hardcoding paths.
    dataset_root: str | None = Field(default=None, alias="DATASET_ROOT")
    evaluation_data_roots: str | None = Field(default=None, alias="EVALUATION_DATA_ROOTS")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    # Auth / JWT
    jwt_secret: str = Field(
        default="dev-only-change-me-jwt-secret-32b!", alias="JWT_SECRET"
    )
    jwt_access_minutes: int = Field(default=30, alias="JWT_ACCESS_MINUTES")
    jwt_refresh_days: int = Field(default=7, alias="JWT_REFRESH_DAYS")
    auth_required: bool = Field(default=False, alias="AUTH_REQUIRED")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ORIGINS",
    )
    bootstrap_admin_email: str = Field(
        default="admin@verilumen.local", alias="BOOTSTRAP_ADMIN_EMAIL"
    )
    bootstrap_admin_password: str = Field(
        default="ChangeMe123!", alias="BOOTSTRAP_ADMIN_PASSWORD"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _reject_sqlite_url(cls, value: object) -> object:
        if value is None or value == "":
            return None
        text = str(value).strip()
        if "sqlite" in text.lower():
            raise ValueError(
                "SQLite is not supported. Configure PostgreSQL via DATABASE_URL "
                "(postgresql+asyncpg://...) or DATABASE_HOST / DATABASE_PORT / "
                "DATABASE_NAME / DATABASE_USER / DATABASE_PASSWORD."
            )
        if not text.startswith("postgresql+asyncpg://") and not text.startswith(
            "postgres+asyncpg://"
        ):
            if text.startswith("postgresql://") or text.startswith("postgres://"):
                # Normalize sync-style URLs to asyncpg
                return text.replace("postgresql://", "postgresql+asyncpg://", 1).replace(
                    "postgres://", "postgresql+asyncpg://", 1
                )
            raise ValueError(
                "DATABASE_URL must use the asyncpg driver "
                "(postgresql+asyncpg://user:pass@host:port/dbname)."
            )
        return text

    @model_validator(mode="after")
    def _require_password_when_building_url(self) -> Settings:
        if not self.database_url and not self.database_password:
            raise ValueError(
                "DATABASE_PASSWORD is required when DATABASE_URL is not set. "
                "Update the .env file with your PostgreSQL password."
            )
        return self

    def assert_credentials_ready(self) -> None:
        """Fail fast when .env still contains a password placeholder."""
        if self.database_url:
            return
        if self.database_password in {"CHANGE_ME", "<prompt user to update>", "changeme", ""}:
            raise DatabaseConfigurationError(
                "DATABASE_PASSWORD is missing or still uses a placeholder. "
                "Edit .env and set DATABASE_PASSWORD to your PostgreSQL password "
                "for user 'postgres' on database 'failure_analysis_db'."
            )

    def resolved_database_url(self) -> str:
        """Return the async SQLAlchemy URL for PostgreSQL."""
        if self.database_url:
            return self.database_url
        user = quote_plus(self.database_user)
        password = quote_plus(self.database_password)
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{self.database_host}:{self.database_port}/{self.database_name}"
        )

    def safe_database_url(self) -> str:
        """URL with password redacted for logging."""
        url = self.resolved_database_url()
        if "@" not in url:
            return url
        scheme, rest = url.split("://", 1)
        if "@" not in rest:
            return url
        _, hostpart = rest.rsplit("@", 1)
        return f"{scheme}://***@{hostpart}"


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:  # noqa: BLE001 — surface as DatabaseConfigurationError
        raise DatabaseConfigurationError(str(exc)) from None
