"""HTTP request logging middleware."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.constants import REQUEST_ID_HEADER
from backend.core.logging import get_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request completion with status, latency, and correlation ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            get_logger().exception(
                "Request failed method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            raise

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        get_logger().info(
            "Request complete method=%s path=%s status=%d duration_ms=%.2f "
            "request_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )
        return response
