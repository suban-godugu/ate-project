"""Deterministic statistical engine for FA-FR-006."""

from __future__ import annotations

import hashlib
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class CorrelationComputationError(ValueError):
    pass


@dataclass(frozen=True)
class CorrelationConfig:
    version: str
    algorithm: str
    coefficient_threshold: float
    strong_threshold: float
    very_strong_threshold: float
    min_confidence: float
    min_support: float
    significance_level: float
    min_sample_size: int
    high_impact_threshold: float
    trend_delta: float
    batch_size: int

    @classmethod
    def load(cls, path: str | Path | None = None) -> "CorrelationConfig":
        target = Path(path) if path else Path(__file__).resolve().parents[2] / "config" / "correlation.yaml"
        raw = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
        thresholds = raw.get("thresholds", {})
        return cls(
            version=str(raw.get("config_version", "correlation-v2.0")),
            algorithm=str(raw.get("algorithm", "phi_coefficient")),
            coefficient_threshold=float(thresholds.get("minimum_coefficient", 0.15)),
            strong_threshold=float(thresholds.get("strong", 0.5)),
            very_strong_threshold=float(thresholds.get("very_strong", 0.7)),
            min_confidence=float(thresholds.get("minimum_confidence", 0.6)),
            min_support=float(thresholds.get("minimum_support", 0.01)),
            significance_level=float(thresholds.get("significance_level", 0.05)),
            min_sample_size=int(thresholds.get("minimum_sample_size", 20)),
            high_impact_threshold=float(thresholds.get("high_impact", 0.55)),
            trend_delta=float(thresholds.get("trend_delta", 0.05)),
            batch_size=int(raw.get("batch_size", 10_000)),
        )


