"""Enterprise Cost Intelligence Engine — deterministic aggregation from real parser data only.

All dollar amounts originate from:
  • LOG parser `estimated_cost` / `estimated_savings` (ai_log_summaries)
  • Optional equipment cost from upload `processing_ms` × COST_TESTER_USD_PER_HOUR (when configured)

Module splits use proportional allocation from real operational counts (patterns, scan chains,
memory/logic blocks, wafer count, defects). No seeded or placeholder values.
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.analytics import Alert, ScanChainFailure, WaferDefectUpload
from app.models.core import Lot, Product, Wafer
from app.models.recommendations import Recommendation
from app.models.uploads import AILogSummary, UploadJob
from app.schemas.common import GlobalFilters
from app.services.chart_aggregation import CHART_COLORS, _day_label
from app.services.date_filters import resolve_date_range
from app.services.filters import resolve_dimension_ids

logger = logging.getLogger("verilumen.cost")

_DOLLAR_RE = re.compile(r"\$?\s*([\d,]+(?:\.\d+)?)\s*([KkMm])?", re.IGNORECASE)

MODULE_LABELS = {
    "scan_chain": "Scan Chain",
    "mbist": "MBIST",
    "lbist": "LBIST",
    "wafer": "Wafer",
    "equipment": "Equipment",
}


@dataclass
class CostFacts:
    upload_job_id: str
    estimated_cost: float | None
    estimated_savings: float | None
    patterns_found: int
    scan_chains: int
    memory_blocks: int
    logic_blocks: int
    wafer_count: int
    defects_found: int
    yield_pct: float | None
    processing_ms: int | None
    file_format: str | None
    product_code: str | None
    lot_code: str | None
    wafer_code: str | None
    total_dies: int | None
    created_at: datetime


@dataclass
class CostAggregate:
    total_cost: float = 0.0
    total_savings: float = 0.0
    upload_count: int = 0
    uploads_with_cost: int = 0
    module_costs: dict[str, float] = field(default_factory=dict)
    yield_loss_cost: float = 0.0
    retest_cost: float = 0.0
    equipment_cost: float = 0.0
    facts: list[CostFacts] = field(default_factory=list)


def parse_dollar_amount(text: str | None) -> float | None:
    """Parse '$42K', '42800', '$1.2M' from recommendation impact strings."""
    if not text:
        return None
    m = _DOLLAR_RE.search(text)
    if not m:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    suffix = (m.group(2) or "").upper()
    if suffix == "K":
        val *= 1_000
    elif suffix == "M":
        val *= 1_000_000
    return val


def format_usd(amount: float | None, *, compact: bool = False) -> str:
    if amount is None or amount <= 0:
        return "—"
    if compact and amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if compact and amount >= 1_000:
        return f"${amount / 1_000:.1f}K"
    return f"${amount:,.0f}"


def format_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def compute_roi(total_cost: float, total_savings: float) -> float | None:
    """ROI = Savings / Investment (documented formula)."""
    if total_cost <= 0 or total_savings <= 0:
        return None
    return round(total_savings / total_cost, 4)


def equipment_cost_from_processing_ms(processing_ms: int | None) -> float | None:
    """Equipment/test-time cost = hours × COST_TESTER_USD_PER_HOUR when configured."""
    rate = get_settings().cost_tester_usd_per_hour
    if rate is None or processing_ms is None or processing_ms <= 0:
        return None
    hours = processing_ms / 3_600_000
    return round(hours * rate, 2)


def allocate_module_costs(facts: CostFacts) -> dict[str, float]:
    """Split upload cost by real operational weights (patterns/scan/memory/logic/wafers)."""
    base = facts.estimated_cost
    if base is None or base <= 0:
        return {}
    weights = {
        "scan_chain": float(max(facts.scan_chains, facts.defects_found, facts.patterns_found, 0)),
        "mbist": float(facts.memory_blocks or 0),
        "lbist": float(facts.logic_blocks or 0),
        "wafer": float(facts.wafer_count or 0),
    }
    total_w = sum(weights.values())
    if total_w <= 0:
        return {"scan_chain": base}
    return {k: round(base * (w / total_w), 2) for k, w in weights.items() if w > 0}


def compute_yield_loss_cost(facts: CostFacts) -> float | None:
    """Yield loss cost = Total Cost × (100 − Yield%) / 100."""
    if facts.estimated_cost is None or facts.yield_pct is None:
        return None
    return round(facts.estimated_cost * max(0.0, (100.0 - facts.yield_pct) / 100.0), 2)


def compute_retest_cost(facts: CostFacts) -> float | None:
    """Retest cost = Total Cost × Defects / max(Patterns, Defects, 1)."""
    if facts.estimated_cost is None or not facts.defects_found:
        return None
    denom = max(facts.patterns_found or 1, facts.defects_found, 1)
    return round(facts.estimated_cost * (facts.defects_found / denom), 2)


def _apply_summary_filters(query, filters: GlobalFilters, dim_ids: dict):
    from app.services.dashboard_service import _apply_date_filter, _apply_dim_filters

    query = _apply_dim_filters(
        query,
        dim_ids,
        [
            ("lot_id", UploadJob.lot_id),
            ("wafer_id", UploadJob.wafer_id),
            ("fab_id", UploadJob.fab_id),
            ("tester_id", UploadJob.tester_id),
            ("product_id", UploadJob.product_id),
        ],
    )
    return _apply_date_filter(query, AILogSummary.created_at, filters)


async def fetch_cost_facts(db: AsyncSession, filters: GlobalFilters) -> list[CostFacts]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = (
        select(AILogSummary, UploadJob, Lot, Wafer, Product)
        .join(UploadJob, AILogSummary.upload_job_id == UploadJob.id)
        .outerjoin(Lot, UploadJob.lot_id == Lot.id)
        .outerjoin(Wafer, UploadJob.wafer_id == Wafer.id)
        .outerjoin(Product, UploadJob.product_id == Product.id)
    )
    query = _apply_summary_filters(query, filters, dim_ids)
    result = await db.execute(query.order_by(AILogSummary.created_at.desc()).limit(500))
    facts: list[CostFacts] = []
    for summary, job, lot, wafer, product in result.all():
        meta = summary.raw_summary_json or {}
        fmt = meta.get("format") or job.file_type
        product_code = (product.code if product else None) or meta.get("product_code")
        lot_code = lot.lot_code if lot else meta.get("lot_id")
        wafer_code = wafer.wafer_code if wafer else meta.get("wafer_id")
        facts.append(
            CostFacts(
                upload_job_id=str(job.id),
                estimated_cost=float(summary.estimated_cost) if summary.estimated_cost is not None else None,
                estimated_savings=float(summary.estimated_savings) if summary.estimated_savings is not None else None,
                patterns_found=int(summary.patterns_found or 0),
                scan_chains=int(summary.scan_chains or 0),
                memory_blocks=int(summary.memory_blocks or 0),
                logic_blocks=int(summary.logic_blocks or 0),
                wafer_count=int(summary.wafer_count or 0),
                defects_found=int(summary.defects_found or 0),
                yield_pct=float(summary.yield_pct) if summary.yield_pct is not None else None,
                processing_ms=job.processing_ms,
                file_format=fmt,
                product_code=product_code,
                lot_code=lot_code,
                wafer_code=wafer_code,
                total_dies=int(wafer.total_dies) if wafer and wafer.total_dies else None,
                created_at=summary.created_at or datetime.now(UTC),
            )
        )
    return facts


def aggregate_cost_facts(facts: list[CostFacts]) -> CostAggregate:
    agg = CostAggregate(facts=facts)
    agg.upload_count = len(facts)
    module_totals: Counter[str] = Counter()

    for f in facts:
        if f.estimated_cost is not None and f.estimated_cost > 0:
            agg.total_cost += f.estimated_cost
            agg.uploads_with_cost += 1
            for mod, amt in allocate_module_costs(f).items():
                module_totals[mod] += amt
        if f.estimated_savings is not None and f.estimated_savings > 0:
            agg.total_savings += f.estimated_savings
        ylc = compute_yield_loss_cost(f)
        if ylc:
            agg.yield_loss_cost += ylc
        rtc = compute_retest_cost(f)
        if rtc:
            agg.retest_cost += rtc
        eq = equipment_cost_from_processing_ms(f.processing_ms)
        if eq:
            agg.equipment_cost += eq

    agg.module_costs = dict(module_totals)
    return agg


def _sparkline_from_series(values: list[float], limit: int = 7) -> list[float]:
    if not values:
        return []
    tail = values[-limit:]
    return [round(v, 2) for v in tail]


def _trend_pct(current: float, previous: float) -> tuple[float, str]:
    if previous <= 0:
        return 0.0, "up"
    change = round((current - previous) / previous * 100, 1)
    return change, "down" if change < 0 else "up"


def build_overview_kpis(agg: CostAggregate) -> list[dict]:
    if agg.uploads_with_cost == 0 and agg.total_savings <= 0:
        return []

    cost_series = [
        f.estimated_cost for f in agg.facts if f.estimated_cost is not None and f.estimated_cost > 0
    ]
    cost_series_chrono = list(reversed(cost_series))
    wafer_units = sum(max(f.wafer_count, 1) for f in agg.facts if f.estimated_cost)
    die_units = sum(f.total_dies or 0 for f in agg.facts if f.total_dies)

    total = agg.total_cost
    prev_total = sum(cost_series_chrono[:-1]) if len(cost_series_chrono) > 1 else total
    change, trend = _trend_pct(total, prev_total)

    kpis = [
        {
            "id": "total-cost",
            "title": "Total Test Cost",
            "value": format_usd(total, compact=True),
            "change": change,
            "trend": trend,
            "sparkline": _sparkline_from_series(cost_series_chrono),
            "positiveIsGood": False,
        },
        {
            "id": "cost-per-wafer",
            "title": "Cost per Wafer",
            "value": format_usd(total / wafer_units if wafer_units and total else None),
            "change": 0,
            "trend": "down",
            "sparkline": [],
            "positiveIsGood": False,
        },
        {
            "id": "projected-savings",
            "title": "Projected Savings",
            "value": format_usd(agg.total_savings, compact=True),
            "change": 0,
            "trend": "up",
            "sparkline": _sparkline_from_series(
                [f.estimated_savings or 0 for f in agg.facts if f.estimated_savings]
            ),
            "positiveIsGood": True,
        },
    ]
    if die_units > 0 and total > 0:
        kpis.insert(
            2,
            {
                "id": "cost-per-die",
                "title": "Cost per Die",
                "value": f"${total / die_units:.4f}",
                "change": 0,
                "trend": "down",
                "sparkline": [],
                "positiveIsGood": False,
            },
        )
    roi = compute_roi(agg.total_cost, agg.total_savings)
    if roi is not None:
        kpis.append(
            {
                "id": "roi",
                "title": "ROI",
                "value": f"{roi * 100:.0f}%",
                "change": 0,
                "trend": "up",
                "sparkline": [],
                "positiveIsGood": True,
            }
        )
    return kpis


def build_tab_kpis(agg: CostAggregate, tab: str) -> list[dict]:
    mod_key = {"scan-chain": "scan_chain", "mbist": "mbist", "lbist": "lbist", "wafer": "wafer"}.get(tab)
    if not mod_key:
        return build_overview_kpis(agg)
    mod_cost = agg.module_costs.get(mod_key, 0.0)
    if mod_cost <= 0 and agg.uploads_with_cost == 0:
        return []
    extra: dict[str, tuple[str, float]] = {
        "scan-chain": ("Pattern Cost", agg.module_costs.get("scan_chain", 0)),
        "mbist": ("MBIST Cost", agg.module_costs.get("mbist", 0)),
        "lbist": ("LBIST Cost", agg.module_costs.get("lbist", 0)),
        "wafer": ("Wafer Cost", agg.module_costs.get("wafer", 0)),
    }
    title, val = extra.get(tab, ("Module Cost", mod_cost))
    return [
        {
            "id": f"{tab}:total",
            "title": title,
            "value": format_usd(val, compact=True),
            "change": 0,
            "trend": "down",
            "sparkline": [],
            "positiveIsGood": False,
        },
        {
            "id": f"{tab}:retest",
            "title": "Retest Cost",
            "value": format_usd(agg.retest_cost, compact=True),
            "change": 0,
            "trend": "up",
            "sparkline": [],
            "positiveIsGood": False,
        },
        {
            "id": f"{tab}:yield-loss",
            "title": "Yield Loss Cost",
            "value": format_usd(agg.yield_loss_cost, compact=True),
            "change": 0,
            "trend": "up",
            "sparkline": [],
            "positiveIsGood": False,
        },
    ]


def build_product_cost_rows(facts: list[CostFacts]) -> list[dict]:
    rows: list[dict] = []
    for f in facts:
        if f.estimated_cost is None and f.estimated_savings is None:
            continue
        cost_per_die = None
        if f.estimated_cost and f.total_dies and f.total_dies > 0:
            cost_per_die = f.estimated_cost / f.total_dies
        rows.append(
            {
                "product": f.product_code or "—",
                "lot": f.lot_code or "—",
                "wafer": f.wafer_code or "—",
                "totalCost": format_usd(f.estimated_cost),
                "costPerDie": f"${cost_per_die:.4f}" if cost_per_die else "—",
                "yield": format_pct(f.yield_pct),
                "estimatedSavings": format_usd(f.estimated_savings),
            }
        )
    return rows


async def build_scan_chain_cost_rows(
    db: AsyncSession, filters: GlobalFilters, agg: CostAggregate
) -> list[dict]:
    from app.services.dashboard_service import _apply_date_filter, _apply_dim_filters

    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(ScanChainFailure)
    query = _apply_dim_filters(
        query, dim_ids, [("lot_id", ScanChainFailure.lot_id), ("wafer_id", ScanChainFailure.wafer_id)]
    )
    query = _apply_date_filter(query, ScanChainFailure.created_at, filters)
    result = await db.execute(query.order_by(ScanChainFailure.created_at.desc()).limit(200))
    failures = result.scalars().all()
    if not failures:
        return []

    scan_budget = agg.module_costs.get("scan_chain", 0.0)
    pattern_counts: Counter[str] = Counter()
    chain_by_pattern: dict[str, str] = {}
    for fail in failures:
        pid = fail.pattern_id or "unknown"
        pattern_counts[pid] += 1
        chain_by_pattern.setdefault(pid, fail.chain_id or "—")

    total_fail = sum(pattern_counts.values()) or 1
    total_processing_ms = sum(f.processing_ms or 0 for f in agg.facts if f.processing_ms)
    rows: list[dict] = []
    savings_pool = agg.total_savings
    for pid, count in pattern_counts.most_common(25):
        share = count / total_fail
        cost = scan_budget * share if scan_budget else None
        savings = savings_pool * share if savings_pool else None
        exec_ms = (total_processing_ms * share) if total_processing_ms else None
        exec_label = f"{exec_ms / 60_000:.1f} min" if exec_ms else "—"
        rows.append(
            {
                "patternId": pid,
                "scanChain": chain_by_pattern.get(pid, "—"),
                "executionTime": exec_label,
                "cost": format_usd(cost),
                "recommendation": "Review pattern cost share" if cost else "Awaiting cost data",
                "expectedSavings": format_usd(savings),
            }
        )
    return rows


def build_mbist_cost_rows(agg: CostAggregate) -> list[dict]:
    mbist_cost = agg.module_costs.get("mbist", 0.0)
    blocks = sum(f.memory_blocks for f in agg.facts if f.memory_blocks)
    if mbist_cost <= 0 and blocks == 0:
        return []
    per_block = mbist_cost / blocks if blocks else mbist_cost
    return [
        {
            "memory": f"Memory Blocks ({blocks or '—'})",
            "bank": "Aggregate",
            "cost": format_usd(mbist_cost),
            "repairCost": format_usd(per_block * max(blocks, 1) if blocks else None),
            "recommendation": "Derived from LOG memory block count" if blocks else "Awaiting LOG upload",
        }
    ]


def build_lbist_cost_rows(agg: CostAggregate) -> list[dict]:
    lbist_cost = agg.module_costs.get("lbist", 0.0)
    blocks = sum(f.logic_blocks for f in agg.facts if f.logic_blocks)
    if lbist_cost <= 0 and blocks == 0:
        return []
    return [
        {
            "logicBlock": f"Logic Blocks ({blocks or '—'})",
            "runtime": "—",
            "cost": format_usd(lbist_cost),
            "recommendation": "Derived from LOG logic block count" if blocks else "Awaiting LOG upload",
        }
    ]


def build_wafer_cost_rows(facts: list[CostFacts], agg: CostAggregate) -> list[dict]:
    rows: list[dict] = []
    wafer_budget = agg.module_costs.get("wafer", 0.0)
    wafer_facts = [f for f in facts if f.wafer_code or f.wafer_count]
    denom = len(wafer_facts) or 1
    for f in wafer_facts:
        ylc = compute_yield_loss_cost(f)
        share = wafer_budget / denom if wafer_budget else None
        cost = share or ylc
        rows.append(
            {
                "lot": f.lot_code or "—",
                "wafer": f.wafer_code or "—",
                "yield": format_pct(f.yield_pct),
                "cost": format_usd(cost),
                "recommendation": "Yield loss cost from parsed yield" if ylc else "Awaiting cost/yield data",
            }
        )
    return rows


async def build_ai_cost_recommendation_rows(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    from app.services.dashboard_service import _apply_date_filter, _apply_dim_filters

    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(Recommendation).where(Recommendation.agent_type.in_(["test-optimization", "pattern", "scan-debug"]))
    query = _apply_dim_filters(query, dim_ids, [("lot_id", Recommendation.lot_id)])
    query = _apply_date_filter(query, Recommendation.created_at, filters)
    result = await db.execute(query.order_by(Recommendation.created_at.desc()).limit(50))
    recs = list(result.scalars().all())

    def savings_key(r: Recommendation) -> float:
        parsed = parse_dollar_amount(r.expected_impact)
        return parsed if parsed is not None else 0.0

    recs.sort(key=lambda r: (savings_key(r), float(r.confidence or 0)), reverse=True)

    rows: list[dict] = []
    for r in recs[:20]:
        savings = parse_dollar_amount(r.expected_impact)
        module_map = {"pattern": "Scan Chain", "scan-debug": "Scan Chain", "test-optimization": "Scan Chain"}
        rows.append(
            {
                "module": module_map.get(r.agent_type or "", "Scan Chain"),
                "issue": r.category or r.action_text or "—",
                "currentCost": "—",
                "optimizedCost": "—",
                "savings": format_usd(savings),
                "priority": r.priority or "Medium",
                "confidence": float(r.confidence or 0),
                "recommendation": r.action_text or "—",
            }
        )
    return rows


def build_cost_time_series(facts: list[CostFacts], granularity: str = "daily") -> list[dict]:
    """Group uploads with explicit cost by day/week/month."""
    buckets: dict[str, list[float]] = defaultdict(list)
    wafer_buckets: dict[str, list[int]] = defaultdict(list)

    for f in facts:
        if f.estimated_cost is None:
            continue
        dt = f.created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        if granularity == "weekly":
            key = dt.strftime("%Y-W%W")
        elif granularity == "monthly":
            key = dt.strftime("%Y-%m")
        else:
            key = _day_label(dt)
        buckets[key].append(f.estimated_cost)
        wafer_buckets[key].append(max(f.wafer_count, 1))

    points: list[dict] = []
    for label in sorted(buckets.keys()):
        costs = buckets[label]
        wafers = wafer_buckets[label]
        total = sum(costs)
        points.append(
            {
                "label": label,
                "value": round(total, 2),
                "value2": round(total / sum(wafers), 2) if wafers else 0,
                "day": label,
                "totalCost": round(total, 2),
                "costPerWafer": round(total / sum(wafers), 2) if wafers else 0,
            }
        )
    return points[-14:]


def build_cost_charts_payload(agg: CostAggregate, facts: list[CostFacts], tab: str) -> dict[str, Any]:
    charts: dict[str, Any] = {}
    if agg.module_costs:
        segments = [
            {"name": MODULE_LABELS.get(k, k), "value": round(v, 2), "color": CHART_COLORS[i % len(CHART_COLORS)]}
            for i, (k, v) in enumerate(sorted(agg.module_costs.items(), key=lambda x: -x[1]))
        ]
        charts["costContribution"] = segments
        charts["costBreakdown"] = [
            {"label": MODULE_LABELS.get(k, k), "value": round(v / 1000, 2)} for k, v in agg.module_costs.items()
        ]

    trend = build_cost_time_series(facts)
    if trend:
        charts["monthlyCostTrend"] = trend
        charts["costTrendLive"] = trend

    if agg.total_savings > 0:
        charts["projectedSavings"] = [{"label": "Savings", "value": round(agg.total_savings, 2)}]

    stacked = {
        "label": "Aggregate",
        "equipment": round(agg.equipment_cost / 1000, 2),
        "tester": 0,
        "engineering": 0,
        "pattern": round(agg.module_costs.get("scan_chain", 0) / 1000, 2),
        "repair": round(agg.module_costs.get("mbist", 0) / 1000, 2),
        "retest": round(agg.retest_cost / 1000, 2),
    }
    if any(v > 0 for k, v in stacked.items() if k != "label"):
        charts["costDistribution"] = [stacked]

    if tab == "scan-chain" and agg.module_costs.get("scan_chain"):
        charts["patternCostTrend"] = trend
        charts["scanChainCostBars"] = charts.get("costBreakdown", [])

    if tab == "mbist":
        charts["memoryCostTrend"] = trend
    if tab == "lbist":
        charts["logicCostTrend"] = trend
    if tab == "wafer":
        charts["waferCostTrend"] = trend

    charts["aiCostSummary"] = build_ai_cost_summary(agg, facts)
    charts["enterpriseCostSummary"] = build_enterprise_summary(agg)
    return charts


async def build_wafer_tab_charts(
    db: AsyncSession, filters: GlobalFilters, agg: CostAggregate, facts: list[CostFacts]
) -> dict[str, Any]:
    """Live wafer cost charts from defect uploads and parsed yield facts."""
    from app.services.dashboard_service import _apply_date_filter, _apply_dim_filters

    charts: dict[str, Any] = {}
    wafer_budget = agg.module_costs.get("wafer", 0.0)
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(WaferDefectUpload)
    query = _apply_dim_filters(
        query, dim_ids, [("lot_id", WaferDefectUpload.lot_id), ("wafer_id", WaferDefectUpload.wafer_id)]
    )
    query = _apply_date_filter(query, WaferDefectUpload.created_at, filters)
    result = await db.execute(query.order_by(WaferDefectUpload.created_at.desc()).limit(200))
    uploads = result.scalars().all()

    zone_map = {
        "edge-ring": "Zone A",
        "edge-loc": "Zone A",
        "centre": "Zone B",
        "donut": "Zone B",
        "scratch": "Zone C",
        "local": "Zone C",
        "random": "Zone D",
        "near-full": "Zone D",
        "normal": "Zone D",
    }
    zone_counts: Counter[str] = Counter()
    grid: list[list[float]] = [[0.0 for _ in range(16)] for _ in range(12)]

    cost_per_die = None
    total_dies = sum(f.total_dies or 0 for f in facts if f.total_dies)
    if agg.total_cost and total_dies:
        cost_per_die = agg.total_cost / total_dies

    for upload in uploads:
        cls = upload.defect_class.value if upload.defect_class else "normal"
        zone_counts[zone_map.get(cls, "Zone D")] += 1
        if upload.hotspot_x is not None and upload.hotspot_y is not None:
            row = int(upload.hotspot_y) % 12
            col = int(upload.hotspot_x) % 16
            weight = float(upload.confidence or 50) / 100
            if cost_per_die:
                grid[row][col] = min(1.0, grid[row][col] + (weight * cost_per_die) / max(cost_per_die, 1))
            else:
                grid[row][col] = min(1.0, grid[row][col] + weight)

    if zone_counts and wafer_budget:
        total_zones = sum(zone_counts.values()) or 1
        charts["defectDensityCost"] = [
            {
                "label": zone,
                "value": round(wafer_budget * (count / total_zones) / 1000, 2),
            }
            for zone, count in zone_counts.most_common()
        ]
    elif zone_counts:
        charts["defectDensityCost"] = [
            {"label": zone, "value": round(count, 2)} for zone, count in zone_counts.most_common()
        ]

    yields = [f.yield_pct for f in facts if f.yield_pct is not None]
    if yields:
        avg_yield = sum(yields) / len(yields)
        pass_pct = round(avg_yield, 1)
        fail_pct = round(100 - avg_yield, 1)
        charts["yieldBinDistribution"] = [
            {"name": "Pass", "value": pass_pct, "color": "#22C55E"},
            {"name": "Fail", "value": fail_pct, "color": "#EF4444"},
        ]
    elif uploads:
        avg_yield = sum(float(u.yield_pct or 0) for u in uploads) / len(uploads)
        charts["yieldBinDistribution"] = [
            {"name": "Pass", "value": round(avg_yield, 1), "color": "#22C55E"},
            {"name": "Fail", "value": round(100 - avg_yield, 1), "color": "#EF4444"},
        ]

    max_cell = max((cell for row in grid for cell in row), default=0.0)
    if max_cell > 0:
        cells = [
            {"row": r, "col": c, "value": round(grid[r][c] / max_cell, 3)}
            for r in range(12)
            for c in range(16)
            if grid[r][c] > 0
        ]
    else:
        # Derive coarse heatmap from yield-loss cost when spatial defects are absent.
        cells = []
        for f in facts:
            if f.yield_pct is None or f.estimated_cost is None:
                continue
            intensity = max(0.0, (100.0 - f.yield_pct) / 100.0)
            if intensity <= 0:
                continue
            seed = abs(hash(f.wafer_code or f.upload_job_id)) % (12 * 16)
            cells.append({"row": seed // 16, "col": seed % 16, "value": round(intensity, 3)})

    if cells:
        charts["waferCostHeatmap"] = cells

    return charts


def build_ai_cost_summary(agg: CostAggregate, facts: list[CostFacts]) -> dict:
    if agg.uploads_with_cost == 0:
        return {}
    top_module = max(agg.module_costs.items(), key=lambda x: x[1])[0] if agg.module_costs else "—"
    top_pattern = "—"
    for f in facts:
        meta_pat = (f.file_format or "")
        if f.patterns_found:
            top_pattern = f"{meta_pat or 'upload'} ({f.patterns_found} patterns)"
            break
    longest_ms = max((f.processing_ms or 0 for f in facts), default=0)
    return {
        "highestCostModule": MODULE_LABELS.get(top_module, top_module),
        "mostExpensivePattern": top_pattern,
        "longestTestTime": f"{longest_ms / 1000:.1f}s" if longest_ms else "—",
        "highestRetestCost": format_usd(agg.retest_cost, compact=True),
        "highestRepairCost": format_usd(agg.module_costs.get("mbist", 0), compact=True),
        "estimatedSavings": format_usd(agg.total_savings, compact=True),
    }


def build_enterprise_summary(agg: CostAggregate) -> dict:
    if agg.uploads_with_cost == 0 and agg.total_savings <= 0:
        return {}
    optimized = max(agg.total_cost - agg.total_savings, 0)
    roi = compute_roi(agg.total_cost, agg.total_savings)
    modules = []
    for k, v in agg.module_costs.items():
        mod_savings = (agg.total_savings * v / agg.total_cost) if agg.total_cost and agg.total_savings else None
        modules.append(
            {
                "module": MODULE_LABELS.get(k, k),
                "currentCost": format_usd(v, compact=True),
                "optimizedCost": format_usd(v - mod_savings, compact=True) if mod_savings else "—",
                "savings": format_usd(mod_savings, compact=True) if mod_savings else "—",
            }
        )
    avg_yield = None
    yields = [f.yield_pct for f in agg.facts if f.yield_pct is not None]
    if yields:
        avg_yield = sum(yields) / len(yields)
    return {
        "modules": modules,
        "totalCost": format_usd(agg.total_cost, compact=True),
        "totalSavings": format_usd(agg.total_savings, compact=True),
        "roi": f"{roi * 100:.0f}%" if roi else "—",
        "yieldImprovement": format_pct(avg_yield),
        "testTimeReduction": "—",
    }


async def build_cost_intelligence_payload(
    db: AsyncSession, tab: str, filters: GlobalFilters
) -> dict[str, Any]:
    facts = await fetch_cost_facts(db, filters)
    agg = aggregate_cost_facts(facts)

    if tab == "overview":
        rows = build_product_cost_rows(facts)
        kpis = build_overview_kpis(agg)
    elif tab == "scan-chain":
        rows = await build_scan_chain_cost_rows(db, filters, agg)
        kpis = build_tab_kpis(agg, tab)
    elif tab == "mbist":
        rows = build_mbist_cost_rows(agg)
        kpis = build_tab_kpis(agg, tab)
    elif tab == "lbist":
        rows = build_lbist_cost_rows(agg)
        kpis = build_tab_kpis(agg, tab)
    elif tab == "wafer":
        rows = build_wafer_cost_rows(facts, agg)
        kpis = build_tab_kpis(agg, tab)
    elif tab == "ai-optimization":
        rows = await build_ai_cost_recommendation_rows(db, filters)
        kpis = build_overview_kpis(agg)
    else:
        rows = []
        kpis = []

    charts = build_cost_charts_payload(agg, facts, tab)
    if tab == "wafer":
        charts.update(await build_wafer_tab_charts(db, filters, agg, facts))
    return {"kpis": kpis, "rows": rows, "charts": charts}


async def build_executive_cost_trend(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    facts = await fetch_cost_facts(db, filters)
    return build_cost_time_series(facts)


async def evaluate_cost_alerts(db: AsyncSession, upload_job_id: str) -> None:
    """Create cost alerts when parsed cost exceeds rolling average (real data only)."""
    settings = get_settings()
    threshold_pct = settings.cost_alert_threshold_pct

    result = await db.execute(
        select(AILogSummary, UploadJob)
        .join(UploadJob, AILogSummary.upload_job_id == UploadJob.id)
        .where(UploadJob.id == upload_job_id)
    )
    row = result.one_or_none()
    if not row:
        return
    summary, job = row
    if summary.estimated_cost is None:
        return

    current = float(summary.estimated_cost)
    since = datetime.now(UTC) - timedelta(days=30)
    avg_result = await db.execute(
        select(func.avg(AILogSummary.estimated_cost)).where(
            AILogSummary.created_at >= since,
            AILogSummary.estimated_cost.isnot(None),
            AILogSummary.upload_job_id != job.id,
        )
    )
    avg_val = avg_result.scalar()
    if avg_val is None or float(avg_val) <= 0:
        return

    avg = float(avg_val)
    over_pct = (current - avg) / avg * 100
    if over_pct < threshold_pct:
        return

    existing = await db.execute(
        select(Alert).where(
            Alert.source_module == "Cost",
            Alert.lot_id == job.lot_id,
            Alert.title == "Cost Budget Alert",
            Alert.status == "Open",
        )
    )
    if existing.scalar_one_or_none():
        return

    db.add(
        Alert(
            source_module="Cost",
            severity="Medium",
            status="Open",
            title="Cost Budget Alert",
            description=(
                f"Parsed test cost ${current:,.0f} exceeds 30-day average "
                f"${avg:,.0f} by {over_pct:.1f}% (threshold {threshold_pct}%)"
            ),
            lot_id=job.lot_id,
            wafer_id=job.wafer_id,
        )
    )


def recommendation_savings_score(rec: Recommendation) -> float:
    """Rank recommendations by parsed savings text then confidence."""
    return parse_dollar_amount(rec.expected_impact) or 0.0
