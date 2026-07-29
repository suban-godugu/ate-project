# FA-FR-003 Technical AI Agent Specification — Failure Rate Computation Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-003  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-003 Technical AI Agent Specification — Failure Rate Computation Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Failure Rate Computation Engine |
| FR ID | FA-FR-003 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-003 computes failure rates, historical trends, and threshold breaches from ingested normalized records and FA-FR-002 detected patterns, providing the quantitative foundation for classification, recurrence, and reporting modules.

**Scope:** Failure rate API, statistical aggregation, trend analysis, threshold configuration, computation history, dashboard visualization.  
**Stakeholders:** Yield Engineering, Failure Analysis Engineers, Test Operations, Fab Management, Platform/DevOps.  
**Out of scope for this agent:** Pattern rule matching (FA-FR-002), fault taxonomy (FA-FR-004), recurrence detection (FA-FR-005), correlation (FA-FR-006), spatial analytics (FA-FR-007/008), prediction (FA-FR-009), report PDF generation (FA-FR-010).

---

## 3. Business Objective

**Problem:** Failure rates are computed manually in spreadsheets with inconsistent formulas, no historical baselines, and delayed threshold alerting. Engineers lack auditable, reproducible rate calculations tied to specific lots and test stages.

**Expected outcome:** Automated, formula-consistent failure rate computation with historical trend lines, configurable thresholds, and computation audit trail available within minutes of pattern detection completion.

**KPIs:**
- Rate computation completion &lt; 3 min for 100k records  
- Formula consistency 100% against engineering-approved rate definitions  
- Historical trend data retained for ≥12 months  
- Threshold breach alerts within 1 min of computation  
- 100% lineage to `upload_id`, `dataset_id`, and detection run  

---

## 4. Technical Overview

FA-FR-003 implements a statistical computation pipeline gated on FA-FR-001 and FA-FR-002:

1. **Edge:** Next.js `ate-dashboard` `/failure-rates` screen with rate charts and threshold controls  
2. **API:** FastAPI routers under `/api/v1/failure-rate`  
3. **Application:** FailureRateService orchestrates aggregation → rate formula → trend → threshold check → persist  
4. **Domain:** Rate formulas, statistical aggregators, trend calculators, threshold evaluators  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for computation job cache  

Architecture decision: rate formulas are versioned and immutable per computation run. Re-computation with same inputs produces identical outputs.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (read-only lineage reference) |
| Cache | Redis (computation status, threshold config cache) |
| AI | Rules-based formulas only; no LLM authority over rate values |
| Testing | Pytest, formula regression fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 completed ingestion and FA-FR-002 pattern detection  
- Compute failure rates per lot, wafer, die, test stage, and pattern  
- Persist `failure_rates`, `failure_statistics`, `historical_failure_rates`  
- Generate `trend_analysis` with moving averages and period-over-period deltas  
- Evaluate `threshold_configuration` and flag breaches  
- Append `computation_history` for every run  
- Expose REST APIs and `/failure-rates` dashboard  

**Exclusions:**
- Pattern detection rules (FA-FR-002)  
- Fault classification (FA-FR-004)  
- Recurrence tracking (FA-FR-005)  
- Correlation statistics (FA-FR-006)  
- Modification of source records or detected patterns  

---

## 7. Functional Requirements

### FR ID
FA-FR-003

### Description
The agent shall compute semiconductor failure rates from normalized records and detected patterns, produce historical trends and threshold evaluations, and persist auditable statistics for downstream FA modules.

### Priority
**Critical / P0** — quantitative gate for classification and recurrence modules.

### Inputs
- `dataset_id` or `detection_run_id` from FA-FR-002  
- Optional scope filters: `lot_id`, `wafer_id`, `test_stage`, `pattern_id`, `date_range`  
- Optional `threshold_config_id` for breach evaluation  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `failure_rates` per scope dimension  
- `failure_statistics` aggregate summaries  
- `historical_failure_rates` time-series rows  
- `trend_analysis` with direction and delta  
- Threshold breach flags  
- `computation_history` run metadata  

