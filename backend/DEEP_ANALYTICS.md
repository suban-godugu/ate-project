# Enterprise Deep Analytics Engine

**Modules:** `app/services/deep_analytics.py`, `app/services/chart_aggregation.py`  
**Status:** Stage 7 complete — real SQL aggregation, explicit blocked states

---

## Architecture

```
Parsers → PostgreSQL (failures, summaries, uploads, alerts, feedback)
                    ↓
         chart_aggregation.build_*_charts()
                    ↓
         deep_analytics.merge_deep_analytics()
                    ↓
    GET /dashboard/{module}/{tab}  +  Redis dash:*
                    ↓
         React Query hooks → existing chart components
```

---

## Data sources

| Table / store | Analytics |
|---------------|-----------|
| `scan_chain_failures` | Failure trends, lot comparison, chain ranking, heatmap cells |
| `ai_log_summaries` + `raw_summary_json` | Pattern names, format distribution, MBIST/LBIST block counts |
| `upload_jobs` | Upload growth, pattern import trend |
| `wafer_defect_uploads` | Defect class, spatial hotspot heatmap, yield trend |
| `alerts` | Severity, frequency, resolution time |
| `recommendations` + `recommendation_feedback` | Trends, confidence, reward, application |
| `cost_engine` | Cost module charts (Prompt 29) |

---

## Time series

Trend buckets use upload/failure timestamps grouped by weekday label (`Mon`–`Sun`) within the active date filter. Extended granularities (hourly/monthly) can be added via `resolve_date_range` without new APIs.

---

## Empty and blocked states

Charts without data return `[]`. Blocked analytics include `charts._meta.{chartKey}`:

```json
{
  "status": "blocked",
  "reason": "Pattern embeddings not available",
  "blockedBy": "pattern_embeddings",
  "requiredParser": "embedding pipeline"
}
```

Frontend `AnalyticsChartEmpty` renders these in live mode instead of mock fallbacks.

---

## Known limitations

1. Pattern “clusters” are **file format** distribution (STIL/WGL/LOG), not ML clusters.
2. MBIST/LBIST depth requires LOG summary fields or future `mbist_failures` / `lbist_sessions` tables.
3. Executive wafer spatial heatmap needs `wafer_defect_uploads` or `die_results`.
4. Sub-tab KPIs still depend on `kpi_snapshots` seeds when no live KPI query exists.

---

## Tests

```bash
python -m pytest tests/test_chart_aggregation.py -v
```

---

## Related docs

- [`DEEP_ANALYTICS_ANALYSIS.md`](DEEP_ANALYTICS_ANALYSIS.md) — full chart inventory
- [`COST_ENGINE.md`](COST_ENGINE.md) — cost tab analytics
- [`PARSER_SCHEMA_ANALYSIS.md`](PARSER_SCHEMA_ANALYSIS.md) — deferred tables
