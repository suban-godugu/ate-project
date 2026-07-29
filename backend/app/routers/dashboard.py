import json
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import cache_get, cache_set, executive_cache_key, filter_cache_key
from app.core.config import get_settings
from app.core.database import get_db
from app.models.analytics import Alert, KpiSnapshot, WaferDefectUpload
from app.models.core import Fab, Lot, Product, Tester, Wafer
from app.schemas.common import (
    AlertCreate,
    AlertUpdate,
    DashboardTabResponse,
    GlobalFilters,
    KPIOut,
    SearchResultItem,
)
from app.services.deps import get_current_user, get_optional_user
from app.services.alert_service import create_alert, delete_alert, update_alert
from app.services.dashboard_service import build_executive_payload, build_module_payload, build_search_index
from app.storage.minio_client import get_presigned_get_url

settings = get_settings()

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _filters_dict(filters: GlobalFilters) -> dict:
    return filters.model_dump(exclude_none=True)


@router.get("/executive")
async def get_executive(
    filters: GlobalFilters = Depends(),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_optional_user),
):
    key = executive_cache_key(_filters_dict(filters))
    cached = await cache_get(key)
    if cached:
        return cached
    payload = await build_executive_payload(db, filters)
    await cache_set(key, payload, 60)
    return payload


@router.get("/scan-chain/{tab}", response_model=DashboardTabResponse)
async def get_scan_chain(tab: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "scan-chain", tab, filters)


@router.get("/mbist/{tab}", response_model=DashboardTabResponse)
async def get_mbist(tab: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "mbist", tab, filters)


@router.get("/lbist/{tab}", response_model=DashboardTabResponse)
async def get_lbist(tab: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "lbist", tab, filters)


@router.get("/wafer-analysis/overview")
async def get_wafer_overview(filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "wafer-analysis", "overview", filters)


@router.get("/wafer-analysis/images/{upload_id}/{image_type}")
async def get_wafer_image(upload_id: str, image_type: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WaferDefectUpload).where(WaferDefectUpload.id == uuid.UUID(upload_id)))
    upload = result.scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    key_map = {
        "wafer": upload.image_wafer_key,
        "overlay": upload.image_overlay_key,
        "density": upload.image_density_key,
    }
    object_key = key_map.get(image_type)
    if not object_key:
        raise HTTPException(status_code=404, detail="Image not found")
    url = get_presigned_get_url(settings.minio_bucket_wafer, object_key)
    return RedirectResponse(url)


@router.get("/wafer-analysis/{defect_class}")
async def get_wafer_defect(defect_class: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "wafer-analysis", defect_class, filters)


@router.get("/wafer-analysis/{defect_class}/uploads")
async def get_wafer_uploads(defect_class: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    key = filter_cache_key("wafer-analysis", f"{defect_class}-uploads", _filters_dict(filters))
    cached = await cache_get(key)
    if cached:
        return cached
    from app.models.analytics import WaferDefectClass

    try:
        defect_enum = WaferDefectClass(defect_class)
    except ValueError:
        defect_enum = None
    query = select(WaferDefectUpload).order_by(WaferDefectUpload.created_at.desc()).limit(20)
    if defect_enum:
        query = query.where(WaferDefectUpload.defect_class == defect_enum)
    result = await db.execute(query)
    uploads = [
        {
            "id": str(u.id),
            "defectClass": u.defect_class.value if u.defect_class else defect_class,
            "confidence": float(u.confidence or 0),
            "yieldPct": float(u.yield_pct or 0),
        }
        for u in result.scalars().all()
    ]
    payload = {"uploads": uploads}
    await cache_set(key, payload, 120)
    return payload


@router.get("/recommendation-analysis/{agent}")
async def get_recommendation_agent(agent: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "recommendation-analysis", agent, filters)


@router.get("/cost-intelligence/{tab}")
async def get_cost_intelligence(tab: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "cost-intelligence", tab, filters)


@router.get("/alerts/{tab}")
async def get_alerts_tab(tab: str, filters: GlobalFilters = Depends(), db: AsyncSession = Depends(get_db)):
    return await _cached_module(db, "alerts", tab, filters)


@router.post("/alerts")
async def post_alert(body: AlertCreate, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    row = await create_alert(db, body)
    await db.commit()
    return row


@router.patch("/alerts/{alert_id}")
async def patch_alert(
    alert_id: str, body: AlertUpdate, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)
):
    row = await update_alert(db, alert_id, body)
    await db.commit()
    return row


@router.delete("/alerts/{alert_id}")
async def remove_alert(alert_id: str, db: AsyncSession = Depends(get_db), _user=Depends(get_current_user)):
    await delete_alert(db, alert_id)
    await db.commit()
    return {"ok": True}


async def _cached_module(db: AsyncSession, module: str, tab: str, filters: GlobalFilters) -> dict:
    key = filter_cache_key(module, tab, _filters_dict(filters))
    cached = await cache_get(key)
    if cached:
        return cached
    payload = await build_module_payload(db, module, tab, filters)
    ttl = 120 if module == "wafer-analysis" else 60
    await cache_set(key, payload, ttl)
    return payload


search_router = APIRouter(tags=["search"])


@search_router.get("/search", response_model=list[SearchResultItem])
async def search(q: str = Query("", min_length=0), db: AsyncSession = Depends(get_db)):
    cached = await cache_get("search:index:v1")
    if cached is None:
        cached = await build_search_index(db)
        await cache_set("search:index:v1", cached, 300)
    if not q:
        return cached[:20]
    query = q.lower()
    return [item for item in cached if query in json.dumps(item).lower()][:20]


filters_router = APIRouter(tags=["filters"])


@filters_router.get("/filters/options")
async def filter_options(db: AsyncSession = Depends(get_db)):
    fab_rows = (await db.execute(select(Fab).order_by(Fab.code))).scalars().all()
    tester_rows = (await db.execute(select(Tester).order_by(Tester.code))).scalars().all()
    product_rows = (await db.execute(select(Product).order_by(Product.code))).scalars().all()
    lot_rows = (await db.execute(select(Lot).order_by(Lot.lot_code).limit(50))).scalars().all()
    wafer_rows = (await db.execute(select(Wafer).order_by(Wafer.wafer_code).limit(50))).scalars().all()

    def opts(rows, code_attr: str, label_attr: str):
        items = [{"value": getattr(r, code_attr), "label": getattr(r, label_attr)} for r in rows]
        return items + [{"value": "all", "label": "All"}]

    return {
        "fab": opts(fab_rows, "code", "name"),
        "tester": opts(tester_rows, "code", "name"),
        "product": opts(product_rows, "code", "name"),
        "lot": opts(lot_rows, "lot_code", "lot_code"),
        "wafer": [
            {"value": w.wafer_code.replace("wafer-", "W-"), "label": w.wafer_code.upper()}
            for w in wafer_rows
        ]
        + [{"value": "all", "label": "All Wafers"}],
    }
