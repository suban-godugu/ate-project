"""FA-FR-003: Normalized multi-level failure rate engine with alerts."""

from __future__ import annotations

import json
import logging
import math
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from ingestor import DieLog

logger = logging.getLogger(__name__)

FAILURE_RATE_TOLERANCE_PCT = 0.01
DEFAULT_ALERT_THRESHOLD_PCT = 5.0
CONTROL_LIMIT_SIGMA = 3.0


@dataclass
class RateBucket:
    tested: int = 0
    failed: int = 0

    @property
    def failure_rate_pct(self) -> float:
        if self.tested == 0:
            return 0.0
        return round(100.0 * self.failed / self.tested, 6)

    @property
    def pass_rate_pct(self) -> float:
        return round(100.0 - self.failure_rate_pct, 6)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tested": self.tested,
            "failed": self.failed,
            "passing": self.tested - self.failed,
            "failure_rate_pct": self.failure_rate_pct,
            "pass_rate_pct": self.pass_rate_pct,
            "yield_pct": self.pass_rate_pct,
        }


def compute_failure_rates(
    die_logs: list[DieLog],
    *,
    test_records: list[TestRecord] | None = None,
    alert_threshold_pct: float = DEFAULT_ALERT_THRESHOLD_PCT,
) -> dict[str, Any]:
    """
    Compute normalized failure rates at device, lot, wafer, pattern, bin, tester,
    product, test_stage, and time-window levels.
    """
    device: dict[str, RateBucket] = defaultdict(RateBucket)
    lot: dict[str, RateBucket] = defaultdict(RateBucket)
    wafer: dict[str, RateBucket] = defaultdict(RateBucket)
    pattern: dict[str, RateBucket] = defaultdict(RateBucket)
    bin_level: dict[str, RateBucket] = defaultdict(RateBucket)
    tester: dict[str, RateBucket] = defaultdict(RateBucket)
    product: dict[str, RateBucket] = defaultdict(RateBucket)
    stage: dict[str, RateBucket] = defaultdict(RateBucket)
    time_window: dict[str, RateBucket] = defaultdict(RateBucket)

    record_index = _index_records(test_records)

    for die in die_logs:
        is_fail = die.is_failing_die
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))

        _inc(device[die.device_name or "UNKNOWN"], is_fail)
        _inc(lot[die.lot_id], is_fail)
        _inc(wafer[die.wafer_id], is_fail)
        _inc(tester[die.tester_name or (rec.tester_id if rec else "UNKNOWN")], is_fail)
        _inc(product[die.device_name or (rec.product_id if rec else "UNKNOWN")], is_fail)
        stage_key = (rec.test_stage if rec else die.header_fields.get("TEST_STAGE", "UNKNOWN"))
        _inc(stage[stage_key], is_fail)
        tw = _time_window_key(rec.timestamp if rec else die.header_fields.get("TEST_DATE", ""))
        _inc(time_window[tw], is_fail)

        if rec and rec.hard_bin:
            _inc(bin_level[f"H{rec.hard_bin}"], is_fail)
        elif die.is_failing_die:
            _inc(bin_level["FAIL_UNKNOWN"], is_fail)
        else:
            _inc(bin_level["PASS"], is_fail)

        for pid, count in die.test_counts().items():
            pattern[pid].tested += count
        for fp in die.failing_patterns:
            pattern[fp.pattern_id].failed += 1

    wafer_rates = _serialize_buckets(
        wafer,
        extra=lambda k, _: {"lot_id": _lot_for_wafer(die_logs, k)},
    )
    lot_rates = _serialize_buckets(lot)
    alerts = _build_alerts(
        lot_rates=lot_rates,
        wafer_rates=wafer_rates,
        alert_threshold_pct=alert_threshold_pct,
    )
    trends = _compute_trend_signals(lot_rates, wafer_rates)

    aggregates = {
        "requirement": "FA-FR-003",
        "tolerance_pct": FAILURE_RATE_TOLERANCE_PCT,
        "formula": "failure_rate_pct = failed / tested × 100",
        "device_level": _serialize_buckets(device),
        "lot_level": lot_rates,
        "wafer_level": wafer_rates,
        "pattern_level": _serialize_pattern_buckets(pattern),
        "bin_level": _serialize_buckets(bin_level),
        "tester_level": _serialize_buckets(tester),
        "product_level": _serialize_buckets(product),
        "test_stage_level": _serialize_buckets(stage),
        "time_window_level": _serialize_buckets(time_window),
        "alerts": alerts,
        "trends": trends,
        "summary": {
            "total_dies_tested": len(die_logs),
            "total_failing_dies": sum(1 for d in die_logs if d.is_failing_die),
            "overall_failure_rate_pct": _overall_rate_pct(die_logs),
            "overall_pass_rate_pct": round(100.0 - _overall_rate_pct(die_logs), 6),
            "overall_yield_pct": round(100.0 - _overall_rate_pct(die_logs), 6),
        },
    }
    return aggregates


