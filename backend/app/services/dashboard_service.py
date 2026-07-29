from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Alert, KpiSnapshot, ScanChainFailure, WaferDefectUpload
from app.models.core import Lot, Wafer
from app.models.module_facts import ModuleFactRow
from app.models.recommendations import Recommendation, RecommendationTrainingRun
from app.models.uploads import AILogSummary, UploadJob
from app.models.users import User
from app.schemas.common import GlobalFilters, KPIOut
from app.services.date_filters import resolve_date_range
from app.services.deps import format_relative_time
from app.services.filters import resolve_dimension_ids
from app.services.chart_aggregation import build_executive_charts, build_module_charts
from app.services.cost_engine import build_cost_intelligence_payload, build_executive_cost_trend, recommendation_savings_score
from app.services.deep_analytics import (
    fetch_failure_analysis_rows,
    fetch_mbist_rows_from_summaries,
    fetch_lbist_rows_from_summaries,
    fetch_pattern_analysis_rows,
)

_AGENT_TAB_MAP = {
    "pattern": "pattern-agent",
    "scan-debug": "scan-debug-agent",
    "test-optimization": "test-optimization-agent",
}

_SOURCE_MODULE_MAP = {
    "pattern": "Scan Chain",
    "scan-debug": "Scan Chain",
    "test-optimization": "Scan Chain",
}

_ALERT_TAB_MODULES = {
    "scan-chain": "Scan Chain",
    "mbist": "MBIST",
    "lbist": "LBIST",
    "wafer": "Wafer",
    "cost": "Cost",
    "ai-recommendation": "Recommendation Analysis",
}


def _apply_date_filter(query, column, filters: GlobalFilters):
    start, end = resolve_date_range(filters)
    if start:
        query = query.where(column >= start)
    if end:
        query = query.where(column <= end)
    return query


def _apply_dim_filters(query, dim_ids: dict, mapping: list[tuple[str, Any]]):
    for key, col in mapping:
        if dim_ids.get(key):
            query = query.where(col == dim_ids[key])
    return query


def _rl_fields(rec: Recommendation, confidence_change: float | None = None) -> dict:
    return {
        "rewardScore": float(rec.reward_score or 0),
        "feedbackCount": int(rec.feedback_count or 0),
        "approvalRate": float(rec.approval_rate or 0),
        "rejectionRate": float(rec.rejection_rate or 0),
        "applicationRate": float(rec.application_rate or 0),
        "confidenceChange": confidence_change,
    }


async def _latest_confidence_changes(db: AsyncSession, rec_ids: list) -> dict:
    if not rec_ids:
        return {}
    result = await db.execute(
        select(RecommendationTrainingRun)
        .where(RecommendationTrainingRun.recommendation_id.in_(rec_ids))
        .order_by(RecommendationTrainingRun.recommendation_id, RecommendationTrainingRun.processed_at.desc())
    )
    deltas: dict = {}
    for run in result.scalars().all():
        if run.recommendation_id in deltas:
            continue
        if run.confidence_before is not None and run.confidence_after is not None:
            deltas[run.recommendation_id] = round(float(run.confidence_after) - float(run.confidence_before), 2)
    return deltas


async def _lookup_lot_wafer_codes(db: AsyncSession, lot_ids: set, wafer_ids: set) -> tuple[dict, dict]:
    lots, wafers = {}, {}
    if lot_ids:
        result = await db.execute(select(Lot).where(Lot.id.in_(lot_ids)))
        lots = {l.id: l.lot_code.upper() for l in result.scalars().all()}
    if wafer_ids:
        result = await db.execute(select(Wafer).where(Wafer.id.in_(wafer_ids)))
        wafers = {w.id: w.wafer_code.replace("wafer-", "W-").replace("Wafer-", "W-") for w in result.scalars().all()}
    return lots, wafers


