"""Deterministic, explainable FA-FR-005 recurrence computation."""

from __future__ import annotations

import hashlib
import math
import statistics
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.yaml_config import load_adapter_configs

DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "config" / "recurrence_analysis.yaml"


class RecurrenceComputationError(ValueError):
    """Raised when recurrence metrics cannot be computed safely."""


@dataclass(frozen=True)
class RecurrenceConfig:
    version: str
    requirement: str
    require_fault_classification: bool
    require_same_tenant: bool
    require_product_overlap: bool
    require_test_stage_overlap: bool
    compatible_formula_prefix: str
    minimum_occurrences: int
    minimum_executions: int
    minimum_datasets: int
    similarity_threshold: float
    hotspot_radius: float
    hotspot_min_occurrences: int
    emerging_frequency: float
    trend_delta: float
    high_confidence: float
    critical_frequency: float
    weights: dict[str, float]
    recommendations: dict[str, str]

    @classmethod
    def load(cls, path: Path | str | None = None) -> "RecurrenceConfig":
        raw = load_adapter_configs(Path(path) if path else DEFAULT_CONFIG)
        minimum = dict(raw.get("minimum", {}))
        thresholds = dict(raw.get("thresholds", {}))
        upstream = dict(raw.get("upstream", {}))
        cohort = dict(raw.get("cohort", {}))
        weights = {str(k): float(v) for k, v in dict(raw.get("weights", {})).items()}
        if not weights or abs(sum(weights.values()) - 1.0) > 0.0001:
            raise RecurrenceComputationError("Recurrence confidence weights must sum to 1.0")
        config = cls(
            version=str(raw.get("config_version", "recurrence-v1.0")),
            requirement=str(raw.get("requirement", "FA-FR-005")),
            require_fault_classification=bool(
                upstream.get("require_fault_classification", True)
            ),
            require_same_tenant=bool(cohort.get("require_same_tenant", True)),
            require_product_overlap=bool(cohort.get("require_product_overlap", True)),
            require_test_stage_overlap=bool(
                cohort.get("require_test_stage_overlap", True)
            ),
            compatible_formula_prefix=str(
                cohort.get("compatible_formula_prefix", "failure-rate-v1")
            ),
            minimum_occurrences=int(minimum.get("occurrences", 2)),
            minimum_executions=int(minimum.get("distinct_executions", 2)),
            minimum_datasets=int(minimum.get("distinct_datasets", 2)),
            similarity_threshold=float(thresholds.get("similarity", 0.72)),
            hotspot_radius=float(thresholds.get("hotspot_radius", 1.5)),
            hotspot_min_occurrences=int(thresholds.get("hotspot_min_occurrences", 2)),
            emerging_frequency=float(thresholds.get("emerging_frequency", 0.02)),
            trend_delta=float(thresholds.get("trend_delta", 0.01)),
            high_confidence=float(thresholds.get("high_confidence", 0.85)),
            critical_frequency=float(thresholds.get("critical_frequency", 0.20)),
            weights=weights,
            recommendations={
                str(k): str(v) for k, v in dict(raw.get("recommendations", {})).items()
            },
        )
        if not 0.0 <= config.similarity_threshold <= 1.0:
            raise RecurrenceComputationError("Similarity threshold must be between 0 and 1")
        if config.minimum_occurrences < 2 or config.minimum_executions < 2:
            raise RecurrenceComputationError("Recurrence requires at least two occurrences and executions")
        if config.hotspot_radius < 0 or config.hotspot_min_occurrences < 2:
            raise RecurrenceComputationError("Invalid hotspot thresholds")
        return config


