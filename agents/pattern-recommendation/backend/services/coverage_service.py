"""Coverage improvement engine using toggle and failure proxies only."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from statistics import median
from threading import RLock

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.schemas.coverage import (
    CoverageRecommendation,
    CoverageRecommendationList,
    CoverageReasonCode,
    CoverageStatistics,
)
from backend.schemas.patterns import PatternFeature
from backend.services.gap_analysis_service import (
    GapAnalysisService,
    _extract_lot,
    get_gap_analysis_service,
)
from backend.services.ordering_service import OrderingService, get_ordering_service
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.utils.statistics import percentile_value


class CoverageService:
    """
    Generate toggle/fail proxy coverage recommendations.

    Never computes ATPG fault coverage, stuck-at coverage, or transition coverage.
    """

    def __init__(
        self,
        settings: Settings,
        feature_builder: PatternFeatureBuilder,
        ordering_service: OrderingService,
        gap_analysis_service: GapAnalysisService,
    ) -> None:
        self._settings = settings
        self._feature_builder = feature_builder
        self._ordering_service = ordering_service
        self._gap_analysis_service = gap_analysis_service
        self._lock = RLock()
        self._recommendations: list[CoverageRecommendation] = []
        self._built_at: datetime | None = None
        self._patterns_flagged: set[str] = set()
        self._chains_flagged: set[str] = set()
        self._reorder_count = 0
        self._gap_matches = 0

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> None:
        if not self.is_ready():
            self.analyze()

    def analyze(self) -> CoverageStatistics:
        logger = get_logger()
        logger.info("Coverage analysis started")

        feature_index = self._feature_builder.get_index()
        patterns = list(feature_index.values())
        ordering = self._ordering_service.get_ordering()
        gap_requests = self._gap_analysis_service.get_requests()

        logger.info("Coverage patterns analyzed=%d", len(patterns))

        # Step 1 — low toggle patterns (dataset-relative percentile)
        toggle_by_pattern = {
            item.pattern_id: float(item.mean_toggle_coverage) for item in patterns
        }
        low_toggle_threshold = percentile_value(
            list(toggle_by_pattern.values()),
            self._settings.coverage_gap_percentile,
        )
        low_toggle_patterns = [
            item
            for item in patterns
            if item.mean_toggle_coverage <= low_toggle_threshold
        ]

        # Step 2 — under-tested chains (below median chain toggle)
        chain_means = _chain_mean_toggle(patterns)
        logger.info("Coverage chains analyzed=%d", len(chain_means))
        under_tested_chains = _under_tested_chains(chain_means)

        # Step 3 — late high-severity patterns from OrderingService
        late_threshold_rank = _late_rank_threshold(
            total_patterns=max(ordering.total, 1),
            late_percentile=self._settings.coverage_late_rank_percentile,
        )
        high_severities = {
            token.strip().upper()
            for token in self._settings.coverage_high_severities.split(",")
            if token.strip()
        }
        order_by_id = {item.pattern_id: item for item in ordering.patterns}
        late_high_severity = [
            item
            for item in ordering.patterns
            if item.severity in high_severities
            and item.execution_rank >= late_threshold_rank
            and feature_index.get(item.pattern_id) is not None
            and feature_index[item.pattern_id].fail_executions > 0
        ]

        recommendations: list[CoverageRecommendation] = []
        seen: set[tuple] = set()

        for feature in low_toggle_patterns:
            priority = _priority_low_toggle(
                feature.mean_toggle_coverage,
                low_toggle_threshold,
                min(toggle_by_pattern.values()) if toggle_by_pattern else 0.0,
            )
            rec = CoverageRecommendation(
                pattern_id=feature.pattern_id,
                recommendation_type="IMPROVE_TOGGLE",
                reason_codes=["LOW_TOGGLE_COVERAGE"],
                affected_chains=sorted(feature.failed_chains),
                affected_lots=_lots_from_feature(feature),
                priority=priority,
            )
            if _register(seen, rec):
                recommendations.append(rec)

        for chain in under_tested_chains:
            mean_toggle = chain_means[chain]
            dataset_median = median(list(chain_means.values())) if chain_means else 0.0
            priority = _priority_under_tested(mean_toggle, dataset_median)
            related = [
                p.pattern_id
                for p in patterns
                if chain in p.failed_chains
            ]
            pattern_id = related[0] if related else ""
            reasons: list[CoverageReasonCode] = ["UNDER_TESTED_CHAIN"]
            # Attach high-failure-density if chain appears in gap high-fail requests
            if _chain_in_gap_failure(chain, gap_requests.requests):
                reasons.append("HIGH_FAILURE_DENSITY")
            rec = CoverageRecommendation(
                pattern_id=pattern_id,
                recommendation_type="TARGET_CHAIN",
                reason_codes=reasons,
                affected_chains=[chain],
                affected_lots=[],
                priority=priority,
            )
            if _register(seen, rec):
                recommendations.append(rec)

        for ordered in late_high_severity:
            feature = feature_index[ordered.pattern_id]
            rank_ratio = ordered.execution_rank / max(ordering.total, 1)
            reasons = ["LATE_HIGH_SEVERITY_PATTERN"]
            if ordered.fail_rate > 0:
                # Observed failure signal from cached features/ordering
                if feature.fail_executions > 0:
                    reasons.append("HIGH_FAILURE_DENSITY")
            priority = round(min(1.0, 0.55 + 0.45 * rank_ratio), 6)
            rec = CoverageRecommendation(
                pattern_id=ordered.pattern_id,
                recommendation_type="REORDER",
                reason_codes=reasons,
                affected_chains=sorted(feature.failed_chains),
                affected_lots=_lots_from_feature(feature),
                priority=priority,
            )
            if _register(seen, rec):
                recommendations.append(rec)

        # Step 4 — merge GapAnalysisService requests without duplicates
        gap_matches = 0
        for request in gap_requests.requests:
            reasons: list[CoverageReasonCode] = ["GAP_ANALYSIS_MATCH"]
            if "LOW_TOGGLE_COVERAGE" in request.rationale:
                reasons.append("LOW_TOGGLE_COVERAGE")
            if "HIGH_FAILURE_DENSITY" in request.rationale:
                reasons.append("HIGH_FAILURE_DENSITY")
            if "UNDER_TESTED_CHAIN" not in reasons and request.target_chains:
                # Gap chain targets reinforce under-tested signal when overlapping
                if any(chain in under_tested_chains for chain in request.target_chains):
                    reasons.append("UNDER_TESTED_CHAIN")

            priority = round(
                min(
                    1.0,
                    0.70
                    + 0.05 * len(request.target_chains)
                    + 0.05 * len(request.target_lots),
                ),
                6,
            )
            rec = CoverageRecommendation(
                pattern_id=request.request_id or "",
                recommendation_type="GAP_REQUEST",
                reason_codes=_unique_reasons(reasons),
                affected_chains=sorted(request.target_chains),
                affected_lots=sorted(request.target_lots),
                priority=priority,
            )
            if _register(seen, rec):
                recommendations.append(rec)
                gap_matches += 1

        recommendations.sort(
            key=lambda item: (-item.priority, item.recommendation_type, item.pattern_id)
        )

        patterns_flagged = {
            item.pattern_id
            for item in recommendations
            if item.pattern_id and not item.pattern_id.startswith("GAP-")
        }
        chains_flagged = set(under_tested_chains)
        for item in recommendations:
            chains_flagged.update(item.affected_chains)
        reorder_count = sum(
            1 for item in recommendations if item.recommendation_type == "REORDER"
        )

        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._recommendations = recommendations
            self._built_at = built_at
            self._patterns_flagged = patterns_flagged
            self._chains_flagged = chains_flagged
            self._reorder_count = reorder_count
            self._gap_matches = gap_matches

        logger.info(
            "Coverage recommendations generated=%d",
            len(recommendations),
        )
        logger.info("Coverage recommendation cache built")
        return self.get_statistics()

    def refresh(self) -> CoverageStatistics:
        get_logger().info("Coverage recommendation refresh requested")
        stats = self.analyze()
        get_logger().info(
            "Coverage recommendation refresh completed total=%d",
            stats.patterns_flagged + stats.chains_flagged,
        )
        return stats

    def get_recommendations(self) -> CoverageRecommendationList:
        self.ensure_built()
        with self._lock:
            return CoverageRecommendationList(
                coverage_type="toggle_and_fail_proxy",
                recommendations=list(self._recommendations),
                total=len(self._recommendations),
                built_at=self._built_at,
            )

    def get_statistics(self) -> CoverageStatistics:
        self.ensure_built()
        with self._lock:
            rows = list(self._recommendations)
            avg = (
                sum(item.priority for item in rows) / len(rows) if rows else 0.0
            )
            return CoverageStatistics(
                coverage_type="toggle_and_fail_proxy",
                patterns_flagged=len(self._patterns_flagged),
                chains_flagged=len(self._chains_flagged),
                reorder_recommendations=self._reorder_count,
                gap_matches=self._gap_matches,
                average_priority=round(avg, 6),
            )


def _chain_mean_toggle(patterns: list[PatternFeature]) -> dict[str, float]:
    """Average pattern mean_toggle_coverage per observed scan chain."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for feature in patterns:
        for chain in feature.failed_chains:
            buckets[chain].append(float(feature.mean_toggle_coverage))
    return {
        chain: sum(values) / len(values)
        for chain, values in buckets.items()
        if values
    }


