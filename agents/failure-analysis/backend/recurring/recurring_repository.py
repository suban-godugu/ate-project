"""Persistence for recurring failure analysis runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import RecurringAnalysisRun, RecurringEvent, TestRecordRow


class RecurringRepository:
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

    async def save_run(self, report: dict[str, Any]) -> RecurringAnalysisRun:
        summary = report.get("classification_summary", {})
        run = RecurringAnalysisRun(
            upload_id=report.get("upload_id"),
            status="completed",
            processing_ms=float(report.get("processing_ms", 0.0)),
            recurring_count=int(summary.get("total_recurring_signatures", 0)),
            impacted_lot_count=int(summary.get("impacted_lot_count", 0)),
            alert_count=int(summary.get("alert_count", 0)),
            report_json=report,
            dashboard_json=report.get("dashboard", {}),
        )
        self._session.add(run)
        await self._session.flush()

        for row in report.get("recurring_failure_list", []):
            event = RecurringEvent(
                id=str(row.get("recurrence_id", "")),
                run_id=run.id,
                signature_type=str(row.get("signature_type", "")),
                entity_key=str(row.get("entity_key", "")),
                confidence=float(row.get("confidence", 0.0)),
                failure_count=int(row.get("failure_count", 0)),
                entity_count=int(row.get("entity_count", 0)),
                payload=row,
            )
            self._session.add(event)
        await self._session.flush()
        return run

    async def get_run(self, run_id: str) -> RecurringAnalysisRun | None:
        return await self._session.get(RecurringAnalysisRun, run_id)

    async def get_latest_or(self, run_id: str | None = None) -> RecurringAnalysisRun | None:
        if run_id:
            return await self.get_run(run_id)
        runs = await self.list_runs(limit=1)
        return runs[0] if runs else None

    async def list_runs(self, *, limit: int = 50) -> list[RecurringAnalysisRun]:
        stmt = (
            select(RecurringAnalysisRun)
            .order_by(RecurringAnalysisRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def historical_summaries(self, *, limit: int = 10) -> list[dict[str, Any]]:
        runs = await self.list_runs(limit=limit)
        return [
            {
                "run_id": run.id,
                "upload_id": run.upload_id,
                "recurring_failure_list": run.report_json.get("recurring_failure_list", []),
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
            for run in runs
        ]
