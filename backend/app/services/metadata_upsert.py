from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.core import Fab, Lot, Product, Tester, Wafer


def _slug_code(value: str, prefix: str = "") -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    if not cleaned:
        cleaned = uuid.uuid4().hex[:8]
    code = f"{prefix}{cleaned}" if prefix else cleaned
    return code[:64]


async def get_or_create_fab(db: AsyncSession, code: str | None, name: str | None = None) -> Fab | None:
    if not code:
        return None
    slug = _slug_code(code)
    result = await db.execute(select(Fab).where(Fab.code == slug))
    fab = result.scalar_one_or_none()
    if fab:
        return fab
    fab = Fab(code=slug, name=(name or code)[:128])
    db.add(fab)
    await db.flush()
    return fab


async def get_or_create_tester(
    db: AsyncSession, code: str | None, fab_id: uuid.UUID | None = None, name: str | None = None
) -> Tester | None:
    if not code:
        return None
    slug = _slug_code(code)
    result = await db.execute(select(Tester).where(Tester.code == slug))
    tester = result.scalar_one_or_none()
    if tester:
        return tester
    tester = Tester(code=slug, name=(name or code)[:128], fab_id=fab_id)
    db.add(tester)
    await db.flush()
    return tester


async def get_or_create_product(db: AsyncSession, code: str | None, name: str | None = None) -> Product | None:
    if not code:
        return None
    slug = _slug_code(code)
    result = await db.execute(select(Product).where(Product.code == slug))
    product = result.scalar_one_or_none()
    if product:
        return product
    product = Product(code=slug, name=(name or code)[:128])
    db.add(product)
    await db.flush()
    return product


async def get_or_create_lot(
    db: AsyncSession,
    lot_code: str | None,
    product_id: uuid.UUID | None = None,
    fab_id: uuid.UUID | None = None,
) -> Lot | None:
    if not lot_code:
        return None
    normalized = lot_code.strip()
    result = await db.execute(select(Lot).where(Lot.lot_code == normalized))
    lot = result.scalar_one_or_none()
    if lot:
        return lot
    lot = Lot(lot_code=normalized[:64], product_id=product_id, fab_id=fab_id)
    db.add(lot)
    await db.flush()
    return lot


async def get_or_create_wafer(
    db: AsyncSession,
    wafer_code: str | None,
    lot_id: uuid.UUID | None = None,
    yield_pct: float | None = None,
    good_dies: int | None = None,
    bad_dies: int | None = None,
    total_dies: int | None = None,
) -> Wafer | None:
    if not wafer_code:
        return None
    normalized = wafer_code.strip()
    result = await db.execute(select(Wafer).where(Wafer.wafer_code == normalized, Wafer.lot_id == lot_id))
    wafer = result.scalar_one_or_none()
    if not wafer and lot_id is None:
        result = await db.execute(select(Wafer).where(Wafer.wafer_code == normalized))
        wafer = result.scalar_one_or_none()
    if wafer:
        if yield_pct is not None:
            wafer.yield_pct = yield_pct
        if good_dies is not None:
            wafer.good_dies = good_dies
        if bad_dies is not None:
            wafer.bad_dies = bad_dies
        if total_dies is not None:
            wafer.total_dies = total_dies
        return wafer
    wafer = Wafer(
        wafer_code=normalized[:64],
        lot_id=lot_id,
        yield_pct=yield_pct,
        good_dies=good_dies,
        bad_dies=bad_dies,
        total_dies=total_dies,
    )
    db.add(wafer)
    await db.flush()
    return wafer
