"""Loop-isolated asynchronous FA-FR-003 execution."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from analytics.failure_rates.production_service import ProductionFailureRateService
from analytics.failure_rates.schemas import ComputeFailureRatesRequest
from backend.database import create_engine


async def run_failure_rate_background(payload: dict, execution_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionFailureRateService(session).execute(
                ComputeFailureRatesRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
