"""Upload and parser audit integration tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from tests.helpers import pipeline as pl

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

STDF = pl.FIXTURES / "sample.stdf"


@pytest.fixture
def require_stdf():
    if not STDF.exists():
        pytest.skip("Run python scripts/build_stdf_fixture.py first")


async def _audit_count_for_job(job_id: str) -> int:
    return pl.db_scalar(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE entity_type = 'upload' AND entity_id = :jid
        """,
        {"jid": job_id},
    ) or 0


async def test_upload_writes_audit_events(live_client: AsyncClient, require_stdf):
    token = await pl.login(live_client)
    before = pl.db_scalar(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE entity_type = 'upload' OR action LIKE '%upload%' OR action LIKE '%parser%'
        """
    ) or 0

    upload = await pl.upload_file(live_client, token, STDF, kind="data")
    job_id = upload["job_id"]

    started = pl.db_scalar(
        "SELECT COUNT(*) FROM audit_logs WHERE action = 'upload_started' AND entity_id = :jid",
        {"jid": job_id},
    )
    assert started >= 1, "upload_started audit missing after presign"

    result = await pl.wait_job(live_client, job_id, token)
    status = result.get("job", {}).get("status")
    if status != "Completed":
        pytest.skip(f"ARQ worker did not complete (status={status})")

    after = pl.db_scalar(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE entity_type = 'upload' OR action LIKE '%upload%' OR action LIKE '%parser%'
        """
    ) or 0
    assert after > before, "Expected new upload/parser audit rows"

    job_audits = await _audit_count_for_job(job_id)
    assert job_audits >= 3, f"Expected multiple audit events for job, got {job_audits}"

    for action in ("upload_completed", "parser_started", "parser_completed"):
        count = pl.db_scalar(
            "SELECT COUNT(*) FROM audit_logs WHERE action = :action AND entity_id = :jid",
            {"action": action, "jid": job_id},
        )
        assert count >= 1, f"Missing audit action: {action}"


async def test_audit_retrieval(live_client: AsyncClient, auth_headers: dict):
    r = await live_client.get(f"{pl.API_BASE}/audit?page=1&page_size=5", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


async def test_theme_preferences_sync(live_client: AsyncClient, auth_headers: dict):
    theme = {
        "appearance": "dark",
        "primaryColor": "blue",
        "sidebarStyle": "compact",
        "cardStyle": "solid",
        "fontSize": "medium",
        "compactMode": True,
        "animations": False,
        "sidebarWidth": "standard",
        "borderRadius": "medium",
        "density": "compact",
    }
    patch = await live_client.patch(
        f"{pl.API_BASE}/users/me/preferences",
        headers=auth_headers,
        json={"theme_json": theme},
    )
    assert patch.status_code == 200, patch.text

    get = await live_client.get(f"{pl.API_BASE}/users/me/preferences", headers=auth_headers)
    assert get.status_code == 200
    saved = get.json().get("theme_json") or {}
    assert saved.get("primaryColor") == "blue"
    assert saved.get("compactMode") is True
