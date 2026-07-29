"""Loop-isolated background execution for FA-FR-006."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.correlation.production_service import ProductionCorrelationService
from backend.correlation.schemas import AnalyzeCorrelationRequest
from backend.database import create_engine


async def run_correlation_background(payload: dict, execution_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionCorrelationService(session).execute(
                AnalyzeCorrelationRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