### Processing Logic
1. Verify FA-FR-001 and FA-FR-002 gates  
2. Load normalized records and detected patterns for scope  
3. Apply approved rate formulas (fail_count / total_count × 100)  
4. Aggregate by lot, wafer, die, stage, pattern  
5. Compute historical trends against prior computation_history  
6. Evaluate thresholds; flag breaches  
7. Persist all entities; append computation_history  
8. Return rate summary with trend and breach alerts  

### Dependencies
- FA-FR-001 (`normalized_records`)  
- FA-FR-002 (`detected_patterns`, `pattern_occurrences`)  
- PostgreSQL, Redis  
- Downstream: FA-FR-004…010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Computation &lt; 3 min for 100k records; API list &lt; 400 ms |
| Scalability | Batch aggregation; indexed historical lookups |
| Availability | API N≥2; PostgreSQL HA |
| Logging | JSON with computation_run_id, scope, rates computed, duration_ms |
| Security | RBAC for compute trigger and threshold config changes |
| Maintainability | Versioned rate formulas; Alembic migrations |
| Reliability | Deterministic re-computation; append-only history |
| Monitoring | Threshold breach alerts; rate drift detection |

---

## 9. AI Behavior Specification

### Role
Deterministic statistical calculator — no AI inference over rate values.

### Reasoning Strategy
Formula application → aggregation → trend comparison → threshold evaluation. Fully rule-based.

### Workflow
Gate → Aggregate → Compute → Trend → Threshold → Persist → Expose.

### Decision Logic
If upstream gates fail → reject. If total_count = 0 for scope → rate = null with explicit zero-denominator flag.

### Confidence Handling
Not applicable to rate values (deterministic). Trend confidence based on sample size thresholds in BR-004.

### Limitations
Rates reflect input data quality; garbage-in produces auditable but misleading rates flagged by integrity metadata.

### Fallback Behaviour
Missing historical data → trend marked `INSUFFICIENT_HISTORY`. Threshold config missing → compute rates without breach evaluation.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| dataset_id | UUID | Yes (or detection_run_id) | FA-FR-001 completed | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| detection_run_id | UUID | Alt scope | FA-FR-002 completed | `d4e5f6a7-b8c9-0123-def4-567890abcdef` |
| lot_id | string | No | Non-empty if provided | `LOT-2026-0412` |
| test_stage | string | No | Enum | `SCAN` |
| pattern_id | string | No | Must exist in detected_patterns | `PAT-STUCK-AT-1000` |
| threshold_config_id | UUID | No | Must exist | `t1h2r3e4-s5h6-7890-abcd-ef1234567890` |
| date_range | object | No | ISO8601 | `{"start":"2026-07-01","end":"2026-07-17"}` |
| X-User-Id | string | Prod | Non-empty | `yield-engineer-05` |

---

## 11. Output Specification

### Schema (computation success — conceptual)
`computation_run.id`, `status`, `rates_computed`, `threshold_breaches`, `failure_rates[]`, `trend_analysis`, `processing_duration_ms`

### JSON Example

```json
{
  "computation_run": {
    "id": "c3d4e5f6-a7b8-9012-cdef-345678901234",
    "dataset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "rates_computed": 42,
    "threshold_breaches": 3,
    "processing_duration_ms": 4200
  },
  "failure_rates": [
    {
      "scope": "lot",
      "scope_id": "LOT-2026-0412",
      "fail_count": 847,
      "total_count": 10000,
      "failure_rate_pct": 8.47,
      "trend": "increasing",
      "threshold_breached": true
    }
  ]
}
```

### Engineering Report
Failure rate section in FA-FR-010 cites top rates, trend direction, and threshold breaches.

