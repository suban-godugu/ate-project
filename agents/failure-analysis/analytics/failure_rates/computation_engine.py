"""Deterministic, versioned failure-rate calculations for FA-FR-003."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adapters.yaml_config import load_adapter_configs

DEFAULT_CONFIG = (
    Path(__file__).resolve().parents[2] / "config" / "failure_rate_computation.yaml"
)


class FailureRateComputationError(ValueError):
    """Raised when a mathematically invalid computation is requested."""


@dataclass(frozen=True)
class Threshold:
    key: str
    version: str
    warning: float
    critical: float
    abnormal_delta: float
    pattern_id: str | None = None
    aggregation_level: str | None = None


@dataclass(frozen=True)
class ComputationConfig:
    schema_version: str
    formula_version: str
    window_size: int
    aggregation_levels: tuple[str, ...]
    thresholds: tuple[Threshold, ...]

    @classmethod
    def load(cls, path: Path | None = None) -> "ComputationConfig":
        raw = load_adapter_configs(path or DEFAULT_CONFIG)
        if str(raw.get("schema_version")) != "1.0":
            raise FailureRateComputationError("Unsupported computation schema version")
        thresholds: list[Threshold] = []
        for item in raw.get("thresholds", []):
            warning = float(item["warning_percentage"])
            critical = float(item["critical_percentage"])
            abnormal = float(item["abnormal_delta_percentage"])
            if not 0 <= warning <= critical <= 100 or not 0 <= abnormal <= 100:
                raise FailureRateComputationError(
                    f"Invalid threshold configuration: {item.get('configuration_key')}"
                )
            thresholds.append(
                Threshold(
                    key=str(item["configuration_key"]),
                    version=str(item["version"]),
                    warning=warning,
                    critical=critical,
                    abnormal_delta=abnormal,
                    pattern_id=item.get("pattern_id"),
                    aggregation_level=item.get("aggregation_level"),
                )
            )
        return cls(
            schema_version="1.0",
            formula_version=str(raw["formula_version"]),
            window_size=int(raw.get("default_window_size", 5)),
            aggregation_levels=tuple(raw.get("default_aggregation_levels", [])),
            thresholds=tuple(thresholds),
        )


class FailureRateComputationEngine:
    """Compute pattern metrics using unique normalized source records."""

    def __init__(self, config: ComputationConfig | None = None) -> None:
        self.config = config or ComputationConfig.load()

    def compute(
        self,
        *,
        records: list[dict[str, Any]],
        patterns: list[dict[str, Any]],
        occurrences: list[dict[str, Any]],
        aggregation_levels: list[str],
        baselines: dict[tuple[str, str, str], list[dict[str, Any]]],
        batch_key: str,
        window_size: int,
    ) -> list[dict[str, Any]]:
        if not records:
            raise FailureRateComputationError("Cannot compute rates for an empty dataset")
        record_by_key = {str(row["record_key"]): row for row in records}
        if len(record_by_key) != len(records):
            raise FailureRateComputationError("Duplicate normalized record keys detected")
        patterns_by_id = {str(row["id"]): row for row in patterns}
        if not patterns_by_id:
            raise FailureRateComputationError(
                "No completed FA-FR-002 detected patterns are available"
            )
        occurrence_keys: dict[str, set[str]] = {}
        for occurrence in occurrences:
            detected_id = str(occurrence["detected_pattern_id"])
            source_key = str(occurrence["source_record_id"])
            if detected_id not in patterns_by_id:
                raise FailureRateComputationError(
                    f"Occurrence references unknown detected pattern {detected_id}"
                )
            if source_key not in record_by_key:
                raise FailureRateComputationError(
                    f"Occurrence source record is not present: {source_key}"
                )
            occurrence_keys.setdefault(detected_id, set()).add(source_key)

        groups = _build_groups(records, aggregation_levels, batch_key)
        total_pattern_failures = sum(len(keys) for keys in occurrence_keys.values()) or 1
        metrics: list[dict[str, Any]] = []
        for detected_id, pattern in patterns_by_id.items():
            failed_keys = occurrence_keys.get(detected_id, set())
            if not failed_keys:
                raise FailureRateComputationError(
                    f"Detected pattern {detected_id} has no traceable occurrences"
                )
            for level in aggregation_levels:
                candidate_groups = groups[level]
                for group_key, source_keys in candidate_groups.items():
                    failed = len(failed_keys & source_keys)
                    if level != "pattern" and failed == 0:
                        continue
                    total = len(source_keys)
                    if total <= 0 or failed > total:
                        raise FailureRateComputationError(
                            f"Invalid counts for {level}/{group_key}: {failed}/{total}"
                        )
                    percentage = round((failed / total) * 100.0, 6)
                    metric_key = (
                        str(pattern["pattern_id"]) if level == "pattern" else group_key
                    )
                    baseline_rows = baselines.get(
                        (str(pattern["pattern_id"]), level, metric_key), []
                    )[:window_size]
                    historical_values = [
                        float(row["failure_percentage"]) for row in baseline_rows
                    ]
                    baseline = (
                        round(statistics.mean(historical_values), 6)
                        if historical_values
                        else None
                    )
                    moving = (
                        round(statistics.mean([percentage, *historical_values]), 6)
                        if historical_values
                        else percentage
                    )
                    threshold = self.resolve_threshold(str(pattern["pattern_id"]), level)
                    delta = round(percentage - baseline, 6) if baseline is not None else None
                    trend = _trend(delta, threshold.abnormal_delta)
                    threshold_status, severity = _threshold_status(percentage, threshold)
                    unique_failed_dies = {
                        (
                            record_by_key[key].get("lot_id"),
                            record_by_key[key].get("wafer_id"),
                            record_by_key[key].get("die_id"),
                        )
                        for key in failed_keys & source_keys
                    }
                    unique_scope_dies = {
                        (
                            record_by_key[key].get("lot_id"),
                            record_by_key[key].get("wafer_id"),
                            record_by_key[key].get("die_id"),
                        )
                        for key in source_keys
                    }
                    metrics.append(
                        {
                            "detected_pattern_id": detected_id,
                            "pattern_id": str(pattern["pattern_id"]),
                            "aggregation_level": level,
                            "aggregation_key": metric_key,
                            "total_tests": total,
                            "pass_count": total - failed,
                            "fail_count": failed,
                            "failure_percentage": percentage,
                            "failure_density": round(
                                len(unique_failed_dies) / max(len(unique_scope_dies), 1),
                                6,
                            ),
                            "pattern_frequency": round(
                                len(failed_keys) / total_pattern_failures, 6
                            ),
                            "moving_average": moving,
                            "baseline_percentage": baseline,
                            "historical_delta": delta,
                            "trend_status": trend,
                            "threshold_status": threshold_status,
                            "threshold_value": (
                                threshold.critical
                                if threshold_status == "critical"
                                else threshold.warning
                            ),
                            "severity_level": severity,
                            "threshold_key": threshold.key,
                            "history_ids": [
                                row["computation_id"] for row in baseline_rows
                            ],
                        }
                    )
        return metrics

    def resolve_threshold(self, pattern_id: str, level: str) -> Threshold:
        ordered = sorted(
            self.config.thresholds,
            key=lambda item: (
                item.pattern_id == pattern_id,
                item.aggregation_level == level,
                item.pattern_id is not None,
                item.aggregation_level is not None,
            ),
            reverse=True,
        )
        for threshold in ordered:
            if threshold.pattern_id not in (None, pattern_id):
                continue
            if threshold.aggregation_level not in (None, level):
                continue
            return threshold
        raise FailureRateComputationError("No applicable threshold configuration")


def _build_groups(
    records: list[dict[str, Any]], levels: list[str], batch_key: str
) -> dict[str, dict[str, set[str]]]:
    groups: dict[str, dict[str, set[str]]] = {level: {} for level in levels}
    for row in records:
        key = str(row["record_key"])
        values = {
            "pattern": "all-records",
            "device": str(row.get("device_id") or "UNKNOWN"),
            "die": "|".join(
                map(
                    str,
                    (row.get("lot_id"), row.get("wafer_id"), row.get("die_id")),
                )
            ),
            "wafer": "|".join(map(str, (row.get("lot_id"), row.get("wafer_id")))),
            "lot": str(row.get("lot_id") or "UNKNOWN"),
            "test_program": str(row.get("test_program") or "UNKNOWN"),
            "batch": batch_key,
        }
        for level in levels:
            groups[level].setdefault(values[level], set()).add(key)
    return groups


def _trend(delta: float | None, abnormal_delta: float) -> str:
    if delta is None:
        return "insufficient_data"
    if delta > abnormal_delta:
        return "worsening"
    if delta < -abnormal_delta:
        return "improving"
    return "stable"


def _threshold_status(percentage: float, threshold: Threshold) -> tuple[str, str]:
    if percentage >= threshold.critical:
        return "critical", "critical"
    if percentage >= threshold.warning:
        return "warning", "high"
    return "within_limit", "low"
