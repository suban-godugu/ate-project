"""FA-FR-006: Multi-factor failure-to-pattern correlation engine."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.yaml_config import load_adapter_configs
from fault_classifier import classify_fault_type
from ingestor import DieLog

DEFAULT_WEIGHTS_PATH = (
    Path(__file__).resolve().parent / "config" / "correlation_weights.yaml"
)


@dataclass
class CorrelationWeights:
    high_risk_threshold: float
    weights: dict[str, float]
    ranking_method: str

    @classmethod
    def load(cls, path: Path | None = None) -> CorrelationWeights:
        raw = load_adapter_configs(path or DEFAULT_WEIGHTS_PATH)
        weights = {str(k): float(v) for k, v in dict(raw.get("weights", {})).items()}
        total = sum(weights.values()) or 1.0
        normalized = {k: round(v / total, 6) for k, v in weights.items()}
        return cls(
            high_risk_threshold=float(raw.get("high_risk_threshold", 0.75)),
            weights=normalized,
            ranking_method=str(raw.get("ranking_method", "")).strip(),
        )


def correlate_failures_with_patterns(
    die_logs: list[DieLog],
    pattern_rates: dict[str, Any] | None = None,
    *,
    test_records: list[TestRecord] | None = None,
    recurring_failures: dict[str, Any] | None = None,
    weights_path: Path | None = None,
    top_n: int = 50,
) -> dict[str, Any]:
    """Rank patterns using multi-factor correlation beyond raw failure frequency."""
    config = CorrelationWeights.load(weights_path)
    if pattern_rates is None:
        pattern_rates = calculate_pattern_level_failure_rates(die_logs)

    if not pattern_rates:
        return _empty_report(config)

    record_index = _index_records(test_records)
    pattern_meta = _collect_pattern_meta(die_logs, record_index)
    recurrence_scores = _recurrence_scores(recurring_failures)
    baseline = _baseline_rate(pattern_rates)
    max_lot_spread = max((len(meta.get("lots", set())) for meta in pattern_meta.values()), default=1)
    max_wafer_spread = max((len(meta.get("wafers", set())) for meta in pattern_meta.values()), default=1)

    correlation_report: list[dict[str, Any]] = []
    for pattern_id, stats in pattern_rates.items():
        row = _score_pattern(
            pattern_id=pattern_id,
            stats=stats,
            meta=pattern_meta.get(pattern_id, {}),
            baseline=baseline,
            recurrence_score=recurrence_scores.get(pattern_id, 0.0),
            config=config,
            max_lot_spread=max_lot_spread,
            max_wafer_spread=max_wafer_spread,
        )
        correlation_report.append(row)

    correlation_report.sort(
        key=lambda item: (item["correlation_score"], item["failures"]),
        reverse=True,
    )
    top_patterns = correlation_report[:top_n]

    return {
        "manifest_source": str(weights_path or DEFAULT_WEIGHTS_PATH),
        "baseline_failure_rate": round(baseline, 6),
        "high_risk_threshold": config.high_risk_threshold,
        "ranking_method": config.ranking_method
        or _default_ranking_method(config.weights),
        "weights": config.weights,
        "correlation_report": top_patterns,
        "correlation_report_total": len(correlation_report),
        "top_failing_patterns": [
            {
                "rank": idx + 1,
                "pattern_id": item["pattern_id"],
                "correlation_score": item["correlation_score"],
                "failure_rate": item["failure_rate"],
                "status": item["status"],
            }
            for idx, item in enumerate(top_patterns[:20])
        ],
        "engineering_recommendations": _recommendations(top_patterns, config),
        "downstream_export": _downstream_export(top_patterns, config),
    }


def calculate_pattern_level_failure_rates(die_logs: list[DieLog]) -> dict[str, Any]:
    """Frequency of pattern failures across dies and executions."""
    pattern_failures: Counter[str] = Counter()
    pattern_tests: Counter[str] = Counter()
    execution_totals: Counter[str] = Counter()

    for die in die_logs:
        for pattern_id, count in die.test_counts().items():
            pattern_tests[pattern_id] += 1
            execution_totals[pattern_id] += count
        for pattern in die.failing_patterns:
            pattern_failures[pattern.pattern_id] += 1

    results: dict[str, Any] = {}
    for pattern_id in sorted(pattern_tests.keys()):
        failures = pattern_failures[pattern_id]
        tested = pattern_tests[pattern_id]
        executions = execution_totals[pattern_id]
        results[pattern_id] = {
            "failure_count": failures,
            "dies_tested": tested,
            "execution_count": executions,
            "failure_frequency": _safe_rate(failures, tested),
            "normalized_failure_rate": _safe_rate(failures, executions),
        }
    return results


def _score_pattern(
    *,
    pattern_id: str,
    stats: dict[str, Any],
    meta: dict[str, Any],
    baseline: float,
    recurrence_score: float,
    config: CorrelationWeights,
    max_lot_spread: int = 1,
    max_wafer_spread: int = 1,
) -> dict[str, Any]:
    failures = int(stats["failure_count"])
    tested = int(stats["dies_tested"])
    executions = int(stats.get("execution_count", tested))
    rate = float(stats["failure_frequency"])
    normalized_rate = float(stats.get("normalized_failure_rate", _safe_rate(failures, executions)))

    frequency_score = min(rate / baseline, 1.0) if baseline > 0 else 0.0
    normalized_rate_score = min(normalized_rate / baseline, 1.0) if baseline > 0 else normalized_rate
    uniqueness_score = _uniqueness_score(meta)
    lift_score = _co_failure_lift_score(meta)
    spatial_score, spatial_handoff = _spatial_concentration(meta)

    factor_scores = {
        "failure_frequency": round(frequency_score, 4),
        "normalized_failure_rate": round(normalized_rate_score, 4),
        "uniqueness": round(uniqueness_score, 4),
        "co_failure_lift": round(lift_score, 4),
        "spatial_concentration": round(spatial_score, 4),
        "cross_lot_persistence": round(recurrence_score, 4),
    }
    factor_contributions = {
        factor: round(config.weights.get(factor, 0.0) * score, 4)
        for factor, score in factor_scores.items()
    }
    correlation_score = round(sum(factor_contributions.values()), 4)
    status = (
        "HIGH_RISK"
        if correlation_score >= config.high_risk_threshold
        else "NORMAL"
    )

    top_chain = ""
    top_fault = ""
    if meta.get("scan_chains"):
        top_chain = meta["scan_chains"].most_common(1)[0][0]
    if meta.get("fault_categories"):
        top_fault = meta["fault_categories"].most_common(1)[0][0]

    lot_count = len(meta.get("lots", set()))
    wafer_count = len(meta.get("wafers", set()))

    return {
        "pattern_id": pattern_id,
        "executions": executions,
        "failures": failures,
        "failure_rate": round(rate, 6),
        "normalized_failure_rate": round(normalized_rate, 6),
        "correlation_score": correlation_score,
        "status": status,
        "factor_scores": factor_scores,
        "factor_contributions": factor_contributions,
        "frequency_score": factor_scores["failure_frequency"],
        "lot_spread_score": round(lot_count / max_lot_spread, 4) if max_lot_spread else 0.0,
        "wafer_spread_score": round(wafer_count / max_wafer_spread, 4) if max_wafer_spread else 0.0,
        "scan_chain_id": top_chain,
        "primary_fault_category": top_fault,
        "affected_lots": lot_count,
        "affected_wafers": wafer_count,
        "spatial_ai_handoff": spatial_handoff,
    }


def _collect_pattern_meta(
    die_logs: list[DieLog],
    record_index: dict[tuple[str, str, str], TestRecord],
) -> dict[str, dict[str, Any]]:
    meta: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "scan_chains": Counter(),
            "fault_categories": Counter(),
            "lots": set(),
            "wafers": set(),
            "dies": set(),
            "die_pattern_counts": Counter(),
            "bins": Counter(),
            "coordinates": [],
        }
    )

    for die in die_logs:
        failing_ids = [p.pattern_id for p in die.failing_patterns]
        die_pattern_count = len(set(failing_ids))
        rec = record_index.get((die.lot_id, die.wafer_id, die.die_id))
        hard_bin = _hard_bin(die, rec)
        x, y = _die_xy(die, rec)

        for pattern in die.failing_patterns:
            row = meta[pattern.pattern_id]
            row["lots"].add(die.lot_id)
            row["wafers"].add(die.wafer_id)
            row["dies"].add((die.lot_id, die.wafer_id, die.die_id))
            row["die_pattern_counts"][die_pattern_count] += 1
            if hard_bin:
                row["bins"][hard_bin] += 1
            if x is not None and y is not None:
                row["coordinates"].append((x, y, die.lot_id, die.wafer_id))
            if pattern.scan_chain_id:
                row["scan_chains"][pattern.scan_chain_id] += 1
            row["fault_categories"][classify_fault_type(pattern)] += 1

    return meta


def _uniqueness_score(meta: dict[str, Any]) -> float:
    counts = meta.get("die_pattern_counts", Counter())
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    unique_only = counts.get(1, 0)
    return min(1.0, unique_only / total)


def _co_failure_lift_score(meta: dict[str, Any]) -> float:
    bins = meta.get("bins", Counter())
    failures = sum(bins.values())
    if failures <= 0 or not bins:
        return 0.0

    lifts: list[float] = []
    total_bin_failures = sum(bins.values())
    for bin_id, count in bins.items():
        observed = count / failures
        expected = total_bin_failures / max(len(bins), 1) / failures
        if expected <= 0:
            continue
        lift = observed / expected
        chi_component = ((count - expected * failures) ** 2) / max(expected * failures, 1e-6)
        combined = min(1.0, (lift / 3.0) * 0.6 + min(1.0, chi_component / 4.0) * 0.4)
        lifts.append(combined)
    return round(max(lifts) if lifts else 0.0, 4)


def _spatial_concentration(meta: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    coords = meta.get("coordinates", [])
    if len(coords) < 2:
        return 0.0, {"status": "insufficient_coordinates", "points": len(coords)}

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    variance = sum((x - mean_x) ** 2 + (y - mean_y) ** 2 for x, y in zip(xs, ys)) / len(coords)
    spread = math.sqrt(variance)
    unique_positions = len({(x, y) for x, y in zip(xs, ys)})
    concentration = 1.0 - min(1.0, spread / max(spread, unique_positions))
    if unique_positions == 1:
        concentration = 1.0
    elif unique_positions < len(coords):
        concentration = max(concentration, 1.0 - (unique_positions / len(coords)))

    handoff = {
        "status": "ready",
        "centroid": {"x": round(mean_x, 3), "y": round(mean_y, 3)},
        "point_count": len(coords),
        "unique_positions": unique_positions,
        "spread": round(spread, 3),
        "points": [
            {"x": x, "y": y, "lot_id": lot, "wafer_id": wafer}
            for x, y, lot, wafer in coords[:50]
        ],
        "agent": "Spatial AI Agent",
    }
    return round(min(1.0, concentration), 4), handoff


def _recurrence_scores(recurring_failures: dict[str, Any] | None) -> dict[str, float]:
    if not recurring_failures:
        return {}
    scores: dict[str, float] = {}
    for event in recurring_failures.get("recurrence_events", []):
        if event.get("signature_type") != "pattern_recurrence":
            continue
        pattern_id = str(event.get("entity_key", ""))
        confidence = float(event.get("confidence", 0.0))
        scores[pattern_id] = max(scores.get(pattern_id, 0.0), confidence)
    for row in recurring_failures.get("recurring_failures", []):
        pattern_id = str(row.get("pattern_id", ""))
        lot_count = int(row.get("lot_count", row.get("entity_count", 0)))
        scores[pattern_id] = max(scores.get(pattern_id, 0.0), min(1.0, lot_count / 3.0))
    return scores


def _recommendations(
    top_patterns: list[dict[str, Any]],
    config: CorrelationWeights,
) -> list[str]:
    if not top_patterns:
        return []
    leader = top_patterns[0]
    recommendations = [
        (
            f"Pattern {leader['pattern_id']} has the highest composite correlation score "
            f"({leader['correlation_score']:.2f}) with dominant factor "
            f"{_top_factor(leader)}."
        )
    ]
    if leader.get("scan_chain_id"):
        recommendations.append(f"Inspect scan chain: {leader['scan_chain_id']}")
    if leader.get("primary_fault_category"):
        recommendations.append(
            f"Review {leader['primary_fault_category']} constraints for pattern "
            f"{leader['pattern_id']}."
        )
    high_risk = [p for p in top_patterns if p["status"] == "HIGH_RISK"]
    if high_risk:
        recommendations.append(
            f"{len(high_risk)} pattern(s) exceed the HIGH_RISK threshold "
            f"({config.high_risk_threshold})."
        )
    spatial = leader.get("spatial_ai_handoff", {})
    if spatial.get("status") == "ready" and leader["factor_scores"]["spatial_concentration"] >= 0.5:
        recommendations.append(
            "Spatial concentration detected — hand off to Spatial AI Agent for wafer-map overlay."
        )
    return recommendations


def _downstream_export(
    top_patterns: list[dict[str, Any]],
    config: CorrelationWeights,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "requirement": "FA-FR-006",
        "ranking_weights": config.weights,
        "patterns": [
            {
                "pattern_id": item["pattern_id"],
                "correlation_score": item["correlation_score"],
                "status": item["status"],
                "factor_scores": item["factor_scores"],
                "factor_contributions": item["factor_contributions"],
                "spatial_ai_handoff": item.get("spatial_ai_handoff", {}),
            }
            for item in top_patterns
        ],
    }


def _top_factor(row: dict[str, Any]) -> str:
    contributions = row.get("factor_contributions", {})
    if not contributions:
        return "failure_frequency"
    return max(contributions, key=lambda key: contributions[key])


def _baseline_rate(pattern_rates: dict[str, Any]) -> float:
    rates = [float(stats["failure_frequency"]) for stats in pattern_rates.values()]
    return sum(rates) / len(rates) if rates else 0.0


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _index_records(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index


def _hard_bin(die: DieLog, rec: TestRecord | None) -> str:
    if rec and rec.hard_bin:
        return str(rec.hard_bin)
    for key in ("HARD_BIN", "hard_bin", "BIN"):
        value = die.header_fields.get(key)
        if value:
            return str(value)
    return ""


def _die_xy(die: DieLog, rec: TestRecord | None) -> tuple[int | None, int | None]:
    if rec and rec.x is not None and rec.y is not None:
        return rec.x, rec.y
    x_raw = die.header_fields.get("DIE_X") or die.header_fields.get("X")
    y_raw = die.header_fields.get("DIE_Y") or die.header_fields.get("Y")
    try:
        x = int(x_raw) if x_raw not in (None, "") else None
        y = int(y_raw) if y_raw not in (None, "") else None
        return x, y
    except (TypeError, ValueError):
        return None, None


def _default_ranking_method(weights: dict[str, float]) -> str:
    parts = [f"{value:.0%} x {key}" for key, value in weights.items()]
    return "Composite correlation score = " + " + ".join(parts)


def _empty_report(config: CorrelationWeights) -> dict[str, Any]:
    return {
        "manifest_source": str(DEFAULT_WEIGHTS_PATH),
        "baseline_failure_rate": 0.0,
        "high_risk_threshold": config.high_risk_threshold,
        "ranking_method": config.ranking_method or _default_ranking_method(config.weights),
        "weights": config.weights,
        "correlation_report": [],
        "correlation_report_total": 0,
        "top_failing_patterns": [],
        "engineering_recommendations": [],
        "downstream_export": {
            "schema_version": "1.0",
            "requirement": "FA-FR-006",
            "ranking_weights": config.weights,
            "patterns": [],
        },
    }
