# Deep Analytics Analysis (Prompt 30)

**Date:** 2026-07-06  
**Module:** `app/services/deep_analytics.py` + extensions to `chart_aggregation.py`

---

## Summary

Stage 7 deep analytics extend existing `/dashboard/{module}/{tab}` responses with SQL-aggregated `charts`, tab-specific `rows`, and `_meta` blocked markers. No new APIs. No fabricated series.

---

## Chart inventory

| Chart | Module / Tab | Data source | Real? | Status |
|-------|--------------|-------------|-------|--------|
| uploadTrend | Executive | `upload_jobs.created_at` | ✓ | Ready |
| alertTrend | Executive | `alerts` | ✓ | Ready |
| recommendationTrend | Executive | `recommendations` | ✓ | Ready |
| yieldTrend | Executive | `wafer_defect_uploads.yield_pct` | ✓ | Ready (when uploads exist) |
| costTrendLive | Executive | `ai_log_summaries.estimated_cost` | ✓ | Ready (LOG cost) |
| failureTrend | Executive | `scan_chain_failures` | ✓ | Ready |
| patternGrowthTrend | Executive | `ai_log_summaries` pattern counts | ✓ | Ready |
| failureDistribution | Scan Chain | `scan_chain_failures.fail_type` | ✓ | Ready |
| failureByLotData | Scan Chain / Failure | `scan_chain_failures` + `lots` | ✓ | Ready |
| chainFailureRanking | Scan Diagnosis | `scan_chain_failures.chain_id` | ✓ | Ready |
| patternImportTrend | Pattern Analysis | `upload_jobs` / summaries by day | ✓ | Ready |
| patternClusterDistribution | Pattern Analysis | File format (STIL/WGL/LOG) | ✓ | Ready (format, not AI cluster) |
| patternFrequency | Pattern Analysis | `raw_summary_json.pattern_names` | ✓ | Ready |
| patternSimilarityMatrix | Pattern Analysis | — | ✗ | **Blocked** — embeddings |
| patternAnalysisCoverageTrend | Pattern Analysis | — | ✗ | **Blocked** — ATPG coverage |
| patternScatterData | Pattern Analysis | — | ✗ | **Blocked** — embeddings |
| connectivityGraphData | Scan Chain | — | ✗ | **Blocked** — graph store |
| memoryBlockTrend | MBIST | `ai_log_summaries.memory_blocks` | ✓ | Ready (LOG) |
| addressHeatmap | MBIST | — | ✗ | **Blocked** — mbist_failures |
| sessionTrend | LBIST | `ai_log_summaries.logic_blocks` | ✓ | Ready (LOG) |
| coverageHeatmap | LBIST | — | ✗ | **Blocked** — lbist_sessions |
| spatialHeatmap | Wafer | `wafer_defect_uploads` hotspots | ✓ | Ready |
| dieYieldHeatmap | Wafer / Executive | — | ✗ | **Blocked** — die_results |
| costContribution | Cost | cost_engine module split | ✓ | Ready |
| rewardTrend | Recommendations | `recommendation_feedback.reward_value` | ✓ | Ready |
| confidenceTrend | Recommendations | `recommendations.confidence` | ✓ | Ready |
| resolutionTimeTrend | Alerts | `alerts.read_at − created_at` | ✓ | Ready (when read) |

---

## Blocked analytics (documented, not simulated)

| Analytic | Blocked by | Required |
|----------|------------|----------|
| Pattern similarity matrix | `pattern_embeddings` | Embedding pipeline + vector store |
| ATPG coverage trend | `coverage_metrics` | STDF or coverage file parser |
| Die yield/cost heatmap | `die_results` | STDF per-die x/y from PIR/PRR |
| MBIST address heatmap | `mbist_failures` | Per-address MBIST log/STDF |
| LBIST coverage heatmap | `lbist_sessions` | Per-block LBIST metrics |
| Scan/pattern dependency graphs | `connectivity_graph` | STIL/WGL relational graph export |
| Diagnosis confidence 30-day | `diagnosis_confidence` | AI diagnosis worker scores |

---

## API mapping

All analytics flow through existing routes:

```
GET /api/v1/dashboard/executive
GET /api/v1/dashboard/{module}/{tab}
```

Extended response shape:

```json
{
  "kpis": [],
  "rows": [],
  "charts": {
    "failureTrend": [{"label": "Mon", "value": 2}],
    "_meta": {
      "patternSimilarityMatrix": {"status": "blocked", "reason": "...", "blockedBy": "..."}
    }
  }
}
```

---

## Cache

Heavy aggregations cached via existing `dash:{module}:{tab}:{filter_hash}` keys (60–120s). Invalidated on parse complete (`dash:*`).

---

## Frontend

- `AnalyticsChartEmpty` — blocked / empty chart states in live mode
- `useLiveModuleCharts` — exposes `chartMeta` from `charts._meta`
- Executive `WaferHeatmap` — no dummy grid in live mode without data
