"""Recommendation orchestrator — integration layer only, no new algorithms."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from backend.core.config import Settings, get_settings
from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.orchestrator import (
    OrchestratorArtifacts,
    OrchestratorResponse,
    RecommendationFeasibility,
    UnifiedRecommendationBundle,
    UnifiedRecommendationSummary,
)
from backend.services.coverage_service import CoverageService, get_coverage_service
from backend.services.gap_analysis_service import (
    GapAnalysisService,
    get_gap_analysis_service,
)
from backend.services.low_power_service import LowPowerService, get_low_power_service
from backend.services.ordering_service import OrderingService, get_ordering_service
from backend.services.pattern_feature_builder import (
    PatternFeatureBuilder,
    get_pattern_feature_builder,
)
from backend.services.redundancy_service import (
    RedundancyService,
    get_redundancy_service,
)
from backend.services.removal_service import RemovalService, get_removal_service


class RecommendationOrchestrator:
    """
    Aggregate existing recommendation services into one dashboard contract.

    Does not recompute analytics or alter recommendation algorithms.
    """

    def __init__(
        self,
        settings: Settings,
        feature_builder: PatternFeatureBuilder,
        redundancy_service: RedundancyService,
        removal_service: RemovalService,
        ordering_service: OrderingService,
        gap_analysis_service: GapAnalysisService,
        low_power_service: LowPowerService,
        coverage_service: CoverageService,
    ) -> None:
        self._settings = settings
        self._feature_builder = feature_builder
        self._redundancy_service = redundancy_service
        self._removal_service = removal_service
        self._ordering_service = ordering_service
        self._gap_analysis_service = gap_analysis_service
        self._low_power_service = low_power_service
        self._coverage_service = coverage_service
        self._lock = RLock()
        self._bundle: UnifiedRecommendationBundle | None = None
        self._artifacts = OrchestratorArtifacts()
        self._built_at: datetime | None = None

    def is_ready(self) -> bool:
        with self._lock:
            return self._bundle is not None

    def ensure_built(self) -> OrchestratorResponse:
        if not self.is_ready():
            return self.build()
        return self._snapshot()

    def build(self) -> OrchestratorResponse:
        """Call every recommendation service once and persist artifacts."""
        logger = get_logger()
        logger.info("Recommendation orchestration started")

        self._validate_services()

        patterns = self._feature_builder.ensure_built()
        redundancy_stats = self._redundancy_service.get_statistics()
        redundancy = self._redundancy_service.get_redundant_patterns()
        removal = self._removal_service.get_recommendations()
        ordering = self._ordering_service.get_ordering()
        gaps = self._gap_analysis_service.get_requests()
        low_power = self._low_power_service.get_pattern_set()
        coverage = self._coverage_service.get_recommendations()

        bundle = UnifiedRecommendationBundle(
            summary=UnifiedRecommendationSummary(
                patterns_analyzed=patterns.total,
                clusters=redundancy_stats.clusters,
                removal_candidates=removal.total,
                ordering_candidates=ordering.total,
                gap_requests=gaps.total,
                low_power_patterns=low_power.total,
                coverage_recommendations=coverage.total,
            ),
            feasibility=RecommendationFeasibility(),
            redundant_patterns=[item.model_dump(mode="json") for item in redundancy.patterns],
            removal_recommendations=[
                item.model_dump(mode="json") for item in removal.recommendations
            ],
            ordered_patterns=[item.model_dump(mode="json") for item in ordering.patterns],
            additional_pattern_requests=[
                item.model_dump(mode="json") for item in gaps.requests
            ],
            low_activity_pattern_set=[
                item.model_dump(mode="json") for item in low_power.patterns
            ],
            coverage_gap_recommendations=[
                item.model_dump(mode="json") for item in coverage.recommendations
            ],
        )

        artifacts = self._write_artifacts(bundle)
        built_at = datetime.now(timezone.utc)

        with self._lock:
            self._bundle = bundle
            self._artifacts = artifacts
            self._built_at = built_at

        logger.info(
            "Recommendation orchestration completed patterns=%d removal=%d "
            "ordering=%d gaps=%d low_power=%d coverage=%d",
            bundle.summary.patterns_analyzed,
            bundle.summary.removal_candidates,
            bundle.summary.ordering_candidates,
            bundle.summary.gap_requests,
            bundle.summary.low_power_patterns,
            bundle.summary.coverage_recommendations,
        )
        logger.info(
            "Orchestrator artifacts written json=%s csv=%s md=%s",
            artifacts.json_path,
            artifacts.csv_path,
            artifacts.markdown_path,
        )
        return self._snapshot()

    def refresh(self) -> OrchestratorResponse:
        """Rebuild unified recommendations and regenerate report files."""
        get_logger().info("Recommendation orchestration refresh requested")
        # Explicitly refresh dependent caches without changing algorithms.
        self._feature_builder.refresh()
        self._redundancy_service.refresh()
        self._removal_service.refresh()
        self._ordering_service.refresh()
        self._gap_analysis_service.refresh()
        self._low_power_service.refresh()
        self._coverage_service.refresh()
        result = self.build()
        get_logger().info("Recommendation orchestration refresh completed")
        return result

    def get_unified(self) -> OrchestratorResponse:
        return self.ensure_built()

    def get_summary(self) -> UnifiedRecommendationSummary:
        return self.ensure_built().recommendations.summary

    def get_dashboard(self) -> dict[str, Any]:
        """Dashboard-ready payload without requiring additional client transforms."""
        payload = self.ensure_built()
        bundle = payload.recommendations
        return {
            "summary": bundle.summary.model_dump(mode="json"),
            "feasibility": bundle.feasibility.model_dump(mode="json"),
            "tables": {
                "redundant_patterns": bundle.redundant_patterns,
                "removal_recommendations": bundle.removal_recommendations,
                "ordered_patterns": bundle.ordered_patterns,
                "additional_pattern_requests": bundle.additional_pattern_requests,
                "low_activity_pattern_set": bundle.low_activity_pattern_set,
                "coverage_gap_recommendations": bundle.coverage_gap_recommendations,
            },
            "artifacts": payload.artifacts.model_dump(mode="json"),
            "built_at": payload.built_at.isoformat() if payload.built_at else None,
        }

    def _snapshot(self) -> OrchestratorResponse:
        with self._lock:
            if self._bundle is None:
                raise AppException(
                    "Unified recommendations are unavailable",
                    status_code=503,
                )
            return OrchestratorResponse(
                success=True,
                message="Unified recommendations ready",
                built_at=self._built_at,
                recommendations=self._bundle,
                artifacts=self._artifacts,
            )

    def _validate_services(self) -> None:
        missing: list[str] = []
        checks = {
            "PatternFeatureBuilder": self._feature_builder,
            "RedundancyService": self._redundancy_service,
            "RemovalService": self._removal_service,
            "OrderingService": self._ordering_service,
            "GapAnalysisService": self._gap_analysis_service,
            "LowPowerService": self._low_power_service,
            "CoverageService": self._coverage_service,
        }
        for name, service in checks.items():
            if service is None:
                missing.append(name)
        if missing:
            raise AppException(
                "Recommendation services unavailable",
                status_code=503,
                details={"missing": missing},
            )

    def _write_artifacts(
        self,
        bundle: UnifiedRecommendationBundle,
    ) -> OrchestratorArtifacts:
        output_dir = Path(self._settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        json_path = output_dir / "pattern_recommendations.json"
        csv_path = output_dir / "pattern_recommendations.csv"
        md_path = output_dir / "pattern_recommendation_report.md"

        with json_path.open("w", encoding="utf-8") as handle:
            json.dump(bundle.model_dump(mode="json"), handle, indent=4)

        rows = _flatten_for_csv(bundle)
        fieldnames = [
            "recommendation_type",
            "pattern_id",
            "priority",
            "reason_codes",
            "cluster_id",
            "severity",
            "confidence",
        ]
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        md_path.write_text(_render_markdown(bundle), encoding="utf-8")

        return OrchestratorArtifacts(
            json_path=str(json_path.resolve()),
            csv_path=str(csv_path.resolve()),
            markdown_path=str(md_path.resolve()),
        )


def _flatten_for_csv(bundle: UnifiedRecommendationBundle) -> list[dict[str, Any]]:
    """Flatten heterogeneous recommendations into dashboard-friendly rows."""
    rows: list[dict[str, Any]] = []

    for item in bundle.redundant_patterns:
        rows.append(
            {
                "recommendation_type": "REDUNDANCY",
                "pattern_id": item.get("pattern_id", ""),
                "priority": item.get("similarity_to_representative", ""),
                "reason_codes": "REDUNDANT_NEAR_DUP"
                if item.get("redundant_flag")
                else "REPRESENTATIVE",
                "cluster_id": item.get("cluster_id", ""),
                "severity": "",
                "confidence": item.get("similarity_to_representative", ""),
            }
        )

    for item in bundle.removal_recommendations:
        rows.append(
            {
                "recommendation_type": "REMOVAL",
                "pattern_id": item.get("pattern_id", ""),
                "priority": item.get("removal_priority", ""),
                "reason_codes": _join_codes(item.get("reason_codes")),
                "cluster_id": item.get("cluster_id", ""),
                "severity": "",
                "confidence": item.get("confidence", ""),
            }
        )

    for item in bundle.ordered_patterns:
        rows.append(
            {
                "recommendation_type": "ORDERING",
                "pattern_id": item.get("pattern_id", ""),
                "priority": item.get("order_score", ""),
                "reason_codes": _join_codes(item.get("reason_codes")),
                "cluster_id": "",
                "severity": item.get("severity", ""),
                "confidence": item.get("order_score", ""),
            }
        )

    for item in bundle.additional_pattern_requests:
        rows.append(
            {
                "recommendation_type": "GAP_REQUEST",
                "pattern_id": item.get("request_id", ""),
                "priority": "",
                "reason_codes": _join_codes(item.get("rationale")),
                "cluster_id": "",
                "severity": "",
                "confidence": "",
            }
        )

    for item in bundle.low_activity_pattern_set:
        rows.append(
            {
                "recommendation_type": "LOW_POWER_PROXY",
                "pattern_id": item.get("pattern_id", ""),
                "priority": item.get("activity_score", ""),
                "reason_codes": _join_codes(item.get("reason_codes")),
                "cluster_id": "",
                "severity": "",
                "confidence": "",
            }
        )

    for item in bundle.coverage_gap_recommendations:
        rows.append(
            {
                "recommendation_type": item.get("recommendation_type", "COVERAGE"),
                "pattern_id": item.get("pattern_id", ""),
                "priority": item.get("priority", ""),
                "reason_codes": _join_codes(item.get("reason_codes")),
                "cluster_id": "",
                "severity": "",
                "confidence": item.get("priority", ""),
            }
        )

    return rows


def _join_codes(value: object) -> str:
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _render_markdown(bundle: UnifiedRecommendationBundle) -> str:
    summary = bundle.summary
    lines: list[str] = [
        "# Pattern Recommendation Report",
        "",
        "## Executive Summary",
        "",
        f"- Patterns analyzed: **{summary.patterns_analyzed}**",
        f"- Clusters: **{summary.clusters}**",
        f"- Removal candidates: **{summary.removal_candidates}**",
        f"- Ordering candidates: **{summary.ordering_candidates}**",
        f"- ATPG gap requests: **{summary.gap_requests}**",
        f"- Low-power (toggle proxy) patterns: **{summary.low_power_patterns}**",
        f"- Coverage proxy recommendations: **{summary.coverage_recommendations}**",
        "",
        "### Feasibility",
        "",
        f"- Redundant patterns: `{bundle.feasibility.redundant_patterns}`",
        f"- Pattern removal: `{bundle.feasibility.pattern_removal}`",
        f"- Pattern ordering: `{bundle.feasibility.pattern_ordering}`",
        f"- Additional ATPG: `{bundle.feasibility.additional_atpg}`",
        f"- Low-power sets: `{bundle.feasibility.low_power_sets}`",
        f"- Coverage improvement: `{bundle.feasibility.coverage_improvement}`",
        "",
        "## Redundant Patterns",
        "",
        f"Total redundant patterns: **{len(bundle.redundant_patterns)}**",
        "",
    ]
    for item in bundle.redundant_patterns[:20]:
        lines.append(
            f"- `{item.get('pattern_id')}` cluster=`{item.get('cluster_id')}` "
            f"sim={item.get('similarity_to_representative')} "
            f"rep=`{item.get('representative_pattern')}`"
        )
    if len(bundle.redundant_patterns) > 20:
        lines.append(f"- … {len(bundle.redundant_patterns) - 20} more")

    lines.extend(
        [
            "",
            "## Removal Recommendations",
            "",
            f"Total removal recommendations: **{len(bundle.removal_recommendations)}**",
            "",
        ]
    )
    for item in bundle.removal_recommendations[:20]:
        lines.append(
            f"- `{item.get('pattern_id')}` priority={item.get('removal_priority')} "
            f"confidence={item.get('confidence')} "
            f"reasons={_join_codes(item.get('reason_codes'))}"
        )
    if len(bundle.removal_recommendations) > 20:
        lines.append(f"- … {len(bundle.removal_recommendations) - 20} more")

    lines.extend(
        [
            "",
            "## Pattern Ordering",
            "",
            f"Total ordered patterns: **{len(bundle.ordered_patterns)}**",
            "",
            "Top 20 execution ranks:",
            "",
        ]
    )
    for item in bundle.ordered_patterns[:20]:
        lines.append(
            f"- rank={item.get('execution_rank')} `{item.get('pattern_id')}` "
            f"score={item.get('order_score')} severity={item.get('severity')}"
        )

    lines.extend(
        [
            "",
            "## ATPG Gap Requests",
            "",
            f"Total gap requests: **{len(bundle.additional_pattern_requests)}**",
            "",
            "_All gap entries are request-only and do not claim ATPG execution._",
            "",
        ]
    )
    for item in bundle.additional_pattern_requests:
        lines.append(
            f"- `{item.get('request_id')}` request_only={item.get('request_only')} "
            f"fault_model={item.get('suggested_fault_model')} "
            f"chains={len(item.get('target_chains') or [])} "
            f"lots={item.get('target_lots')} "
            f"rationale={_join_codes(item.get('rationale'))}"
        )

    lines.extend(
        [
            "",
            "## Low-Power Pattern Set",
            "",
            f"Total low-activity patterns: **{len(bundle.low_activity_pattern_set)}**",
            "",
            "_Toggle-activity proxy only — not measured power, IR-drop, or energy._",
            "",
        ]
    )
    for item in bundle.low_activity_pattern_set[:20]:
        lines.append(
            f"- `{item.get('pattern_id')}` activity={item.get('activity_score')} "
            f"proxy={item.get('power_proxy')} "
            f"reasons={_join_codes(item.get('reason_codes'))}"
        )
    if len(bundle.low_activity_pattern_set) > 20:
        lines.append(f"- … {len(bundle.low_activity_pattern_set) - 20} more")

    lines.extend(
        [
            "",
            "## Coverage Improvement Recommendations",
            "",
            f"Total coverage recommendations: **{len(bundle.coverage_gap_recommendations)}**",
            "",
            "_coverage_type = toggle_and_fail_proxy — not ATPG fault coverage._",
            "",
        ]
    )
    for item in bundle.coverage_gap_recommendations[:20]:
        lines.append(
            f"- type={item.get('recommendation_type')} "
            f"`{item.get('pattern_id')}` priority={item.get('priority')} "
            f"reasons={_join_codes(item.get('reason_codes'))}"
        )
    if len(bundle.coverage_gap_recommendations) > 20:
        lines.append(f"- … {len(bundle.coverage_gap_recommendations) - 20} more")

    lines.extend(
        [
            "",
            "---",
            "",
            "_Generated by Recommendation Orchestrator. Integration only — "
            "no new recommendation algorithms._",
            "",
        ]
    )
    return "\n".join(lines)


_orchestrator: RecommendationOrchestrator | None = None
_service_lock = RLock()


def get_recommendation_orchestrator(
    settings: Settings | None = None,
    feature_builder: PatternFeatureBuilder | None = None,
    redundancy_service: RedundancyService | None = None,
    removal_service: RemovalService | None = None,
    ordering_service: OrderingService | None = None,
    gap_analysis_service: GapAnalysisService | None = None,
    low_power_service: LowPowerService | None = None,
    coverage_service: CoverageService | None = None,
) -> RecommendationOrchestrator:
    """Return the process-wide RecommendationOrchestrator singleton."""
    global _orchestrator
    with _service_lock:
        if _orchestrator is None:
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
            ordering = ordering_service or get_ordering_service(
                settings=cfg,
                feature_builder=builder,
            )
            gap = gap_analysis_service or get_gap_analysis_service(
                settings=cfg,
                feature_builder=builder,
                ordering_service=ordering,
            )
            low_power = low_power_service or get_low_power_service(
                settings=cfg,
                feature_builder=builder,
                redundancy_service=redundancy,
                removal_service=removal,
            )
            coverage = coverage_service or get_coverage_service(
                settings=cfg,
                feature_builder=builder,
                ordering_service=ordering,
                gap_analysis_service=gap,
            )
            _orchestrator = RecommendationOrchestrator(
                cfg,
                builder,
                redundancy,
                removal,
                ordering,
                gap,
                low_power,
                coverage,
            )
        return _orchestrator


def reset_recommendation_orchestrator() -> None:
    """Clear the RecommendationOrchestrator singleton."""
    global _orchestrator
    with _service_lock:
        _orchestrator = None