class ProductionCorrelationEngine:
    def __init__(self, config: CorrelationConfig) -> None:
        self.config = config

    def analyze(
        self,
        *,
        observations: list[dict[str, Any]],
        source_record_counts: dict[str, int],
        recurrences: list[dict[str, Any]],
        failure_rates: dict[str, float],
        analysis_id: str,
        current_execution_id: str | None = None,
    ) -> dict[str, Any]:
        if not observations or not recurrences:
            raise CorrelationComputationError("Correlation requires observations and FA-FR-005 recurrences")
        if any(value <= 0 for value in source_record_counts.values()):
            raise CorrelationComputationError("Every source execution requires a positive record count")

        executions = sorted(
            source_record_counts,
            key=lambda item: (item == current_execution_id, item),
        )
        pattern_records: dict[tuple[str, str], set[str]] = defaultdict(set)
        fault_records: dict[tuple[str, str], set[str]] = defaultdict(set)
        both_records: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        upstream_scores: dict[tuple[str, str], list[float]] = defaultdict(list)
        coordinates: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        scope_values: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        for row in observations:
            pattern_id = str(row.get("pattern_id", "")).strip()
            fault_type = str(row.get("fault_type", "")).strip()
            execution_id = str(row.get("execution_id", "")).strip()
            record_id = str(row.get("source_record_id", "")).strip()
            if not all((pattern_id, fault_type, execution_id, record_id)):
                raise CorrelationComputationError("Observations require pattern, fault, execution and source record IDs")
            scoped = f"{execution_id}:{record_id}"
            pattern_records[(execution_id, pattern_id)].add(scoped)
            fault_records[(execution_id, fault_type)].add(scoped)
            both_records[(execution_id, pattern_id, fault_type)].add(scoped)
            upstream_scores[(pattern_id, fault_type)].extend(
                [float(row.get("pattern_confidence", 0.0)), float(row.get("classification_confidence", 0.0))]
            )
            for dimension in (
                "device_id",
                "die_id",
                "wafer_id",
                "lot_id",
                "batch_id",
                "failure_code",
            ):
                value = str(row.get(dimension, "")).strip()
                if value:
                    scope_values[(pattern_id, fault_type)][dimension].add(value)
            if row.get("x") is not None and row.get("y") is not None:
                coordinates[(pattern_id, fault_type)].append(
                    {
                        "lot_id": str(row.get("lot_id", "")),
                        "wafer_id": str(row.get("wafer_id", "")),
                        "x": float(row["x"]),
                        "y": float(row["y"]),
                    }
                )

        recurrence_by_pair = {
            (str(item["pattern_id"]), str(item["fault_type"])): item for item in recurrences
        }
        results: list[dict[str, Any]] = []
        for (pattern_id, fault_type), recurrence in sorted(recurrence_by_pair.items()):
            series: list[dict[str, Any]] = []
            aggregate = [0, 0, 0, 0]
            for execution_id in executions:
                counts = _contingency(
                    pattern_records.get((execution_id, pattern_id), set()),
                    fault_records.get((execution_id, fault_type), set()),
                    both_records.get((execution_id, pattern_id, fault_type), set()),
                    source_record_counts[execution_id],
                )
                coefficient, p_value = _phi_and_p_value(*counts)
                aggregate = [left + right for left, right in zip(aggregate, counts)]
                series.append(
                    {
                        "execution_id": execution_id,
                        "coefficient": round(coefficient, 6),
                        "p_value": round(p_value, 8),
                        "sample_size": source_record_counts[execution_id],
                    }
                )
            coefficient, p_value = _phi_and_p_value(*aggregate)
            sample_size = sum(source_record_counts.values())
            support = aggregate[0] / max(1, sample_size)
            upstream = _mean(upstream_scores.get((pattern_id, fault_type), [0.0]))
            recurrence_confidence = float(recurrence.get("confidence_score", 0.0))
            statistical_confidence = max(0.0, min(1.0, 1.0 - p_value))
            sample_confidence = min(1.0, math.log1p(sample_size) / math.log1p(max(1000, sample_size)))
            confidence = (
                statistical_confidence * 0.35
                + upstream * 0.25
                + recurrence_confidence * 0.25
                + sample_confidence * 0.15
            )
            if (
                sample_size < self.config.min_sample_size
                or support < self.config.min_support
                or abs(coefficient) < self.config.coefficient_threshold
                or confidence < self.config.min_confidence
                or p_value > self.config.significance_level
            ):
                continue
            current = series[-1]["coefficient"]
            historical = _mean([item["coefficient"] for item in series[:-1]]) if len(series) > 1 else 0.0
            trend = _trend(current, historical, self.config.trend_delta)
            strength = _strength(abs(coefficient), self.config)
            failure_rate = float(failure_rates.get(pattern_id, 0.0)) / 100.0
            recurrence_frequency = float(recurrence.get("recurrence_frequency", 0.0))
            impact_score = min(
                1.0,
                abs(coefficient) * 0.40
                + confidence * 0.20
                + failure_rate * 0.20
                + recurrence_frequency * 0.20,
            )
            severity = _severity(impact_score)
            canonical = hashlib.sha256(f"{pattern_id.lower()}|{fault_type.lower()}".encode()).hexdigest()
            correlation_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{analysis_id}:{canonical}"))
            hotspot = _hotspot(coordinates.get((pattern_id, fault_type), []))
            recommendations = _recommendations(
                correlation_id, pattern_id, fault_type, strength, severity, trend, hotspot, coefficient
            )
            results.append(
                {
                    "correlation_id": correlation_id,
                    "canonical_correlation_key": canonical,
                    "recurrence_id": recurrence["recurrence_id"],
                    "pattern_id": pattern_id,
                    "fault_type": fault_type,
                    "correlated_failures": aggregate[0],
                    "correlation_coefficient": round(coefficient, 6),
                    "correlation_strength": strength,
                    "confidence_score": round(confidence, 6),
                    "p_value": round(p_value, 8),
                    "sample_size": sample_size,
                    "support": round(support, 6),
                    "impact_score": round(impact_score, 6),
                    "severity": severity,
                    "trend_status": trend,
                    "current_coefficient": current,
                    "historical_coefficient": round(historical, 6),
                    "time_series": series,
                    "hotspot_location": hotspot,
                    "engineering_recommendation": recommendations[0]["action"],
                    "recommendations": recommendations,
                    "source_execution_ids": executions,
                    "scope_breakdown": {
                        dimension: sorted(values)
                        for dimension, values in scope_values[
                            (pattern_id, fault_type)
                        ].items()
                    },
                    "contingency": {"both": aggregate[0], "pattern_only": aggregate[1], "fault_only": aggregate[2], "neither": aggregate[3]},
                }
            )
        results.sort(key=lambda item: (item["impact_score"], abs(item["correlation_coefficient"])), reverse=True)
        return {
            "correlations": results,
            "matrix": _matrix(results),
            "relationship_graph": _graph(results),
            "statistics": _statistics(results),
        }


def _contingency(pattern: set[str], fault: set[str], both: set[str], total: int) -> tuple[int, int, int, int]:
    a = len(both)
    b = max(0, len(pattern) - a)
    c = max(0, len(fault) - a)
    d = total - a - b - c
    if d < 0:
        raise CorrelationComputationError("Invalid contingency table: traceable records exceed source count")
    return a, b, c, d


