"""Loop-isolated background execution for FA-FR-005."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import create_engine
from backend.recurring.production_service import ProductionRecurrenceService
from backend.recurring.schemas import AnalyzeRecurrenceRequest


async def run_recurrence_background(payload: dict, execution_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionRecurrenceService(session).execute(
                AnalyzeRecurrenceRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
