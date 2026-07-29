"""Structured JSON logging with optional human-readable console output."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.core.request_context import (
    get_request_id,
    lot_ctx,
    route_ctx,
    upload_job_ctx,
    user_id_ctx,
    wafer_ctx,
    worker_name_ctx,
)


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
            "user_id": getattr(record, "user_id", None) or user_id_ctx.get(),
            "route": getattr(record, "route", None) or route_ctx.get(),
            "method": getattr(record, "method", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "worker_name": getattr(record, "worker_name", None) or worker_name_ctx.get(),
            "upload_job": getattr(record, "upload_job", None) or upload_job_ctx.get(),
            "lot": getattr(record, "lot", None) or lot_ctx.get(),
            "wafer": getattr(record, "wafer", None) or wafer_ctx.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "structured_extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str)


class ConsoleFormatter(logging.Formatter):
    """Readable single-line logs for local development."""

    def format(self, record: logging.LogRecord) -> str:
        rid = getattr(record, "request_id", None) or get_request_id()
        prefix = f"[{rid}] " if rid else ""
        base = super().format(record)
        return f"{prefix}{base}"


def configure_logging(*, json_logs: bool = True, level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            ConsoleFormatter("%(asctime)s %(levelname)s %(name)s — %(message)s", datefmt="%H:%M:%S")
        )
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
