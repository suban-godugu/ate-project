"""Persistence for failure rate calculation runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import FailureRateRun, TestRecordRow


class FailureRateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_test_records(self, upload_id: str) -> list[TestRecord]:
        stmt = select(TestRecordRow).where(TestRecordRow.upload_id == upload_id)
        result = await self._session.execute(stmt)
        records: list[TestRecord] = []
        for row in result.scalars().all():
            payload = dict(row.payload)
            records.append(TestRecord.from_dict(payload))
        return records

    async def save_run(self, report: dict[str, Any], dashboard: dict[str, Any]) -> FailureRateRun:
        run = FailureRateRun(
            upload_id=report.get("upload_id"),
            processing_ms=float(report.get("processing_ms", 0.0)),
            overall_yield_pct=float(
                report.get("summary", {}).get("overall_yield_pct", 0.0)
            ),
            overall_failure_rate_pct=float(
                report.get("summary", {}).get("overall_failure_rate_pct", 0.0)
            ),
            report_json=report,
            dashboard_json=dashboard,
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, run_id: str) -> FailureRateRun | None:
        return await self._session.get(FailureRateRun, run_id)

    async def list_runs(self, *, limit: int = 50) -> list[FailureRateRun]:
        stmt = (
            select(FailureRateRun)
            .order_by(FailureRateRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def historical_summaries(self, *, limit: int = 10) -> list[dict[str, Any]]:
        runs = await self.list_runs(limit=limit)
        return [
            {
                "run_id": run.id,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "summary": {
                    "overall_yield_pct": run.overall_yield_pct,
                    "overall_failure_rate_pct": run.overall_failure_rate_pct,
                },
            }
            for run in runs
        ]
