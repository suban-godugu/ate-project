"""Loop-isolated background execution for FA-FR-010."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.database import create_engine
from backend.reporting.production_service import ProductionReportingService
from backend.reporting.schemas import ExportReportRequest, GenerateReportRequest


async def run_report_generation_background(payload: dict, report_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionReportingService(session).execute(
                GenerateReportRequest.model_validate(payload),
                report_id=report_id,
            )
    finally:
        await engine.dispose()


async def run_report_export_background(payload: dict, export_id: str) -> None:
    engine = create_engine()
    sessions = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with sessions() as session:
            await ProductionReportingService(session).export(
                ExportReportRequest.model_validate(payload),
                export_id=export_id,
            )
    finally:
        await engine.dispose()
