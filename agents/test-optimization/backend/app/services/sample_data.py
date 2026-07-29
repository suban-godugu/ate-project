"""Sample OptimizationContext fixtures."""

from __future__ import annotations

from ..domain.models import (
    ATELogs,
    CostMetrics,
    CoverageReport,
    HistoricalLot,
    OptimizationContext,
    PatternRecommendationInput,
    ProductionHistory,
    ScanDebugRecommendationInput,
    WaferAnalytics,
    YieldData,
)


def _heatmap(seed: float = 0.1) -> list[list[float]]:
    grid: list[list[float]] = []
    for r in range(20):
        row = []
        for c in range(20):
            edge = 1 if r < 2 or c < 2 or r > 17 or c > 17 else 0
            val = min(1.0, seed + edge * 0.35 + ((r * c) % 7) * 0.02)
            row.append(round(val, 3))
        grid.append(row)
    return grid


def low_risk_lot() -> OptimizationContext:
    return OptimizationContext(
        device="SOC_XYZ",
        lot_id="LOT_245",
        fab="FAB-A",
        pattern_recommendation=PatternRecommendationInput(
            patterns_removed=["PAT_101", "PAT_088"],
            patterns_added=[],
            patterns_reordered=["PAT_012", "PAT_015"],
            coverage_after_optimization=98.9,
            power_reduction="12% peak capture power",
            estimated_test_time_saved=4.8,
            low_power_recommendations=["Prefer low-power ATPG set LP_A"],
        ),
        yield_data=YieldData(
            current_yield=98.4,
            historical_yield=97.8,
            yield_trend="stable-up",
            yield_loss=-0.6,
            yield_by_lot={"LOT_240": 97.8, "LOT_241": 98.1, "LOT_245": 98.4},
            yield_by_device={"SOC_XYZ": 98.0},
            defect_density=0.12,
            fail_bins={"BIN_SCAN": 8, "BIN_IDDQ": 3},
            lot_id="LOT_245",
            wafer_id="W03",
        ),
        ate_logs=ATELogs(
            execution_time_s=42.0,
            tester_utilization=0.88,
            retest_count=18,
            abort_rate=0.003,
            machine_errors=1,
            equipment_failures=0,
            pattern_execution_time_s=36.0,
            tester_id="ATE-07",
            site_count=4,
            site_utilization={1: 0.91, 2: 0.88, 3: 0.85, 4: 0.87},
            total_devices=1200,
            timeout_count=6,
        ),
        coverage_report=CoverageReport(
            stuck_at=99.2,
            transition=98.9,
            path_delay=98.9,
            cell_aware=98.7,
            coverage_pct=98.9,
            pattern_count=4200,
            target_coverage_pct=98.8,
        ),
        production_history=ProductionHistory(
            device="SOC_XYZ",
            fab="FAB-A",
            tester="ATE-07",
            lots=["LOT_240", "LOT_241", "LOT_245"],
            historical_failures=["occasional IDDQ outlier"],
            customer_returns=[],
            high_failure_lots=[],
            escape_rate_ppm=42.0,
            avg_cost_per_die_usd=0.42,
        ),
        historical_lots=[
            HistoricalLot(
                lot_id="LOT_240", device="SOC_XYZ", yield_pct=97.8, test_time_s=44.0,
                escape_rate_ppm=45, cost_per_die_usd=0.42, flow_mode="full",
            ),
            HistoricalLot(
                lot_id="LOT_241", device="SOC_XYZ", yield_pct=98.1, test_time_s=43.5,
                escape_rate_ppm=38, cost_per_die_usd=0.41, flow_mode="full",
            ),
        ],
        wafer_analytics=WaferAnalytics(
            wafer_id="W03",
            heatmap=_heatmap(0.08),
            hotspots=[],
            bin_distributions={"BIN_PASS": 1187, "BIN_SCAN": 8, "BIN_IDDQ": 3},
            edge_die_fail_rate=0.02,
            center_die_fail_rate=0.01,
        ),
        cost_metrics=CostMetrics(
            cost_per_second_usd=0.05,
            cost_per_die_usd=0.415,
            target_cost_per_die_usd=0.40,
            tester_hour_cost_usd=180.0,
            retest_cost_usd=0.02,
            yield_loss_cost_usd=0.0,
        ),
    )


