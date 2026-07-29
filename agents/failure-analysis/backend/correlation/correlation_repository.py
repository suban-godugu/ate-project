"""Persistence for FA-FR-006 correlation analysis runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import CorrelationAnalysisRun, TestRecordRow


class CorrelationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def load_test_records(self, upload_id: str) -> list[TestRecord]:
        stmt = select(TestRecordRow).where(TestRecordRow.upload_id == upload_id)
        result = await self._session.execute(stmt)
        records: list[TestRecord] = []
        for row in result.scalars().all():
            payload = dict(row.payload)
            payload.setdefault("lot_id", row.lot_id)
            payload.setdefault("wafer_id", row.wafer_id)
            payload.setdefault("die_id", row.die_id)
            records.append(TestRecord.from_dict(payload))
        return records

    async def save_run(self, report: dict[str, Any]) -> CorrelationAnalysisRun:
        top = report.get("top_failing_patterns", [])
        leader_score = float(top[0]["correlation_score"]) if top else 0.0
        run = CorrelationAnalysisRun(
            upload_id=report.get("upload_id"),
            status="completed",
            processing_ms=float(report.get("processing_ms", 0.0)),
            pattern_count=int(report.get("correlation_report_total", 0)),
            top_correlation_score=leader_score,
            report_json=report,
            matrix_json=report.get("correlation_matrix", {}),
            network_json=report.get("failure_dependency_graph", {}),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, run_id: str) -> CorrelationAnalysisRun | None:
        return await self._session.get(CorrelationAnalysisRun, run_id)

    async def get_latest_or(self, run_id: str | None = None) -> CorrelationAnalysisRun | None:
        if run_id:
            return await self.get_run(run_id)
        runs = await self.list_runs(limit=1)
        return runs[0] if runs else None

    async def list_runs(self, *, limit: int = 50) -> list[CorrelationAnalysisRun]:
        stmt = (
            select(CorrelationAnalysisRun)
            .order_by(CorrelationAnalysisRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
