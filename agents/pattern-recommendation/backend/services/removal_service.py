"""Pattern removal recommendation engine."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from backend.core.config import Settings, get_settings
from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.patterns import PatternFeature
from backend.schemas.redundancy import ClusterSummary, RedundantPattern
from backend.schemas.removal import (
    RemovalReasonCode,
    RemovalRecommendation,
    RemovalRecommendationList,
    RemovalStatistics,
)
from backend.services.data_loader import DataLoader, get_data_loader
from backend.services.ml_scoring_service import (
    MlScoringService,
    get_ml_scoring_service,
)
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.services.redundancy_service import (
    RedundancyService,
    get_redundancy_service,
)
from backend.utils.pattern_ids import normalize_pattern_id


class RemovalService:
    """
    Rank redundant non-representative patterns for safe removal.

    Consumes PatternFeatureBuilder + RedundancyService only for metrics.
    Optionally blends LightGBM removal scores when ML is enabled.
    """

    def __init__(
        self,
        settings: Settings,
        data_loader: DataLoader,
        feature_builder: PatternFeatureBuilder,
        redundancy_service: RedundancyService,
        ml_scoring: MlScoringService | None = None,
    ) -> None:
        self._settings = settings
        self._data_loader = data_loader
        self._feature_builder = feature_builder
        self._redundancy_service = redundancy_service
        self._ml_scoring = ml_scoring
        self._lock = RLock()
        self._recommendations: dict[str, RemovalRecommendation] = {}
        self._ordered: list[RemovalRecommendation] = []
        self._built_at: datetime | None = None
        self._candidate_count: int = 0

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> None:
        if not self.is_ready():
            self.analyze()

    def analyze(self) -> RemovalStatistics:
        """Build and cache ranked removal recommendations."""
        logger = get_logger()
        logger.info("Removal analysis started")

        pattern_index = self._feature_builder.get_index()
        self._redundancy_service.ensure_built()
        # Ensure supporting datasets remain reachable through DataLoader only.
        if not self._data_loader.has_cached("failure_summary"):
            self._data_loader.get_failure_summary()
        cluster_index = self._redundancy_service.get_cluster_index()
        redundancy_patterns = self._redundancy_service.get_pattern_index()

        candidates = [
            item
            for item in redundancy_patterns.values()
            if item.redundant_flag and not item.is_representative
        ]
        logger.info("Removal candidate count=%d", len(candidates))

        unique_contrib = {
            item.pattern_id: _unique_fail_contribution(
                item, pattern_index, cluster_index
            )
            for item in candidates
        }
        toggle_values = {
            item.pattern_id: _toggle_coverage(item.pattern_id, pattern_index)
            for item in candidates
        }

        norm_unique = _min_max_normalize(unique_contrib)
        norm_toggle = _min_max_normalize(toggle_values)

        w1, w2, w3 = _normalized_weights(self._settings)
        low_unique_max = self._settings.removal_low_unique_normalized_max
        low_toggle_max = self._settings.removal_low_toggle_normalized_max

        recommendations: list[RemovalRecommendation] = []
        feature_payloads: list[dict] = []
        for item in candidates:
            n_unique = norm_unique[item.pattern_id]
            n_toggle = norm_toggle[item.pattern_id]
            priority = (
                w1 * 1.0
                + w2 * (1.0 - n_unique)
                + w3 * (1.0 - n_toggle)
            )
            priority = round(max(0.0, min(1.0, priority)), 6)
            feature = pattern_index.get(item.pattern_id)
            cluster = cluster_index.get(item.cluster_id)
            feature_payloads.append(
                {
                    "pattern_id": item.pattern_id,
                    "fail_rate": float(feature.fail_rate) if feature else 0.0,
                    "severity": feature.severity if feature else "NONE",
                    "mean_toggle_coverage": (
                        float(feature.mean_toggle_coverage) if feature else 0.0
                    ),
                    "mean_toggle_density": (
                        float(feature.mean_toggle_density) if feature else 0.0
                    ),
                    "mean_toggle_count": (
                        float(feature.mean_toggle_count) if feature else 0.0
                    ),
                    "coverage_percent": (
                        float(feature.coverage_percent) if feature else 0.0
                    ),
                    "failed_log_count": len(feature.failed_logs) if feature else 0,
                    "failed_chain_count": len(feature.failed_chains) if feature else 0,
                    "total_executions": int(feature.total_executions) if feature else 0,
                    "fail_executions": int(feature.fail_executions) if feature else 0,
                    "similarity_to_representative": float(
                        item.similarity_to_representative
                    ),
                    "cluster_size": int(cluster.cluster_size) if cluster else 1,
                    "is_representative": 0.0,
                    "redundant_flag": 1.0,
                    "unique_fail_contribution": float(unique_contrib[item.pattern_id]),
                    "normalized_unique_fail_contribution": float(n_unique),
                    "normalized_toggle_coverage": float(n_toggle),
                    "heuristic_removal_priority": float(priority),
                    "heuristic_order_score": 0.0,
                }
            )
            reasons = _reason_codes(
                normalized_unique=n_unique,
                normalized_toggle=n_toggle,
                low_unique_max=low_unique_max,
                low_toggle_max=low_toggle_max,
            )
            recommendations.append(
                RemovalRecommendation(
                    pattern_id=item.pattern_id,
                    cluster_id=item.cluster_id,
                    representative_pattern=item.representative_pattern,
                    removal_priority=priority,
                    confidence=priority,
                    unique_fail_contribution=float(
                        unique_contrib[item.pattern_id]
                    ),
                    normalized_unique_fail_contribution=round(n_unique, 6),
                    normalized_toggle_coverage=round(n_toggle, 6),
                    reason_codes=reasons,
                )
            )

        ml = self._ml_scoring or get_ml_scoring_service(self._settings)
        if ml.has_removal_model() and (ml.should_apply() or ml.should_shadow_log()):
            ml_scores = ml.predict_removal_proba(feature_payloads)
            for idx, row in enumerate(recommendations):
                ml_score = ml_scores[idx] if idx < len(ml_scores) else None
                blended = ml.blend_score(
                    row.removal_priority,
                    ml_score,
                    blend=ml.removal_blend,
                    unique_fail_contribution=row.unique_fail_contribution,
                    for_removal=True,
                )
                if ml.should_shadow_log():
                    logger.info(
                        "ML removal shadow pattern=%s heuristic=%.6f ml=%s blended=%.6f",
                        row.pattern_id,
                        row.removal_priority,
                        None if ml_score is None else round(ml_score, 6),
                        blended,
                    )
                if ml.should_apply() and ml_score is not None:
                    recommendations[idx] = row.model_copy(
                        update={
                            "removal_priority": blended,
                            "confidence": blended,
                        }
                    )

        recommendations.sort(
            key=lambda row: (-row.removal_priority, row.pattern_id)
        )

        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._ordered = recommendations
            self._recommendations = {
                row.pattern_id: row for row in recommendations
            }
            self._built_at = built_at
            self._candidate_count = len(candidates)

        logger.info(
            "Removal recommendation count=%d",
            len(recommendations),
        )
        logger.info("Removal recommendation cache built")
        return self.get_statistics()

    def refresh(self) -> RemovalStatistics:
        get_logger().info("Removal recommendation refresh requested")
        stats = self.analyze()
        get_logger().info(
            "Removal recommendation refresh completed recommended=%d",
            stats.recommended,
        )
        return stats

    def get_recommendations(self) -> RemovalRecommendationList:
        self.ensure_built()
        with self._lock:
            return RemovalRecommendationList(
                recommendations=list(self._ordered),
                total=len(self._ordered),
                built_at=self._built_at,
            )

    def get_recommendation(self, pattern_id: str) -> RemovalRecommendation:
        self.ensure_built()
        canonical = normalize_pattern_id(pattern_id)
        with self._lock:
            item = self._recommendations.get(canonical)
            if item is None and pattern_id in self._recommendations:
                item = self._recommendations[pattern_id]
        if item is None:
            raise AppException(
                f"Removal recommendation for pattern '{pattern_id}' not found",
                status_code=404,
                details={"pattern_id": pattern_id},
            )
        return item

    def get_statistics(self) -> RemovalStatistics:
        self.ensure_built()
        with self._lock:
            rows = list(self._ordered)
            candidates = self._candidate_count

        if not rows:
            return RemovalStatistics(candidates=candidates, recommended=0)

        priorities = [row.removal_priority for row in rows]
        return RemovalStatistics(
            candidates=candidates,
            recommended=len(rows),
            average_priority=round(sum(priorities) / len(priorities), 6),
            highest_priority=round(max(priorities), 6),
        )


def _unique_fail_contribution(
    redundant: RedundantPattern,
    pattern_index: dict[str, PatternFeature],
    cluster_index: dict[str, ClusterSummary],
) -> int:
    """
    Count failed logs uniquely explained by this pattern versus kept
    representatives in the same cluster.
    """
    feature = pattern_index.get(redundant.pattern_id)
    pattern_logs = set(feature.failed_logs) if feature else set()

    cluster = cluster_index.get(redundant.cluster_id)
    representative_id = (
        cluster.representative
        if cluster is not None
        else redundant.representative_pattern
    )
    rep_feature = pattern_index.get(representative_id)
    kept_rep_logs = set(rep_feature.failed_logs) if rep_feature else set()

    return len(pattern_logs - kept_rep_logs)


def _toggle_coverage(
    pattern_id: str,
    pattern_index: dict[str, PatternFeature],
) -> float:
    feature = pattern_index.get(pattern_id)
    if feature is None:
        return 0.0
    return float(feature.mean_toggle_coverage)


def _min_max_normalize(values: dict[str, float]) -> dict[str, float]:
    """Dataset-relative min-max normalization over the candidate set."""
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
    w1 = float(settings.removal_redundancy_weight)
    w2 = float(settings.removal_unique_contribution_weight)
    w3 = float(settings.removal_toggle_weight)
    total = w1 + w2 + w3
    if total <= 0:
        return 0.5, 0.3, 0.2
    return w1 / total, w2 / total, w3 / total


def _reason_codes(
    *,
    normalized_unique: float,
    normalized_toggle: float,
    low_unique_max: float,
    low_toggle_max: float,
) -> list[RemovalReasonCode]:
    reasons: list[RemovalReasonCode] = ["REDUNDANT_NEAR_DUP"]
    if normalized_unique <= low_unique_max:
        reasons.append("LOW_UNIQUE_DETECTION")
    if normalized_toggle <= low_toggle_max:
        reasons.append("LOW_TOGGLE_ACTIVITY")
    return reasons


_removal_service: RemovalService | None = None
_service_lock = RLock()


def get_removal_service(
    settings: Settings | None = None,
    data_loader: DataLoader | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
    redundancy_service: RedundancyService | None = None,
    ml_scoring: MlScoringService | None = None,
) -> RemovalService:
    """Return the process-wide RemovalService singleton."""
    global _removal_service
    with _service_lock:
        if _removal_service is None:
            cfg = settings or get_settings()
            loader = data_loader or get_data_loader(cfg)
            builder = feature_builder or get_pattern_feature_builder(loader)
            redundancy = redundancy_service or get_redundancy_service(
                loader, builder
            )
            _removal_service = RemovalService(
                cfg,
                loader,
                builder,
                redundancy,
                ml_scoring or get_ml_scoring_service(cfg),
            )
        return _removal_service


def reset_removal_service() -> None:
    """Clear the RemovalService singleton."""
    global _removal_service
    with _service_lock:
        _removal_service = None
