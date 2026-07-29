# Cost Engine Analysis (Prompt 29)

**Date:** 2026-07-06  
**Decision:** **No new tables** — cost data fits `ai_log_summaries`, `scan_chain_failures`, `upload_jobs`, `recommendations`, `alerts`.

---

## Existing cost-related fields

| Field | Current source | Dashboard usage | Missing? |
|-------|----------------|-----------------|----------|
| `estimated_cost` | LOG parser → `ai_log_summaries` | Cost KPIs, product rows, trends | Only when LOG uploaded with cost lines |
| `estimated_savings` | LOG parser → `ai_log_summaries` | Savings KPI, ROI, projected savings chart | Same |
| `yield_pct` | STDF/LOG → `ai_log_summaries`, `wafers` | Yield loss cost formula | ✓ |
| `patterns_found` | All parsers → summary columns | Module allocation weights | ✓ |
| `scan_chains` | LOG/STIL/WGL summaries | Scan chain cost allocation | ✓ |
| `memory_blocks` | LOG parser | MBIST cost allocation | LOG only |
| `logic_blocks` | LOG parser | LBIST cost allocation | LOG only |
| `defects_found` | STDF/LOG | Retest cost, scan allocation | ✓ |
| `processing_ms` | `upload_jobs` | Equipment cost (optional rate) | Needs `COST_TESTER_USD_PER_HOUR` |
| `pattern_id` | `scan_chain_failures` | Pattern-level cost rows | Needs cost + failures |
| `expected_impact` | `recommendations` | AI optimization ranking | Parsed `$` text only |
| Seeded `module_fact_rows` | `seed.py` | Was overview product table | **Replaced by cost engine** |
| Seeded `KpiSnapshot` cost KPIs | `seed_data.py` | Was overview KPIs | **Replaced when real uploads exist** |

---

## What was NOT available (before Prompt 29)

| Need | Gap |
|------|-----|
| Central cost aggregation | Logic scattered in `chart_aggregation.py` + seeds |
| Module breakdown | No SQL from parser counts |
| Sub-tab rows | Empty backend; frontend mock |
| ROI / trends | Partial; executive trend from seeds |
| Cost alerts | Manual seed only |

---

## Schema candidates (deferred)

| Table | Verdict |
|-------|---------|
| `cost_snapshot` | **No** — aggregate at query time |
| `module_cost_summary` | **No** — `cost_engine.py` + Redis `dash:cost-intelligence:*` |
| `test_cost_events` | **Defer** — no per-event parser output yet |
| `equipment_cost_history` | **No** — use `processing_ms` + optional rate |

---

## Implementation

| Component | Path |
|-----------|------|
| Cost engine | `app/services/cost_engine.py` |
| Dashboard wiring | `dashboard_service.build_module_payload` (cost-intelligence) |
| Charts | `chart_aggregation.build_cost_charts` → engine |
| Executive trend | `build_executive_cost_trend` |
| Alerts | `evaluate_cost_alerts` from `parse_worker` |
| Search | Cost entries in `build_search_index` |
| Cache | Existing `dash:cost-intelligence:{tab}:{hash}` (60s TTL) |

---

## Verification matrix

| Cost source | Calculation | Dashboard | API | Cache |
|-------------|-------------|-----------|-----|-------|
| LOG `Test Cost:` | Direct | Overview KPI | `GET /dashboard/cost-intelligence/overview` | `dash:cost-intelligence:*` |
| Module split | Proportional by scan/memory/logic/wafer counts | Contribution donut | Same | Same |
| Yield loss | `cost × (100−yield)/100` | Tab KPI | Sub-tabs | Same |
| Retest | `cost × defects/max(patterns,defects)` | Tab KPI | Sub-tabs | Same |
| Pattern rows | Scan budget × failure share | Scan chain tab | `scan-chain` tab | Same |
| ROI | `savings/cost` | Overview KPI | Same | Same |
| Alerts | Cost > rolling avg + threshold | Alerts module | `POST` auto on parse | N/A |