def _under_tested_chains(chain_means: dict[str, float]) -> list[str]:
    if not chain_means:
        return []
    dataset_median = median(list(chain_means.values()))
    return sorted(
        chain
        for chain, value in chain_means.items()
        if value < dataset_median
    )


def _late_rank_threshold(*, total_patterns: int, late_percentile: float) -> int:
    """Ranks at/above this threshold are considered late (1-based ranks)."""
    if total_patterns <= 1:
        return 1
    # e.g. percentile 70 → rank starting around 70% through the ordered list
    value = percentile_value(
        [float(rank) for rank in range(1, total_patterns + 1)],
        late_percentile,
    )
    return max(1, int(round(value)))


def _lots_from_feature(feature: PatternFeature) -> list[str]:
    lots: set[str] = set()
    for log_name in feature.failed_logs:
        lot = _extract_lot(log_name)
        if lot:
            lots.add(lot)
    return sorted(lots)


def _priority_low_toggle(
    value: float,
    threshold: float,
    minimum: float,
) -> float:
    if threshold <= minimum:
        return 0.80
    # Farther below threshold → higher priority
    span = threshold - minimum
    depth = max(0.0, threshold - value) / span if span > 0 else 0.0
    return round(min(1.0, 0.60 + 0.40 * depth), 6)


