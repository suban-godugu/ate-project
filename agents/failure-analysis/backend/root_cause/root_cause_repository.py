"""Persistence for FA-FR-009 root cause prediction runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import RootCausePredictionRun, TestRecordRow


class RootCauseRepository:
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

    async def save_run(self, report: dict[str, Any]) -> RootCausePredictionRun:
        run = RootCausePredictionRun(
            upload_id=report.get("upload_id"),
            status="completed",
            processing_ms=float(report.get("processing_ms", 0.0)),
            semantic_search_ms=float(report.get("semantic_search_ms", 0.0)),
            total_predictions=int(report.get("total_predictions", 0)),
            average_confidence=float(report.get("average_confidence", 0.0)),
            high_confidence_count=sum(
                1
                for p in report.get("predictions", [])
                if float(p.get("confidence_score", 0)) >= 0.75
            ),
            ml_model_trained=1 if report.get("ml_model_trained") else 0,
            report_json=report,
            dashboard_json=report.get("engineering_dashboard", {}),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, run_id: str) -> RootCausePredictionRun | None:
        return await self._session.get(RootCausePredictionRun, run_id)

    async def get_latest_or(self, run_id: str | None = None) -> RootCausePredictionRun | None:
        if run_id:
            return await self.get_run(run_id)
        runs = await self.list_runs(limit=1)
        return runs[0] if runs else None

    async def list_runs(self, *, limit: int = 50) -> list[RootCausePredictionRun]:
        stmt = (
            select(RootCausePredictionRun)
            .order_by(RootCausePredictionRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
