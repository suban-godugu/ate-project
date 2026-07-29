"""File-based recommendation repository (swapable for DB later)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ...core.logging import get_logger
from ...domain.schemas import OptimizationRecommendation

logger = get_logger(__name__)


class RecommendationRepository:
    """Repository Pattern — JSON file store under data/recommendations."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, rec_id: str) -> Path:
        return self.root / f"{rec_id}.json"

    async def save(self, recommendation: OptimizationRecommendation) -> OptimizationRecommendation:
        path = self._path(recommendation.id)
        path.write_text(
            recommendation.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("Saved recommendation id=%s lot=%s", recommendation.id, recommendation.lot_id)
        return recommendation

    async def get(self, rec_id: str) -> Optional[OptimizationRecommendation]:
        path = self._path(rec_id)
        if not path.exists():
            return None
        return OptimizationRecommendation.model_validate_json(path.read_text(encoding="utf-8"))

    async def list(
        self,
        *,
        q: Optional[str] = None,
        risk_level: Optional[str] = None,
        device: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OptimizationRecommendation]:
        items: list[OptimizationRecommendation] = []
        for path in sorted(self.root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                items.append(
                    OptimizationRecommendation.model_validate_json(path.read_text(encoding="utf-8"))
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping corrupt recommendation file %s: %s", path, exc)

        if risk_level:
            items = [i for i in items if i.risk_level.lower() == risk_level.lower()]
        if device:
            items = [i for i in items if device.lower() in i.device.lower()]
        if q:
            ql = q.lower()
            items = [
                i
                for i in items
                if ql in i.lot_id.lower()
                or ql in i.device.lower()
                or ql in i.summary.lower()
                or ql in i.recommended_strategy.lower()
            ]
        return items[offset : offset + limit]

    async def delete(self, rec_id: str) -> bool:
        path = self._path(rec_id)
        if path.exists():
            path.unlink()
            return True
        return False

    async def count(self) -> int:
        return len(list(self.root.glob("*.json")))
