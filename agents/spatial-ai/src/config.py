"""
Centralized configuration for WaferVision-AI.

Owns environment-driven settings such as paths, ports, model location,
timeouts, and CORS origins. No business logic belongs here.

Loads optional ``.env`` from the project root when python-dotenv is available.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # pragma: no cover - optional at import time
    pass

# Repository root (parent of src/)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Semantic version (also exposed via GET /version)
APP_NAME: str = "WaferVision-AI"
APP_VERSION: str = os.getenv("WAFERVISION_VERSION", "1.0.0")
APP_ENV: str = os.getenv("WAFERVISION_ENV", "development")  # development|testing|production

# Dataset root — use the existing local dataset only
DATASET_ROOT: Path = PROJECT_ROOT / "wafer dataset" / "data"
TRAIN_DIR: Path = DATASET_ROOT / "train"
VALID_DIR: Path = DATASET_ROOT / "valid"
TEST_DIR: Path = DATASET_ROOT / "test"

# Model artifacts / versioning metadata (load path only — does not alter weights).
# Single source of truth for the default inference checkpoint. Override with
# WAFERVISION_MODEL_PATH (CLI/env) without changing prediction logic.
MODELS_DIR: Path = PROJECT_ROOT / "models"
MODEL_PATH: Path = Path(
    os.getenv(
        "WAFERVISION_MODEL_PATH",
        str(MODELS_DIR / "resnet50_layer4_ft.pth"),
    )
)
MODEL_VERSION: str = os.getenv("WAFERVISION_MODEL_VERSION", "1.1.0")

# Runtime directories — shared personal I/O roots (same as VERILUMEN parser/agents)
INPUT_ROOT: Path = Path(
    os.getenv("WAFERVISION_INPUT_ROOT", r"C:\personal\input all file")
)
OUTPUT_ROOT: Path = Path(
    os.getenv("WAFERVISION_OUTPUT_ROOT", r"C:\personal\agent and parser output")
)
LOGS_DIR: Path = Path(
    os.getenv("WAFERVISION_LOGS_DIR", str(OUTPUT_ROOT / "wafer" / "logs"))
)
TEMP_DIR: Path = Path(
    os.getenv("WAFERVISION_TEMP_DIR", str(INPUT_ROOT / "wafer_uploads"))
)
VISUALIZATIONS_DIR: Path = Path(
    os.getenv(
        "WAFERVISION_VISUALIZATIONS_DIR",
        str(OUTPUT_ROOT / "wafer" / "visualizations"),
    )
)
EVALUATION_DIR: Path = PROJECT_ROOT / "evaluation"

# ---------------------------------------------------------------------------
# API / server configuration (env-overridable)
# ---------------------------------------------------------------------------
API_HOST: str = os.getenv("WAFERVISION_API_HOST", "127.0.0.1")
API_PORT: int = int(os.getenv("WAFERVISION_API_PORT", "8000"))
API_TITLE: str = "WaferVision-AI API"
API_VERSION: str = APP_VERSION
API_WORKERS: int = int(os.getenv("WAFERVISION_API_WORKERS", "1"))
API_REQUEST_TIMEOUT_SECONDS: float = float(
    os.getenv("WAFERVISION_REQUEST_TIMEOUT_SECONDS", "300")
)
API_KEEPALIVE_SECONDS: int = int(os.getenv("WAFERVISION_KEEPALIVE_SECONDS", "75"))

# Maximum upload size in bytes (default 20 MB)
API_MAX_UPLOAD_BYTES: int = int(
    os.getenv("WAFERVISION_MAX_UPLOAD_BYTES", str(20 * 1024 * 1024))
)

# Batch upload limits
API_MAX_BATCH_FILES: int = int(os.getenv("WAFERVISION_MAX_BATCH_FILES", "100"))

# Comma-separated CORS origins
_DEFAULT_ORIGINS = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173,"
    "http://localhost:8000,"
    "http://127.0.0.1:8000"
)
API_ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("WAFERVISION_ALLOWED_ORIGINS", _DEFAULT_ORIGINS).split(",")
    if origin.strip()
]

API_ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ext.strip().lower()
        for ext in os.getenv(
            "WAFERVISION_ALLOWED_EXTENSIONS", ".jpg,.jpeg,.png,.bmp"
        ).split(",")
        if ext.strip()
    }
)

# Logging
LOG_LEVEL: str = os.getenv("WAFERVISION_LOG_LEVEL", "INFO")
LOG_MAX_BYTES: int = int(os.getenv("WAFERVISION_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
LOG_BACKUP_COUNT: int = int(os.getenv("WAFERVISION_LOG_BACKUP_COUNT", "5"))

# Frontend (Docker / docs)
FRONTEND_PORT: int = int(os.getenv("WAFERVISION_FRONTEND_PORT", "3000"))
FRONTEND_API_BASE_URL: str = os.getenv(
    "NEXT_PUBLIC_API_BASE_URL", f"http://{API_HOST}:{API_PORT}"
)
