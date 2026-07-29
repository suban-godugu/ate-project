"""Per-tab dashboard API reads (P1-9 regression paths)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

DASHBOARD_TABS = [
    "/dashboard/executive",
    "/dashboard/scan-chain/overview",
    "/dashboard/scan-chain/pattern-agent",
    "/dashboard/mbist/overview",
    "/dashboard/lbist/overview",
    "/dashboard/wafer-analysis/overview",
    "/dashboard/recommendation-analysis/overview",
    "/dashboard/recommendation-analysis/pattern-agent",
    "/dashboard/recommendation-analysis/scan-debug-agent",
    "/dashboard/recommendation-analysis/test-optimization-agent",
    "/dashboard/cost-intelligence/overview",
    "/dashboard/cost-intelligence/scan-chain",
    "/dashboard/cost-intelligence/wafer",
    "/dashboard/alerts/overview",
]


@pytest.mark.parametrize("path", DASHBOARD_TABS)
async def test_dashboard_tab_returns_200(api_client: AsyncClient, auth_headers, path: str):
    r = await api_client.get(path, headers=auth_headers)
    assert r.status_code == 200, f"{path}: {r.text[:300]}"
    data = r.json()
    assert any(k in data for k in ("kpis", "rows", "charts", "patterns", "costTrend")), f"{path}: unexpected shape"


async def test_protected_route_requires_auth(api_client: AsyncClient, require_stack):
    r = await api_client.get("/auth/me")
    assert r.status_code == 401
