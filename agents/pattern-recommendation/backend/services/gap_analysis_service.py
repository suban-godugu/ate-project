"""ATPG gap analysis engine — request generation only."""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timezone
from threading import RLock

from backend.core.config import Settings, get_settings
from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.gap_analysis import (
    AdditionalPatternRequest,
    GapAnalysisList,
    GapAnalysisStatistics,
    GapRationaleCode,
    SuggestedFaultModel,
)
from backend.schemas.patterns import PatternFeature
from backend.services.data_loader import DataLoader, get_data_loader
from backend.services.ordering_service import OrderingService, get_ordering_service
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.utils.statistics import percentile_value

_LOT_RE = re.compile(r"(?i)(?:^|[/\\])(LOT[_\-]?\d+)(?:[_/\\]|$)")
_LOT_INLINE_RE = re.compile(r"(?i)\b(LOT[_\-]?\d+)(?=\D|$)")


def _extract_lot(value: str) -> str | None:
    match = _LOT_RE.search(value) or _LOT_INLINE_RE.search(value)
    if not match:
        return None
    token = match.group(1).upper().replace("-", "_")
    digits = re.search(r"(\d+)$", token)
    if not digits:
        return None
    return f"LOT_{int(digits.group(1))}"


class GapAnalysisService:
    """
    Identify testing gaps and emit ATPG *requests* only.

    Never generates STIL/vectors and never claims ATPG execution.
    """

    def __init__(
        self,
        settings: Settings,
        data_loader: DataLoader,
        feature_builder: PatternFeatureBuilder,
        ordering_service: OrderingService,
    ) -> None:
        self._settings = settings
        self._data_loader = data_loader
        self._feature_builder = feature_builder
        self._ordering_service = ordering_service
        self._lock = RLock()
        self._requests: list[AdditionalPatternRequest] = []
        self._built_at: datetime | None = None
        self._chains_flagged: set[str] = set()
        self._lots_flagged: set[str] = set()
        self._average_toggle_percentile: float = 0.0
        self._gap_percentile: float = 0.0

    def is_ready(self) -> bool:
        with self._lock:
            return self._built_at is not None

    def ensure_built(self) -> None:
        if not self.is_ready():
            self.analyze()

    def analyze(self) -> GapAnalysisStatistics:
        logger = get_logger()
        logger.info("Gap analysis started")

        patterns = list(self._feature_builder.get_index().values())
        optional_chains = self._optional_chain_names()
        chain_stats = _build_chain_stats(patterns, optional_chains)
        lot_stats = _build_lot_stats(patterns)
        high_priority_chains, high_priority_lots = self._ordering_hotspots()

        logger.info("Gap analysis chains analyzed=%d", len(chain_stats))
        logger.info("Gap analysis lots analyzed=%d", len(lot_stats))

        gap_p = float(self._settings.gap_percentile)
        high_fail_p = float(self._settings.gap_high_failure_percentile)
        lot_fail_p = float(self._settings.gap_lot_high_failure_percentile)
        lot_div_p = float(self._settings.gap_lot_low_diversity_percentile)

        toggle_by_chain = {
            chain: stats["mean_toggle_coverage"] for chain, stats in chain_stats.items()
        }
        fail_density_by_chain = {
            chain: stats["failure_density"] for chain, stats in chain_stats.items()
        }
        lot_density = {lot: stats["failure_density"] for lot, stats in lot_stats.items()}
        lot_diversity = {
            lot: float(stats["pattern_diversity"]) for lot, stats in lot_stats.items()
        }

        low_toggle_threshold = percentile_value(list(toggle_by_chain.values()), gap_p)
        high_fail_threshold = percentile_value(
            list(fail_density_by_chain.values()), 100.0 - high_fail_p
        )
        high_lot_fail_threshold = percentile_value(
            list(lot_density.values()), 100.0 - lot_fail_p
        )
        low_diversity_threshold = percentile_value(
            list(lot_diversity.values()), lot_div_p
        )

        low_toggle_chains = sorted(
            chain
            for chain, value in toggle_by_chain.items()
            if value <= low_toggle_threshold
        )
        high_fail_chains = sorted(
            chain
            for chain, value in fail_density_by_chain.items()
            if value >= high_fail_threshold and value > 0.0
        )
        gap_lots = sorted(
            lot
            for lot, density in lot_density.items()
            if density >= high_lot_fail_threshold
            and lot_diversity.get(lot, 0.0) <= low_diversity_threshold
        )

        # Reinforce with ordering hotspots when present.
        for chain in high_priority_chains:
            if chain in chain_stats and chain not in high_fail_chains:
                high_fail_chains.append(chain)
        high_fail_chains = sorted(set(high_fail_chains))
        for lot in high_priority_lots:
            if lot in lot_stats and lot not in gap_lots:
                # Only add if density is above median-equivalent using high threshold family
                if lot_density.get(lot, 0.0) >= high_lot_fail_threshold:
                    gap_lots.append(lot)
        gap_lots = sorted(set(gap_lots))

        requests = _build_requests(
            low_toggle_chains=low_toggle_chains,
            high_fail_chains=high_fail_chains,
            gap_lots=gap_lots,
            high_priority_chains=high_priority_chains,
            high_priority_lots=high_priority_lots,
        )

        avg_toggle_pct = _average_toggle_percentile(toggle_by_chain)

        built_at = datetime.now(timezone.utc)
        with self._lock:
            self._requests = requests
            self._built_at = built_at
            self._chains_flagged = set(low_toggle_chains) | set(high_fail_chains)
            self._lots_flagged = set(gap_lots)
            self._average_toggle_percentile = avg_toggle_pct
            self._gap_percentile = gap_p

        logger.info("Gap analysis requests generated=%d", len(requests))
        logger.info("Gap analysis cache built")
        return self.get_statistics()

    def refresh(self) -> GapAnalysisStatistics:
        get_logger().info("Gap analysis refresh requested")
        stats = self.analyze()
        get_logger().info(
            "Gap analysis refresh completed requests=%d",
            stats.requests_generated,
        )
        return stats

    def get_requests(self) -> GapAnalysisList:
        self.ensure_built()
        with self._lock:
            return GapAnalysisList(
                requests=list(self._requests),
                total=len(self._requests),
                built_at=self._built_at,
                gap_percentile=self._gap_percentile,
            )

    def get_statistics(self) -> GapAnalysisStatistics:
        self.ensure_built()
        with self._lock:
            return GapAnalysisStatistics(
                requests_generated=len(self._requests),
                chains_flagged=len(self._chains_flagged),
                lots_flagged=len(self._lots_flagged),
                average_toggle_percentile=round(self._average_toggle_percentile, 6),
            )

    def _optional_chain_names(self) -> set[str]:
        names: set[str] = set()
        try:
            cpm = self._data_loader.get_cpm_report()
        except AppException:
            cpm = None
        if isinstance(cpm, dict):
            scan_chains = cpm.get("scan_chains")
            if isinstance(scan_chains, dict):
                for key in scan_chains:
                    names.add(str(key))
            count = cpm.get("scan_chains_count")
            if isinstance(count, int) and count > 0:
                for index in range(1, count + 1):
                    names.add(f"CH{index}")

        try:
            metadata = self._data_loader.get_metadata()
        except AppException:
            metadata = None
        if isinstance(metadata, dict):
            count = metadata.get("chain_count")
            if isinstance(count, int) and count > 0:
                for index in range(1, count + 1):
                    names.add(f"CH{index}")
        return names

    def _ordering_hotspots(self) -> tuple[set[str], set[str]]:
        """Use OrderingService high-priority patterns to reinforce gap targets."""
        chains: set[str] = set()
        lots: set[str] = set()
        ordering = self._ordering_service.get_ordering()
        high_min = self._settings.ordering_high_priority_score_min
        pattern_index = self._feature_builder.get_index()
        for item in ordering.patterns:
            if item.order_score < high_min:
                continue
            feature = pattern_index.get(item.pattern_id)
            if feature is None:
                continue
            chains.update(feature.failed_chains)
            for log_name in feature.failed_logs:
                lot = _extract_lot(log_name)
                if lot:
                    lots.add(lot)
        return chains, lots


