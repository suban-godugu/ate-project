"""Canonical pattern feature builder and in-memory pattern index."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any

from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.patterns import (
    PatternFeature,
    PatternList,
    PatternStatistics,
    SeverityValue,
)
from backend.services.data_loader import DataLoader, get_data_loader
from backend.utils.pattern_ids import normalize_pattern_id


@dataclass
class _PatternAccumulator:
    total_executions: int = 0
    fail_executions: int = 0
    coverage_sum: float = 0.0
    density_sum: float = 0.0
    toggle_sum: float = 0.0
    failed_logs: set[str] = field(default_factory=set)
    failed_chains: set[str] = field(default_factory=set)


class PatternFeatureBuilder:
    """
    Build and cache the canonical pattern feature index.

    Streams executions exactly once per build and joins failure_summary.
    """

    def __init__(self, data_loader: DataLoader) -> None:
        self._data_loader = data_loader
        self._lock = RLock()
        self._index: dict[str, PatternFeature] = {}
        self._built_at: datetime | None = None

    @property
    def built_at(self) -> datetime | None:
        with self._lock:
            return self._built_at

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> PatternList:
        """Return cached features, building lazily on first access."""
        if not self.is_ready():
            return self.build()
        return self.get_patterns()

    def build(self) -> PatternList:
        """Stream executions, join failure summary, and replace the cache."""
        logger = get_logger()
        logger.info("Pattern feature build started")

        accumulators = self._accumulate_executions()
        summary_by_pattern = self._load_failure_summary_index()
        features = self._materialize_features(accumulators, summary_by_pattern)

        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._index = {item.pattern_id: item for item in features}
            self._built_at = built_at

        logger.info(
            "Pattern feature cache created pattern_count=%d",
            len(features),
        )
        return self.get_patterns()

    def refresh(self) -> PatternList:
        """Rebuild the pattern index from source datasets."""
        get_logger().info("Pattern feature refresh requested")
        self._data_loader.clear_cache()
        result = self.build()
        get_logger().info(
            "Pattern feature refresh completed pattern_count=%d",
            result.total,
        )
        return result

    def get_patterns(self) -> PatternList:
        with self._lock:
            patterns = sorted(
                self._index.values(),
                key=lambda item: _pattern_sort_key(item.pattern_id),
            )
            return PatternList(
                patterns=patterns,
                total=len(patterns),
                built_at=self._built_at,
            )

    def get_pattern(self, pattern_id: str) -> PatternFeature:
        self.ensure_built()
        canonical = normalize_pattern_id(pattern_id)
        with self._lock:
            feature = self._index.get(canonical)
            if feature is None and pattern_id in self._index:
                feature = self._index[pattern_id]
        if feature is None:
            raise AppException(
                f"Pattern '{pattern_id}' not found",
                status_code=404,
                details={"pattern_id": pattern_id},
            )
        return feature

    def get_index(self) -> dict[str, PatternFeature]:
        """Return a shallow copy of the canonical pattern index."""
        self.ensure_built()
        with self._lock:
            return dict(self._index)

    def get_statistics(self) -> PatternStatistics:
        payload = self.ensure_built()
        patterns = payload.patterns
        if not patterns:
            return PatternStatistics()

        total_executions = sum(item.total_executions for item in patterns)
        failed_patterns = sum(1 for item in patterns if item.fail_executions > 0)
        avg_fail_rate = sum(item.fail_rate for item in patterns) / len(patterns)
        avg_density = sum(item.mean_toggle_density for item in patterns) / len(
            patterns
        )
        return PatternStatistics(
            patterns=len(patterns),
            total_executions=total_executions,
            failed_patterns=failed_patterns,
            average_fail_rate=round(avg_fail_rate, 6),
            average_toggle_density=round(avg_density, 6),
        )

    def _accumulate_executions(self) -> dict[str, _PatternAccumulator]:
        logger = get_logger()
        accumulators: dict[str, _PatternAccumulator] = {}

        for row in self._data_loader.iter_executions():
            pattern_id = normalize_pattern_id(row.get("pattern_id"))
            if not pattern_id:
                continue

            acc = accumulators.get(pattern_id)
            if acc is None:
                acc = _PatternAccumulator()
                accumulators[pattern_id] = acc

            acc.total_executions += 1
            acc.coverage_sum += _as_float(row.get("toggle_coverage_pct"))
            acc.density_sum += _as_float(row.get("toggle_density_pct"))
            acc.toggle_sum += _as_float(row.get("toggle_count"))

            result = str(row.get("latest_result", "")).strip().upper()
            if result == "FAIL":
                acc.fail_executions += 1
                log_name = _execution_log_name(row)
                chain = str(row.get("scan_chain_id", "")).strip()
                if log_name:
                    acc.failed_logs.add(log_name)
                if chain:
                    acc.failed_chains.add(chain)

        logger.info(
            "Execution aggregation completed unique_patterns=%d",
            len(accumulators),
        )
        return accumulators

    def _load_failure_summary_index(self) -> dict[str, dict[str, Any]]:
        try:
            summary = self._data_loader.get_failure_summary()
        except AppException as exc:
            get_logger().warning(
                "failure_summary unavailable during feature build: %s",
                exc.message,
            )
            return {}

        patterns = summary.get("patterns", []) if isinstance(summary, dict) else []
        indexed: dict[str, dict[str, Any]] = {}
        if not isinstance(patterns, list):
            return indexed

        for item in patterns:
            if not isinstance(item, dict):
                continue
            pattern_id = normalize_pattern_id(item.get("pattern_id"))
            if pattern_id:
                indexed[pattern_id] = item
        return indexed

    def _materialize_features(
        self,
        accumulators: dict[str, _PatternAccumulator],
        summary_by_pattern: dict[str, dict[str, Any]],
    ) -> list[PatternFeature]:
        features: list[PatternFeature] = []

        # Include patterns present in either executions or failure summary.
        all_ids = set(accumulators) | set(summary_by_pattern)

        for pattern_id in all_ids:
            acc = accumulators.get(pattern_id, _PatternAccumulator())
            summary = summary_by_pattern.get(pattern_id, {})

            total = acc.total_executions
            fail_rate = (acc.fail_executions / total) if total else 0.0
            mean_coverage = (acc.coverage_sum / total) if total else 0.0
            mean_density = (acc.density_sum / total) if total else 0.0
            mean_toggle = (acc.toggle_sum / total) if total else 0.0

            failed_logs = _summary_failed_logs(summary)
            if not failed_logs:
                failed_logs = sorted(acc.failed_logs)

            coverage_percent = _as_float(summary.get("coverage_percent", 0.0))
            severity = _normalize_severity(summary.get("severity"))

            features.append(
                PatternFeature(
                    pattern_id=pattern_id,
                    total_executions=total,
                    fail_executions=acc.fail_executions,
                    fail_rate=round(fail_rate, 6),
                    mean_toggle_coverage=round(mean_coverage, 6),
                    mean_toggle_density=round(mean_density, 6),
                    mean_toggle_count=round(mean_toggle, 6),
                    failed_logs=failed_logs,
                    failed_chains=sorted(acc.failed_chains),
                    coverage_percent=coverage_percent,
                    severity=severity,
                )
            )
        return features


def _as_float(value: object) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _execution_log_name(row: dict[str, Any]) -> str:
    rel = str(row.get("source_log_relpath") or "").strip()
    if rel:
        return rel
    return str(row.get("source_log") or "").strip()


def _summary_failed_logs(summary: dict[str, Any]) -> list[str]:
    raw = summary.get("failing_logs")
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _normalize_severity(value: object) -> SeverityValue:
    token = str(value or "NONE").strip().upper()
    if token in {"HIGH", "MEDIUM", "LOW", "NONE"}:
        return token  # type: ignore[return-value]
    return "NONE"


def _pattern_sort_key(pattern_id: str) -> tuple[int, Any]:
    canonical = normalize_pattern_id(pattern_id)
    if canonical.startswith("Pattern_"):
        suffix = canonical.split("_", 1)[1]
        if suffix.isdigit():
            return (0, int(suffix))
    return (1, canonical)


_feature_builder: PatternFeatureBuilder | None = None
_builder_lock = RLock()


def get_pattern_feature_builder(
    data_loader: DataLoader | None = None,
) -> PatternFeatureBuilder:
    """Return the process-wide PatternFeatureBuilder singleton."""
    global _feature_builder
    with _builder_lock:
        if _feature_builder is None:
            loader = data_loader or get_data_loader()
            _feature_builder = PatternFeatureBuilder(loader)
        return _feature_builder


def reset_pattern_feature_builder() -> None:
    """Clear the PatternFeatureBuilder singleton."""
    global _feature_builder
    with _builder_lock:
        _feature_builder = None