def _phi_and_p_value(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    denominator = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    if denominator == 0:
        return 0.0, 1.0
    phi = ((a * d) - (b * c)) / denominator
    n = a + b + c + d
    chi_square = n * phi * phi
    return max(-1.0, min(1.0, phi)), math.erfc(math.sqrt(chi_square / 2.0))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _strength(value: float, config: CorrelationConfig) -> str:
    if value >= config.very_strong_threshold:
        return "very_strong"
    if value >= config.strong_threshold:
        return "strong"
    if value >= config.coefficient_threshold:
        return "moderate"
    return "weak"


def _trend(current: float, historical: float, delta: float) -> str:
    change = current - historical
    if change >= delta:
        return "increasing"
    if change <= -delta:
        return "decreasing"
    return "stable"


def _severity(impact: float) -> str:
    if impact >= 0.75:
        return "critical"
    if impact >= 0.55:
        return "high"
    if impact >= 0.35:
        return "medium"
    return "low"


def _hotspot(points: list[dict[str, Any]]) -> dict[str, Any]:
    if not points:
        return {}
    ordered = sorted(points, key=lambda item: (item["lot_id"], item["wafer_id"], item["x"], item["y"]))
    lots = {item["lot_id"] for item in ordered}
    wafers = {item["wafer_id"] for item in ordered}
    return {
        "lot_id": next(iter(lots)) if len(lots) == 1 else "MULTI",
        "wafer_id": next(iter(wafers)) if len(wafers) == 1 else "MULTI",
        "x": round(_mean([item["x"] for item in ordered]), 4),
        "y": round(_mean([item["y"] for item in ordered]), 4),
        "point_count": len(ordered),
        "coordinates": ordered[:500],
    }


def _recommendations(
    correlation_id: str,
    pattern_id: str,
    fault_type: str,
    strength: str,
    severity: str,
    trend: str,
    hotspot: dict[str, Any],
    coefficient: float,
) -> list[dict[str, Any]]:
    actions = [
        (
            "CORRELATED_PATTERN_CONTAINMENT",
            "critical" if severity == "critical" else "high",
            f"Prioritize containment and root-cause review for {pattern_id} / {fault_type}.",
            f"{strength} statistically significant association (coefficient {coefficient:.3f}).",
        )
    ]
    if trend == "increasing":
        actions.append(("ESCALATING_CORRELATION", "high", "Escalate process-window and equipment drift review.", "Correlation strength is increasing against its compatible historical baseline."))
    if hotspot:
        actions.append(("SPATIAL_HOTSPOT_REVIEW", "high", f"Inspect wafer {hotspot['wafer_id']} around ({hotspot['x']}, {hotspot['y']}).", "Correlated failures exhibit spatial concentration."))
    return [
        {
            "recommendation_id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"{correlation_id}:{code}")),
            "recommendation_code": code,
            "priority": priority,
            "action": action,
            "rationale": rationale,
            "evidence": {"coefficient": round(coefficient, 6), "trend": trend, "hotspot": hotspot},
        }
        for code, priority, action, rationale in actions
    ]


def _matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    patterns = sorted({row["pattern_id"] for row in rows})
    faults = sorted({row["fault_type"] for row in rows})
    values = {(row["fault_type"], row["pattern_id"]): row["correlation_coefficient"] for row in rows}
    return {
        "patterns": patterns,
        "fault_types": faults,
        "values": [[values.get((fault, pattern), 0.0) for pattern in patterns] for fault in faults],
    }


def _graph(rows: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges = []
    for row in rows:
        pattern_key = f"pattern:{row['pattern_id']}"
        fault_key = f"fault:{row['fault_type']}"
        nodes[pattern_key] = {"id": pattern_key, "label": row["pattern_id"], "type": "pattern"}
        nodes[fault_key] = {"id": fault_key, "label": row["fault_type"], "type": "fault"}
        edges.append({"source": pattern_key, "target": fault_key, "weight": abs(row["correlation_coefficient"]), "severity": row["severity"], "correlation_id": row["correlation_id"]})
    return {"nodes": sorted(nodes.values(), key=lambda item: item["id"]), "edges": edges}


def _statistics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "correlation_count": len(rows),
        "strong_count": sum(row["correlation_strength"] in {"strong", "very_strong"} for row in rows),
        "high_impact_count": sum(row["severity"] in {"high", "critical"} for row in rows),
        "mean_coefficient": round(_mean([abs(row["correlation_coefficient"]) for row in rows]), 6),
        "mean_confidence": round(_mean([row["confidence_score"] for row in rows]), 6),
    }
