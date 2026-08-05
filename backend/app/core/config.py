from functools import lru_cache
import os

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    app_version: str = "1.0.0"

    database_url: str = "postgresql+asyncpg://verilumen:verilumen@localhost:5432/verilumen"

    @field_validator("database_url", mode="before")
    @classmethod
    def _ensure_asyncpg(cls, value: object) -> object:
        """Railway/Postgres URLs are often postgresql:// — SQLAlchemy async needs asyncpg."""
        if not isinstance(value, str) or not value:
            return value
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://") :]
        if value.startswith("postgresql://") and not value.startswith("postgresql+asyncpg://"):
            value = "postgresql+asyncpg://" + value[len("postgresql://") :]
        # asyncpg rejects libpq sslmode=; map to ssl=true
        if "sslmode=" in value:
            value = (
                value.replace("sslmode=require", "ssl=true")
                .replace("sslmode=verify-full", "ssl=true")
                .replace("sslmode=verify-ca", "ssl=true")
                .replace("sslmode=prefer", "ssl=true")
                .replace("sslmode=disable", "ssl=false")
            )
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> object:
        """Accept JSON list or comma-separated origins from Railway/Vercel env vars."""
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return ["http://localhost:3000"]
            if raw.startswith("["):
                return value
            return [part.strip() for part in raw.split(",") if part.strip()]
        return value

    # Accept Railway MinIO template names (PRIVATE/PUBLIC) as well as MINIO_ENDPOINT.
    minio_endpoint: str = Field(
        default="localhost:9000",
        validation_alias=AliasChoices(
            "MINIO_ENDPOINT",
            "MINIO_PRIVATE_ENDPOINT",
            "MINIO_PUBLIC_ENDPOINT",
            "minio_endpoint",
        ),
    )
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_use_ssl: bool = False
    # Cloudflare R2 requires region "auto"; leave empty for classic MinIO.
    minio_region: str = ""
    minio_bucket_raw: str = "verilumen-raw-uploads"
    minio_bucket_parsed: str = "verilumen-parsed"
    minio_bucket_wafer: str = "verilumen-wafer-images"
    minio_bucket_exports: str = "verilumen-exports"
    minio_bucket_ai: str = "verilumen-ai-artifacts"

    @field_validator("minio_endpoint", mode="before")
    @classmethod
    def _normalize_minio_endpoint(cls, value: object) -> object:
        if not isinstance(value, str) or not value.strip():
            # Fall back to Railway template env vars if primary is blank.
            for key in ("MINIO_ENDPOINT", "MINIO_PRIVATE_ENDPOINT", "MINIO_PUBLIC_ENDPOINT"):
                alt = os.getenv(key)
                if alt and alt.strip():
                    value = alt.strip()
                    break
            else:
                return value
        endpoint = str(value).strip()
        if endpoint.startswith("https://"):
            endpoint = endpoint[len("https://") :]
        elif endpoint.startswith("http://"):
            endpoint = endpoint[len("http://") :]
        return endpoint.rstrip("/")

    @model_validator(mode="after")
    def _minio_ssl_from_endpoint(self) -> "Settings":
        # If user pasted an https public endpoint into env before normalize, prefer SSL.
        raw = (
            os.getenv("MINIO_ENDPOINT")
            or os.getenv("MINIO_PRIVATE_ENDPOINT")
            or os.getenv("MINIO_PUBLIC_ENDPOINT")
            or ""
        )
        if raw.startswith("https://"):
            object.__setattr__(self, "minio_use_ssl", True)
        return self

    redis_url: str = "redis://localhost:6379/0"
    redis_prefix: str = "verilumen:"

    jwt_secret: str = "change-me-in-production"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 7

    @field_validator("jwt_secret", mode="before")
    @classmethod
    def _jwt_secret_not_blank(cls, value: object) -> object:
        if value is None or (isinstance(value, str) and not value.strip()):
            return "change-me-in-production"
        return value

    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000"]
    pattern_agent_base_url: str = "http://127.0.0.1:8011"
    failure_agent_api_url: str = "http://127.0.0.1:8021"
    failure_agent_dashboard_url: str = "http://127.0.0.1:3020/embed/failure/overview"
    scan_diagnosis_agent_api_url: str = "http://127.0.0.1:8031"
    scan_diagnosis_agent_dashboard_url: str = "http://127.0.0.1:3030/embed/scan"

    # Recommendation analysis agents (embedded into dashboard tabs)
    pattern_recommendation_agent_api_url: str = "http://127.0.0.1:8041"
    pattern_recommendation_agent_dashboard_url: str = "http://127.0.0.1:3041/embed/pattern-rec/"
    scan_debug_recommendation_agent_api_url: str = "http://127.0.0.1:8042"
    scan_debug_recommendation_agent_dashboard_url: str = "http://127.0.0.1:3042/embed/scan-debug-rec/dashboard/recommendation-analysis"
    test_optimization_agent_api_url: str = "http://127.0.0.1:8043"
    test_optimization_agent_dashboard_url: str = "http://127.0.0.1:3043/embed/test-opt/"
    # WaferVision / Spatial AI (image wafer maps — separate from STIL+log pipeline)
    wafer_agent_api_url: str = "http://127.0.0.1:8000"
    wafer_agent_dashboard_url: str = "http://127.0.0.1:3000/dashboard/wafervision"

    verilumen_service_key: str = "dev-service-key-change-me"
    agent_http_timeout_sec: float = 600.0
    agent_http_retries: int = 3
    # Fast platform orchestration: Pattern dataset KPIs + Failure skip Postgres ingest.
    # Set AGENT_FAST_MODE=false to force full Pattern Validate + FA dual-write.
    agent_fast_mode: bool = True
    # Free-tier safe parse: stream download + lighter STIL/log handling (avoids 512MB OOM).
    # Set PARSER_LIGHT_MODE=false for full-fidelity parse on a 2GB+ instance.
    parser_light_mode: bool = True
    parser_engine_path: str = r"C:\personal\parser engine"
    agent_output_root: str = r"C:\personal\agent and parser output"
    upload_input_root: str = r"C:\personal\input all file"
    scan_diagnosis_data_dir: str = r"C:\personal\Scan-diagnosis-Agent-v1.1-main\data"
    max_upload_bytes: int = 10 * 1024**3

    worker_heartbeat_max_age_sec: int = 120
    enable_hsts: bool = False
    json_logs: bool = True
    log_level: str = "INFO"

    backup_dir: str = "backups"
    backup_retention_daily: int = 7
    backup_retention_weekly: int = 4
    cost_tester_usd_per_hour: float | None = None
    cost_alert_threshold_pct: float = 12.0
    cost_cache_ttl_sec: int = 300


@lru_cache
def get_settings() -> Settings:
    return Settings()