def _priority_under_tested(value: float, dataset_median: float) -> float:
    if dataset_median <= 0:
        return 0.75
    depth = max(0.0, dataset_median - value) / dataset_median
    return round(min(1.0, 0.55 + 0.45 * depth), 6)


def _chain_in_gap_failure(chain: str, requests: list) -> bool:
    for request in requests:
        if "HIGH_FAILURE_DENSITY" in request.rationale and chain in request.target_chains:
            return True
    return False


def _unique_reasons(reasons: list[CoverageReasonCode]) -> list[CoverageReasonCode]:
    seen: set[str] = set()
    ordered: list[CoverageReasonCode] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    return ordered


def _register(seen: set[tuple], recommendation: CoverageRecommendation) -> bool:
    key = (
        recommendation.recommendation_type,
        recommendation.pattern_id,
        tuple(recommendation.affected_chains),
        tuple(recommendation.affected_lots),
        tuple(recommendation.reason_codes),
    )
    if key in seen:
        return False
    seen.add(key)
    return True


_coverage_service: CoverageService | None = None
_service_lock = RLock()


def get_coverage_service(
    settings: Settings | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
    ordering_service: OrderingService | None = None,
    gap_analysis_service: GapAnalysisService | None = None,
) -> CoverageService:
    """Return the process-wide CoverageService singleton."""
    global _coverage_service
    with _service_lock:
        if _coverage_service is None:
            cfg = settings or get_settings()
            builder = feature_builder or get_pattern_feature_builder()
            ordering = ordering_service or get_ordering_service(
                settings=cfg,
                feature_builder=builder,
            )
            gap = gap_analysis_service or get_gap_analysis_service(
                settings=cfg,
                feature_builder=builder,
                ordering_service=ordering,
            )
            _coverage_service = CoverageService(cfg, builder, ordering, gap)
        return _coverage_service


def reset_coverage_service() -> None:
    """Clear the CoverageService singleton."""
    global _coverage_service
    with _service_lock:
        _coverage_service = None
