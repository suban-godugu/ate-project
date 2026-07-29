"""RBAC extension point and bounded throttling for FA-FR-007."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

ALLOWED_ROLES = {
    "admin",
    "failure_engineer",
    "yield_engineer",
    "quality_engineer",
    "service",
}
_requests: dict[str, deque[float]] = defaultdict(deque)


async def die_access_context(
    x_user_id: str | None = Header(default=None, max_length=128),
    x_role: str | None = Header(default=None, max_length=64),
) -> dict[str, str]:
    role = (x_role or "service").strip().lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "DIE_ANALYSIS_ACCESS_DENIED",
                "message": "Role is not permitted",
            },
        )
    return {"actor": (x_user_id or "system")[:128], "role": role}


async def die_analysis_rate_limit(request: Request) -> None:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    client = forwarded or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    window = _requests[client]
    while window and now - window[0] > 60.0:
        window.popleft()
    if len(window) >= 30:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DIE_ANALYSIS_RATE_LIMITED",
                "message": "Retry after one minute",
            },
        )
    window.append(now)
