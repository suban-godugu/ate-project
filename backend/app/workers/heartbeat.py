"""Worker heartbeat for readiness probes."""

from __future__ import annotations

import asyncio
import socket
from datetime import UTC, datetime

from app.cache.redis_client import cache_set


async def record_worker_heartbeat(worker_id: str | None = None) -> None:
    wid = worker_id or socket.gethostname()
    await cache_set(
        "worker:heartbeat",
        {"timestamp": datetime.now(UTC).isoformat(), "worker_id": wid},
        ttl=300,
    )


async def worker_heartbeat_loop(interval_sec: int = 30) -> None:
    while True:
        try:
            await record_worker_heartbeat()
        except Exception:
            pass
        await asyncio.sleep(interval_sec)