def verify_rates_against_reference(
    computed: dict[str, Any],
    reference: dict[str, Any],
    *,
    tolerance_pct: float = FAILURE_RATE_TOLERANCE_PCT,
    level: str = "lot_level",
) -> dict[str, Any]:
    """Verify computed rates match hand-computed reference within tolerance."""
    comp_level = computed.get(level, {})
    ref_level = reference.get(level, {})
    mismatches: list[dict[str, Any]] = []

    for key, ref_bucket in ref_level.items():
        comp_bucket = comp_level.get(key)
        if not comp_bucket:
            mismatches.append({"key": key, "error": "missing in computed"})
            continue
        ref_rate = ref_bucket.get("failure_rate_pct", ref_bucket.get("failure_rate", 0) * 100)
        comp_rate = comp_bucket.get("failure_rate_pct", 0)
        delta = abs(comp_rate - ref_rate)
        if delta > tolerance_pct:
            mismatches.append(
                {
                    "key": key,
                    "computed_pct": comp_rate,
                    "reference_pct": ref_rate,
                    "delta_pct": round(delta, 6),
                }
            )

    return {
        "passed": len(mismatches) == 0,
        "tolerance_pct": tolerance_pct,
        "level": level,
        "mismatches": mismatches,
    }


def persist_aggregates(aggregates: dict[str, Any], path: Path) -> None:
    """Persist rate aggregates for cross-lot recurrence and dashboards."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "persisted_at": datetime.utcnow().isoformat() + "Z",
        "aggregates": aggregates,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    logger.info("Persisted failure-rate aggregates to %s", path)


def _inc(bucket: RateBucket, failed: bool) -> None:
    bucket.tested += 1
    if failed:
        bucket.failed += 1


def _serialize_buckets(
    buckets: dict[str, RateBucket],
    *,
    extra: Any = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in sorted(buckets):
        data = buckets[key].to_dict()
        if extra:
            data.update(extra(key, buckets))
        result[key] = data
    return result


def _serialize_pattern_buckets(buckets: dict[str, RateBucket]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in sorted(buckets):
        bucket = buckets[key]
        result[key] = {
            **bucket.to_dict(),
            "failure_frequency_pct": bucket.failure_rate_pct,
        }
    return result


def _lot_for_wafer(die_logs: list[DieLog], wafer_id: str) -> str:
    for die in die_logs:
        if die.wafer_id == wafer_id:
            return die.lot_id
    return ""


def _overall_rate_pct(die_logs: list[DieLog]) -> float:
    if not die_logs:
        return 0.0
    failed = sum(1 for d in die_logs if d.is_failing_die)
    return round(100.0 * failed / len(die_logs), 6)


def _time_window_key(timestamp: str) -> str:
    if not timestamp:
        return "unknown"
    ts = timestamp.strip()
    if len(ts) >= 10:
        return ts[:10]
    return ts


def _index_records(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def _build_alerts(
    *,
    lot_rates: dict[str, Any],
    wafer_rates: dict[str, Any],
    alert_threshold_pct: float,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for lot_id, stats in lot_rates.items():
        rate = stats["failure_rate_pct"]
        if rate > alert_threshold_pct:
            alerts.append(
                {
                    "level": "lot",
                    "entity_id": lot_id,
                    "alert_type": "THRESHOLD_BREACH",
                    "current_failure_rate_pct": rate,
                    "threshold_pct": alert_threshold_pct,
                    "message": f"Lot {lot_id} failure rate {rate:.2f}% exceeds {alert_threshold_pct:.2f}%",
                }
            )

    for wafer_id, stats in wafer_rates.items():
        rate = stats["failure_rate_pct"]
        if rate > alert_threshold_pct:
            alerts.append(
                {
                    "level": "wafer",
                    "entity_id": wafer_id,
                    "lot_id": stats.get("lot_id", ""),
                    "alert_type": "THRESHOLD_BREACH",
                    "current_failure_rate_pct": rate,
                    "threshold_pct": alert_threshold_pct,
                    "message": (
                        f"Wafer {wafer_id} failure rate {rate:.2f}% exceeds "
                        f"{alert_threshold_pct:.2f}%"
                    ),
                }
            )

    alerts.extend(_control_limit_alerts(wafer_rates))
    return alerts


def _control_limit_alerts(wafer_rates: dict[str, Any]) -> list[dict[str, Any]]:
    """Flag wafers beyond lot sibling mean + 3σ (rolling control limit proxy)."""
    by_lot: dict[str, list[float]] = defaultdict(list)
    wafer_lot: dict[str, str] = {}
    for wafer_id, stats in wafer_rates.items():
        lot_id = stats.get("lot_id", "UNKNOWN")
        by_lot[lot_id].append(stats["failure_rate_pct"])
        wafer_lot[wafer_id] = lot_id

    alerts: list[dict[str, Any]] = []
    for wafer_id, stats in wafer_rates.items():
        lot_id = wafer_lot.get(wafer_id, "UNKNOWN")
        siblings = by_lot.get(lot_id, [])
        if len(siblings) < 3:
            continue
        mean = statistics.mean(siblings)
        stdev = statistics.pstdev(siblings)
        if stdev == 0:
            continue
        ucl = mean + CONTROL_LIMIT_SIGMA * stdev
        rate = stats["failure_rate_pct"]
        if rate > ucl:
            alerts.append(
                {
                    "level": "wafer",
                    "entity_id": wafer_id,
                    "lot_id": lot_id,
                    "alert_type": "CONTROL_LIMIT_3SIGMA",
                    "current_failure_rate_pct": rate,
                    "lot_mean_pct": round(mean, 4),
                    "upper_control_limit_pct": round(ucl, 4),
                    "message": (
                        f"Wafer {wafer_id} rate {rate:.2f}% exceeds 3σ UCL {ucl:.2f}% "
                        f"(lot mean {mean:.2f}%)"
                    ),
                }
            )
    return alerts


def _compute_trend_signals(
    lot_rates: dict[str, Any],
    wafer_rates: dict[str, Any],
) -> dict[str, Any]:
    lot_sorted = sorted(
        lot_rates.items(),
        key=lambda item: item[1]["failure_rate_pct"],
        reverse=True,
    )
    wafer_sorted = sorted(
        wafer_rates.items(),
        key=lambda item: item[1]["failure_rate_pct"],
        reverse=True,
    )
    return {
        "worst_lots": [
            {"lot_id": k, "failure_rate_pct": v["failure_rate_pct"]} for k, v in lot_sorted[:5]
        ],
        "worst_wafers": [
            {"wafer_id": k, "failure_rate_pct": v["failure_rate_pct"]} for k, v in wafer_sorted[:5]
        ],
        "control_limit_sigma": CONTROL_LIMIT_SIGMA,
    }
