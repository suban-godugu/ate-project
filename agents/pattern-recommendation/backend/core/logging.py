"""Centralized logging configuration."""

import logging
from logging.config import dictConfig

from backend.core.config import Settings
from backend.core.constants import APP_LOGGER_NAME


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure console logging and return the application logger."""
    level = settings.log_level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": (
                        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    )
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": level,
                }
            },
            "loggers": {
                APP_LOGGER_NAME: {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                "uvicorn.error": {"level": level},
                "uvicorn.access": {"level": level},
            },
        }
    )
    return logging.getLogger(APP_LOGGER_NAME)


def get_logger() -> logging.Logger:
    """Return the configured application logger."""
    return logging.getLogger(APP_LOGGER_NAME)
