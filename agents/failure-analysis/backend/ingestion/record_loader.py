"""Load normalized test records scoped to a dataset or single upload."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.schema import TestRecord
from backend.models import TestRecordRow, Upload


def _rows_to_records(rows: list[TestRecordRow]) -> list[TestRecord]:
    records: list[TestRecord] = []
    for row in rows:
        payload = dict(row.payload or {})
        payload.setdefault("lot_id", row.lot_id)
        payload.setdefault("wafer_id", row.wafer_id)
        payload.setdefault("die_id", row.die_id)
        payload.setdefault("record_key", row.record_key)
        records.append(TestRecord.from_dict(payload))
    return records


async def load_test_records(
    session: AsyncSession,
    *,
    dataset_id: str | None = None,
    upload_id: str | None = None,
) -> list[TestRecord]:
    if bool(dataset_id) == bool(upload_id):
        raise ValueError("Exactly one of dataset_id or upload_id is required")

    if dataset_id:
        stmt = (
            select(TestRecordRow)
            .join(Upload, Upload.id == TestRecordRow.upload_id)
            .where(Upload.dataset_id == dataset_id)
            .order_by(TestRecordRow.created_at.asc())
        )
    else:
        stmt = (
            select(TestRecordRow)
            .where(TestRecordRow.upload_id == upload_id)
            .order_by(TestRecordRow.created_at.asc())
        )

    rows = list((await session.execute(stmt)).scalars().all())
    return _rows_to_records(rows)
