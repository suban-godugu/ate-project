"""API request/response schemas — enterprise JSON contract."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .models import OptimizationContext

RiskLevel = Literal["Low", "Medium", "High"]
FlowMode = Literal["full", "reduced", "extended", "skip"]


class AdaptiveTestingBlock(BaseModel):
    recommendation: str
    flow_mode: FlowMode = "full"
    applicable_to: Optional[str] = None
    rationale: str = ""
    trade_offs: str = ""
    business_impact: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)


class TestStopBlock(BaseModel):
    recommendation: str
    stop_coverage_pct: Optional[float] = Field(default=None, ge=0, le=100)
    early_stop: bool = False
    rationale: str = ""
    trade_offs: str = ""
    business_impact: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)


class RiskBasedTestingBlock(BaseModel):
    recommendation: str
    high_risk_lots: list[str] = Field(default_factory=list)
    action_for_high_risk: str = ""
    action_for_low_risk: str = ""
    rationale: str = ""
    trade_offs: str = ""
    business_impact: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)


class RecommendationItem(BaseModel):
    action: str
    rationale: str = ""
    trade_offs: str = ""
    business_impact: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)
    estimated_impact: dict[str, Any] = Field(default_factory=dict)


class MultiSiteBlock(BaseModel):
    recommendation: str
    site_actions: list[str] = Field(default_factory=list)
    rationale: str = ""
    trade_offs: str = ""
    business_impact: str = ""
    confidence: float = Field(default=0.7, ge=0, le=1)


class OptimizationRecommendation(BaseModel):
    """Enterprise recommendation JSON output."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    device: str = ""
    lot_id: str = ""
    summary: str
    recommended_strategy: str
    risk_level: RiskLevel
    confidence: float = Field(..., ge=0, le=1)
    risk_score: float = Field(default=0.0, ge=0, le=100)
    adaptive_testing: AdaptiveTestingBlock
    test_stop: TestStopBlock
    risk_based_testing: RiskBasedTestingBlock = Field(
        default_factory=lambda: RiskBasedTestingBlock(
            recommendation="No risk-based override",
            rationale="Insufficient risk signals",
        )
    )
    yield_recommendations: list[RecommendationItem] = Field(default_factory=list)
    cost_recommendations: list[RecommendationItem] = Field(default_factory=list)
    coverage_recommendations: list[RecommendationItem] = Field(default_factory=list)
    production_recommendations: list[RecommendationItem] = Field(default_factory=list)
    multi_site_optimization: Optional[MultiSiteBlock] = None
    estimated_time_reduction: str = "N/A"
    estimated_cost_reduction: str = "N/A"
    expected_yield_improvement: str = "N/A"
    business_impact: str = ""
    assumptions: list[str] = Field(default_factory=list)
    data_gaps: list[str] = Field(default_factory=list)
    engine: Literal["llm", "heuristic"] = "heuristic"


class OptimizeRequest(BaseModel):
    context: OptimizationContext
    persist: bool = True


class HealthResponse(BaseModel):
    status: str
    agent: str
    version: str
    llm_enabled: bool
    model: Optional[str] = None
    environment: str


class RecommendationListResponse(BaseModel):
    items: list[OptimizationRecommendation]
    total: int


class CompareRequest(BaseModel):
    ids: list[str] = Field(..., min_length=2, max_length=5)


class AnalyticsSummary(BaseModel):
    total_recommendations: int
    avg_confidence: float
    risk_distribution: dict[str, int]
    avg_yield: Optional[float] = None
    recent: list[OptimizationRecommendation] = Field(default_factory=list)