### Dashboard Output
`/failure-rates` line charts, rate tables, threshold breach badges, historical comparison.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Computation shall not execute unless FA-FR-001 ingestion and FA-FR-002 detection are completed. |
| BR-002 | Failure rate = (fail_count / total_count) × 100; zero denominator yields null rate with flag. |
| BR-003 | Quarantined FA-FR-001 records are excluded from rate denominators. |
| BR-004 | Trend analysis requires minimum 3 historical data points; otherwise mark INSUFFICIENT_HISTORY. |
| BR-005 | Threshold breach when failure_rate_pct exceeds configured upper bound. |
| BR-006 | Each computation appends immutable row to `computation_history`. |
| BR-007 | Rate formulas are versioned; computation_history stores formula_version. |
| BR-008 | Historical rates are never deleted; retention ≥12 months. |

---

## 13. Key Engineering Rules

1. Never fabricate fail_count or total_count values.  
2. Always validate upstream gates before computation.  
3. Maintain deterministic outputs for identical inputs + formula version.  
4. Never modify source records or detected patterns.  
5. Preserve semiconductor terminology (lot, wafer, die, yield, DPM).  
6. Explicit null rates for zero denominators; never divide by zero.  
7. Persist formula_version on every computation run.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 + FA-FR-002 completed |
| Latency | &lt; 3 min for 100k records |
| Historical retention | ≥12 months |
| Memory | Batch aggregation; stream large scopes |
| Concurrency | One active computation per dataset_id scope |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/failure-rate/compute`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON body with `dataset_id` or `detection_run_id`, optional filters and `threshold_config_id`.

### Response
200 JSON computation run + failure_rates + trend_analysis.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Upstream gate failed |
| 429 | Rate limited |
| 500 | Unexpected |

### Validation Errors
`UPSTREAM_GATE_FAILED`, `DATASET_NOT_FOUND`, `THRESHOLD_CONFIG_INVALID`, `ZERO_DENOMINATOR_SCOPE`.

Additional endpoints: `GET /api/v1/failure-rate`, `GET /api/v1/failure-rate/{scope_id}`, `GET /api/v1/failure-rate/trends`, `GET /api/v1/failure-rate/history`, `GET /api/v1/failure-rate/thresholds`, `PUT /api/v1/failure-rate/thresholds/{id}`.

---

## 16. Database Design

### Tables
`failure_rates`, `failure_statistics`, `historical_failure_rates`, `trend_analysis`, `threshold_configuration`, `computation_history`

### Columns (representative — `failure_rates`)
`id` (PK UUID), `computation_run_id`, `scope`, `scope_id`, `fail_count`, `total_count`, `failure_rate_pct`, `formula_version`, `dataset_id`, `created_at`

### Primary Keys
UUID PKs on all entity tables.

### Foreign Keys
`failure_rates.computation_run_id` → `computation_history.id`; `historical_failure_rates` references prior rate rows; `trend_analysis.computation_run_id` → `computation_history.id`.

### Indexes
`(scope, scope_id, created_at)`, `(dataset_id)`, `(computation_run_id)`, `(threshold_breached)` partial index.

### Relationships
One computation run → many failure_rates; one threshold_configuration → many breach evaluations.

### ER Explanation
Failure rates read FA-FR-001/002 outputs and write analytics consumed by FA-FR-004 onward. Historical rates enable trend analysis without recomputing from raw records.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/failure-rates`, `/failure-rates/trends`, `/failure-rates/thresholds` |
| User Actions | Trigger computation, configure thresholds, filter by lot/stage, export |
| Charts | Rate line charts, trend arrows, breach heatmap (Recharts) |
| Tables | Rate by scope, historical comparison, breach list |
| Filters | Dataset, lot, wafer, test stage, pattern, date range |
| Downloads | Rate CSV, trend export |
| Notifications | Toast on breach detection; React Query polling |

---

## 18. AI Workflow

