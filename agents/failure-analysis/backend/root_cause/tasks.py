"""Loop-isolated background execution for FA-FR-009."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import create_engine
from backend.root_cause.production_service import ProductionFaultPredictionService
from backend.root_cause.schemas import PredictFaultRequest


async def run_fault_prediction_background(payload: dict, execution_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionFaultPredictionService(session).execute(
                PredictFaultRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
