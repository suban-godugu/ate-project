from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.cache.redis_client import increment_rate_limit

PROBE_PATHS = {
    "/health",
    "/ready",
    "/live",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PROBE_PATHS:
            return await call_next(request)
        ip = request.client.host if request.client else "unknown"
        route = request.url.path
        if not await increment_rate_limit(ip, route):
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        return await call_next(request)
