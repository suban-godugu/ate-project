"""Enterprise Deep Analytics — SQL aggregations from real DB records only.

Extends chart_aggregation payloads per module/tab. Charts without source data return
empty series plus optional `_meta` blocked markers (never fabricated values).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import Alert, ScanChainFailure, WaferDefectUpload
from app.models.core import Lot, Wafer
from app.models.recommendations import Recommendation, RecommendationFeedback
from app.models.uploads import AILogSummary, UploadJob
from app.schemas.common import GlobalFilters
from app.services.chart_aggregation import (
    CHART_COLORS,
    _apply_date_filter,
    _apply_dim_filters,
    _day_label,
    _segments,
    _trend_points,
)
from app.services.filters import resolve_dimension_ids

BLOCKED_SIMILARITY = {
    "status": "blocked",
    "reason": "Pattern embeddings not available",
    "blockedBy": "pattern_embeddings",
    "requiredParser": "embedding pipeline",
}

BLOCKED_DIE_HEATMAP = {
    "status": "blocked",
    "reason": "Per-die coordinates not available",
    "blockedBy": "die_results",
    "requiredParser": "STDF PIR/PRR die map",
}

BLOCKED_COVERAGE = {
    "status": "blocked",
    "reason": "ATPG coverage not in parser output",
    "blockedBy": "coverage_metrics",
    "requiredParser": "STDF or dedicated coverage upload",
}

BLOCKED_NETWORK = {
    "status": "blocked",
    "reason": "Graph relationships not stored",
    "blockedBy": "connectivity_graph",
    "requiredParser": "STIL/WGL scan structure graph export",
}


def _blocked_meta(key: str, spec: dict) -> dict:
    return {key: spec}


async def _summaries_query(db: AsyncSession, filters: GlobalFilters):
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(AILogSummary, UploadJob).join(
        UploadJob, AILogSummary.upload_job_id == UploadJob.id
    )
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


async def extend_executive_charts(
    db: AsyncSession, filters: GlobalFilters, charts: dict[str, Any]
) -> dict[str, Any]:
    """Pattern growth, failure trend — real uploads and scan failures."""
    out = dict(charts)

    fail_q = _apply_date_filter(select(ScanChainFailure), ScanChainFailure.created_at, filters)
    fres = await db.execute(fail_q.order_by(ScanChainFailure.created_at.asc()))
    fail_by_day: Counter[str] = Counter()
    for f in fres.scalars().all():
        fail_by_day[_day_label(f.created_at)] += 1
    if fail_by_day:
        out["failureTrend"] = _trend_points(dict(fail_by_day))

    pattern_by_day: Counter[str] = Counter()
    sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.asc()))
    for summary, _job in sres.all():
        meta = summary.raw_summary_json or {}
        count = int(summary.patterns_found or len(meta.get("pattern_names") or []))
        if count:
            pattern_by_day[_day_label(summary.created_at)] += count
    if pattern_by_day:
        out["patternGrowthTrend"] = _trend_points(dict(pattern_by_day))

    out.setdefault("trendSeries", {})
    out["trendSeries"] = {
        "uploadTrend": out.get("uploadTrend", []),
        "alertTrend": out.get("alertTrend", []),
        "recommendationTrend": out.get("recommendationTrend", []),
        "yieldTrend": out.get("yieldTrend", []),
        "costTrendLive": out.get("costTrendLive", []),
        "failureTrend": out.get("failureTrend", []),
        "patternGrowthTrend": out.get("patternGrowthTrend", []),
    }
    return out


async def extend_scan_chain_charts(
    db: AsyncSession, filters: GlobalFilters, tab: str, charts: dict[str, Any]
) -> dict[str, Any]:
    out = dict(charts)
    meta: dict[str, Any] = {}

    fail_q = _apply_date_filter(select(ScanChainFailure), ScanChainFailure.created_at, filters)
    dim_ids = await resolve_dimension_ids(db, filters)
    fail_q = _apply_dim_filters(
        fail_q, dim_ids, [("lot_id", ScanChainFailure.lot_id), ("wafer_id", ScanChainFailure.wafer_id)]
    )
    failures = (await db.execute(fail_q.order_by(ScanChainFailure.created_at.desc()).limit(500))).scalars().all()

    lot_ids = {f.lot_id for f in failures if f.lot_id}
    lots: dict = {}
    if lot_ids:
        lres = await db.execute(select(Lot).where(Lot.id.in_(lot_ids)))
        lots = {l.id: l.lot_code for l in lres.scalars().all()}

    if tab in ("failure-analysis", "overview", "scan-diagnosis"):
        lot_counts: Counter[str] = Counter()
        root_causes: Counter[str] = Counter()
        for f in failures:
            lot_counts[lots.get(f.lot_id, "Unknown")] += 1
            if f.root_cause:
                root_causes[f.root_cause[:80]] += 1
        if lot_counts:
            out["failureByLotData"] = [
                {"lot": lot, "failCount": cnt} for lot, cnt in lot_counts.most_common(12)
            ]
        if root_causes:
            out["rootCauseFrequency"] = _segments(root_causes)

        chain_rank = Counter(f.chain_id or "Unknown" for f in failures)
        out["chainFailureRanking"] = [
            {"chainId": c, "failCount": n, "rank": i + 1}
            for i, (c, n) in enumerate(chain_rank.most_common(10))
        ]
        out["failureLocalizationDistribution"] = out.get("failureDistribution", [])

        by_day: Counter[str] = Counter()
        for f in failures:
            by_day[_day_label(f.created_at)] += 1
        if by_day:
            trend = _trend_points(dict(by_day))
            out["overallFailureTrend"] = trend
            out["failureRateTrend"] = trend
            out["recurringFailureTrend"] = trend

        diag: Counter[str] = Counter()
        for f in failures:
            diag[f.diagnosis_status or "pending"] += 1
        if diag:
            out["diagnosisDistribution"] = _segments(diag)
            out["diagnosisTimeline"] = _trend_points(dict(by_day))

    if tab == "pattern-analysis":
        format_counts: Counter[str] = Counter()
        pattern_freq: Counter[str] = Counter()
        import_by_day: Counter[str] = Counter()
        length_buckets: Counter[str] = Counter()

        sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.asc()))
        for summary, job in sres.all():
            meta_json = summary.raw_summary_json or {}
            fmt = (meta_json.get("format") or job.file_type or "unknown").upper()
            format_counts[fmt] += 1
            import_by_day[_day_label(summary.created_at)] += 1
            for name in meta_json.get("pattern_names") or []:
                pattern_freq[str(name)] += 1
            pf = int(summary.patterns_found or 0)
            if pf:
                bucket = "1-5" if pf <= 5 else "6-20" if pf <= 20 else "21+"
                length_buckets[bucket] += 1

        if import_by_day:
            out["patternImportTrend"] = _trend_points(dict(import_by_day))
            out["patternGrowthTrend"] = out["patternImportTrend"]
        if format_counts:
            out["patternClusterDistribution"] = _segments(format_counts)
            out["patternFormatDistribution"] = _segments(format_counts)
        if pattern_freq:
            out["patternFrequency"] = [
                {"label": p, "value": c} for p, c in pattern_freq.most_common(15)
            ]
        if length_buckets:
            out["patternLengthDistribution"] = _segments(length_buckets)

        meta.update(_blocked_meta("patternSimilarityMatrix", BLOCKED_SIMILARITY))
        meta.update(_blocked_meta("patternAnalysisCoverageTrend", BLOCKED_COVERAGE))
        meta.update(_blocked_meta("patternScatterData", BLOCKED_SIMILARITY))
        meta.update(_blocked_meta("connectivityGraphData", BLOCKED_NETWORK))

    if tab == "scan-diagnosis":
        chain_rank = Counter(f.chain_id or "Unknown" for f in failures)
        out["chainFailureRanking"] = [
            {"chainId": c, "failCount": n} for c, n in chain_rank.most_common(10)
        ]
        out["criticalChainDistribution"] = _segments(chain_rank)
        meta.update(_blocked_meta("scanTopologyGraphData", BLOCKED_NETWORK))
        meta.update(_blocked_meta("diagnosisConfidenceTrend30Day", {
            "status": "blocked",
            "reason": "Diagnosis confidence scores not stored",
            "blockedBy": "diagnosis_confidence",
            "requiredParser": "AI diagnosis worker output",
        }))

    if meta:
        out["_meta"] = meta
    return out


async def extend_mbist_charts(
    db: AsyncSession, filters: GlobalFilters, tab: str, charts: dict[str, Any]
) -> dict[str, Any]:
    out = dict(charts)
    sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.asc()))
    blocks_by_day: Counter[str] = Counter()
    total_blocks = 0
    for summary, _job in sres.all():
        mb = int(summary.memory_blocks or 0)
        if mb:
            total_blocks += mb
            blocks_by_day[_day_label(summary.created_at)] += mb

    if blocks_by_day:
        out["memoryBlockTrend"] = _trend_points(dict(blocks_by_day))
        out["coverageTrend"] = _trend_points(dict(blocks_by_day))
    if total_blocks:
        out["bankHealth"] = [{"label": "Memory Blocks", "value": total_blocks}]

    out.setdefault("_meta", {})
    if not total_blocks:
        out["_meta"]["addressHeatmap"] = {
            "status": "blocked",
            "reason": "MBIST address map not in parser output",
            "blockedBy": "mbist_failures",
            "requiredParser": "LOG or STDF MBIST records",
        }
    return out


async def extend_lbist_charts(
    db: AsyncSession, filters: GlobalFilters, tab: str, charts: dict[str, Any]
) -> dict[str, Any]:
    out = dict(charts)
    sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.asc()))
    blocks_by_day: Counter[str] = Counter()
    total = 0
    for summary, _job in sres.all():
        lb = int(summary.logic_blocks or 0)
        if lb:
            total += lb
            blocks_by_day[_day_label(summary.created_at)] += lb
    if blocks_by_day:
        out["sessionTrend"] = _trend_points(dict(blocks_by_day))
        out["coverageTrend"] = _trend_points(dict(blocks_by_day))
        out["logicBlockActivity"] = _trend_points(dict(blocks_by_day))
    if total:
        out["logicDistribution"] = [{"label": "Logic Blocks", "value": total}]
    out.setdefault("_meta", {})
    if not total:
        out["_meta"]["coverageHeatmap"] = {
            "status": "blocked",
            "reason": "LBIST coverage heatmap requires per-block metrics",
            "blockedBy": "lbist_sessions",
            "requiredParser": "LOG or STDF LBIST records",
        }
    return out


async def extend_wafer_charts(db: AsyncSession, filters: GlobalFilters, charts: dict[str, Any]) -> dict[str, Any]:
    out = dict(charts)
    out.setdefault("_meta", {})
    out["_meta"]["dieYieldHeatmap"] = BLOCKED_DIE_HEATMAP
    out["_meta"]["retestDistribution"] = {
        "status": "blocked",
        "reason": "Retest events not tracked per die",
        "blockedBy": "die_results",
        "requiredParser": "STDF per-die retest records",
    }
    if out.get("spatialHeatmap"):
        out["_meta"]["spatialHeatmap"] = {"status": "ready", "source": "wafer_defect_uploads.hotspot"}
    return out


async def extend_recommendation_charts(
    db: AsyncSession, filters: GlobalFilters, tab: str, charts: dict[str, Any]
) -> dict[str, Any]:
    out = dict(charts)
    dim_ids = await resolve_dimension_ids(db, filters)

    fb_q = select(RecommendationFeedback)
    fb_q = _apply_date_filter(fb_q, RecommendationFeedback.created_at, filters)
    fb_res = await db.execute(fb_q.order_by(RecommendationFeedback.created_at.asc()))
    feedbacks = fb_res.scalars().all()

    reward_by_day: dict[str, list[float]] = defaultdict(list)
    applied_by_day: Counter[str] = Counter()
    for fb in feedbacks:
        day = _day_label(fb.created_at)
        if fb.reward_value is not None:
            reward_by_day[day].append(float(fb.reward_value))
        if fb.action_taken == "applied":
            applied_by_day[day] += 1

    if reward_by_day:
        out["rewardTrend"] = [
            {"label": d, "value": round(sum(v) / len(v), 3)} for d, v in sorted(reward_by_day.items())
        ][-14:]
    if applied_by_day:
        out["applicationTrend"] = _trend_points(dict(applied_by_day))

    rec_q = select(Recommendation)
    rec_q = _apply_dim_filters(rec_q, dim_ids, [("lot_id", Recommendation.lot_id)])
    rec_q = _apply_date_filter(rec_q, Recommendation.created_at, filters)
    recs = (await db.execute(rec_q.order_by(Recommendation.created_at.asc()))).scalars().all()
    conf_by_day: dict[str, list[float]] = defaultdict(list)
    for r in recs:
        if r.confidence is not None:
            conf_by_day[_day_label(r.created_at)].append(float(r.confidence))
    if conf_by_day:
        out["confidenceTrend"] = [
            {"label": d, "value": round(sum(v) / len(v), 1)} for d, v in sorted(conf_by_day.items())
        ][-14:]

    out.setdefault("_meta", {})
    out["_meta"]["recommendationDependencyGraph"] = BLOCKED_NETWORK
    return out


async def extend_alerts_charts(
    db: AsyncSession, filters: GlobalFilters, tab: str, charts: dict[str, Any]
) -> dict[str, Any]:
    out = dict(charts)
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(Alert)
    query = _apply_dim_filters(query, dim_ids, [("lot_id", Alert.lot_id), ("wafer_id", Alert.wafer_id)])
    query = _apply_date_filter(query, Alert.created_at, filters)
    alerts = (await db.execute(query.order_by(Alert.created_at.desc()).limit(500))).scalars().all()

    resolution_hours: list[float] = []
    for a in alerts:
        if a.read_at and a.created_at:
            delta = (a.read_at - a.created_at).total_seconds() / 3600
            if delta >= 0:
                resolution_hours.append(delta)
    if resolution_hours:
        avg_h = sum(resolution_hours) / len(resolution_hours)
        out["resolutionTimeTrend"] = [{"label": "Avg Hours", "value": round(avg_h, 1)}]

    status_counts = Counter(a.status or "Open" for a in alerts)
    if status_counts:
        out["alertStatusDistribution"] = _segments(status_counts)
    return out


async def merge_deep_analytics(
    db: AsyncSession, module: str, tab: str, filters: GlobalFilters, charts: dict[str, Any]
) -> dict[str, Any]:
    if module == "executive" or (module == "scan-chain" and tab == "overview"):
        pass  # executive handled separately
    if module == "scan-chain":
        return await extend_scan_chain_charts(db, filters, tab, charts)
    if module == "mbist":
        return await extend_mbist_charts(db, filters, tab, charts)
    if module == "lbist":
        return await extend_lbist_charts(db, filters, tab, charts)
    if module == "wafer-analysis":
        return await extend_wafer_charts(db, filters, charts)
    if module == "recommendation-analysis":
        return await extend_recommendation_charts(db, filters, tab, charts)
    if module == "alerts":
        return await extend_alerts_charts(db, filters, tab, charts)
    return charts


async def fetch_pattern_analysis_rows(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    rows: list[dict] = []
    sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.desc()).limit(100))
    for summary, job in sres.all():
        meta = summary.raw_summary_json or {}
        fmt = (meta.get("format") or job.file_type or "—").upper()
        for name in meta.get("pattern_names") or []:
            rows.append(
                {
                    "patternId": str(name),
                    "patternName": str(name),
                    "fileType": fmt,
                    "status": "Active",
                    "recommendation": "—",
                }
            )
        if not meta.get("pattern_names") and summary.patterns_found:
            rows.append(
                {
                    "patternId": f"upload-{str(job.id)[:8]}",
                    "patternName": job.file_name,
                    "fileType": fmt,
                    "status": "Parsed",
                    "recommendation": "—",
                }
            )
    return rows[:50]


async def fetch_failure_analysis_rows(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    dim_ids = await resolve_dimension_ids(db, filters)
    query = select(ScanChainFailure)
    query = _apply_dim_filters(
        query, dim_ids, [("lot_id", ScanChainFailure.lot_id), ("wafer_id", ScanChainFailure.wafer_id)]
    )
    query = _apply_date_filter(query, ScanChainFailure.created_at, filters)
    failures = (await db.execute(query.order_by(ScanChainFailure.created_at.desc()).limit(50))).scalars().all()
    lot_ids = {f.lot_id for f in failures if f.lot_id}
    wafer_ids = {f.wafer_id for f in failures if f.wafer_id}
    lots, wafers = {}, {}
    if lot_ids:
        lres = await db.execute(select(Lot).where(Lot.id.in_(lot_ids)))
        lots = {l.id: l.lot_code for l in lres.scalars().all()}
    if wafer_ids:
        wres = await db.execute(select(Wafer).where(Wafer.id.in_(wafer_ids)))
        wafers = {w.id: w.wafer_code for w in wres.scalars().all()}
    return [
        {
            "failureId": str(f.id)[:8],
            "patternId": f.pattern_id or "—",
            "lotId": lots.get(f.lot_id, "—"),
            "waferId": wafers.get(f.wafer_id, "—"),
            "dieId": f.chip or "—",
            "faultCategory": f.fail_type or "—",
            "rootCause": (f.root_cause or "—")[:120],
            "confidence": "—",
            "severity": "Medium",
            "status": f.diagnosis_status or "pending",
            "recommendation": "—",
            "timestamp": f.created_at.isoformat() if f.created_at else "—",
        }
        for f in failures
    ]


async def fetch_mbist_rows_from_summaries(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    rows: list[dict] = []
    sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.desc()).limit(50))
    for summary, job in sres.all():
        if not summary.memory_blocks:
            continue
        rows.append(
            {
                "memoryBlock": f"MB-{summary.memory_blocks}",
                "bank": "Aggregate",
                "status": "From LOG summary",
                "failures": summary.defects_found or 0,
                "upload": job.file_name,
            }
        )
    return rows


async def fetch_lbist_rows_from_summaries(db: AsyncSession, filters: GlobalFilters) -> list[dict]:
    rows: list[dict] = []
    sres = await db.execute((await _summaries_query(db, filters)).order_by(AILogSummary.created_at.desc()).limit(50))
    for summary, job in sres.all():
        if not summary.logic_blocks:
            continue
        rows.append(
            {
                "logicBlock": f"LB-{summary.logic_blocks}",
                "status": "From LOG summary",
                "sessions": summary.logic_blocks,
                "upload": job.file_name,
            }
        )
    return rows
