"""SQL aggregation for dashboard chart payloads (Stage 7)."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Alert, ScanChainFailure, WaferDefectUpload
from app.models.module_facts import ModuleFactRow
from app.models.recommendations import Recommendation
from app.models.uploads import AILogSummary, UploadJob
from app.schemas.common import GlobalFilters
from app.services.date_filters import resolve_date_range
from app.services.filters import resolve_dimension_ids

CHART_COLORS = [
    "#7C3AED",
    "#06B6D4",
    "#F97316",
    "#22C55E",
    "#EAB308",
    "#EF4444",
    "#EC4899",
    "#64748B",
]

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _apply_date_filter(query, column, filters: GlobalFilters):
    start, end = resolve_date_range(filters)
    if start:
        query = query.where(column >= start)
    if end:
        query = query.where(column <= end)
    return query


def _apply_dim_filters(query, dim_ids: dict, mapping: list[tuple[str, object]]):
    for key, col in mapping:
        if dim_ids.get(key):
            query = query.where(col == dim_ids[key])
    return query


async def _fetch_fact_rows(
    db: AsyncSession, module: str, tab: str | None, filters: GlobalFilters, limit: int = 50
) -> list[dict]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(ModuleFactRow).where(ModuleFactRow.module == module)
    if tab:
        query = query.where(ModuleFactRow.tab == tab)
    query = _apply_dim_filters(
        query,
        dim_ids,
        [
            ("fab_id", ModuleFactRow.fab_id),
            ("lot_id", ModuleFactRow.lot_id),
            ("wafer_id", ModuleFactRow.wafer_id),
        ],
    )
    query = _apply_date_filter(query, ModuleFactRow.created_at, filters)
    result = await db.execute(query.order_by(ModuleFactRow.created_at.desc()).limit(limit))
    return [dict(r.row_data) for r in result.scalars().all()]


def _segments(counter: Counter, total: int | None = None) -> list[dict]:
    items = counter.most_common(12)
    if not items:
        return []
    return [
        {"name": name, "value": count, "color": CHART_COLORS[i % len(CHART_COLORS)]}
        for i, (name, count) in enumerate(items)
    ]


def _trend_points(day_counts: dict[str, int], value_key: str = "value") -> list[dict]:
    if not day_counts:
        return []
    ordered = sorted(day_counts.items())
    return [{"label": label, value_key: count} for label, count in ordered[-14:]]


def _day_label(dt: datetime | None) -> str:
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return DAY_LABELS[dt.weekday()]


async def _scan_failures_query(db: AsyncSession, filters: GlobalFilters):
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(ScanChainFailure)
    query = _apply_dim_filters(
        query, dim_ids, [("lot_id", ScanChainFailure.lot_id), ("wafer_id", ScanChainFailure.wafer_id)]
    )
    return _apply_date_filter(query, ScanChainFailure.created_at, filters)


async def build_executive_charts(db: AsyncSession, filters: GlobalFilters) -> dict[str, Any]:
    from app.services.deep_analytics import extend_executive_charts

    charts: dict[str, Any] = {}

    wafers_q = select(WaferDefectUpload).order_by(WaferDefectUpload.created_at.asc())
    wafers_q = _apply_date_filter(wafers_q, WaferDefectUpload.created_at, filters)
    wres = await db.execute(wafers_q.limit(100))
    yield_by_day: dict[str, list[float]] = defaultdict(list)
    for w in wres.scalars().all():
        if w.yield_pct is not None:
            yield_by_day[_day_label(w.created_at)].append(float(w.yield_pct))
    charts["yieldTrend"] = [
        {"label": d, "value": round(sum(v) / len(v), 1)} for d, v in yield_by_day.items()
    ]

    alerts_q = _apply_date_filter(select(Alert), Alert.created_at, filters)
    ares = await db.execute(alerts_q.order_by(Alert.created_at.asc()))
    alert_by_day: Counter[str] = Counter()
    for a in ares.scalars().all():
        alert_by_day[_day_label(a.created_at)] += 1
    charts["alertTrend"] = _trend_points(dict(alert_by_day))

    uploads_q = _apply_date_filter(select(UploadJob), UploadJob.created_at, filters)
    ures = await db.execute(uploads_q.order_by(UploadJob.created_at.asc()))
    upload_by_day: Counter[str] = Counter()
    for u in ures.scalars().all():
        upload_by_day[_day_label(u.created_at)] += 1
    charts["uploadTrend"] = _trend_points(dict(upload_by_day))

    rec_q = _apply_date_filter(select(Recommendation), Recommendation.created_at, filters)
    rres = await db.execute(rec_q.order_by(Recommendation.created_at.asc()))
    rec_by_day: Counter[str] = Counter()
    for r in rres.scalars().all():
        rec_by_day[_day_label(r.created_at)] += 1
    charts["recommendationTrend"] = _trend_points(dict(rec_by_day))

    summaries_q = _apply_date_filter(select(AILogSummary), AILogSummary.created_at, filters)
    sres = await db.execute(summaries_q.order_by(AILogSummary.created_at.asc()))
    cost_trend_live: list[dict] = []
    for s in sres.scalars().all():
        if s.estimated_cost is not None:
            cost_trend_live.append(
                {
                    "day": _day_label(s.created_at),
                    "totalCost": float(s.estimated_cost),
                    "costPerWafer": float(s.estimated_cost / max(s.wafer_count or 1, 1)),
                }
            )
    if cost_trend_live:
        charts["costTrendLive"] = cost_trend_live[-14:]

    return await extend_executive_charts(db, filters, charts)


async def build_scan_chain_charts(db: AsyncSession, filters: GlobalFilters, tab: str) -> dict[str, Any]:
    result = await db.execute((await _scan_failures_query(db, filters)).order_by(ScanChainFailure.created_at.desc()))
    failures = result.scalars().all()
    charts: dict[str, Any] = {}

    fail_types: Counter[str] = Counter()
    chips: Counter[str] = Counter()
    patterns: Counter[str] = Counter()
    by_day: Counter[str] = Counter()
    diagnosis: Counter[str] = Counter()

    for f in failures:
        fail_types[f.fail_type or "Unknown"] += 1
        if f.chip:
            chips[f.chip] += 1
        if f.pattern_id:
            patterns[f.pattern_id] += 1
        by_day[_day_label(f.created_at)] += 1
        diagnosis[f.diagnosis_status or "pending"] += 1

    total_fail = len(failures)
    healthy = max(0, 100 - total_fail)
    charts["failureDistribution"] = _segments(fail_types)
    charts["failureAnalysisDistribution"] = charts["failureDistribution"]
    charts["failureTrendData"] = _trend_points(dict(by_day))
    charts["overallFailureTrend"] = charts["failureTrendData"]
    charts["failureRateTrend"] = charts["failureTrendData"]
    charts["topFailingChips"] = [{"chip": c, "failCount": n} for c, n in chips.most_common(10)]
    charts["patternDistribution"] = _segments(patterns)
    charts["chainHealthData"] = _segments(
        Counter({"Failing": total_fail, "Healthy": healthy}) if total_fail else Counter()
    )
    charts["diagnosisDistribution"] = _segments(diagnosis)

    heat_cells: list[dict] = []
    for f in failures[:200]:
        if f.chip and f.chip.startswith("M") and "-" in f.chip:
            parts = f.chip[1:].split("-", 1)
            try:
                x, y = int(parts[0]), int(parts[1])
                heat_cells.append({"row": y % 12, "col": x % 12, "value": 1.0})
            except ValueError:
                continue
    charts["heatmapCells"] = heat_cells

    if tab in ("failure-analysis", "overview"):
        charts["failureByLotData"] = [{"lot": "All", "failCount": total_fail}]
    return charts


async def build_alerts_charts(db: AsyncSession, filters: GlobalFilters, tab: str) -> dict[str, Any]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(Alert)
    query = _apply_dim_filters(query, dim_ids, [("lot_id", Alert.lot_id), ("wafer_id", Alert.wafer_id)])
    query = _apply_date_filter(query, Alert.created_at, filters)
    result = await db.execute(query.order_by(Alert.created_at.desc()))
    alerts = result.scalars().all()

    severity: Counter[str] = Counter()
    modules: Counter[str] = Counter()
    by_day: Counter[str] = Counter()
    for a in alerts:
        severity[a.severity or "Info"] += 1
        modules[a.source_module or "Unknown"] += 1
        by_day[_day_label(a.created_at)] += 1

    charts = {
        "severityDistribution": _segments(severity),
        "alertDistribution": _segments(modules),
        "alertTrend": _trend_points(dict(by_day)),
    }
    if tab != "overview":
        charts["moduleAlertTrend"] = charts["alertTrend"]
    return charts


async def build_wafer_charts(db: AsyncSession, filters: GlobalFilters) -> dict[str, Any]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(WaferDefectUpload)
    query = _apply_dim_filters(
        query, dim_ids, [("lot_id", WaferDefectUpload.lot_id), ("wafer_id", WaferDefectUpload.wafer_id)]
    )
    query = _apply_date_filter(query, WaferDefectUpload.created_at, filters)
    result = await db.execute(query.order_by(WaferDefectUpload.created_at.desc()))
    uploads = result.scalars().all()

    by_class: Counter[str] = Counter()
    yield_by_day: dict[str, list[float]] = defaultdict(list)
    grid = [[0.0 for _ in range(12)] for _ in range(12)]

    for u in uploads:
        cls = (u.defect_class.value if u.defect_class else "normal").replace("-", " ").title()
        by_class[cls] += 1
        if u.yield_pct is not None:
            yield_by_day[_day_label(u.created_at)].append(float(u.yield_pct))
        if u.hotspot_x is not None and u.hotspot_y is not None:
            row, col = int(u.hotspot_y) % 12, int(u.hotspot_x) % 12
            grid[row][col] = min(1.0, grid[row][col] + float(u.confidence or 50) / 100)

    charts: dict[str, Any] = {
        "defectClassBreakdown": _segments(by_class),
        "defectTrend": _segments(by_class),
        "yieldTrend30": [
            {"label": d, "value": round(sum(v) / len(v), 1)} for d, v in yield_by_day.items()
        ],
        "yieldTrend": [
            {"label": d, "value": round(sum(v) / len(v), 1)} for d, v in yield_by_day.items()
        ],
        "waferHeatmapGrid": grid,
        "spatialHeatmap": [
            {"row": r, "col": c, "value": grid[r][c]} for r in range(12) for c in range(12) if grid[r][c] > 0
        ],
    }
    if uploads:
        avg_y = sum(float(u.yield_pct or 0) for u in uploads) / len(uploads)
        charts["positiveNegativeYield"] = [
            {"label": "Pass", "value": round(avg_y, 1)},
            {"label": "Fail", "value": round(100 - avg_y, 1)},
        ]
    return charts


async def build_recommendation_charts(
    db: AsyncSession, filters: GlobalFilters, tab: str = "overview"
) -> dict[str, Any]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(Recommendation)
    if tab not in ("overview",) and tab.endswith("-agent"):
        agent = tab.replace("-agent", "")
        if agent == "test-opt":
            agent = "test-optimization"
        query = query.where(Recommendation.agent_type == agent)
    query = _apply_dim_filters(query, dim_ids, [("lot_id", Recommendation.lot_id)])
    query = _apply_date_filter(query, Recommendation.created_at, filters)
    result = await db.execute(query.order_by(Recommendation.created_at.desc()))
    recs = result.scalars().all()

    priority: Counter[str] = Counter()
    agent: Counter[str] = Counter()
    category: Counter[str] = Counter()
    by_day: Counter[str] = Counter()
    status: Counter[str] = Counter()

    for r in recs:
        priority[r.priority or "Medium"] += 1
        agent[r.agent_type or "unknown"] += 1
        category[r.category or "General"] += 1
        status[r.status or "pending"] += 1
        by_day[_day_label(r.created_at)] += 1

    return {
        "priorityDistribution": _segments(priority),
        "sourceDistribution": _segments(agent),
        "recommendationTrend": _trend_points(dict(by_day)),
        "approvalTrend": _segments(status),
        "recommendationCategories": _segments(category),
    }


async def build_cost_charts(db: AsyncSession, filters: GlobalFilters, tab: str) -> dict[str, Any]:
    from app.services.cost_engine import build_cost_charts_payload, aggregate_cost_facts, fetch_cost_facts

    facts = await fetch_cost_facts(db, filters)
    agg = aggregate_cost_facts(facts)
    return build_cost_charts_payload(agg, facts, tab)


async def _charts_from_fact_rows(
    db: AsyncSession, module: str, tab: str, filters: GlobalFilters, status_field: str = "status"
) -> dict[str, Any]:
    rows = await _fetch_fact_rows(db, module, tab or "overview", filters, limit=100)
    status_counter: Counter[str] = Counter()
    block_coverage: list[dict] = []
    by_day: Counter[str] = Counter()

    for row in rows:
        status_counter[row.get(status_field) or "Unknown"] += 1
        block = row.get("logicBlock") or row.get("memoryBlock") or row.get("block")
        cov = row.get("coverage")
        if block and cov is not None:
            try:
                block_coverage.append({"label": str(block), "value": float(cov)})
            except (TypeError, ValueError):
                pass
        ts = row.get("timestamp") or row.get("createdAt")
        if ts:
            by_day[str(ts)[:10]] += 1

    charts: dict[str, Any] = {
        "failureTypeDistribution": _segments(status_counter),
        "memoryHealthData": _segments(status_counter),
        "coverageDistribution": _segments(status_counter),
        "failureByModule": _segments(
            Counter({str(r.get("logicBlock") or r.get("memoryBlock") or "?"): 1 for r in rows})
        ),
    }
    if block_coverage:
        charts["utilizationTrend"] = block_coverage[:12]
        charts["coverageByBlock"] = block_coverage[:12]
    if by_day:
        charts["failureTrend"] = _trend_points(dict(by_day))
    return charts


async def build_module_charts(
    db: AsyncSession, module: str, tab: str, filters: GlobalFilters
) -> dict[str, Any]:
    from app.services.deep_analytics import merge_deep_analytics

    if module == "scan-chain":
        base = await build_scan_chain_charts(db, filters, tab)
    elif module == "alerts":
        base = await build_alerts_charts(db, filters, tab)
    elif module == "wafer-analysis":
        base = await build_wafer_charts(db, filters)
    elif module == "recommendation-analysis":
        base = await build_recommendation_charts(db, filters, tab)
    elif module == "cost-intelligence":
        base = await build_cost_charts(db, filters, tab)
    elif module == "mbist":
        base = await _charts_from_fact_rows(db, "mbist", tab, filters)
    elif module == "lbist":
        base = await _charts_from_fact_rows(db, "lbist", tab, filters)
    else:
        base = {}
    return await merge_deep_analytics(db, module, tab, filters, base)
