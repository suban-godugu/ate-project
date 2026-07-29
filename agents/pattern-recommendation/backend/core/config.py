"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Runtime settings with environment-variable overrides."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="BACKEND_",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "Pattern Recommendation Backend"
    description: str = "Backend API for pattern-analysis agents and dashboard services."
    version: str = "1.0.0"
    status: str = "operational"
    api_prefix: str = ""

    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"

    project_root: Path = _PROJECT_ROOT
    backend_dir: Path = _BACKEND_DIR
    # Prefer shared company folders when present; env overrides win.
    data_dir: Path = Path(
        os.environ.get(
            "BACKEND_DATA_DIR",
            os.path.join(
                os.environ.get("UPLOAD_INPUT_ROOT", r"C:\personal\input all file"),
                "pattern-recommendation",
            ),
        )
    )
    output_dir: Path = Path(
        os.environ.get(
            "BACKEND_OUTPUT_DIR",
            os.path.join(
                os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output"),
                "pattern-recommendation",
            ),
        )
    )

    # Comma-separated glob patterns — override via BACKEND_DATA_DATASET_PATTERNS
    data_dataset_patterns: str = (
        "PA-Analysis-Session_*.json,"
        "PA-FR-*.json,"
        "PA-FR-*.csv"
    )
    # Comma-separated glob patterns — override via BACKEND_OUTPUT_DATASET_PATTERNS
    output_dataset_patterns: str = "failure_summary.json,*_summary.json"

    # Comma-separated prefix=type rules for classifying discovered files
    dataset_type_rules: str = (
        "PA-Analysis-Session_=analysis_session,"
        "PA-FR-=failure_report,"
        "failure_summary=generated_output"
    )

    # role=substring,... used by DataLoader to resolve datasets from the registry
    dataset_role_markers: str = (
        "executions=execution,"
        "clustering=clustering,"
        "embeddings=embedding,"
        "failure_summary=failure_summary,"
        "metadata=metadata_metrics,"
        "cpm=cpm_report,"
        "cvm=cvm_cycles"
    )

    # Files at/above this size use streaming unless role is always-full
    full_load_max_bytes: int = Field(default=100_000_000, ge=1)

    # Roles that must never be fully loaded into memory
    always_stream_roles: str = "executions"

    # Roles allowed to fully load even when large (never includes executions)
    always_full_roles: str = (
        "clustering,embeddings,failure_summary,metadata,cpm"
    )

    # Removal recommendation weights (must be configuration-driven)
    removal_redundancy_weight: float = Field(default=0.5, ge=0.0)
    removal_unique_contribution_weight: float = Field(default=0.3, ge=0.0)
    removal_toggle_weight: float = Field(default=0.2, ge=0.0)

    # Relative reason thresholds on candidate-normalized [0, 1] scores
    removal_low_unique_normalized_max: float = Field(default=0.5, ge=0.0, le=1.0)
    removal_low_toggle_normalized_max: float = Field(default=0.5, ge=0.0, le=1.0)

    # Ordering recommendation weights
    ordering_fail_rate_weight: float = Field(default=0.50, ge=0.0)
    ordering_severity_weight: float = Field(default=0.30, ge=0.0)
    ordering_toggle_weight: float = Field(default=0.20, ge=0.0)

    # Relative thresholds for ordering reason codes (normalized [0, 1])
    ordering_high_fail_rate_min: float = Field(default=0.70, ge=0.0, le=1.0)
    ordering_medium_fail_rate_min: float = Field(default=0.30, ge=0.0, le=1.0)
    ordering_high_toggle_min: float = Field(default=0.70, ge=0.0, le=1.0)
    ordering_high_priority_score_min: float = Field(default=0.70, ge=0.0, le=1.0)

    # Gap analysis percentiles (dataset-relative; never hardcoded in algorithms)
    gap_percentile: float = Field(default=10.0, ge=0.0, le=100.0)
    gap_high_failure_percentile: float = Field(default=10.0, ge=0.0, le=100.0)
    gap_lot_high_failure_percentile: float = Field(default=10.0, ge=0.0, le=100.0)
    gap_lot_low_diversity_percentile: float = Field(default=10.0, ge=0.0, le=100.0)

    # Toggle-activity proxy settings (not real power measurements)
    low_power_percentile: float = Field(default=10.0, ge=0.0, le=100.0)
    coverage_retention_ratio: float = Field(default=0.95, ge=0.0, le=1.0)

    # Coverage improvement proxy settings (not ATPG fault coverage)
    coverage_gap_percentile: float = Field(default=10.0, ge=0.0, le=100.0)
    coverage_late_rank_percentile: float = Field(default=70.0, ge=0.0, le=100.0)
    coverage_high_severities: str = "HIGH,MEDIUM"

    # Supervised ML scoring (removal classifier + ordering ranker)
    ml_enabled: bool = False
    ml_shadow_mode: bool = True
    ml_removal_blend: float = Field(default=0.7, ge=0.0, le=1.0)
    ml_ordering_blend: float = Field(default=0.7, ge=0.0, le=1.0)
    ml_artifacts_dir: Path = _PROJECT_ROOT / "ml" / "artifacts"
    ml_feedback_path: Path = _PROJECT_ROOT / "ml" / "data" / "operator_feedback.jsonl"

    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    @field_validator(
        "data_dir",
        "output_dir",
        "project_root",
        "backend_dir",
        "ml_artifacts_dir",
        "ml_feedback_path",
        mode="before",
    )
    @classmethod
    def _coerce_path(cls, value: object) -> Path:
        return Path(value) if not isinstance(value, Path) else value

    def parsed_data_patterns(self) -> list[str]:
        return _split_csv(self.data_dataset_patterns)

    def parsed_output_patterns(self) -> list[str]:
        return _split_csv(self.output_dataset_patterns)

    def parsed_type_rules(self) -> list[tuple[str, str]]:
        rules: list[tuple[str, str]] = []
        for item in _split_csv(self.dataset_type_rules):
            if "=" not in item:
                continue
            prefix, dataset_type = item.split("=", 1)
            prefix = prefix.strip()
            dataset_type = dataset_type.strip()
            if prefix and dataset_type:
                rules.append((prefix, dataset_type))
        return rules

    def parsed_role_markers(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for item in _split_csv(self.dataset_role_markers):
            if "=" not in item:
                continue
            role, marker = item.split("=", 1)
            role = role.strip()
            marker = marker.strip().lower()
            if role and marker:
                mapping[role] = marker
        return mapping

    def parsed_always_stream_roles(self) -> set[str]:
        return set(_split_csv(self.always_stream_roles))

    def parsed_always_full_roles(self) -> set[str]:
        return set(_split_csv(self.always_full_roles))


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return one validated settings instance per process."""
    return Settings()
