"""Application exceptions and global FastAPI exception handlers."""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.logging import get_logger
from backend.schemas.responses import ErrorResponse


class AppException(Exception):
    """Expected application error with a public response payload."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def _error_response(
    status_code: int,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(message=message, details=details or {})
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register consistent handlers for expected and unexpected errors."""

    @app.exception_handler(AppException)
    async def handle_app_exception(
        request: Request, exc: AppException
    ) -> JSONResponse:
        get_logger().warning(
            "Application error method=%s path=%s status=%d message=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.message,
        )
        return _error_response(exc.status_code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        get_logger().warning(
            "Validation error method=%s path=%s",
            request.method,
            request.url.path,
        )
        return _error_response(
            422,
            "Request validation failed",
            {"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        get_logger().warning(
            "HTTP error method=%s path=%s status=%d",
            request.method,
            request.url.path,
            exc.status_code,
        )
        return _error_response(
            exc.status_code,
            str(exc.detail),
            {},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        get_logger().exception(
            "Unhandled exception method=%s path=%s",
            request.method,
            request.url.path,
        )
        return _error_response(
            500,
            "Internal server error",
            {},
        )
