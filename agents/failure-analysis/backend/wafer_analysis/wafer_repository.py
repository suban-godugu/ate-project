"""Persistence for FA-FR-008 wafer analysis runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import TestRecordRow, WaferAnalysisRun


class WaferAnalysisRepository:
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

    async def save_run(self, report: dict[str, Any]) -> WaferAnalysisRun:
        run = WaferAnalysisRun(
            upload_id=report.get("upload_id"),
            status="completed",
            processing_ms=float(report.get("processing_ms", 0.0)),
            total_wafers=int(report.get("total_wafers", 0)),
            overall_yield_pct=float(report.get("overall_yield_pct", 0.0)),
            outlier_wafer_count=int(report.get("outlier_wafer_count", 0)),
            hotspot_count=int(report.get("hotspot_analysis", {}).get("hotspot_count", 0)),
            cluster_count=int(report.get("cluster_report", {}).get("cluster_count", 0)),
            report_json=report,
            map_json=report.get("wafer_heatmap", {}),
            dashboard_json=report.get("engineering_dashboard", {}),
        )
        self._session.add(run)
        await self._session.flush()
        return run

    async def get_run(self, run_id: str) -> WaferAnalysisRun | None:
        return await self._session.get(WaferAnalysisRun, run_id)

    async def get_latest_or(self, run_id: str | None = None) -> WaferAnalysisRun | None:
        if run_id:
            return await self.get_run(run_id)
        runs = await self.list_runs(limit=1)
        return runs[0] if runs else None

    async def list_runs(self, *, limit: int = 50) -> list[WaferAnalysisRun]:
        stmt = (
            select(WaferAnalysisRun)
            .order_by(WaferAnalysisRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