async def _fetch_kpis(
    db: AsyncSession, module: str, filters: GlobalFilters, tab: str | None = None
) -> list[KPIOut]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(KpiSnapshot).where(KpiSnapshot.module == module)
    if tab:
        query = query.where(KpiSnapshot.kpi_id.like(f"{tab}:%"))
    query = _apply_dim_filters(
        query,
        dim_ids,
        [
            ("fab_id", KpiSnapshot.fab_id),
            ("tester_id", KpiSnapshot.tester_id),
            ("product_id", KpiSnapshot.product_id),
            ("lot_id", KpiSnapshot.lot_id),
            ("wafer_id", KpiSnapshot.wafer_id),
        ],
    )
    query = _apply_date_filter(query, KpiSnapshot.captured_at, filters)
    result = await db.execute(query.order_by(KpiSnapshot.captured_at.desc()).limit(20))
    rows = result.scalars().all()
    if not rows:
        return []
    return [
        KPIOut(
            id=r.kpi_id.split(":", 1)[-1] if ":" in r.kpi_id else r.kpi_id,
            title=r.title or r.kpi_id,
            value=r.value_text or str(r.value_num or ""),
            change=float(r.change_pct or 0),
            trend=r.trend or "up",
            sparkline=r.sparkline or [],
        )
        for r in rows
    ]


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


