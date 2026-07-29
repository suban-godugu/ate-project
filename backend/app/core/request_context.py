"""Request-scoped context for structured logging and audit correlation."""

from __future__ import annotations

import contextvars
from typing import Any

request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
user_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)
route_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("route", default=None)
upload_job_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("upload_job", default=None)
lot_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("lot", default=None)
wafer_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("wafer", default=None)
worker_name_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("worker_name", default=None)


def get_request_id() -> str | None:
    return request_id_ctx.get()


def bind_log_context(**fields: Any) -> None:
    if "request_id" in fields:
        request_id_ctx.set(fields["request_id"])
    if "user_id" in fields:
        user_id_ctx.set(str(fields["user_id"]) if fields["user_id"] else None)
    if "route" in fields:
        route_ctx.set(fields["route"])
    if "upload_job" in fields:
        upload_job_ctx.set(fields["upload_job"])
    if "lot" in fields:
        lot_ctx.set(fields["lot"])
    if "wafer" in fields:
        wafer_ctx.set(fields["wafer"])
    if "worker_name" in fields:
        worker_name_ctx.set(fields["worker_name"])
