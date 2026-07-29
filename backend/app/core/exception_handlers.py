"""Consistent JSON error responses with request correlation."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.request_context import get_request_id

logger = logging.getLogger("verilumen.errors")


def _error_body(request: Request, *, error: str, detail: str | None = None, status_code: int = 500) -> JSONResponse:
    request_id = get_request_id() or getattr(request.state, "request_id", None)
    payload = {
        "error": error,
        "detail": detail,
        "request_id": request_id,
        "path": str(request.url.path),
    }
    return JSONResponse(status_code=status_code, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _error_body(request, error="http_error", detail=str(exc.detail), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return _error_body(request, error="validation_error", detail=str(exc.errors()), status_code=422)

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error", extra={"request_id": get_request_id()})
        return _error_body(request, error="database_error", detail="Database operation failed", status_code=503)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", extra={"request_id": get_request_id()})
        return _error_body(request, error="internal_error", detail="An unexpected error occurred", status_code=500)
