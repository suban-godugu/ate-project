"""Operational endpoints: health, readiness, liveness, metrics."""

from __future__ import annotations

import json

from fastapi import APIRouter, Response
from app.core.metrics import CONTENT_TYPE_LATEST, generate_latest
from app.schemas.common import IntegrationHealthOut
from app.services.health_service import (
    check_failure_agent_dashboard,
    check_pattern_agent_dashboard,
    check_scan_diagnosis_agent_dashboard,
    check_pattern_recommendation_agent_dashboard,
    check_scan_debug_recommendation_agent_dashboard,
    check_test_optimization_agent_dashboard,
    full_health_payload,
    ready_payload,
    refresh_gauge_metrics,
)

router = APIRouter(tags=["operations"])
integration_router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/health")
async def health_check():
    payload = await full_health_payload()
    status_code = 200 if payload["status"] == "healthy" else 503
    return Response(content=json.dumps(payload), media_type="application/json", status_code=status_code)


@router.get("/ready")
async def ready_check():
    payload, status_code = await ready_payload()
    return Response(content=json.dumps(payload), media_type="application/json", status_code=status_code)


@router.get("/live")
async def live_check():
    return {"status": "alive"}


@router.get("/metrics")
async def metrics():
    await refresh_gauge_metrics()
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@integration_router.get("/pattern-agent/health", response_model=IntegrationHealthOut)
async def pattern_agent_health():
    return check_pattern_agent_dashboard()


@integration_router.get("/failure-agent/health", response_model=IntegrationHealthOut)
async def failure_agent_health():
    return check_failure_agent_dashboard()


@integration_router.get("/scan-diagnosis-agent/health", response_model=IntegrationHealthOut)
async def scan_diagnosis_agent_health():
    return check_scan_diagnosis_agent_dashboard()


@integration_router.get(
    "/pattern-recommendation-agent/health", response_model=IntegrationHealthOut
)
async def pattern_recommendation_agent_health():
    return check_pattern_recommendation_agent_dashboard()


@integration_router.get(
    "/scan-debug-recommendation-agent/health", response_model=IntegrationHealthOut
)
async def scan_debug_recommendation_agent_health():
    return check_scan_debug_recommendation_agent_dashboard()


@integration_router.get(
    "/test-optimization-agent/health", response_model=IntegrationHealthOut
)
async def test_optimization_agent_health():
    return check_test_optimization_agent_dashboard()
