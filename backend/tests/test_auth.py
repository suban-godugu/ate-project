"""Auth flow tests: login, refresh, logout, invalid credentials."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.helpers.pipeline import TEST_LOGIN

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


async def test_login_success(auth_tokens):
    assert auth_tokens["access_token"]
    assert auth_tokens["refresh_token"]


async def test_login_invalid_credentials(api_client: AsyncClient, require_stack):
    r = await api_client.post(
        "/auth/login",
        json={"email": TEST_LOGIN["email"], "password": "wrong-password"},
    )
    assert r.status_code == 401
    assert "Invalid credentials" in r.json()["detail"]


async def test_login_unknown_email(api_client: AsyncClient, require_stack):
    r = await api_client.post(
        "/auth/login",
        json={"email": "nobody@verilumen.ai", "password": "changeme123"},
    )
    assert r.status_code == 401


async def test_refresh_token(api_client: AsyncClient, auth_tokens):
    r = await api_client.post(
        "/auth/refresh",
        json={"refresh_token": auth_tokens["refresh_token"]},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["access_token"] != auth_tokens["access_token"]

    me = await api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == TEST_LOGIN["email"]


async def test_refresh_invalid_token(api_client: AsyncClient, require_stack):
    r = await api_client.post(
        "/auth/refresh",
        json={"refresh_token": "not.a.valid.jwt"},
    )
    assert r.status_code == 401


async def test_logout(api_client: AsyncClient, auth_tokens):
    r = await api_client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    me = await api_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {auth_tokens['access_token']}"},
    )
    assert me.status_code == 401
