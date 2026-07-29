"""Recommendation feedback round-trip and UUID integrity."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.recommendations import RecommendationFeedback

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


async def test_feedback_invalid_recommendation_id(api_client: AsyncClient, auth_headers):
    fake_id = str(uuid.uuid4())
    r = await api_client.post(
        f"/recommendations/{fake_id}/feedback",
        headers=auth_headers,
        json={"action_taken": "approved", "outcome_metric": "status"},
    )
    assert r.status_code == 404


async def test_feedback_round_trip(api_client: AsyncClient, auth_headers, test_recommendation: uuid.UUID):
    rec_id = str(test_recommendation)
    r = await api_client.post(
        f"/recommendations/{rec_id}/feedback",
        headers=auth_headers,
        json={"action_taken": "approved", "outcome_metric": "status"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert "reward_value" in body
    feedback_id = body["feedback_id"]
    assert feedback_id

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RecommendationFeedback).where(RecommendationFeedback.id == uuid.UUID(feedback_id))
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert str(row.recommendation_id) == rec_id
        assert row.action_taken == "approved"
        assert float(row.reward_value) == float(body["reward_value"])


async def test_metrics_for_recommendation(api_client: AsyncClient, auth_headers, test_recommendation: uuid.UUID):
    rec_id = str(test_recommendation)
    await api_client.post(
        f"/recommendations/{rec_id}/feedback",
        headers=auth_headers,
        json={"action_taken": "applied", "outcome_metric": "status"},
    )
    r = await api_client.get(
        f"/recommendations/{rec_id}/metrics",
        headers=auth_headers,
    )
    if r.status_code == 404:
        pytest.skip("Metrics endpoint not available on running API — restart uvicorn after Prompt 22")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["recommendation_id"] == rec_id
    assert len(data["feedback_history"]) >= 1
    assert data["feedback_history"][0]["action_taken"] == "applied"
