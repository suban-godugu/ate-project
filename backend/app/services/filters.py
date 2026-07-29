from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Fab, Lot, Product, Tester, Wafer
from app.schemas.common import GlobalFilters


def _norm_code(value: str | None) -> str | None:
    if not value or value == "all":
        return None
    return value.lower().strip().replace(" ", "-")


async def resolve_dimension_ids(db: AsyncSession, filters: GlobalFilters) -> dict[str, UUID | None]:
    """Map frontend filter codes (fab-12, lot-4421) to UUID FKs for SQL queries."""
    ids: dict[str, UUID | None] = {
        "fab_id": None,
        "tester_id": None,
        "product_id": None,
        "lot_id": None,
        "wafer_id": None,
    }

    fab_code = _norm_code(filters.fab)
    if fab_code:
        r = await db.execute(select(Fab.id).where(Fab.code == fab_code))
        ids["fab_id"] = r.scalar_one_or_none()

    tester_code = _norm_code(filters.tester)
    if tester_code:
        r = await db.execute(select(Tester.id).where(Tester.code == tester_code))
        ids["tester_id"] = r.scalar_one_or_none()

    product_code = _norm_code(filters.product)
    if product_code:
        r = await db.execute(select(Product.id).where(Product.code == product_code))
        ids["product_id"] = r.scalar_one_or_none()

    lot_code = _norm_code(filters.lot)
    if lot_code:
        r = await db.execute(select(Lot.id).where(Lot.lot_code == lot_code))
        ids["lot_id"] = r.scalar_one_or_none()

    wafer_code = _norm_code(filters.wafer)
    if wafer_code:
        r = await db.execute(select(Wafer.id).where(Wafer.wafer_code == wafer_code))
        ids["wafer_id"] = r.scalar_one_or_none()

    return ids


async def resolve_metadata_fks(db: AsyncSession, metadata: dict) -> dict[str, UUID | None]:
    """Resolve upload presign metadata strings to dimension UUIDs."""
    fake_filters = GlobalFilters(
        date_preset="7d",
        fab=_norm_code(metadata.get("fab") or metadata.get("fabId")),
        tester=_norm_code(metadata.get("tester") or metadata.get("testerId")),
        product=_norm_code(metadata.get("product") or metadata.get("productId")),
        lot=_norm_code(metadata.get("lotId") or metadata.get("lot")),
        wafer=_norm_code(metadata.get("waferId") or metadata.get("wafer")),
    )
    return await resolve_dimension_ids(db, fake_filters)