def _build_chain_stats(
    patterns: list[PatternFeature],
    optional_chains: set[str],
) -> dict[str, dict[str, float]]:
    """
    Derive per-chain toggle and failure density from PatternFeature caches only.

    Toggle: mean of pattern mean_toggle_coverage for patterns associated with the chain.
    Failure density: attributed fail_executions / attributed total_executions.
    """
    toggle_sums: dict[str, float] = defaultdict(float)
    toggle_counts: dict[str, int] = defaultdict(int)
    fail_sums: dict[str, float] = defaultdict(float)
    total_sums: dict[str, float] = defaultdict(float)

    discovered: set[str] = set(optional_chains)
    for feature in patterns:
        discovered.update(feature.failed_chains)

    chain_count = max(len(discovered), 1)
    global_toggle = (
        sum(f.mean_toggle_coverage for f in patterns) / len(patterns)
        if patterns
        else 0.0
    )

    for feature in patterns:
        share_total = feature.total_executions / chain_count
        for chain in discovered:
            total_sums[chain] += share_total

        if feature.failed_chains:
            share_fail = feature.fail_executions / len(feature.failed_chains)
            for chain in feature.failed_chains:
                fail_sums[chain] += share_fail
                toggle_sums[chain] += feature.mean_toggle_coverage
                toggle_counts[chain] += 1

    stats: dict[str, dict[str, float]] = {}
    for chain in sorted(discovered):
        mean_toggle = (
            toggle_sums[chain] / toggle_counts[chain]
            if toggle_counts[chain] > 0
            else global_toggle
        )
        total = total_sums[chain]
        density = (fail_sums[chain] / total) if total > 0 else 0.0
        stats[chain] = {
            "mean_toggle_coverage": float(mean_toggle),
            "failure_density": float(density),
            "failed_executions": float(fail_sums[chain]),
            "total_executions": float(total),
        }
    return stats


