"""Low-activity pattern-set recommendations using toggle activity as a proxy."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.schemas.low_power import (
    LowPowerPattern,
    LowPowerPatternSet,
    LowPowerReasonCode,
    LowPowerStatistics,
    ToggleMetric,
)
from backend.schemas.patterns import PatternFeature
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.services.redundancy_service import (
    RedundancyService,
    get_redundancy_service,
)
from backend.services.removal_service import RemovalService, get_removal_service
from backend.utils.statistics import percentile_value


class LowPowerService:
    """Build a cached low-activity set without estimating actual power."""

    def __init__(
        self,
        settings: Settings,
        feature_builder: PatternFeatureBuilder,
        redundancy_service: RedundancyService,
        removal_service: RemovalService,
    ) -> None:
        self._settings = settings
        self._feature_builder = feature_builder
        self._redundancy_service = redundancy_service
        self._removal_service = removal_service
        self._lock = RLock()
        self._patterns: list[LowPowerPattern] = []
        self._built_at: datetime | None = None
        self._patterns_analyzed = 0
        self._coverage_retention = 0.0
        self._average_activity = 0.0
        self._proxy_metric: ToggleMetric = "toggle_density"

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> None:
        if not self.is_ready():
            self.analyze()

    def analyze(self) -> LowPowerStatistics:
        """Build and cache the deterministic toggle-activity proxy set."""
        logger = get_logger()
        logger.info("Low-activity proxy analysis started")

        feature_index = self._feature_builder.get_index()
        redundancy_index = self._redundancy_service.get_pattern_index()
        # Consume the existing removal service without modifying its results.
        self._removal_service.get_recommendations()

        features = list(feature_index.values())
        proxy_metric = _choose_proxy_metric(features)
        activity = {
            feature.pattern_id: _activity_score(feature, proxy_metric)
            for feature in features
        }
        threshold = percentile_value(
            list(activity.values()),
            self._settings.low_power_percentile,
        )

        low_activity_ids = {
            pattern_id
            for pattern_id, score in activity.items()
            if score <= threshold
        }
        required_representatives = {
            pattern_id
            for pattern_id, redundancy in redundancy_index.items()
            if redundancy.is_representative
            and feature_index.get(pattern_id) is not None
            and feature_index[pattern_id].fail_executions > 0
        }

        selected_ids = low_activity_ids | required_representatives
        total_failed_logs = _all_failed_logs(features)
        covered_logs = _covered_logs(selected_ids, feature_index)
        retention_target = self._settings.coverage_retention_ratio
        coverage_added_ids: set[str] = set()

        # Add the lowest-activity remaining patterns that contribute uncovered
        # failed logs until the configured retention target is satisfied.
        remaining = sorted(
            (
                feature
                for feature in features
                if feature.pattern_id not in selected_ids
            ),
            key=lambda feature: (
                activity[feature.pattern_id],
                feature.pattern_id,
            ),
        )
        for feature in remaining:
            if _retention(covered_logs, total_failed_logs) >= retention_target:
                break
            new_logs = set(feature.failed_logs) - covered_logs
            if not new_logs:
                continue
            selected_ids.add(feature.pattern_id)
            coverage_added_ids.add(feature.pattern_id)
            covered_logs.update(new_logs)

        coverage_retention = _retention(covered_logs, total_failed_logs)
        selected = [
            _to_low_power_pattern(
                feature=feature_index[pattern_id],
                activity_score=activity[pattern_id],
                proxy_metric=proxy_metric,
                representative=pattern_id in required_representatives,
                low_activity=pattern_id in low_activity_ids,
                coverage_added=pattern_id in coverage_added_ids,
            )
            for pattern_id in selected_ids
        ]
        selected.sort(key=lambda item: (item.activity_score, item.pattern_id))

        average_activity = (
            sum(activity.values()) / len(activity) if activity else 0.0
        )
        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._patterns = selected
            self._built_at = built_at
            self._patterns_analyzed = len(features)
            self._coverage_retention = coverage_retention
            self._average_activity = average_activity
            self._proxy_metric = proxy_metric

        logger.info("Low-activity patterns analyzed=%d", len(features))
        logger.info("Low-activity patterns selected=%d", len(selected))
        logger.info("Failure-log coverage retained=%.6f", coverage_retention)
        logger.info("Low-activity proxy cache created")
        return self.get_statistics()

    def refresh(self) -> LowPowerStatistics:
        """Explicitly rebuild the proxy recommendations."""
        get_logger().info("Low-activity proxy refresh requested")
        statistics = self.analyze()
        get_logger().info(
            "Low-activity proxy refresh completed selected=%d",
            statistics.selected_patterns,
        )
        return statistics

    def get_pattern_set(self) -> LowPowerPatternSet:
        """Return the cached selected set with an explicit proxy disclaimer."""
        self.ensure_built()
        with self._lock:
            return LowPowerPatternSet(
                power_proxy=True,
                proxy_metric=self._proxy_metric,
                patterns=list(self._patterns),
                total=len(self._patterns),
                built_at=self._built_at,
            )

    def get_statistics(self) -> LowPowerStatistics:
        """Return cached proxy-analysis statistics."""
        self.ensure_built()
        with self._lock:
            return LowPowerStatistics(
                power_proxy=True,
                proxy_metric=self._proxy_metric,
                patterns_analyzed=self._patterns_analyzed,
                selected_patterns=len(self._patterns),
                coverage_retention=round(self._coverage_retention, 6),
                average_activity=round(self._average_activity, 6),
                threshold_percentile=self._settings.low_power_percentile,
            )


def _choose_proxy_metric(features: list[PatternFeature]) -> ToggleMetric:
    """Use density when available; otherwise fall back globally to count."""
    if any(feature.mean_toggle_density != 0.0 for feature in features):
        return "toggle_density"
    return "toggle_count"


def _activity_score(feature: PatternFeature, metric: ToggleMetric) -> float:
    if metric == "toggle_density":
        return float(feature.mean_toggle_density)
    return float(feature.mean_toggle_count)


def _all_failed_logs(features: list[PatternFeature]) -> set[str]:
    logs: set[str] = set()
    for feature in features:
        logs.update(feature.failed_logs)
    return logs


def _covered_logs(
    selected_ids: set[str],
    feature_index: dict[str, PatternFeature],
) -> set[str]:
    logs: set[str] = set()
    for pattern_id in selected_ids:
        feature = feature_index.get(pattern_id)
        if feature is not None:
            logs.update(feature.failed_logs)
    return logs


def _retention(covered: set[str], total: set[str]) -> float:
    if not total:
        return 1.0
    return len(covered) / len(total)


def _to_low_power_pattern(
    *,
    feature: PatternFeature,
    activity_score: float,
    proxy_metric: ToggleMetric,
    representative: bool,
    low_activity: bool,
    coverage_added: bool,
) -> LowPowerPattern:
    reasons: list[LowPowerReasonCode] = []
    if low_activity:
        reasons.append("LOW_ACTIVITY")
    if representative:
        reasons.append("REQUIRED_FAILED_REPRESENTATIVE")
    if coverage_added or (representative and feature.failed_logs):
        reasons.append("FAILURE_COVERAGE_PRESERVED")
    return LowPowerPattern(
        pattern_id=feature.pattern_id,
        activity_score=round(activity_score, 6),
        toggle_metric=proxy_metric,
        selected=True,
        representative=representative,
        coverage_retained=bool(feature.failed_logs),
        reason_codes=reasons,
        power_proxy=proxy_metric,
    )


_low_power_service: LowPowerService | None = None
_service_lock = RLock()


def get_low_power_service(
    settings: Settings | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
    redundancy_service: RedundancyService | None = None,
    removal_service: RemovalService | None = None,
) -> LowPowerService:
    """Return the process-wide LowPowerService singleton."""
    global _low_power_service
    with _service_lock:
        if _low_power_service is None:
            cfg = settings or get_settings()
            builder = feature_builder or get_pattern_feature_builder()
            redundancy = redundancy_service or get_redundancy_service(
                feature_builder=builder
            )
            removal = removal_service or get_removal_service(
                settings=cfg,
                feature_builder=builder,
                redundancy_service=redundancy,
            )
            _low_power_service = LowPowerService(
                cfg,
                builder,
                redundancy,
                removal,
            )
        return _low_power_service


def reset_low_power_service() -> None:
    """Clear the LowPowerService singleton."""
    global _low_power_service
    with _service_lock:
        _low_power_service = None
