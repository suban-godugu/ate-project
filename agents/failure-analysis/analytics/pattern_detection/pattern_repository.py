"""Persistence layer for pattern analysis runs."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import DetectedPattern, PatternAnalysisRun, TestRecordRow


class PatternRepository:
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

    async def save_analysis(self, report: dict[str, Any]) -> PatternAnalysisRun:
        run = PatternAnalysisRun(
            upload_id=report.get("upload_id"),
            status="completed",
            failure_count=int(report.get("failure_count", 0)),
            unique_patterns=int(report.get("unique_patterns", 0)),
            processing_ms=float(report.get("processing_ms", 0.0)),
            report_json=report,
        )
        self._session.add(run)
        await self._session.flush()

        for row in report.get("pattern_ranking", []):
            pattern = DetectedPattern(
                analysis_id=run.id,
                pattern_id=str(row.get("pattern_id", "")),
                rank=int(row.get("rank", 0)),
                rank_score=float(row.get("rank_score", 0.0)),
                confidence=float(row.get("confidence", 0.0)),
                failure_count=int(row.get("failure_count", 0)),
                cluster_id=row.get("cluster_id"),
                is_anomaly=1 if row.get("is_anomaly") else 0,
                payload=row,
            )
            self._session.add(pattern)
        await self._session.flush()
        return run

    async def get_analysis(self, analysis_id: str) -> PatternAnalysisRun | None:
        return await self._session.get(PatternAnalysisRun, analysis_id)

    async def list_analyses(self, *, limit: int = 50) -> list[PatternAnalysisRun]:
        stmt = (
            select(PatternAnalysisRun)
            .order_by(PatternAnalysisRun.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pattern(self, pattern_row_id: str) -> DetectedPattern | None:
        return await self._session.get(DetectedPattern, pattern_row_id)

    async def top_patterns(
        self,
        *,
        analysis_id: str | None = None,
        limit: int = 20,
    ) -> list[DetectedPattern]:
        stmt = select(DetectedPattern).order_by(DetectedPattern.rank.asc())
        if analysis_id:
            stmt = stmt.where(DetectedPattern.analysis_id == analysis_id)
        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
