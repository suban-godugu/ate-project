# Enterprise Cost Intelligence Engine

**Module:** `app/services/cost_engine.py`  
**Status:** Production — real parsed data only

---

## Architecture

```
Upload (LOG/STDF/…) → ai_log_summaries + scan_chain_failures
                              ↓
                      cost_engine.py (SQL aggregate)
                              ↓
              GET /dashboard/cost-intelligence/{tab}
                              ↓
                   Redis dash:cost-intelligence:*
```

No duplicate APIs. No speculative tables. Empty states when no cost-bearing uploads exist.

---

## Data sources

| Source | Fields used |
|--------|-------------|
| `ai_log_summaries` | `estimated_cost`, `estimated_savings`, counts, yield |
| `upload_jobs` | `processing_ms`, lot/wafer/product FKs |
| `scan_chain_failures` | `pattern_id`, `chain_id` for pattern cost shares |
| `recommendations` | `expected_impact` ($ parsing for ranking) |
| `wafers` | `total_dies` for cost-per-die |

STIL/WGL/PAT uploads contribute operational counts but **no dollar amounts** until LOG-style cost lines or explicit cost fields exist.

---

## Documented formulas

| Metric | Formula |
|--------|---------|
| **Total test cost** | `SUM(estimated_cost)` where not null |
| **Cost per wafer** | `total_cost / SUM(wafer_count)` |
| **Cost per die** | `total_cost / SUM(total_dies)` |
| **Module allocation** | `cost × weight / SUM(weights)` where weights = scan chains, memory blocks, logic blocks, wafer count |
| **Yield loss cost** | `cost × (100 − yield_pct) / 100` |
| **Retest cost** | `cost × defects / max(patterns, defects, 1)` |
| **Equipment cost** | `(processing_ms / 3_600_000) × COST_TESTER_USD_PER_HOUR` (optional env) |
| **ROI** | `total_savings / total_cost` |
| **Pattern cost share** | `scan_chain_budget × failures_for_pattern / total_failures` |
| **Module savings share** | `total_savings × module_cost / total_cost` |

---

## API

Existing endpoint only:

```
GET /api/v1/dashboard/cost-intelligence/{tab}
```

Tabs: `overview`, `scan-chain`, `mbist`, `lbist`, `wafer`, `ai-optimization`

Response: `{ kpis, rows, charts }` — charts include `aiCostSummary`, `enterpriseCostSummary`, `costBreakdown`.

Executive cost trend: `GET /dashboard/executive` → `costTrend` from real uploads.

---

## Cache

- Key: `dash:cost-intelligence:{tab}:{filter_sha256}:p1` (60s)
- Invalidated: `dash:*` on parse complete (`parse_worker`)

Optional env:

```
COST_TESTER_USD_PER_HOUR=120
COST_ALERT_THRESHOLD_PCT=12
```

---

## Alerts

After successful parse, `evaluate_cost_alerts()` creates a **Cost** alert when parsed `estimated_cost` exceeds the 30-day rolling average by `COST_ALERT_THRESHOLD_PCT`.

---

## Known limitations

1. **Dollar amounts require LOG cost lines** (or future `test_cost_events` table).
2. STDF/STIL/WGL provide yield and counts but not test cost unless LOG also uploaded.
3. MBIST/LBIST rows are aggregate (block counts from LOG), not per-block names.
4. Wafer heatmap cost still needs per-die spatial data (`die_results` — deferred).
5. Seeded `module_fact_rows` cost data is bypassed when cost engine returns live aggregates.

---

## Tests

```bash
python -m pytest tests/test_cost_engine.py -v
```
