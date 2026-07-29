"""Pytest fixtures for VERILUMEN API tests."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy import create_engine, text

from tests.helpers.pipeline import API_BASE, TEST_LOGIN, stack_available, sync_db_url

pytestmark = pytest.mark.asyncio


@dataclass
class TestUser:
    id: uuid.UUID


@pytest.fixture
async def require_stack():
    if not await stack_available():
        pytest.skip("Postgres + API stack not reachable on localhost:8000")


@pytest.fixture
async def api_client(require_stack) -> AsyncClient:
    async with httpx.AsyncClient(base_url=API_BASE, timeout=120.0) as client:
        yield client


@pytest.fixture
async def live_client(api_client):
    yield api_client


@pytest.fixture
async def test_user(api_client: AsyncClient) -> TestUser:
    """Resolve seeded user via login + /auth/me (no direct async DB in fixtures)."""
    r = await api_client.post("/auth/login", json=TEST_LOGIN)
    if r.status_code != 200:
        pytest.skip(f"Test user unavailable — seed alex@verilumen.ai first: {r.text}")
    token = r.json()["access_token"]
    me = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200, me.text
    return TestUser(id=uuid.UUID(me.json()["id"]))


@pytest.fixture
async def auth_tokens(api_client: AsyncClient, test_user: TestUser) -> dict:
    r = await api_client.post("/auth/login", json=TEST_LOGIN)
    assert r.status_code == 200, r.text
    data = r.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "user_id": str(test_user.id),
    }


@pytest.fixture
def auth_headers(auth_tokens: dict) -> dict:
    return {"Authorization": f"Bearer {auth_tokens['access_token']}"}


@pytest.fixture
def test_recommendation(test_user: TestUser):
    rec_id = uuid.uuid4()
    engine = create_engine(sync_db_url())
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO recommendations
                  (id, agent_type, category, priority, confidence, expected_impact, action_text, status, assigned_user_id)
                VALUES
                  (:id, 'pattern', 'PAT-TEST', 'Medium', 75.0, 'pytest fixture', 'Integration test recommendation', 'pending', :uid)
                """
            ),
            {"id": str(rec_id), "uid": str(test_user.id)},
        )
    yield rec_id
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM recommendation_feedback WHERE recommendation_id = :id"),
            {"id": str(rec_id)},
        )
        conn.execute(text("DELETE FROM recommendations WHERE id = :id"), {"id": str(rec_id)})