async def _fetch_module_rows(
    db: AsyncSession, module: str, filters: GlobalFilters, tab: str
) -> list[dict[str, Any]]:
    dim_ids = await resolve_dimension_ids(db, filters)

    if module == "scan-chain":
        if tab == "pattern-analysis":
            return await fetch_pattern_analysis_rows(db, filters)
        if tab == "failure-analysis":
            return await fetch_failure_analysis_rows(db, filters)
        if tab == "scan-diagnosis":
            query = select(ScanChainFailure)
            query = _apply_dim_filters(
                query, dim_ids, [("lot_id", ScanChainFailure.lot_id), ("wafer_id", ScanChainFailure.wafer_id)]
            )
            query = _apply_date_filter(query, ScanChainFailure.created_at, filters)
            result = await db.execute(query.order_by(ScanChainFailure.created_at.desc()).limit(50))
            chain_rank: dict[str, int] = {}
            for r in result.scalars().all():
                cid = r.chain_id or "Unknown"
                chain_rank[cid] = chain_rank.get(cid, 0) + 1
            return [
                {
                    "chainId": cid,
                    "failCount": cnt,
                    "priority": "High" if cnt >= 3 else "Medium",
                    "recommendation": "Investigate chain failures",
                }
                for cid, cnt in sorted(chain_rank.items(), key=lambda x: -x[1])[:20]
            ]

        query = select(ScanChainFailure)
        query = _apply_dim_filters(query, dim_ids, [("lot_id", ScanChainFailure.lot_id), ("wafer_id", ScanChainFailure.wafer_id)])
        query = _apply_date_filter(query, ScanChainFailure.created_at, filters)
        result = await db.execute(query.order_by(ScanChainFailure.created_at.desc()).limit(50))
        return [
            {
                "id": str(r.id),
                "chainId": r.chain_id,
                "patternId": r.pattern_id,
                "chip": r.chip,
                "failCycle": r.fail_cycle,
                "failType": r.fail_type,
                "rootCause": r.root_cause,
                "diagnosisStatus": r.diagnosis_status,
            }
            for r in result.scalars().all()
        ]

    if module == "alerts":
        query = select(Alert)
        if tab and tab != "overview":
            source = _ALERT_TAB_MODULES.get(tab)
            if source:
                query = query.where(Alert.source_module == source)
        query = _apply_dim_filters(query, dim_ids, [("lot_id", Alert.lot_id), ("wafer_id", Alert.wafer_id)])
        query = _apply_date_filter(query, Alert.created_at, filters)
        result = await db.execute(query.order_by(Alert.created_at.desc()).limit(50))
        alerts = result.scalars().all()
        lot_ids = {a.lot_id for a in alerts if a.lot_id}
        wafer_ids = {a.wafer_id for a in alerts if a.wafer_id}
        user_ids = {a.assigned_user_id for a in alerts if a.assigned_user_id}
        lots, wafers = await _lookup_lot_wafer_codes(db, lot_ids, wafer_ids)
        users = {}
        if user_ids:
            ures = await db.execute(select(User).where(User.id.in_(user_ids)))
            users = {u.id: u.name for u in ures.scalars().all()}
        return [
            {
                "id": str(a.id),
                "sourceModule": a.source_module,
                "lotId": lots.get(a.lot_id, ""),
                "waferId": wafers.get(a.wafer_id, ""),
                "severity": a.severity,
                "description": a.description or a.title or "",
                "status": a.status,
                "assignedEngineer": users.get(a.assigned_user_id, "Unassigned"),
                "createdTime": format_relative_time(a.created_at),
            }
            for a in alerts
        ]

    if module == "mbist":
        rows = await fetch_mbist_rows_from_summaries(db, filters)
        if rows:
            return rows
        return await _fetch_fact_rows(db, "mbist", tab or "overview", filters)

    if module == "lbist":
        rows = await fetch_lbist_rows_from_summaries(db, filters)
        if rows:
            return rows
        return await _fetch_fact_rows(db, "lbist", tab or "overview", filters)

    if module == "wafer-analysis":
        query = select(WaferDefectUpload)
        query = _apply_dim_filters(query, dim_ids, [("lot_id", WaferDefectUpload.lot_id), ("wafer_id", WaferDefectUpload.wafer_id)])
        query = _apply_date_filter(query, WaferDefectUpload.created_at, filters)
        result = await db.execute(query.order_by(WaferDefectUpload.created_at.desc()).limit(50))
        uploads = result.scalars().all()
        lot_ids = {u.lot_id for u in uploads if u.lot_id}
        wafer_ids = {u.wafer_id for u in uploads if u.wafer_id}
        lots, wafers = await _lookup_lot_wafer_codes(db, lot_ids, wafer_ids)
        return [
            {
                "id": str(u.id),
                "waferId": wafers.get(u.wafer_id, ""),
                "lotId": lots.get(u.lot_id, ""),
                "yield": float(u.yield_pct or 0),
                "defectType": (u.defect_class.value if u.defect_class else "normal").replace("-", " ").title(),
                "confidence": float(u.confidence or 0),
                "status": "Review" if float(u.yield_pct or 100) < 85 else "Open",
            }
            for u in uploads
        ]

    if module == "cost-intelligence":
        return []  # rows served by cost engine

    if module == "recommendation-analysis":
        if tab in ("overview",):
            return await _fetch_unified_recommendations(db, filters)

        agent = tab.replace("-agent", "") if tab.endswith("-agent") else tab
        if agent == "test-opt":
            agent = "test-optimization"

        query = select(Recommendation).where(Recommendation.agent_type == agent)
        query = _apply_dim_filters(query, dim_ids, [("lot_id", Recommendation.lot_id)])
        query = _apply_date_filter(query, Recommendation.created_at, filters)
        result = await db.execute(
            query.order_by(Recommendation.confidence.desc().nullslast(), Recommendation.created_at.desc()).limit(50)
        )
        recs = result.scalars().all()
        deltas = await _latest_confidence_changes(db, [r.id for r in recs])
        if agent == "pattern":
            return [
                {
                    "recommendationId": str(r.id),
                    "patternId": r.category or "PAT-001",
                    "recommendation": r.action_text or "",
                    "priority": r.priority or "Medium",
                    "confidence": float(r.confidence or 0),
                    "coverageGain": r.expected_impact or "",
                    "powerSaving": "",
                    "status": r.status or "pending",
                    **_rl_fields(r, deltas.get(r.id)),
                }
                for r in recs
            ]
        if agent == "scan-debug":
            return [
                {
                    "recommendationId": str(r.id),
                    "category": r.category or "",
                    "scanChain": r.action_text or "",
                    "rootCause": r.expected_impact or "",
                    "recommendation": r.action_text or "",
                    "priority": r.priority or "Medium",
                    "confidence": float(r.confidence or 0),
                    "engineer": "Alex Johnson",
                    "status": r.status or "pending",
                    "expectedImpact": r.expected_impact or "",
                    **_rl_fields(r, deltas.get(r.id)),
                }
                for r in recs
            ]
        return [
            {
                "recommendationId": str(r.id),
                "optimizationType": r.category or "",
                "currentValue": "",
                "optimizedValue": "",
                "estimatedBenefit": r.expected_impact or "",
                "priority": r.priority or "Medium",
                "confidence": float(r.confidence or 0),
                "status": r.status or "pending",
                "assignedEngineer": "Alex Johnson",
                **_rl_fields(r, deltas.get(r.id)),
            }
            for r in recs
        ]

    return []


