"""HTTP request logging and Prometheus timing."""

from __future__ import annotations

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import HTTP_DURATION, HTTP_REQUESTS, HTTP_RESPONSE_BYTES
from app.core.request_context import get_request_id

logger = logging.getLogger("verilumen.http")

SKIP_PATHS = {"/live", "/metrics"}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        response = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            route = request.url.path
            method = request.method
            user_id = getattr(request.state, "user_id", None)

            HTTP_REQUESTS.labels(method=method, route=route, status=str(status_code)).inc()
            HTTP_DURATION.labels(method=method, route=route).observe(duration_ms / 1000.0)
            if response is not None:
                size = response.headers.get("content-length")
                if size and size.isdigit():
                    HTTP_RESPONSE_BYTES.labels(method=method, route=route).observe(int(size))

            logger.info(
                "%s %s %s",
                method,
                route,
                status_code,
                extra={
                    "request_id": get_request_id(),
                    "user_id": user_id,
                    "route": route,
                    "method": method,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
