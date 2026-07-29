"""Seed default admin user, dimension data, and dashboard KPIs/facts for all modules."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import asyncio
import uuid

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.analytics import Alert, KpiSnapshot, Notification, ScanChainFailure, WaferDefectUpload
from app.models.analytics import WaferDefectClass
from app.models.core import Fab, Lot, Product, Tester, Wafer
from app.models.module_facts import ModuleFactRow
from app.models.recommendations import Recommendation
from app.models.users import User
import seed_data as data

EXECUTIVE_KPIS = data.EXECUTIVE_KPIS
SCAN_CHAIN_KPIS = data.SCAN_CHAIN_KPIS


def _add_kpis(db, module: str, kpis: list, lot_id=None, wafer_id=None, fab_id=None) -> None:
    for kpi_id, title, value_text, value_num, change_pct, trend, sparkline in kpis:
        db.add(
            KpiSnapshot(
                module=module,
                kpi_id=kpi_id,
                title=title,
                value_text=value_text,
                value_num=value_num,
                change_pct=change_pct,
                trend=trend,
                sparkline=sparkline,
                lot_id=lot_id,
                wafer_id=wafer_id,
                fab_id=fab_id,
            )
        )


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == "alex@verilumen.ai"))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=uuid.uuid4(),
                email="alex@verilumen.ai",
                password_hash=hash_password("changeme123"),
                name="Alex Johnson",
                role="engineer",
                department="Test Engineering",
            )
            db.add(user)
            await db.flush()
            print("Created user alex@verilumen.ai / changeme123")

        fab = await _get_or_create_fab(db)
        tester = await _get_or_create_tester(db, fab.id)
        product = await _get_or_create_product(db)
        lot = await _get_or_create_lot(db, product.id, fab.id)
        wafer = await _get_or_create_wafer(db, lot.id)

        kpi_count = await db.scalar(select(func.count()).select_from(KpiSnapshot))
        if not kpi_count:
            _add_kpis(db, "executive", EXECUTIVE_KPIS, fab_id=fab.id)
            _add_kpis(db, "scan-chain", SCAN_CHAIN_KPIS, lot_id=lot.id, wafer_id=wafer.id)
            _add_kpis(db, "mbist", data.MBIST_KPIS, lot_id=lot.id)
            _add_kpis(db, "lbist", data.LBIST_KPIS, lot_id=lot.id)
            _add_kpis(db, "wafer-analysis", data.WAFER_KPIS, lot_id=lot.id)
            _add_kpis(db, "cost-intelligence", data.COST_KPIS, fab_id=fab.id)
            _add_kpis(db, "recommendation-analysis", data.RECOMMENDATION_KPIS)
            print("Seeded KPI snapshots for all modules")

        fact_count = await db.scalar(select(func.count()).select_from(ModuleFactRow))
        if not fact_count:
            for row in data.MBIST_FAILURE_ROWS:
                db.add(ModuleFactRow(module="mbist", tab="overview", row_data=row, lot_id=lot.id))
            for row in data.LBIST_FAILURE_ROWS:
                db.add(ModuleFactRow(module="lbist", tab="overview", row_data=row, lot_id=lot.id))
            for row in data.COST_PRODUCT_ROWS:
                db.add(ModuleFactRow(module="cost-intelligence", tab="overview", row_data=row, lot_id=lot.id))
            for row in data.EXECUTIVE_PATTERN_ROWS:
                db.add(ModuleFactRow(module="executive", tab="patterns", row_data=row, fab_id=fab.id))
            for row in data.EXECUTIVE_COST_TREND:
                db.add(ModuleFactRow(module="executive", tab="cost-trend", row_data=row, fab_id=fab.id))
            print("Seeded module fact rows")

        failure_count = await db.scalar(select(func.count()).select_from(ScanChainFailure))
        if not failure_count:
            for chain_id, pattern_id, chip, fail_cycle, fail_type, root_cause, status in data.SCAN_CHAIN_FAILURES:
                db.add(
                    ScanChainFailure(
                        chain_id=chain_id,
                        pattern_id=pattern_id,
                        chip=chip,
                        fail_cycle=fail_cycle,
                        fail_type=fail_type,
                        root_cause=root_cause,
                        diagnosis_status=status,
                        lot_id=lot.id,
                        wafer_id=wafer.id,
                    )
                )
            print("Seeded scan chain failures")

        defect_count = await db.scalar(select(func.count()).select_from(WaferDefectUpload))
        if not defect_count:
            for defect_class, confidence, yield_pct, hx, hy, seed in data.WAFER_DEFECTS:
                db.add(
                    WaferDefectUpload(
                        defect_class=WaferDefectClass(defect_class),
                        lot_id=lot.id,
                        wafer_id=wafer.id,
                        confidence=confidence,
                        yield_pct=yield_pct,
                        hotspot_x=hx,
                        hotspot_y=hy,
                        seed=seed,
                    )
                )
            print("Seeded wafer defect uploads")

        alert_count = await db.scalar(select(func.count()).select_from(Alert))
        if not alert_count:
            for source, severity, status, title, description in data.ALERTS:
                db.add(
                    Alert(
                        source_module=source,
                        severity=severity,
                        status=status,
                        title=title,
                        description=description,
                        lot_id=lot.id,
                        wafer_id=wafer.id,
                        assigned_user_id=user.id,
                    )
                )
            print("Seeded alerts")

        notif_count = await db.scalar(
            select(func.count()).select_from(Notification).where(Notification.user_id == user.id)
        )
        if not notif_count:
            for source, severity, _, title, message in data.ALERTS[:5]:
                db.add(
                    Notification(
                        user_id=user.id,
                        severity=severity.lower(),
                        title=title,
                        message=message,
                        alert_route="/dashboard/alerts",
                    )
                )

        rec_count = await db.scalar(select(func.count()).select_from(Recommendation))
        if not rec_count:
            for agent_type, category, priority, confidence, impact, action, status in data.RECOMMENDATIONS:
                db.add(
                    Recommendation(
                        agent_type=agent_type,
                        category=category,
                        priority=priority,
                        confidence=confidence,
                        expected_impact=impact,
                        action_text=action,
                        status=status,
                        lot_id=lot.id,
                        assigned_user_id=user.id,
                    )
                )
            print("Seeded recommendations with real UUIDs")

        await db.commit()
        print(f"Seed complete (user id={user.id})")


async def _get_or_create_fab(db) -> Fab:
    result = await db.execute(select(Fab).where(Fab.code == "fab-12"))
    fab = result.scalar_one_or_none()
    if fab:
        return fab
    fab = Fab(id=uuid.uuid4(), code="fab-12", name="Fab-12")
    db.add(fab)
    await db.flush()
    return fab


async def _get_or_create_tester(db, fab_id: uuid.UUID) -> Tester:
    result = await db.execute(select(Tester).where(Tester.code == "ate-01"))
    tester = result.scalar_one_or_none()
    if tester:
        return tester
    tester = Tester(id=uuid.uuid4(), code="ate-01", name="ATE-01", platform="UltraFlex", fab_id=fab_id)
    db.add(tester)
    await db.flush()
    return tester


async def _get_or_create_product(db) -> Product:
    result = await db.execute(select(Product).where(Product.code == "chip-x7"))
    product = result.scalar_one_or_none()
    if product:
        return product
    product = Product(id=uuid.uuid4(), code="chip-x7", name="Chip-X7")
    db.add(product)
    await db.flush()
    return product


async def _get_or_create_lot(db, product_id: uuid.UUID, fab_id: uuid.UUID) -> Lot:
    result = await db.execute(select(Lot).where(Lot.lot_code == "lot-4421"))
    lot = result.scalar_one_or_none()
    if lot:
        return lot
    lot = Lot(id=uuid.uuid4(), lot_code="lot-4421", product_id=product_id, fab_id=fab_id)
    db.add(lot)
    await db.flush()
    return lot


async def _get_or_create_wafer(db, lot_id: uuid.UUID) -> Wafer:
    result = await db.execute(select(Wafer).where(Wafer.wafer_code == "wafer-12"))
    wafer = result.scalar_one_or_none()
    if wafer:
        return wafer
    wafer = Wafer(id=uuid.uuid4(), wafer_code="wafer-12", lot_id=lot_id, slot=12, yield_pct=93.8)
    db.add(wafer)
    await db.flush()
    return wafer


if __name__ == "__main__":
    asyncio.run(seed())