async def _fetch_unified_recommendations(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(Recommendation)
    query = _apply_dim_filters(query, dim_ids, [("lot_id", Recommendation.lot_id)])
    query = _apply_date_filter(query, Recommendation.created_at, filters)
    result = await db.execute(
        query.order_by(Recommendation.confidence.desc().nullslast(), Recommendation.created_at.desc()).limit(50)
    )
    rec_list = list(result.scalars().all())
    rec_list.sort(key=lambda r: (recommendation_savings_score(r), float(r.confidence or 0)), reverse=True)
    deltas = await _latest_confidence_changes(db, [r.id for r in rec_list])
    rows = []
    for r in rec_list:
        source = _SOURCE_MODULE_MAP.get(r.agent_type or "", "Scan Chain")
        if r.category and "MBIST" in r.category.upper():
            source = "MBIST"
        elif r.category and "LBIST" in r.category.upper():
            source = "LBIST"
        elif r.category and "Wafer" in r.category:
            source = "Wafer"
        status_map = {
            "pending": "Pending",
            "approved": "Approved",
            "applied": "Implemented",
            "rejected": "In Review",
        }
        rows.append(
            {
                "id": str(r.id),
                "sourceModule": source,
                "category": r.category or "",
                "priority": r.priority or "Medium",
                "confidence": float(r.confidence or 0),
                "estimatedImpact": r.expected_impact or "",
                "status": status_map.get(r.status or "pending", r.status or "Pending"),
                "assignedEngineer": "Alex Johnson",
                **_rl_fields(r, deltas.get(r.id)),
            }
        )
    return rows


async def build_executive_payload(db: AsyncSession, filters: GlobalFilters) -> dict[str, Any]:
    kpis = await _fetch_kpis(db, "executive", filters)
    patterns = await _fetch_fact_rows(db, "executive", "patterns", filters, limit=20)
    cost_trend = await build_executive_cost_trend(db, filters)
    charts = await build_executive_charts(db, filters)
    return {
        "kpis": [k.model_dump() for k in kpis],
        "patterns": patterns,
        "costTrend": cost_trend,
        "charts": charts,
    }


async def build_module_payload(db: AsyncSession, module: str, tab: str, filters: GlobalFilters) -> dict[str, Any]:
    if module == "cost-intelligence":
        return await build_cost_intelligence_payload(db, tab, filters)

    kpis = await _fetch_kpis(db, module, filters, tab)
    rows = await _fetch_module_rows(db, module, filters, tab)
    charts = await build_module_charts(db, module, tab, filters)
    return {
        "kpis": [k.model_dump(by_alias=True) for k in kpis],
        "rows": rows,
        "charts": charts,
    }


async def build_search_index(db: AsyncSession) -> list[dict]:
    items: list[dict] = []
    result = await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(30))
    for alert in result.scalars().all():
        items.append(
            {
                "id": str(alert.id),
                "title": alert.title or "Alert",
                "subtitle": alert.description or "",
                "category": "Alerts",
                "route": "/dashboard/alerts",
                "matchedField": alert.source_module,
            }
        )
    result = await db.execute(select(ScanChainFailure).order_by(ScanChainFailure.created_at.desc()).limit(20))
    for row in result.scalars().all():
        items.append(
            {
                "id": str(row.id),
                "title": row.chain_id or "Scan Chain",
                "subtitle": row.pattern_id or "",
                "category": "Scan Chain",
                "route": "/dashboard/scan-chain",
                "matchedField": row.chain_id or "",
            }
        )
    result = await db.execute(select(Recommendation).order_by(Recommendation.created_at.desc()).limit(20))
    for rec in result.scalars().all():
        items.append(
            {
                "id": str(rec.id),
                "title": rec.category or "Recommendation",
                "subtitle": rec.action_text or "",
                "category": "Recommendation Analysis",
                "route": "/dashboard/recommendation-analysis",
                "matchedField": rec.agent_type or "",
            }
        )
    result = await db.execute(select(UploadJob).order_by(UploadJob.created_at.desc()).limit(15))
    for job in result.scalars().all():
        items.append(
            {
                "id": str(job.id),
                "title": job.file_name or "Upload",
                "subtitle": job.module or "",
                "category": "Uploads",
                "route": "/dashboard/uploads",
                "matchedField": job.file_type or "",
            }
        )
    result = await db.execute(select(AILogSummary).order_by(AILogSummary.created_at.desc()).limit(20))
    for summary in result.scalars().all():
        if summary.estimated_cost is not None and float(summary.estimated_cost) > 0:
            items.append(
                {
                    "id": f"cost-{summary.id}",
                    "title": f"Test cost ${float(summary.estimated_cost):,.0f}",
                    "subtitle": f"Savings ${float(summary.estimated_savings or 0):,.0f}",
                    "category": "Cost Intelligence",
                    "route": "/dashboard/cost-intelligence",
                    "matchedField": "estimated_cost",
                }
            )
        meta = summary.raw_summary_json or {}
        fmt = meta.get("format")
        if fmt not in ("stil", "wgl", "pat"):
            continue
        label = {"stil": "STIL", "wgl": "WGL", "pat": "PAT"}.get(fmt, fmt.upper())
        for pattern_name in meta.get("pattern_names") or []:
            items.append(
                {
                    "id": f"{fmt}-pat-{pattern_name}",
                    "title": pattern_name,
                    "subtitle": meta.get("pattern_group") or meta.get("title") or f"{label} Pattern",
                    "category": "Pattern",
                    "route": "/dashboard/scan-chain",
                    "matchedField": "pattern_name",
                }
            )
        generator = meta.get("generator") or meta.get("Generator")
        if generator and fmt == "pat":
            items.append(
                {
                    "id": f"pat-gen-{summary.id}",
                    "title": str(generator),
                    "subtitle": meta.get("vendor") or "PAT Generator",
                    "category": "Pattern",
                    "route": "/dashboard/scan-chain",
                    "matchedField": "generator",
                }
            )
        for chain_name in meta.get("scan_chain_names") or []:
            items.append(
                {
                    "id": f"{fmt}-chain-{chain_name}",
                    "title": chain_name,
                    "subtitle": f"{label} Scan Structure",
                    "category": "Scan Chain",
                    "route": "/dashboard/scan-chain",
                    "matchedField": "scan_chain",
                }
            )
        for waveform_name in meta.get("waveform_names") or []:
            items.append(
                {
                    "id": f"{fmt}-wft-{waveform_name}",
                    "title": waveform_name,
                    "subtitle": f"{label} Waveform",
                    "category": "Waveform",
                    "route": "/dashboard/scan-chain",
                    "matchedField": "waveform_name",
                }
            )
        signal_or_pin_count = meta.get("signal_count") or meta.get("pin_count") or 0
        if signal_or_pin_count:
            items.append(
                {
                    "id": f"{fmt}-pins-{summary.id}",
                    "title": f"{signal_or_pin_count} {label} pin(s)",
                    "subtitle": meta.get("tester") or meta.get("source") or "",
                    "category": "Signals",
                    "route": "/dashboard/scan-chain",
                    "matchedField": "pin",
                }
            )
    if not items:
        items = [
            {
                "id": "dashboard-1",
                "title": "Executive Dashboard",
                "subtitle": "KPI overview",
                "category": "Dashboard",
                "route": "/dashboard",
                "matchedField": "dashboard",
            }
        ]
    return items
