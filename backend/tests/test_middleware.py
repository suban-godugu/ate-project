"""Request ID and security header middleware tests."""

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


async def test_request_id_generated(client: AsyncClient):
    r = await client.get("/live")
    assert r.headers.get("X-Request-ID")


async def test_request_id_echoed(client: AsyncClient):
    rid = "test-correlation-id-12345"
    r = await client.get("/live", headers={"X-Request-ID": rid})
    assert r.headers.get("X-Request-ID") == rid


async def test_security_headers(client: AsyncClient):
    r = await client.get("/live")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
