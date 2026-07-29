"""Environment configuration."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
# Shared company folders:
#   inputs  → UPLOAD_INPUT_ROOT\test-optimization  (OptimizationContext JSON)
#   outputs → AGENT_OUTPUT_ROOT\test-optimization  (persisted recommendations)
_DEFAULT_INPUT = Path(
    os.environ.get(
        "INPUT_DIR",
        os.path.join(
            os.environ.get("UPLOAD_INPUT_ROOT", r"C:\personal\input all file"),
            "test-optimization",
        ),
    )
)
_DEFAULT_OUTPUT = Path(
    os.environ.get(
        "DATA_DIR",
        os.path.join(
            os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output"),
            "test-optimization",
        ),
    )
)
DATA_DIR = _DEFAULT_OUTPUT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "ATE Test Optimization Recommendation Agent"
    app_version: str = "3.0.0"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:3043",
        alias="CORS_ORIGINS",
    )

    # OpenAI-compatible LLM
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=3500, alias="LLM_MAX_TOKENS")
    llm_timeout_s: float = Field(default=90.0, alias="LLM_TIMEOUT_S")
    force_heuristic: bool = Field(default=False, alias="FORCE_HEURISTIC")

    # Persistence / I/O
    data_dir: Path = Field(default=_DEFAULT_OUTPUT, alias="DATA_DIR")
    input_dir: Path = Field(default=_DEFAULT_INPUT, alias="INPUT_DIR")

    # Optional upstream agent URLs (future integration)
    pattern_agent_url: str = Field(default="", alias="PATTERN_AGENT_URL")
    scan_debug_agent_url: str = Field(default="", alias="SCAN_DEBUG_AGENT_URL")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key.strip()) and not self.force_heuristic

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.input_dir.mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "recommendations").mkdir(parents=True, exist_ok=True)
    (settings.data_dir / "uploads").mkdir(parents=True, exist_ok=True)
    return settings
