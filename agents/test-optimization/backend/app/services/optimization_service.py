"""Application service — orchestrates LLM + heuristic + persistence."""

from __future__ import annotations

from typing import Optional

import httpx

from ..core.config import Settings
from ..core.logging import get_logger
from ..domain.models import (
    OptimizationContext,
    PatternRecommendationInput,
    ScanDebugRecommendationInput,
)
from ..domain.schemas import (
    AnalyticsSummary,
    OptimizationRecommendation,
    RecommendationListResponse,
)
from ..infrastructure.llm.client import LLMClient
from ..infrastructure.repositories.recommendation_repository import RecommendationRepository
from .heuristic_engine import detect_data_gaps, run_heuristic

logger = get_logger(__name__)


class OptimizationService:
    def __init__(
        self,
        settings: Settings,
        llm: LLMClient,
        repository: RecommendationRepository,
    ) -> None:
        self.settings = settings
        self.llm = llm
        self.repository = repository

    async def optimize(
        self, context: OptimizationContext, *, persist: bool = True
    ) -> OptimizationRecommendation:
        context = await self._enrich_upstream(context)
        gaps = detect_data_gaps(context)
        recommendation: OptimizationRecommendation

        if self.llm.enabled:
            try:
                raw = await self.llm.generate_recommendation_json(
                    context.model_dump(mode="json"), gaps
                )
                recommendation = self._coerce_llm_result(raw, context, gaps)
                recommendation.engine = "llm"
            except Exception as exc:  # noqa: BLE001
                logger.warning("LLM failed (%s); falling back to heuristic", exc)
                recommendation = run_heuristic(context)
        else:
            recommendation = run_heuristic(context)

        if persist:
            await self.repository.save(recommendation)
        return recommendation

    async def get(self, rec_id: str) -> Optional[OptimizationRecommendation]:
        return await self.repository.get(rec_id)

    async def list_recommendations(
        self,
        *,
        q: Optional[str] = None,
        risk_level: Optional[str] = None,
        device: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> RecommendationListResponse:
        items = await self.repository.list(
            q=q, risk_level=risk_level, device=device, limit=limit, offset=offset
        )
        total = await self.repository.count()
        return RecommendationListResponse(items=items, total=total)

    async def compare(self, ids: list[str]) -> list[OptimizationRecommendation]:
        out: list[OptimizationRecommendation] = []
        for rid in ids:
            item = await self.repository.get(rid)
            if item:
                out.append(item)
        return out

    async def analytics(self) -> AnalyticsSummary:
        items = await self.repository.list(limit=500)
        if not items:
            return AnalyticsSummary(
                total_recommendations=0,
                avg_confidence=0.0,
                risk_distribution={"Low": 0, "Medium": 0, "High": 0},
                recent=[],
            )
        dist = {"Low": 0, "Medium": 0, "High": 0}
        for i in items:
            dist[i.risk_level] = dist.get(i.risk_level, 0) + 1
        avg_conf = sum(i.confidence for i in items) / len(items)
        return AnalyticsSummary(
            total_recommendations=len(items),
            avg_confidence=round(avg_conf, 3),
            risk_distribution=dist,
            recent=items[:10],
        )

    async def delete(self, rec_id: str) -> bool:
        return await self.repository.delete(rec_id)

    def _coerce_llm_result(
        self, raw: dict, context: OptimizationContext, gaps: list[str]
    ) -> OptimizationRecommendation:
        raw.setdefault("device", context.device)
        raw.setdefault("lot_id", context.lot_id)
        raw.setdefault("data_gaps", gaps)
        assumptions = list(raw.get("assumptions") or [])
        for a in context.assumptions:
            if a not in assumptions:
                assumptions.append(a)
        for g in gaps:
            note = f"Missing input '{g}' — recommendation may be incomplete."
            if note not in assumptions:
                assumptions.append(note)
        raw["assumptions"] = assumptions
        raw.setdefault("coverage_recommendations", [])
        raw.setdefault("expected_yield_improvement", "N/A")
        raw.setdefault("business_impact", "")
        raw.setdefault("risk_score", 0)
        return OptimizationRecommendation.model_validate(raw)

    async def _enrich_upstream(self, context: OptimizationContext) -> OptimizationContext:
        updates: dict = {}
        if self.settings.pattern_agent_url and context.pattern_recommendation is None:
            data = await self._fetch(self.settings.pattern_agent_url)
            if data:
                updates["pattern_recommendation"] = PatternRecommendationInput.model_validate(data)
        if self.settings.scan_debug_agent_url and context.scan_debug_recommendation is None:
            data = await self._fetch(self.settings.scan_debug_agent_url)
            if data:
                updates["scan_debug_recommendation"] = ScanDebugRecommendationInput.model_validate(
                    data
                )
        return context.model_copy(update=updates) if updates else context

    async def _fetch(self, url: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                return data if isinstance(data, dict) else None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Upstream fetch failed %s: %s", url, exc)
            return None
