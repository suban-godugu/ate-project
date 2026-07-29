"""Backend tests."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.domain.models import OptimizationContext, YieldData
from app.infrastructure.llm.client import LLMClient
from app.infrastructure.repositories.recommendation_repository import RecommendationRepository
from app.services.heuristic_engine import run_heuristic
from app.services.optimization_service import OptimizationService
from app.services.sample_data import high_risk_lot, low_risk_lot


@pytest.fixture
def settings(tmp_path):
    return Settings(
        OPENAI_API_KEY="",
        FORCE_HEURISTIC=True,
        DATA_DIR=tmp_path,
    )


@pytest.fixture
def service(settings, tmp_path):
    repo = RecommendationRepository(tmp_path / "recommendations")
    llm = LLMClient(settings)
    return OptimizationService(settings=settings, llm=llm, repository=repo)


@pytest.mark.asyncio
async def test_low_risk_optimize(service):
    result = await service.optimize(low_risk_lot(), persist=True)
    assert result.risk_level == "Low"
    assert result.adaptive_testing.flow_mode == "reduced"
    assert result.test_stop.early_stop is True
    assert result.coverage_recommendations
    assert result.business_impact
    saved = await service.get(result.id)
    assert saved is not None


@pytest.mark.asyncio
async def test_high_risk_optimize(service):
    result = await service.optimize(high_risk_lot(), persist=True)
    assert result.risk_level == "High"
    assert result.adaptive_testing.flow_mode == "extended"
    assert "defer" in " ".join(r.action.lower() for r in result.cost_recommendations)


def test_missing_data_not_invented():
    ctx = OptimizationContext(
        device="SOC_XYZ",
        lot_id="LOT_001",
        yield_data=YieldData(current_yield=96.3, historical_yield=97.8, yield_loss=1.5),
    )
    result = run_heuristic(ctx)
    assert "coverage_report" in result.data_gaps
    assert result.test_stop.early_stop is False
    assert any("Missing input" in a for a in result.assumptions)


@pytest.mark.asyncio
async def test_output_contract(service):
    result = await service.optimize(low_risk_lot(), persist=False)
    data = result.model_dump()
    for key in (
        "summary",
        "recommended_strategy",
        "risk_level",
        "confidence",
        "adaptive_testing",
        "test_stop",
        "yield_recommendations",
        "cost_recommendations",
        "coverage_recommendations",
        "production_recommendations",
        "estimated_time_reduction",
        "estimated_cost_reduction",
        "expected_yield_improvement",
        "business_impact",
        "assumptions",
    ):
        assert key in data
