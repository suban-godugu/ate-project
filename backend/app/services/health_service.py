"""Health, readiness, and liveness probes."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from sqlalchemy import func, select, text

from app.cache.redis_client import cache_get, get_redis
from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.models.analytics import Alert
from app.models.recommendations import Recommendation
from app.storage.minio_client import get_minio_client

settings = get_settings()
_started_at = time.monotonic()


def uptime_seconds() -> float:
    return time.monotonic() - _started_at


def _check_dashboard_integration(
    *,
    name: str,
    dashboard_url: str,
    docs_url: str,
    api_url: str | None = None,
    health_url: str | None = None,
    embed_path: str | None = None,
) -> dict[str, Any]:
    # Keep configured URL as-is; Vite bases require trailing slash.
    base_url = dashboard_url.rstrip("/")
    root_candidates = [dashboard_url]
    if base_url not in root_candidates:
        root_candidates.append(base_url)
    if f"{base_url}/" not in root_candidates:
        root_candidates.append(f"{base_url}/")
    started = time.monotonic()

    def fetch(url: str) -> tuple[int | None, str | None]:
        req = Request(url, headers={"User-Agent": "verilumen-backend/1.0"})
        with urlopen(req, timeout=3) as response:  # noqa: S310 - local configured integration endpoint
            status = getattr(response, "status", None)
            content_type = response.headers.get("Content-Type")
            return status, content_type

    try:
        root_status: int | None = None
        root_content_type: str | None = None
        last_root_error: Exception | None = None
        for candidate in root_candidates:
            try:
                root_status, root_content_type = fetch(candidate)
                if root_status == 200:
                    base_url = candidate.rstrip("/")
                    break
            except Exception as exc:  # noqa: BLE001 - try next candidate
                last_root_error = exc
        if root_status is None and last_root_error is not None:
            raise last_root_error

        docs_status, _ = fetch(docs_url)
        reachable = True
        if health_url:
            health_status, _ = fetch(health_url)
            reachable = health_status == 200
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "name": name,
            "base_url": base_url,
            "embed_path": embed_path,
            "api_url": api_url,
            "reachable": reachable,
            "dashboard_present": root_status == 200 and bool(root_content_type and "text/html" in root_content_type.lower()),
            "docs_present": docs_status == 200,
            "latency_ms": latency_ms,
            "status_code": root_status,
            "error": None,
        }
    except URLError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "name": name,
            "base_url": base_url,
            "embed_path": embed_path,
            "api_url": api_url,
            "reachable": False,
            "dashboard_present": False,
            "docs_present": False,
            "latency_ms": latency_ms,
            "status_code": None,
            "error": str(exc.reason),
        }
    except Exception as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return {
            "name": name,
            "base_url": base_url,
            "embed_path": embed_path,
            "api_url": api_url,
            "reachable": False,
            "dashboard_present": False,
            "docs_present": False,
            "latency_ms": latency_ms,
            "status_code": None,
            "error": str(exc),
        }


def check_pattern_agent_dashboard() -> dict[str, Any]:
    base_url = settings.pattern_agent_base_url.rstrip("/")
    return _check_dashboard_integration(
        name="pattern-analysis-agent",
        dashboard_url=base_url,
        docs_url=f"{base_url}/docs",
        embed_path="/embed/pattern",
    )


def check_failure_agent_dashboard() -> dict[str, Any]:
    settings = get_settings()
    api_url = settings.failure_agent_api_url.rstrip("/")
    dashboard_url = settings.failure_agent_dashboard_url.rstrip("/")
    candidates = [dashboard_url]
    if dashboard_url.endswith("/overview"):
        root_url = dashboard_url[: -len("/overview")].rstrip("/")
        if root_url and root_url not in candidates:
            candidates.append(root_url)

    last: dict[str, Any] | None = None
    for candidate in candidates:
        result = _check_dashboard_integration(
            name="failure-analysis-agent",
            dashboard_url=candidate,
            docs_url=f"{api_url}/docs",
            api_url=api_url,
            health_url=f"{api_url}/health",
            embed_path="/embed/failure/overview",
        )
        last = result
        if result.get("reachable") and result.get("dashboard_present"):
            return result
    return last or _check_dashboard_integration(
        name="failure-analysis-agent",
        dashboard_url=dashboard_url,
        docs_url=f"{api_url}/docs",
        api_url=api_url,
        health_url=f"{api_url}/health",
        embed_path="/embed/failure/overview",
    )


def check_scan_diagnosis_agent_dashboard() -> dict[str, Any]:
    api_url = settings.scan_diagnosis_agent_api_url.rstrip("/")
    dashboard_url = settings.scan_diagnosis_agent_dashboard_url.rstrip("/")
    return _check_dashboard_integration(
        name="scan-diagnosis-agent",
        dashboard_url=dashboard_url,
        docs_url=f"{api_url}/docs",
        api_url=api_url,
        health_url=f"{api_url}/api/v1/health",
        embed_path="/embed/scan",
    )


def check_pattern_recommendation_agent_dashboard() -> dict[str, Any]:
    api_url = settings.pattern_recommendation_agent_api_url.rstrip("/")
    dashboard_url = settings.pattern_recommendation_agent_dashboard_url.rstrip("/")
    return _check_dashboard_integration(
        name="pattern-recommendation-agent",
        dashboard_url=dashboard_url,
        docs_url=f"{api_url}/docs",
        api_url=api_url,
        health_url=f"{api_url}/health",
        # Trailing slash required by the agent's React Router basename.
        embed_path="/embed/pattern-rec/",
    )


def check_scan_debug_recommendation_agent_dashboard() -> dict[str, Any]:
    api_url = settings.scan_debug_recommendation_agent_api_url.rstrip("/")
    dashboard_url = settings.scan_debug_recommendation_agent_dashboard_url.rstrip("/")
    return _check_dashboard_integration(
        name="scan-debug-recommendation-agent",
        dashboard_url=dashboard_url,
        docs_url=f"{api_url}/docs",
        api_url=api_url,
        health_url=f"{api_url}/health",
        embed_path="/embed/scan-debug-rec/dashboard/recommendation-analysis",
    )


def check_test_optimization_agent_dashboard() -> dict[str, Any]:
    api_url = settings.test_optimization_agent_api_url.rstrip("/")
    dashboard_url = settings.test_optimization_agent_dashboard_url.rstrip("/")
    return _check_dashboard_integration(
        name="test-optimization-agent",
        dashboard_url=dashboard_url,
        docs_url=f"{api_url}/docs",
        api_url=api_url,
        health_url=f"{api_url}/api/v1/health",
        # Trailing slash required by the agent's React Router basename.
        embed_path="/embed/test-opt/",
    )


async def check_database() -> tuple[bool, str]:
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


async def check_redis() -> tuple[bool, str]:
    try:
        client = await get_redis()
        pong = await client.ping()
        return (pong is True or pong == "PONG"), "ok"
    except Exception as exc:
        return False, str(exc)


async def check_minio() -> tuple[bool, str]:
    try:
        client = get_minio_client()
        buckets = [
            settings.minio_bucket_raw,
            settings.minio_bucket_parsed,
            settings.minio_bucket_wafer,
            settings.minio_bucket_exports,
            settings.minio_bucket_ai,
        ]
        missing = [b for b in buckets if not client.bucket_exists(b)]
        if missing:
            return False, f"missing buckets: {', '.join(missing)}"
        return True, "ok"
    except Exception as exc:
        return False, str(exc)


async def check_worker() -> tuple[bool, str]:
    try:
        heartbeat = await cache_get("worker:heartbeat")
        if not heartbeat or not heartbeat.get("timestamp"):
            return False, "no heartbeat"
        ts = datetime.fromisoformat(heartbeat["timestamp"])
        age = (datetime.now(UTC) - ts).total_seconds()
        if age > settings.worker_heartbeat_max_age_sec:
            return False, f"stale heartbeat ({int(age)}s)"
        return True, heartbeat.get("worker_id", "ok")
    except Exception as exc:
        return False, str(exc)


async def dependency_status() -> dict[str, Any]:
    db_ok, db_msg = await check_database()
    redis_ok, redis_msg = await check_redis()
    minio_ok, minio_msg = await check_minio()
    worker_ok, worker_msg = await check_worker()
    return {
        "database": {"ok": db_ok, "detail": db_msg},
        "redis": {"ok": redis_ok, "detail": redis_msg},
        "minio": {"ok": minio_ok, "detail": minio_msg},
        "worker": {"ok": worker_ok, "detail": worker_msg},
    }


async def full_health_payload() -> dict[str, Any]:
    deps = await dependency_status()
    all_ok = all(d["ok"] for d in deps.values())
    return {
        "status": "healthy" if all_ok else "degraded",
        "database": deps["database"]["ok"],
        "redis": deps["redis"]["ok"],
        "minio": deps["minio"]["ok"],
        "worker": deps["worker"]["ok"],
        "version": settings.app_version,
        "uptime": round(uptime_seconds(), 2),
        "timestamp": datetime.now(UTC).isoformat(),
        "details": {k: v["detail"] for k, v in deps.items()},
    }


async def ready_payload() -> tuple[dict[str, Any], int]:
    deps = await dependency_status()
    required_ok = deps["database"]["ok"] and deps["redis"]["ok"] and deps["minio"]["ok"] and deps["worker"]["ok"]
    payload = {
        "status": "ready" if required_ok else "not_ready",
        "dependencies": deps,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return payload, 200 if required_ok else 503


async def refresh_gauge_metrics() -> None:
    """Lightweight DB gauges for Prometheus scrape."""
    from app.core.metrics import ALERT_COUNT, RECOMMENDATION_COUNT

    try:
        async with AsyncSessionLocal() as db:
            rec_n = await db.scalar(select(func.count()).select_from(Recommendation))
            alert_n = await db.scalar(select(func.count()).select_from(Alert))
            RECOMMENDATION_COUNT.set(rec_n or 0)
            ALERT_COUNT.set(alert_n or 0)
    except Exception:
        pass
