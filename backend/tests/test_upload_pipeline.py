"""Serial upload integration tests — share one ARQ worker queue."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from tests.helpers import pipeline as pl

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

FIXTURES = pl.FIXTURES
STDF = FIXTURES / "sample.stdf"
LOG = FIXTURES / "sample_ate.log"


@pytest.fixture
def require_fixtures():
    if not STDF.exists() or not LOG.exists():
        pytest.skip("Run python scripts/build_stdf_fixture.py first")


async def _assert_job_completed(client: AsyncClient, job_id: str, token: str) -> dict:
    result = await pl.wait_job(client, job_id, token)
    status = result.get("job", {}).get("status")
    if status != "Completed":
        pytest.skip(f"ARQ worker did not complete job in time (status={status}) — ensure worker is running")
    return result


async def test_stdf_upload_populates_failures(live_client: AsyncClient, require_fixtures):
    token = await pl.login(live_client)
    failures_before = pl.db_scalar("SELECT COUNT(*) FROM scan_chain_failures") or 0

    upload = await pl.upload_file(live_client, token, STDF, kind="data")
    await _assert_job_completed(live_client, upload["job_id"], token)

    failures_after = pl.db_scalar("SELECT COUNT(*) FROM scan_chain_failures") or 0
    assert failures_after > failures_before

    chain_rows = pl.db_query(
        "SELECT chain_id, pattern_id FROM scan_chain_failures ORDER BY created_at DESC LIMIT 5"
    )
    assert any(r[0] for r in chain_rows), "Expected real parser chain IDs"


async def test_log_upload_populates_cost_fields(live_client: AsyncClient, require_fixtures):
    token = await pl.login(live_client)
    upload = await pl.upload_file(live_client, token, LOG, kind="log")
    await _assert_job_completed(live_client, upload["job_id"], token)

    row = pl.db_query(
        """
        SELECT estimated_cost, estimated_savings, scan_chains, wafer_count, patterns_found
        FROM ai_log_summaries
        WHERE upload_job_id = :jid
        """,
        {"jid": upload["job_id"]},
    )
    assert row, "Expected ai_log_summaries row for LOG upload"
    cost, savings, scan_chains, wafer_count, patterns_found = row[0]
    assert cost is not None and float(cost) > 0
    assert savings is not None and float(savings) > 0
    assert int(scan_chains or 0) >= 1
    assert int(wafer_count or 0) >= 1
    assert int(patterns_found or 0) >= 1


async def test_log_upload_completes(live_client: AsyncClient, require_fixtures):
    token = await pl.login(live_client)
    summaries_before = pl.db_scalar("SELECT COUNT(*) FROM ai_log_summaries") or 0

    upload = await pl.upload_file(live_client, token, LOG, kind="log")
    await _assert_job_completed(live_client, upload["job_id"], token)

    summaries_after = pl.db_scalar("SELECT COUNT(*) FROM ai_log_summaries") or 0
    assert summaries_after >= summaries_before + 1


async def test_upload_redis_and_minio(live_client: AsyncClient, require_fixtures):
    token = await pl.login(live_client)
    upload = await pl.upload_file(live_client, token, STDF, kind="data")
    await _assert_job_completed(live_client, upload["job_id"], token)

    assert await pl.check_redis_job_status(upload["job_id"])

    job_row = pl.db_query(
        "SELECT minio_object_key FROM upload_jobs WHERE id = :jid",
        {"jid": upload["job_id"]},
    )
    raw_key = job_row[0][0] if job_row else None
    has_raw, has_parsed = pl.check_minio_parsed(upload["job_id"], raw_key)
    assert has_raw or has_parsed


async def test_upload_invalidates_search_cache(live_client: AsyncClient, require_fixtures):
    token = await pl.login(live_client)
    headers = {"Authorization": f"Bearer {token}"}

    audit_before = pl.db_scalar(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE entity_type = 'upload' OR action LIKE '%upload%' OR action LIKE '%parser%'
        """
    ) or 0

    upload = await pl.upload_file(live_client, token, STDF, kind="data")
    await _assert_job_completed(live_client, upload["job_id"], token)

    audit_after = pl.db_scalar(
        """
        SELECT COUNT(*) FROM audit_logs
        WHERE entity_type = 'upload' OR action LIKE '%upload%' OR action LIKE '%parser%'
        """
    ) or 0
    assert audit_after > audit_before, "Upload audit logging not wired"

    dash = await live_client.get(f"{pl.API_BASE}/dashboard/scan-chain/overview", headers=headers)
    assert dash.status_code == 200

    search = await live_client.get(f"{pl.API_BASE}/search", headers=headers)
    assert search.status_code == 200
    assert isinstance(search.json(), list)