class ProductionRecurrenceEngine:
    def __init__(self, config: RecurrenceConfig | None = None) -> None:
        self.config = config or RecurrenceConfig.load()

    def analyze(
        self,
        *,
        observations: list[dict[str, Any]],
        current_execution_id: str,
        source_record_counts: dict[str, int],
        failure_rates: dict[str, float],
        incremental: bool,
    ) -> dict[str, Any]:
        if not observations:
            raise RecurrenceComputationError("No traceable pattern observations")
        current = [
            row for row in observations if str(row.get("execution_id")) == current_execution_id
        ]
        if not current:
            raise RecurrenceComputationError("Current detection execution has no observations")
        if not any(str(row.get("execution_id")) != current_execution_id for row in observations):
            raise RecurrenceComputationError(
                "Historical pattern execution data is required for recurrence analysis"
            )

        by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in observations:
            pattern_id = str(row.get("pattern_id", "")).strip()
            if not pattern_id:
                raise RecurrenceComputationError("Every observation requires a Pattern ID")
            fault_type = str(row.get("fault_type", "")).strip()
            if not fault_type:
                raise RecurrenceComputationError("Every observation requires a Fault Type")
            canonical = _canonical_key(row)
            by_signature[canonical].append(row)

        candidates: list[dict[str, Any]] = []
        for canonical_key, rows in by_signature.items():
            current_rows = [
                row for row in rows if str(row.get("execution_id")) == current_execution_id
            ]
            if not current_rows:
                continue
            pattern_id = str(current_rows[0]["pattern_id"])
            fault_type = str(current_rows[0]["fault_type"])
            execution_ids = sorted({str(row["execution_id"]) for row in rows})
            source_ids = sorted({str(row["source_id"]) for row in rows})
            if (
                len(rows) < self.config.minimum_occurrences
                or len(execution_ids) < self.config.minimum_executions
                or len(source_ids) < self.config.minimum_datasets
            ):
                continue
            frequencies = self._execution_frequencies(rows, source_record_counts)
            current_frequency = frequencies.get(current_execution_id, 0.0)
            historical_values = [
                value for key, value in frequencies.items() if key != current_execution_id
            ]
            historical_frequency = (
                statistics.mean(historical_values) if historical_values else 0.0
            )
            trend, newly_emerging = self._trend(
                current_frequency, historical_frequency, bool(historical_values)
            )
            coordinates = self._coordinates(rows)
            hotspots = self._hotspots(pattern_id, coordinates)
            rate = float(failure_rates.get(pattern_id, current_frequency * 100.0))
            confidence = self._confidence(
                rows=rows,
                executions=len(execution_ids),
                sources=len(source_ids),
                failure_rate_percentage=rate,
            )
            severity = self._severity(
                confidence=confidence,
                frequency=current_frequency,
                trend=trend,
                has_hotspot=bool(hotspots),
            )
            feature_tokens = self._feature_tokens(rows)
            signature = canonical_key
            timestamps = [_timestamp(row.get("timestamp")) for row in rows]
            timestamps = [item for item in timestamps if item is not None]
            if not timestamps:
                raise RecurrenceComputationError(
                    f"Pattern {pattern_id} has no valid occurrence timestamps"
                )
            recommendations = self._recommendations(
                trend=trend,
                newly_emerging=newly_emerging,
                has_hotspot=bool(hotspots),
                device_count=len({str(row.get("device_id", "")) for row in rows}),
                pattern_id=pattern_id,
                fault_type=fault_type,
            )
            candidates.append(
                {
                    "recurrence_id": str(uuid.uuid4()),
                    "detected_pattern_id": str(current_rows[0]["detected_pattern_id"]),
                    "classification_execution_id": str(
                        current_rows[0]["classification_execution_id"]
                    ),
                    "pattern_id": pattern_id,
                    "pattern_name": str(current_rows[0].get("pattern_name") or pattern_id),
                    "fault_type": fault_type,
                    "canonical_recurrence_key": canonical_key,
                    "signature_hash": signature,
                    "feature_tokens": feature_tokens,
                    "recurrence_count": len(rows),
                    "recurrence_frequency": round(current_frequency, 6),
                    "recurrence_percentage": round(current_frequency * 100.0, 6),
                    "confidence_score": round(confidence, 6),
                    "severity": severity,
                    "trend_direction": trend,
                    "first_occurrence": min(timestamps),
                    "latest_occurrence": max(timestamps),
                    "historical_frequency": round(historical_frequency, 6),
                    "hotspot_location": hotspots[0] if hotspots else {},
                    "engineering_recommendation": recommendations[0]["action"],
                    "recommendations": recommendations,
                    "incremental": incremental,
                    "source_execution_ids": execution_ids,
                    "source_ids": source_ids,
                    "affected_devices": sorted(
                        {str(row.get("device_id", "")) for row in rows if row.get("device_id")}
                    ),
                    "affected_dies": sorted(
                        {
                            f"{row.get('lot_id', '')}|{row.get('wafer_id', '')}|{row.get('die_id', '')}"
                            for row in rows
                            if row.get("die_id")
                        }
                    ),
                    "affected_wafers": sorted(
                        {
                            f"{row.get('lot_id', '')}|{row.get('wafer_id', '')}"
                            for row in rows
                            if row.get("wafer_id")
                        }
                    ),
                    "affected_lots": sorted(
                        {str(row.get("lot_id", "")) for row in rows if row.get("lot_id")}
                    ),
                    "affected_batches": source_ids,
                    "time_series": [
                        {
                            "execution_id": key,
                            "frequency": round(value, 6),
                            "is_current": key == current_execution_id,
                        }
                        for key, value in sorted(frequencies.items())
                    ],
                    "newly_emerging": newly_emerging,
                    "hotspots": hotspots,
                    "current_occurrence_count": len(current_rows),
                }
            )

        self._assign_similarity_groups(candidates)
        candidates.sort(
            key=lambda row: (
                _severity_rank(str(row["severity"])),
                float(row["confidence_score"]),
                int(row["recurrence_count"]),
            ),
            reverse=True,
        )
        return {
            "recurrences": candidates,
            "statistics": self._statistics(candidates),
            "hotspots": [
                {**hotspot, "recurrence_id": row["recurrence_id"]}
                for row in candidates
                for hotspot in row["hotspots"]
            ],
        }

    def _execution_frequencies(
        self,
        rows: list[dict[str, Any]],
        source_record_counts: dict[str, int],
    ) -> dict[str, float]:
        unique: dict[str, set[str]] = defaultdict(set)
        for row in rows:
            unique[str(row["execution_id"])].add(str(row["source_record_id"]))
        return {
            execution_id: len(unique.get(execution_id, set()))
            / max(1, int(record_count))
            for execution_id, record_count in source_record_counts.items()
        }

    def _trend(
        self, current: float, historical: float, has_history: bool
    ) -> tuple[str, bool]:
        newly_emerging = has_history and historical == 0 and current >= self.config.emerging_frequency
        if newly_emerging:
            return "emerging", True
        delta = current - historical
        if delta >= self.config.trend_delta:
            return "increasing", False
        if delta <= -self.config.trend_delta:
            return "decreasing", False
        return "stable", False

    def _confidence(
        self,
        *,
        rows: list[dict[str, Any]],
        executions: int,
        sources: int,
        failure_rate_percentage: float,
    ) -> float:
        occurrence_score = min(1.0, len(rows) / (self.config.minimum_occurrences * 3))
        execution_score = min(1.0, executions / max(3, self.config.minimum_executions))
        dataset_score = min(1.0, sources / max(3, self.config.minimum_datasets))
        source_score = statistics.mean(
            (
                max(0.0, min(1.0, float(row.get("pattern_confidence", 0.0))))
                + max(
                    0.0,
                    min(1.0, float(row.get("classification_confidence", 0.0))),
                )
            )
            / 2.0
            for row in rows
        )
        rate_score = min(
            1.0,
            max(0.0, failure_rate_percentage / max(1.0, self.config.critical_frequency * 100)),
        )
        values = {
            "occurrence": occurrence_score,
            "execution_coverage": execution_score,
            "dataset_coverage": dataset_score,
            "source_confidence": source_score,
            "failure_rate": rate_score,
        }
        return sum(self.config.weights[key] * values[key] for key in self.config.weights)

    def _coordinates(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        coordinates = []
        for row in rows:
            if row.get("x") is None or row.get("y") is None:
                continue
            coordinates.append(
                {
                    "x": int(row["x"]),
                    "y": int(row["y"]),
                    "lot_id": str(row.get("lot_id") or ""),
                    "wafer_id": str(row.get("wafer_id") or ""),
                    "source_id": str(row.get("source_id") or ""),
                }
            )
        return coordinates

    def _hotspots(
        self, pattern_id: str, coordinates: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        clusters: list[dict[str, Any]] = []
        for point in sorted(
            coordinates,
            key=lambda item: (
                item["x"],
                item["y"],
                item["source_id"],
                item["lot_id"],
                item["wafer_id"],
            ),
        ):
            for cluster in clusters:
                cx = cluster["sum_x"] / cluster["count"]
                cy = cluster["sum_y"] / cluster["count"]
                if math.dist((point["x"], point["y"]), (cx, cy)) <= self.config.hotspot_radius:
                    cluster["points"].append(point)
                    cluster["sum_x"] += point["x"]
                    cluster["sum_y"] += point["y"]
                    cluster["count"] += 1
                    break
            else:
                clusters.append(
                    {
                        "points": [point],
                        "sum_x": point["x"],
                        "sum_y": point["y"],
                        "count": 1,
                    }
                )
        hotspots = []
        for cluster in clusters:
            points = cluster["points"]
            distinct_wafers = {
                f"{item['source_id']}|{item['lot_id']}|{item['wafer_id']}" for item in points
            }
            if (
                len(points) < self.config.hotspot_min_occurrences
                or len(distinct_wafers) < 2
            ):
                continue
            cx = cluster["sum_x"] / cluster["count"]
            cy = cluster["sum_y"] / cluster["count"]
            max_distance = max(
                (math.dist((item["x"], item["y"]), (cx, cy)) for item in points),
                default=0.0,
            )
            density = len(points) / max(1.0, math.pi * max(1.0, max_distance) ** 2)
            lot_ids = sorted({item["lot_id"] for item in points if item["lot_id"]})
            wafer_ids = sorted(
                {
                    f"{item['lot_id']}|{item['wafer_id']}"
                    for item in points
                    if item["wafer_id"]
                }
            )
            hotspots.append(
                {
                    "hotspot_id": str(uuid.uuid4()),
                    "pattern_id": pattern_id,
                    "lot_id": lot_ids[0] if len(lot_ids) == 1 else "MULTI",
                    "wafer_id": wafer_ids[0] if len(wafer_ids) == 1 else "MULTI",
                    "x": round(cx),
                    "y": round(cy),
                    "radius": round(max_distance, 4),
                    "occurrence_count": len(points),
                    "density": round(density, 6),
                    "confidence_score": round(
                        min(1.0, len(distinct_wafers) / 4 + len(points) / 12), 6
                    ),
                    "severity": "critical" if len(points) >= 5 else "high",
                    "coordinates": points[:2000],
                }
            )
        hotspots.sort(key=lambda row: int(row["occurrence_count"]), reverse=True)
        return hotspots

    def _feature_tokens(self, rows: list[dict[str, Any]]) -> set[str]:
        tokens: set[str] = set()
        for key in (
            "fault_type",
            "failure_category",
            "failure_code",
            "device_id",
            "test_program",
        ):
            for value in {str(row.get(key, "")).strip().lower() for row in rows}:
                if value:
                    tokens.add(f"{key}:{value}")
        return tokens

    def _assign_similarity_groups(self, candidates: list[dict[str, Any]]) -> None:
        parents = list(range(len(candidates)))

        def root(index: int) -> int:
            while parents[index] != index:
                parents[index] = parents[parents[index]]
                index = parents[index]
            return index

        def union(left: int, right: int) -> None:
            left_root, right_root = root(left), root(right)
            if left_root != right_root:
                parents[max(left_root, right_root)] = min(left_root, right_root)

        for left_index, left in enumerate(candidates):
            for right_index in range(left_index + 1, len(candidates)):
                right = candidates[right_index]
                score = _jaccard(
                    set(left["feature_tokens"]),
                    set(right["feature_tokens"]),
                )
                if score >= self.config.similarity_threshold:
                    union(left_index, right_index)
        group_ids: dict[int, str] = {}
        for index, row in enumerate(candidates):
            component = root(index)
            if component not in group_ids:
                component_keys = sorted(
                    str(candidates[item]["canonical_recurrence_key"])
                    for item in range(len(candidates))
                    if root(item) == component
                )
                group_ids[component] = hashlib.sha256(
                    "|".join(component_keys).encode("utf-8")
                ).hexdigest()[:16]
            row["similarity_group"] = group_ids[component]
            row["feature_tokens"] = sorted(row["feature_tokens"])

    def _severity(
        self, *, confidence: float, frequency: float, trend: str, has_hotspot: bool
    ) -> str:
        if (
            frequency >= self.config.critical_frequency
            or (confidence >= self.config.high_confidence and (has_hotspot or trend == "increasing"))
        ):
            return "critical"
        if confidence >= 0.70 or trend in {"increasing", "emerging"} or has_hotspot:
            return "high"
        if confidence >= 0.50:
            return "medium"
        return "low"

    def _recommendations(
        self,
        *,
        trend: str,
        newly_emerging: bool,
        has_hotspot: bool,
        device_count: int,
        pattern_id: str,
        fault_type: str,
    ) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []
        if newly_emerging:
            recommendations.append(
                self._recommendation_row(
                    "EMERGING_CONTAINMENT",
                    "CRITICAL",
                    self.config.recommendations.get("emerging", ""),
                    pattern_id,
                    fault_type,
                )
            )
        if has_hotspot:
            recommendations.append(
                self._recommendation_row(
                    "SPATIAL_DIAGNOSTIC",
                    "HIGH",
                    self.config.recommendations.get("hotspot", ""),
                    pattern_id,
                    fault_type,
                )
            )
        if trend == "increasing":
            recommendations.append(
                self._recommendation_row(
                    "TREND_ESCALATION",
                    "HIGH",
                    self.config.recommendations.get("worsening", ""),
                    pattern_id,
                    fault_type,
                )
            )
        if device_count > 1:
            recommendations.append(
                self._recommendation_row(
                    "CROSS_DEVICE_CORRELATION",
                    "MEDIUM",
                    self.config.recommendations.get("device", ""),
                    pattern_id,
                    fault_type,
                )
            )
        if not recommendations:
            recommendations.append(
                self._recommendation_row(
                    "PERSISTENCE_MONITORING",
                    "LOW",
                    self.config.recommendations.get("stable", ""),
                    pattern_id,
                    fault_type,
                )
            )
        return recommendations

    def _recommendation_row(
        self,
        code: str,
        priority: str,
        action: str,
        pattern_id: str,
        fault_type: str,
    ) -> dict[str, Any]:
        return {
            "recommendation_id": str(uuid.uuid4()),
            "recommendation_code": code,
            "priority": priority,
            "action": action,
            "rationale": (
                f"Rule {code} matched recurring pattern {pattern_id} "
                f"classified as {fault_type}."
            ),
            "evidence": {"pattern_id": pattern_id, "fault_type": fault_type},
        }

    def _statistics(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not rows:
            return []
        scopes: dict[tuple[str, str], list[dict[str, Any]]] = {
            ("global", "all"): rows
        }
        for row in rows:
            for scope_type, key_name in (
                ("pattern", "pattern_id"),
                ("device", "affected_devices"),
                ("die", "affected_dies"),
                ("wafer", "affected_wafers"),
                ("lot", "affected_lots"),
                ("batch", "affected_batches"),
            ):
                values = row[key_name] if isinstance(row[key_name], list) else [row[key_name]]
                for value in values:
                    scopes.setdefault((scope_type, str(value)), []).append(row)
        return [
            {
                "scope_type": scope_type,
                "scope_key": scope_key,
                "pattern_count": len({str(row["pattern_id"]) for row in group}),
                "recurrence_count": sum(int(row["recurrence_count"]) for row in group),
                "mean_frequency": round(
                    statistics.mean(float(row["recurrence_frequency"]) for row in group), 6
                ),
                "mean_confidence": round(
                    statistics.mean(float(row["confidence_score"]) for row in group), 6
                ),
                "hotspot_count": sum(len(row["hotspots"]) for row in group),
            }
            for (scope_type, scope_key), group in scopes.items()
            if scope_key
        ]


def _timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _canonical_key(row: dict[str, Any]) -> str:
    stable = "|".join(
        (
            str(row.get("pattern_id", "")).strip().lower(),
            str(row.get("fault_type", "")).strip().lower(),
            str(row.get("failure_category", "")).strip().lower(),
            str(row.get("test_stage", row.get("test_program", ""))).strip().lower(),
        )
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left and not right:
        return 0.0
    return len(left & right) / len(left | right)


def _severity_rank(value: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(value, 0)