1. User selects dataset with completed detection on `/failure-rates`.  
2. API verifies FA-FR-001 and FA-FR-002 gates.  
3. Records and patterns aggregated by scope dimensions.  
4. Rate formulas applied; results persisted.  
5. Historical trends computed against prior runs.  
6. Thresholds evaluated; breaches flagged.  
7. FA-FR-004 consumes rates for classification context.  
8. FA-FR-010 cites rates and trends in reports.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | FA-FR-001/002 incomplete | Missing upstream | Complete prior modules | High |
| `DATASET_NOT_FOUND` | Invalid dataset_id | Missing entity | Verify ID | Medium |
| `ZERO_DENOMINATOR_SCOPE` | total_count = 0 | Empty scope filter | Widen scope | Low |
| `THRESHOLD_CONFIG_INVALID` | Bad threshold | Missing/invalid config | Fix configuration | Medium |
| `FORMULA_VERSION_MISMATCH` | Unknown formula | Deprecated version | Use active version | Medium |
| `COMPUTATION_IN_PROGRESS` | Mutex conflict | Concurrent run | Wait | Low |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |
| `INSUFFICIENT_HISTORY` | &lt; 3 data points | New scope | Informational flag | Low |

---

## 20. Logging & Monitoring

- **Structured Logging:** computation_run_id, scope, rates_computed, breaches, duration_ms  
- **Audit Logging:** computation_history append-only  
- **Performance Metrics:** records/s, rates/s, elapsed_ms  
- **Health Checks:** GET /health includes formula version status  
- **Prometheus Metrics:** `fa_failure_rate_computations_total`, `fa_threshold_breaches_total`, `fa_rate_compute_duration_ms`  
- **Alerts:** threshold breach spike, computation latency breach  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: compute trigger, threshold admin |
| Input Validation | Pydantic; scope enum validation |
| Encryption | TLS; PostgreSQL at-rest encryption |
| Secrets Management | Env/vault |
| OWASP | ORM-only queries; no user-supplied formulas |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-003-01 | Compute rates on valid dataset | POST compute with gated dataset | 200 completed | rates_computed &gt; 0 |
| TC-003-02 | Reject upstream gate failure | POST without FA-FR-002 | 424 | UPSTREAM_GATE_FAILED |
| TC-003-03 | Zero denominator handling | Compute on empty scope | 200 with null rate | No divide-by-zero |
| TC-003-04 | Threshold breach detection | Set low threshold, compute | breach flagged | threshold_breached = true |
| TC-003-05 | Historical trend | Run compute twice | trend direction present | delta computed |
| TC-003-06 | Deterministic re-run | Same inputs twice | identical rates | formula consistency |

---

## 23. Acceptance Criteria

1. Computation executes only after FA-FR-001 and FA-FR-002 complete.  
2. Failure rates match approved formula definitions.  
3. Historical trends computed when ≥3 data points exist.  
4. Threshold breaches flagged and exposed via API and dashboard.  
5. Computation history records every run with formula version.  
6. Dashboard `/failure-rates` displays rates and trends.  
7. Downstream FA-FR-004 can query rates by scope.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Large scope aggregation timeout | Batch processing; async jobs |
| Business | Misleading rates from bad ingestion | Surface integrity metadata |
| Assumption | FA-FR-002 patterns cover relevant failures | Document scope limitations |
| Assumption | Threshold configs maintained by yield team | Admin UI with audit |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001, FA-FR-002 |
| External APIs | None |
| Database | PostgreSQL |
| Infrastructure | Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-003 | This document | `/api/v1/failure-rate/*` | failure_rates, failure_statistics, historical_failure_rates, trend_analysis, threshold_configuration, computation_history | TC-003-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] API contracts match OpenAPI intent  
- [ ] DB tables align with Alembic migrations  
- [ ] FA-FR-001/002 gate enforced  
- [ ] Rate formulas documented and versioned  
- [ ] Test cases cover gate, formula, threshold  
- [ ] No placeholders remain  
- [ ] Lineage fields documented  

---

## 28. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Prepared By | Principal Enterprise AI Architect | ________________ | 2026-07-17 |
| Reviewed By | Senior Software Architect | ________________ | __________ |
| Approved By | Engineering / FA Lead | ________________ | __________ |

**Version:** 1.0  

### Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-003 |
