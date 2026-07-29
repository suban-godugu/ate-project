"""Domain input models for the Test Optimization Recommendation Agent."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class PatternRecommendationInput(BaseModel):
    patterns_removed: list[str] = Field(default_factory=list)
    patterns_added: list[str] = Field(default_factory=list)
    patterns_reordered: list[str] = Field(default_factory=list)
    coverage_after_optimization: Optional[float] = Field(default=None, ge=0, le=100)
    power_reduction: Optional[str] = None
    estimated_test_time_saved: Optional[float] = None
    low_power_recommendations: list[str] = Field(default_factory=list)
    notes: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ScanDebugRecommendationInput(BaseModel):
    scan_chain: Optional[str] = None
    debug_actions: list[str] = Field(default_factory=list)
    suspected_root_cause: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    timing_debug: list[str] = Field(default_factory=list)
    power_debug: list[str] = Field(default_factory=list)
    physical_defect_actions: list[str] = Field(default_factory=list)
    lot_id: Optional[str] = None
    notes: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class YieldData(BaseModel):
    current_yield: float = Field(..., ge=0, le=100)
    historical_yield: Optional[float] = Field(default=None, ge=0, le=100)
    yield_trend: Optional[str] = None
    yield_loss: Optional[float] = None
    yield_by_lot: dict[str, float] = Field(default_factory=dict)
    yield_by_device: dict[str, float] = Field(default_factory=dict)
    defect_density: Optional[float] = None
    fail_bins: dict[str, int] = Field(default_factory=dict)
    lot_id: Optional[str] = None
    wafer_id: Optional[str] = None


class ATELogs(BaseModel):
    execution_time_s: Optional[float] = None
    tester_utilization: Optional[float] = Field(default=None, ge=0, le=1)
    retest_count: Optional[int] = None
    abort_rate: Optional[float] = Field(default=None, ge=0, le=1)
    machine_errors: Optional[int] = None
    equipment_failures: Optional[int] = None
    pattern_execution_time_s: Optional[float] = None
    pattern_execution_stats: dict[str, Any] = Field(default_factory=dict)
    tester_id: Optional[str] = None
    site_count: Optional[int] = Field(default=None, ge=1)
    site_utilization: dict[int, float] = Field(default_factory=dict)
    total_devices: Optional[int] = None
    timeout_count: Optional[int] = None


class CoverageReport(BaseModel):
    stuck_at: Optional[float] = Field(default=None, ge=0, le=100)
    transition: Optional[float] = Field(default=None, ge=0, le=100)
    path_delay: Optional[float] = Field(default=None, ge=0, le=100)
    cell_aware: Optional[float] = Field(default=None, ge=0, le=100)
    coverage_pct: Optional[float] = Field(default=None, ge=0, le=100)
    pattern_count: Optional[int] = None
    target_coverage_pct: float = Field(default=98.8, ge=0, le=100)


class ProductionHistory(BaseModel):
    device: str = "UNKNOWN"
    fab: Optional[str] = None
    tester: Optional[str] = None
    lots: list[str] = Field(default_factory=list)
    devices: list[str] = Field(default_factory=list)
    historical_failures: list[str] = Field(default_factory=list)
    customer_returns: list[str] = Field(default_factory=list)
    high_failure_lots: list[str] = Field(default_factory=list)
    escape_rate_ppm: Optional[float] = None
    avg_cost_per_die_usd: Optional[float] = None


class HistoricalLot(BaseModel):
    lot_id: str
    device: Optional[str] = None
    yield_pct: Optional[float] = None
    test_time_s: Optional[float] = None
    escape_rate_ppm: Optional[float] = None
    cost_per_die_usd: Optional[float] = None
    flow_mode: Optional[str] = None
    known_issues: list[str] = Field(default_factory=list)
    failure_recurrence: Optional[str] = None
    high_risk: bool = False
    notes: Optional[str] = None


class WaferAnalytics(BaseModel):
    wafer_id: Optional[str] = None
    heatmap: list[list[float]] = Field(
        default_factory=list,
        description="2D grid of fail intensity 0-1 for canvas heatmap",
    )
    hotspots: list[str] = Field(default_factory=list)
    bin_distributions: dict[str, int] = Field(default_factory=dict)
    defect_clustering: list[str] = Field(default_factory=list)
    spatial_fail_clusters: list[str] = Field(default_factory=list)
    edge_die_fail_rate: Optional[float] = None
    center_die_fail_rate: Optional[float] = None
    systematic_signature: Optional[str] = None
    notes: Optional[str] = None


class CostMetrics(BaseModel):
    cost_per_second_usd: Optional[float] = None
    cost_per_die_usd: Optional[float] = None
    target_cost_per_die_usd: Optional[float] = None
    tester_hour_cost_usd: Optional[float] = None
    tester_utilization_cost_usd: Optional[float] = None
    engineering_hours_cost_usd: Optional[float] = None
    retest_cost_usd: Optional[float] = None
    yield_loss_cost_usd: Optional[float] = None


class PolicyKnobs(BaseModel):
    max_escape_rate_ppm: float = 100.0
    min_yield_for_reduced_flow_pct: float = 97.0
    coverage_stop_threshold_pct: float = 98.8
    max_abort_rate: float = 0.02


class OptimizationContext(BaseModel):
    device: str = "UNKNOWN_DEVICE"
    lot_id: str = "UNKNOWN_LOT"
    fab: Optional[str] = None
    pattern_recommendation: Optional[PatternRecommendationInput] = None
    scan_debug_recommendation: Optional[ScanDebugRecommendationInput] = None
    yield_data: Optional[YieldData] = None
    ate_logs: Optional[ATELogs] = None
    coverage_report: Optional[CoverageReport] = None
    production_history: Optional[ProductionHistory] = None
    historical_lots: list[HistoricalLot] = Field(default_factory=list)
    wafer_analytics: Optional[WaferAnalytics] = None
    cost_metrics: Optional[CostMetrics] = None
    policy: PolicyKnobs = Field(default_factory=PolicyKnobs)
    assumptions: list[str] = Field(default_factory=list)
