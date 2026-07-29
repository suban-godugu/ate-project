"""API system-endpoint and error-shape tests (lightweight)."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from src.api import create_app
from src.config import APP_VERSION, MODEL_PATH


@pytest.fixture(scope="module")
def client():
    if not MODEL_PATH.is_file():
        pytest.skip("Model weights not present — skipping API tests that need lifespan load")
    application = create_app()
    with TestClient(application) as test_client:
        yield test_client


def test_root_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Running" in response.json()["message"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["api_running"] is True
    assert "model_loaded" in body


def test_version_endpoint(client):
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == APP_VERSION
    assert body["name"] == "WaferVision-AI"


def test_metrics_endpoint(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "uptime_seconds" in body
    assert "model_loaded" in body


def test_reject_executable_upload(client):
    response = client.post(
        "/predict",
        files={"image": ("malware.exe", b"MZ fake", "application/octet-stream")},
        data={"grid_mode": "automatic"},
    )
    assert response.status_code == 415
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == 415
    assert "detail" in body
    assert "message" in body


def test_reject_archive_upload(client):
    response = client.post(
        "/predict",
        files={"image": ("pack.zip", b"PK fake", "application/zip")},
        data={"grid_mode": "automatic"},
    )
    assert response.status_code == 415