def _build_lot_stats(patterns: list[PatternFeature]) -> dict[str, dict[str, float]]:
    lot_fail_logs: dict[str, set[str]] = defaultdict(set)
    lot_patterns: dict[str, set[str]] = defaultdict(set)

    for feature in patterns:
        for log_name in feature.failed_logs:
            lot = _extract_lot(log_name)
            if not lot:
                continue
            lot_fail_logs[lot].add(log_name)
            lot_patterns[lot].add(feature.pattern_id)

    if not lot_patterns:
        return {}

    max_fail_logs = max(len(logs) for logs in lot_fail_logs.values()) or 1
    stats: dict[str, dict[str, float]] = {}
    for lot in sorted(lot_patterns):
        # Relative log-failure concentration across lots (dataset-relative).
        density = len(lot_fail_logs[lot]) / max_fail_logs
        stats[lot] = {
            "failure_density": float(density),
            "pattern_diversity": float(len(lot_patterns[lot])),
        }
    return stats


def _build_requests(
    *,
    low_toggle_chains: list[str],
    high_fail_chains: list[str],
    gap_lots: list[str],
    high_priority_chains: set[str],
    high_priority_lots: set[str],
) -> list[AdditionalPatternRequest]:
    requests: list[AdditionalPatternRequest] = []
    request_index = 1

    if low_toggle_chains:
        rationale: list[GapRationaleCode] = ["LOW_TOGGLE_COVERAGE"]
        if any(chain in high_priority_chains for chain in low_toggle_chains):
            rationale.append("HIGH_PRIORITY_ORDERING")
        requests.append(
            AdditionalPatternRequest(
                request_only=True,
                request_id=f"GAP-{request_index:03d}",
                target_chains=low_toggle_chains,
                target_lots=[],
                suggested_fault_model=_suggest_fault_model(rationale),
                rationale=rationale,
            )
        )
        request_index += 1

    if high_fail_chains:
        rationale = ["HIGH_FAILURE_DENSITY"]
        if any(chain in high_priority_chains for chain in high_fail_chains):
            rationale.append("HIGH_PRIORITY_ORDERING")
        # Avoid duplicating an identical chain set already emitted.
        if not requests or requests[-1].target_chains != high_fail_chains:
            requests.append(
                AdditionalPatternRequest(
                    request_only=True,
                    request_id=f"GAP-{request_index:03d}",
                    target_chains=high_fail_chains,
                    target_lots=[],
                    suggested_fault_model=_suggest_fault_model(rationale),
                    rationale=rationale,
                )
            )
            request_index += 1

    if gap_lots:
        rationale = ["HIGH_FAILURE_DENSITY", "LOW_PATTERN_DIVERSITY"]
        if any(lot in high_priority_lots for lot in gap_lots):
            rationale.append("HIGH_PRIORITY_ORDERING")
        requests.append(
            AdditionalPatternRequest(
                request_only=True,
                request_id=f"GAP-{request_index:03d}",
                target_chains=[],
                target_lots=gap_lots,
                suggested_fault_model=_suggest_fault_model(rationale),
                rationale=rationale,
            )
        )

    for item in requests:
        item.request_only = True
    return requests


def _suggest_fault_model(rationale: list[GapRationaleCode]) -> SuggestedFaultModel:
    if "LOW_TOGGLE_COVERAGE" in rationale and "HIGH_FAILURE_DENSITY" not in rationale:
        return "stuck-at"
    if "HIGH_FAILURE_DENSITY" in rationale:
        return "transition"
    if "LOW_TOGGLE_COVERAGE" in rationale:
        return "stuck-at"
    return "Unknown"


def _average_toggle_percentile(toggle_by_chain: dict[str, float]) -> float:
    """Average empirical percentile rank of chain toggle coverages."""
    if not toggle_by_chain:
        return 0.0
    values = list(toggle_by_chain.values())
    ordered = sorted(values)
    n = len(ordered)
    ranks: list[float] = []
    for value in values:
        # Mid-rank percentile for ties.
        less = sum(1 for item in ordered if item < value)
        equal = sum(1 for item in ordered if item == value)
        percentile = ((less + 0.5 * equal) / n) * 100.0
        ranks.append(percentile)
    return sum(ranks) / len(ranks)


_gap_service: GapAnalysisService | None = None
_service_lock = RLock()


def get_gap_analysis_service(
    settings: Settings | None = None,
    data_loader: DataLoader | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
    ordering_service: OrderingService | None = None,
) -> GapAnalysisService:
    """Return the process-wide GapAnalysisService singleton."""
    global _gap_service
    with _service_lock:
        if _gap_service is None:
            cfg = settings or get_settings()
            loader = data_loader or get_data_loader(cfg)
            builder = feature_builder or get_pattern_feature_builder(loader)
            ordering = ordering_service or get_ordering_service(cfg, loader, builder)
            _gap_service = GapAnalysisService(cfg, loader, builder, ordering)
        return _gap_service


def reset_gap_analysis_service() -> None:
    """Clear the GapAnalysisService singleton."""
    global _gap_service
    with _service_lock:
        _gap_service = None
