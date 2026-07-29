"""Isolated asynchronous execution for FA-FR-002."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analytics.pattern_detection.detection_service import DetectionService
from analytics.pattern_detection.schemas import DetectPatternsRequest
from backend.database import create_engine


async def run_detection_background(payload: dict, execution_id: str) -> None:
    """Run after HTTP acknowledgement with a loop-local asyncpg engine."""
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await DetectionService(session).execute(
                DetectPatternsRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
