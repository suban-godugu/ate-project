"""Loop-isolated background execution for FA-FR-007."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import create_engine
from backend.die_analysis.production_service import ProductionDieAnalysisService
from backend.die_analysis.schemas import AnalyzeDieRequest


async def run_die_analysis_background(payload: dict, execution_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionDieAnalysisService(session).execute(
                AnalyzeDieRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
