"""Main FA-FR-003 failure rate calculation engine."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.bridge import test_records_to_die_logs
from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from analytics.failure_rates.aggregation import aggregate_all_levels
from analytics.failure_rates.statistics import attach_statistics
from analytics.failure_rates.trend_analysis import build_trend_report
from failure_rate_engine import compute_failure_rates
from ingestor import DieLog

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "failure_rates.yaml"


@dataclass
class RateEngineConfig:
    alert_threshold_pct: float = 5.0
    tolerance_pct: float = 0.01
    control_limit_sigma: float = 3.0
    shift_hours: int = 8

    @classmethod
    def load(cls, path: Path | None = None) -> RateEngineConfig:
        raw = load_adapter_configs(path or DEFAULT_CONFIG)
        return cls(
            alert_threshold_pct=float(raw.get("alert_threshold_pct", 5.0)),
            tolerance_pct=float(raw.get("tolerance_pct", 0.01)),
            control_limit_sigma=float(raw.get("control_limit_sigma", 3.0)),
            shift_hours=int(raw.get("shift_hours", 8)),
        )


class FailureRateEngine:
    """Compute failure rates across all production hierarchies."""

    def __init__(self, config: RateEngineConfig | None = None) -> None:
        self.config = config or RateEngineConfig.load()

    def calculate(
        self,
        *,
        die_logs: list[DieLog] | None = None,
        test_records: list[TestRecord] | None = None,
        upload_id: str | None = None,
        historical_runs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        if test_records and not die_logs:
            die_logs = test_records_to_die_logs(test_records)
        die_logs = die_logs or []

        legacy = compute_failure_rates(
            die_logs,
            test_records=test_records,
            alert_threshold_pct=self.config.alert_threshold_pct,
        )
        levels = aggregate_all_levels(
            die_logs,
            test_records,
            shift_hours=self.config.shift_hours,
        )

        enriched_levels = {
            name: attach_statistics(data) for name, data in levels.items()
        }

        trend_report = build_trend_report(
            lot_level=levels["lot_level"],
            wafer_level=levels["wafer_level"],
            time_window_level=legacy.get("time_window_level"),
            historical_runs=historical_runs,
        )

        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        summary = legacy.get("summary", {})

        return {
            "requirement": "FA-FR-003",
            "upload_id": upload_id,
            "processing_ms": elapsed_ms,
            "meets_performance_target": elapsed_ms < 5000,
            "tolerance_pct": self.config.tolerance_pct,
            "alert_threshold_pct": self.config.alert_threshold_pct,
            "formula": legacy.get("formula", "failure_rate_pct = failed / tested × 100"),
            "summary": summary,
            "overall_manufacturing_yield": {
                "yield_pct": summary.get("overall_yield_pct", 0.0),
                "failure_rate_pct": summary.get("overall_failure_rate_pct", 0.0),
                "total_dies_tested": summary.get("total_dies_tested", 0),
                "total_failing_dies": summary.get("total_failing_dies", 0),
            },
            "levels": enriched_levels,
            "device_level": enriched_levels["device_level"],
            "die_level": enriched_levels["die_level"],
            "wafer_level": enriched_levels["wafer_level"],
            "lot_level": enriched_levels["lot_level"],
            "product_level": enriched_levels["product_level"],
            "tester_level": enriched_levels["tester_level"],
            "shift_level": enriched_levels["shift_level"],
            "production_level": enriched_levels["production_level"],
            "pattern_level": attach_statistics(legacy.get("pattern_level", {})),
            "bin_level": attach_statistics(legacy.get("bin_level", {})),
            "time_window_level": attach_statistics(legacy.get("time_window_level", {})),
            "alerts": legacy.get("alerts", []),
            "trend_report": trend_report,
            "legacy_engine": {
                "test_stage_level": legacy.get("test_stage_level", {}),
                "trends": legacy.get("trends", {}),
            },
        }
