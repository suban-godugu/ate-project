"""RBAC integration hook and bounded request throttling for FA-FR-005."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

ALLOWED_ROLES = {"admin", "failure_engineer", "yield_engineer", "service"}
_ANALYSIS_LIMIT = 30
_WINDOW_SECONDS = 60.0
_requests: dict[str, deque[float]] = defaultdict(deque)


async def recurrence_access_context(
    x_user_id: str | None = Header(default=None, max_length=128),
    x_role: str | None = Header(default=None, max_length=64),
) -> dict[str, str]:
    """Accept trusted gateway identity headers and expose an RBAC extension point."""
    role = (x_role or "service").strip().lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail={"code": "RECURRENCE_ACCESS_DENIED", "message": "Role is not permitted"},
        )
    return {"actor": (x_user_id or "system")[:128], "role": role}


async def recurrence_analysis_rate_limit(request: Request) -> None:
    """Limit expensive analysis requests; use a shared gateway limiter in multi-node deployments."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    client = forwarded or (request.client.host if request.client else "unknown")
    now = time.monotonic()
    window = _requests[client]
    while window and now - window[0] > _WINDOW_SECONDS:
        window.popleft()
    if len(window) >= _ANALYSIS_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RECURRENCE_RATE_LIMITED",
                "message": "Too many recurrence analyses; retry after one minute",
            },
        )
    window.append(now)
