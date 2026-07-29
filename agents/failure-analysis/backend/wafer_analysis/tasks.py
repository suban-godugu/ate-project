"""Loop-isolated background execution for FA-FR-008."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import create_engine
from backend.wafer_analysis.production_service import ProductionWaferAnalysisService
from backend.wafer_analysis.schemas import AnalyzeWaferRequest


async def run_wafer_analysis_background(payload: dict, execution_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionWaferAnalysisService(session).execute(
                AnalyzeWaferRequest.model_validate(payload),
                execution_id=execution_id,
            )
    finally:
        await engine.dispose()
