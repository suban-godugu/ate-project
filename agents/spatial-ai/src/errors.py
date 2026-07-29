"""
Structured API error helpers for WaferVision-AI.

Produces production error payloads while retaining FastAPI ``detail`` for
backward compatibility with existing clients.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_payload(message: str, code: int) -> dict[str, Any]:
    """
    Build a structured error body.

    Args:
        message: Human-readable error message.
        code: HTTP status code.

    Returns:
        Dict with ``status``, ``message``, ``code``, and ``detail`` (compat).
    """
    return {
        "status": "error",
        "message": message,
        "code": int(code),
        "detail": message,
    }


def http_error(status_code: int, message: str) -> HTTPException:
    """Raise an HTTPException whose detail serializes to a string message."""
    return HTTPException(status_code=status_code, detail=message)


async def http_exception_handler(
    _request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Convert HTTPException into the production error JSON shape."""
    detail = exc.detail
    if isinstance(detail, dict) and "message" in detail:
        message = str(detail["message"])
    else:
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(message, exc.status_code),
    )


async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Convert request validation errors into production error JSON."""
    errors = exc.errors()
    first = errors[0] if errors else {"msg": "Validation error"}
    location = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    message = first.get("msg", "Validation error")
    if location:
        message = f"{location}: {message}"
    return JSONResponse(
        status_code=422,
        content=error_payload(message, 422),
    )


async def unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all handler — never leak stack traces to clients."""
    return JSONResponse(
        status_code=500,
        content=error_payload("Internal server error.", 500),
    )


__all__ = [
    "error_payload",
    "http_error",
    "http_exception_handler",
    "validation_exception_handler",
    "unhandled_exception_handler",
]
