"""Persistence layer for FA-FR-004 classification runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import ClassifiedFault, ClassificationRun, TestRecordRow


class ClassificationRepository:
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

    async def save_run(self, report: dict[str, Any]) -> ClassificationRun:
        summary = report.get("classification_summary", {})
        run = ClassificationRun(
            upload_id=report.get("upload_id"),
            status="completed",
            processing_ms=float(report.get("processing_ms", 0.0)),
            total_faults=int(summary.get("total_faults", 0)),
            unique_categories=int(summary.get("unique_categories", 0)),
            dominant_category=str(summary.get("dominant_category", "")),
            estimated_accuracy_pct=float(report.get("estimated_accuracy_pct", 0.0)),
            report_json=report,
        )
        self._session.add(run)
        await self._session.flush()

        for row in report.get("classified_faults", []):
            fault = ClassifiedFault(
                id=str(row.get("fault_id", "")),
                run_id=run.id,
                lot_id=str(row.get("lot_id", "")),
                wafer_id=str(row.get("wafer_id", "")),
                die_id=str(row.get("die_id", "")),
                pattern_id=str(row.get("pattern_id", "")),
                fault_category=str(row.get("fault_category", "")),
                classification_confidence=float(row.get("classification_confidence", 0.0)),
                method=str(row.get("method", "")),
                payload=row,
            )
            self._session.add(fault)
        await self._session.flush()
        return run

    async def get_run(self, run_id: str) -> ClassificationRun | None:
        return await self._session.get(ClassificationRun, run_id)

    async def get_latest_or(self, run_id: str | None = None) -> ClassificationRun | None:
        if run_id:
            return await self.get_run(run_id)
        runs = await self.list_runs(limit=1)
        return runs[0] if runs else None

    async def list_runs(self, *, limit: int = 50) -> list[ClassificationRun]:
        stmt = (
            select(ClassificationRun)
            .order_by(ClassificationRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_fault(self, fault_id: str) -> ClassifiedFault | None:
        return await self._session.get(ClassifiedFault, fault_id)

    async def list_faults(
        self,
        *,
        run_id: str | None = None,
        limit: int = 100,
    ) -> list[ClassifiedFault]:
        stmt = select(ClassifiedFault).order_by(
            ClassifiedFault.classification_confidence.desc()
        )
        if run_id:
            stmt = stmt.where(ClassifiedFault.run_id == run_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
