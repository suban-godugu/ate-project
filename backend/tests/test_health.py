"""Health, readiness, and liveness endpoint tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_live_returns_alive(client: AsyncClient):
    r = await client.get("/live")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"


async def test_health_returns_dependency_fields(client: AsyncClient):
    r = await client.get("/health")
    data = r.json()
    assert "database" in data
    assert "redis" in data
    assert "minio" in data
    assert "worker" in data
    assert "version" in data
    assert "uptime" in data
    assert "timestamp" in data


async def test_ready_returns_dependency_map(client: AsyncClient):
    r = await client.get("/ready")
    data = r.json()
    assert "dependencies" in data
    assert "database" in data["dependencies"]


async def test_metrics_prometheus_format(client: AsyncClient):
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "verilumen_http_requests_total" in r.text or "# HELP" in r.text
