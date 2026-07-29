"""
Centralized logging configuration for WaferVision-AI.

Provides console + rotating file handlers for application, error, and batch
logs. Never log base64 images or large JSON payloads from callers.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from .config import LOG_BACKUP_COUNT, LOG_LEVEL, LOG_MAX_BYTES, LOGS_DIR

_CONFIGURED = False

APPLICATION_LOGGER = "wafervision"
BATCH_LOGGER = "wafervision.batch"
ERROR_LOGGER = "wafervision.error"


def _ensure_logs_dir() -> Path:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR


def _make_rotating_handler(path: Path, level: int) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    return handler


def configure_logging(level: Optional[str] = None) -> None:
    """
    Configure root / application loggers once.

    Args:
        level: Optional override for log level (default from config).

    Example:
        >>> configure_logging("INFO")
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    logs_dir = _ensure_logs_dir()
    resolved = getattr(logging, (level or LOG_LEVEL).upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(resolved)

    # Avoid duplicate handlers across reload
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setLevel(resolved)
    console.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    root.addHandler(console)

    app_handler = _make_rotating_handler(logs_dir / "application.log", resolved)
    root.addHandler(app_handler)

    error_handler = _make_rotating_handler(logs_dir / "error.log", logging.ERROR)
    root.addHandler(error_handler)

    batch_logger = logging.getLogger(BATCH_LOGGER)
    batch_logger.setLevel(resolved)
    batch_logger.propagate = True
    batch_file = _make_rotating_handler(logs_dir / "batch.log", resolved)
    batch_logger.addHandler(batch_file)

    _CONFIGURED = True
    logging.getLogger(APPLICATION_LOGGER).info(
        "Logging configured (level=%s, dir=%s)", logging.getLevelName(resolved), logs_dir
    )


def get_batch_logger() -> logging.Logger:
    """Return the dedicated batch-analysis logger."""
    return logging.getLogger(BATCH_LOGGER)


def get_app_logger(name: str = APPLICATION_LOGGER) -> logging.Logger:
    """Return an application logger."""
    return logging.getLogger(name)


__all__ = [
    "configure_logging",
    "get_batch_logger",
    "get_app_logger",
    "APPLICATION_LOGGER",
    "BATCH_LOGGER",
    "ERROR_LOGGER",
]
