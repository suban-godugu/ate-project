"""Pattern ordering recommendation engine for early failure detection."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from backend.core.config import Settings, get_settings
from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.ordering import (
    OrderedPattern,
    OrderingList,
    OrderingReasonCode,
    OrderingStatistics,
)
from backend.schemas.patterns import PatternFeature, SeverityValue
from backend.services.data_loader import DataLoader, get_data_loader
from backend.services.ml_scoring_service import (
    MlScoringService,
    get_ml_scoring_service,
)
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.utils.pattern_ids import normalize_pattern_id

_SEVERITY_WEIGHT: dict[SeverityValue, int] = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
}
_SEVERITY_MAX = 3.0


class OrderingService:
    """
    Rank patterns for early failure detection using cached PatternFeatures.

    Does not recompute fail_rate, severity, or toggle metrics.
    """

    def __init__(
        self,
        settings: Settings,
        data_loader: DataLoader,
        feature_builder: PatternFeatureBuilder,
        ml_scoring: MlScoringService | None = None,
    ) -> None:
        self._settings = settings
        self._data_loader = data_loader
        self._feature_builder = feature_builder
        self._ml_scoring = ml_scoring
        self._lock = RLock()
        self._ordered: list[OrderedPattern] = []
        self._by_id: dict[str, OrderedPattern] = {}
        self._built_at: datetime | None = None

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> None:
        if not self.is_ready():
            self.analyze()

    def analyze(self) -> OrderingStatistics:
        """Build and cache the recommended execution order."""
        logger = get_logger()
        logger.info("Ordering analysis started")

        # Keep DataLoader in the dependency path for future shared caches.
        if not self._data_loader.has_cached("failure_summary"):
            try:
                self._data_loader.get_failure_summary()
            except AppException:
                logger.warning(
                    "failure_summary unavailable during ordering; continuing"
                )

        pattern_index = self._feature_builder.get_index()
        patterns = list(pattern_index.values())
        logger.info("Ordering pattern count=%d", len(patterns))

        fail_rates = {
            item.pattern_id: float(item.fail_rate) for item in patterns
        }
        toggles = {
            item.pattern_id: float(item.mean_toggle_coverage)
            for item in patterns
        }
        norm_fail = _min_max_normalize(fail_rates)
        norm_toggle = _min_max_normalize(toggles)

        a, b, c = _normalized_weights(self._settings)
        scored: list[tuple[float, str, PatternFeature, float, float, float]] = []
        feature_payloads: list[dict] = []

        for item in patterns:
            n_fail = norm_fail[item.pattern_id]
            n_toggle = norm_toggle[item.pattern_id]
            n_severity = _normalize_severity(item.severity)
            score = a * n_fail + b * n_severity + c * n_toggle
            score = round(max(0.0, min(1.0, score)), 6)
            scored.append((score, item.pattern_id, item, n_fail, n_severity, n_toggle))
            feature_payloads.append(
                {
                    "fail_rate": float(item.fail_rate),
                    "severity": item.severity,
                    "mean_toggle_coverage": float(item.mean_toggle_coverage),
                    "mean_toggle_density": float(item.mean_toggle_density),
                    "mean_toggle_count": float(item.mean_toggle_count),
                    "coverage_percent": float(item.coverage_percent),
                    "failed_log_count": len(item.failed_logs),
                    "failed_chain_count": len(item.failed_chains),
                    "total_executions": int(item.total_executions),
                    "fail_executions": int(item.fail_executions),
                    "similarity_to_representative": 0.0,
                    "cluster_size": 1.0,
                    "is_representative": 0.0,
                    "redundant_flag": 0.0,
                    "unique_fail_contribution": 0.0,
                    "normalized_unique_fail_contribution": 0.0,
                    "normalized_toggle_coverage": float(n_toggle),
                    "heuristic_removal_priority": 0.0,
                    "heuristic_order_score": float(score),
                }
            )

        ml = self._ml_scoring or get_ml_scoring_service(self._settings)
        if ml.has_ordering_model() and (ml.should_apply() or ml.should_shadow_log()):
            raw_ml = ml.predict_ordering_scores(feature_payloads)
            # Min-max normalize ML scores to [0,1] for blending with heuristic.
            if raw_ml:
                lo = min(raw_ml)
                hi = max(raw_ml)
                span = hi - lo
                norm_ml = [
                    0.0 if span <= 0 else (value - lo) / span for value in raw_ml
                ]
            else:
                norm_ml = []
            blended_rows: list[tuple[float, str, PatternFeature, float, float, float]] = []
            for idx, (score, pid, item, n_fail, n_sev, n_toggle) in enumerate(scored):
                ml_score = norm_ml[idx] if idx < len(norm_ml) else None
                blended = ml.blend_score(
                    score,
                    ml_score,
                    blend=ml.ordering_blend,
                )
                if ml.should_shadow_log():
                    logger.info(
                        "ML ordering shadow pattern=%s heuristic=%.6f ml=%s blended=%.6f",
                        pid,
                        score,
                        None if ml_score is None else round(ml_score, 6),
                        blended,
                    )
                final_score = blended if ml.should_apply() and ml_score is not None else score
                blended_rows.append(
                    (final_score, pid, item, n_fail, n_sev, n_toggle)
                )
            scored = blended_rows

        scored.sort(key=lambda row: (-row[0], row[1]))

        ordered: list[OrderedPattern] = []
        for rank, (score, _pid, feature, n_fail, _n_sev, n_toggle) in enumerate(
            scored, start=1
        ):
            ordered.append(
                OrderedPattern(
                    pattern_id=feature.pattern_id,
                    execution_rank=rank,
                    order_score=score,
                    fail_rate=feature.fail_rate,
                    severity=feature.severity,
                    mean_toggle_coverage=feature.mean_toggle_coverage,
                    reason_codes=_reason_codes(
                        settings=self._settings,
                        severity=feature.severity,
                        normalized_fail_rate=n_fail,
                        normalized_toggle=n_toggle,
                    ),
                )
            )

        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._ordered = ordered
            self._by_id = {item.pattern_id: item for item in ordered}
            self._built_at = built_at

        logger.info("Ordering completed total=%d", len(ordered))
        logger.info("Ordering cache created")
        return self.get_statistics()

    def refresh(self) -> OrderingStatistics:
        get_logger().info("Ordering refresh requested")
        stats = self.analyze()
        get_logger().info(
            "Ordering refresh completed total_patterns=%d",
            stats.total_patterns,
        )
        return stats

    def get_ordering(self) -> OrderingList:
        self.ensure_built()
        with self._lock:
            return OrderingList(
                patterns=list(self._ordered),
                total=len(self._ordered),
                built_at=self._built_at,
            )

    def get_pattern(self, pattern_id: str) -> OrderedPattern:
        self.ensure_built()
        canonical = normalize_pattern_id(pattern_id)
        with self._lock:
            item = self._by_id.get(canonical)
            if item is None and pattern_id in self._by_id:
                item = self._by_id[pattern_id]
        if item is None:
            raise AppException(
                f"Ordering recommendation for pattern '{pattern_id}' not found",
                status_code=404,
                details={"pattern_id": pattern_id},
            )
        return item

    def get_statistics(self) -> OrderingStatistics:
        self.ensure_built()
        with self._lock:
            rows = list(self._ordered)

        if not rows:
            return OrderingStatistics()

        scores = [item.order_score for item in rows]
        high_min = self._settings.ordering_high_priority_score_min
        high_priority = sum(1 for score in scores if score >= high_min)
        return OrderingStatistics(
            total_patterns=len(rows),
            highest_score=round(max(scores), 6),
            lowest_score=round(min(scores), 6),
            average_score=round(sum(scores) / len(scores), 6),
            high_priority_patterns=high_priority,
        )


def _normalize_severity(severity: SeverityValue) -> float:
    return _SEVERITY_WEIGHT.get(severity, 0) / _SEVERITY_MAX


def _min_max_normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    numeric = list(values.values())
    lo = min(numeric)
    hi = max(numeric)
    if hi <= lo:
        return {key: 0.0 for key in values}
    span = hi - lo
    return {key: (value - lo) / span for key, value in values.items()}


def _normalized_weights(settings: Settings) -> tuple[float, float, float]:
    a = float(settings.ordering_fail_rate_weight)
    b = float(settings.ordering_severity_weight)
    c = float(settings.ordering_toggle_weight)
    total = a + b + c
    if total <= 0:
        return 0.50, 0.30, 0.20
    return a / total, b / total, c / total


def _reason_codes(
    *,
    settings: Settings,
    severity: SeverityValue,
    normalized_fail_rate: float,
    normalized_toggle: float,
) -> list[OrderingReasonCode]:
    reasons: list[OrderingReasonCode] = []

    high_fail = settings.ordering_high_fail_rate_min
    medium_fail = settings.ordering_medium_fail_rate_min
    if normalized_fail_rate >= high_fail:
        reasons.append("HIGH_FAILURE_RATE")
    elif normalized_fail_rate >= medium_fail:
        reasons.append("MEDIUM_FAILURE_RATE")
    else:
        reasons.append("LOW_FAILURE_RATE")

    if severity == "HIGH":
        reasons.append("HIGH_SEVERITY")

    if normalized_toggle >= settings.ordering_high_toggle_min:
        reasons.append("HIGH_TOGGLE_COVERAGE")

    return reasons


_ordering_service: OrderingService | None = None
_service_lock = RLock()


def get_ordering_service(
    settings: Settings | None = None,
    data_loader: DataLoader | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
    ml_scoring: MlScoringService | None = None,
) -> OrderingService:
    """Return the process-wide OrderingService singleton."""
    global _ordering_service
    with _service_lock:
        if _ordering_service is None:
            cfg = settings or get_settings()
            loader = data_loader or get_data_loader(cfg)
            builder = feature_builder or get_pattern_feature_builder(loader)
            _ordering_service = OrderingService(
                cfg,
                loader,
                builder,
                ml_scoring or get_ml_scoring_service(cfg),
            )
        return _ordering_service


def reset_ordering_service() -> None:
    """Clear the OrderingService singleton."""
    global _ordering_service
    with _service_lock:
        _ordering_service = None