def high_risk_lot() -> OptimizationContext:
    return OptimizationContext(
        device="SOC_XYZ",
        lot_id="LOT_250",
        fab="FAB-A",
        pattern_recommendation=PatternRecommendationInput(
            patterns_removed=[],
            patterns_added=["PAT_T200", "PAT_T201"],
            coverage_after_optimization=96.4,
            estimated_test_time_saved=-5.0,
            notes="Added transition patterns for coverage gap.",
        ),
        scan_debug_recommendation=ScanDebugRecommendationInput(
            scan_chain="Chain12",
            debug_actions=[
                "Inspect Scan Chain 12",
                "Review Capture Clock Timing",
                "Check IR-Drop During Capture",
            ],
            suspected_root_cause="Hold-time violation near Chain12 segment 3",
            confidence=0.91,
            timing_debug=["Review Capture Clock Timing"],
            power_debug=["Check IR-Drop During Capture"],
            physical_defect_actions=["Inspect chain segment vias"],
            lot_id="LOT_250",
        ),
        yield_data=YieldData(
            current_yield=87.2,
            historical_yield=97.8,
            yield_trend="down",
            yield_loss=10.6,
            yield_by_lot={"LOT_240": 97.8, "LOT_248": 91.0, "LOT_250": 87.2},
            yield_by_device={"SOC_XYZ": 92.0},
            defect_density=0.78,
            fail_bins={"BIN_SCAN": 95, "BIN_TIMING": 40, "BIN_IDDQ": 18},
            lot_id="LOT_250",
            wafer_id="W11",
        ),
        ate_logs=ATELogs(
            execution_time_s=48.0,
            tester_utilization=0.72,
            retest_count=90,
            abort_rate=0.032,
            machine_errors=8,
            equipment_failures=3,
            pattern_execution_time_s=41.0,
            tester_id="ATE-03",
            site_count=4,
            site_utilization={1: 0.92, 2: 0.55, 3: 0.88, 4: 0.60},
            total_devices=1100,
            timeout_count=22,
        ),
        coverage_report=CoverageReport(
            stuck_at=97.1,
            transition=96.4,
            path_delay=95.8,
            cell_aware=95.2,
            coverage_pct=95.8,
            pattern_count=4400,
            target_coverage_pct=98.8,
        ),
        production_history=ProductionHistory(
            device="SOC_XYZ",
            fab="FAB-A",
            tester="ATE-03",
            lots=["LOT_240", "LOT_248", "LOT_250"],
            historical_failures=["scan chain fail", "transition timing"],
            customer_returns=["field scan fail Q2"],
            high_failure_lots=["LOT_248", "LOT_250"],
            escape_rate_ppm=120.0,
            avg_cost_per_die_usd=0.44,
        ),
        historical_lots=[
            HistoricalLot(
                lot_id="LOT_248", device="SOC_XYZ", yield_pct=91.0, high_risk=True,
                known_issues=["scan banding"], failure_recurrence="recurring",
                flow_mode="extended",
            ),
            HistoricalLot(
                lot_id="LOT_250", device="SOC_XYZ", yield_pct=87.2, high_risk=True,
                known_issues=["Chain12"], flow_mode="extended",
            ),
        ],
        wafer_analytics=WaferAnalytics(
            wafer_id="W11",
            heatmap=_heatmap(0.35),
            hotspots=["NW quadrant ring", "scribe-adjacent edge"],
            bin_distributions={"BIN_PASS": 960, "BIN_SCAN": 95, "BIN_TIMING": 40},
            defect_clustering=["scan-shift fail banding"],
            spatial_fail_clusters=["NW quadrant ring"],
            edge_die_fail_rate=0.18,
            center_die_fail_rate=0.06,
            systematic_signature="scan-shift fail banding",
        ),
        cost_metrics=CostMetrics(
            cost_per_second_usd=0.05,
            cost_per_die_usd=0.44,
            target_cost_per_die_usd=0.40,
            tester_hour_cost_usd=180.0,
            retest_cost_usd=0.05,
            yield_loss_cost_usd=12000.0,
        ),
    )


SAMPLES = {
    "low_risk": low_risk_lot,
    "high_risk": high_risk_lot,
}
