# FA-FR-008 Technical AI Agent Specification — Wafer Analysis Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-008  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-008 Technical AI Agent Specification — Wafer Analysis Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Wafer Analysis Engine |
| FR ID | FA-FR-008 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-008 performs wafer-level analytics including yield computation, radial pattern analysis, and edge-center failure distribution, aggregating die-level results from FA-FR-007 into wafer-scale insights for prediction and reporting modules.

**Scope:** Wafer analysis API, wafer yield, radial patterns, edge-center distribution, wafer health metrics, dashboard at `/wafer-analysis`.  
**Stakeholders:** Yield Engineering, Failure Analysis Engineers, Fab Management, Test Operations, Platform/DevOps.  
**Out of scope for this agent:** Die-level clustering (FA-FR-007), pattern detection (FA-FR-002), correlation (FA-FR-006), fault prediction (FA-FR-009), report PDF generation (FA-FR-010).

---

## 3. Business Objective

**Problem:** Wafer-level yield and spatial pattern analysis requires manual aggregation of die maps. Engineers lack automated yield curves, radial failure patterns, and edge-vs-center bias detection integrated with die health scores.

**Expected outcome:** Automated wafer-level yield, radial pattern detection, and edge-center analysis with wafer health metrics within minutes of die analysis completion.

**KPIs:**
- Wafer analysis completion &lt; 3 min per wafer  
- Yield calculation accuracy 100% against die pass/fail counts  
- Radial and edge-center patterns detected when bias &gt; 1.5× uniform  
- Wafer health metric (0–100) for every analyzed wafer  
- 100% lineage to die_analysis_run  

---

## 4. Technical Overview

FA-FR-008 implements a wafer-level analytics pipeline gated on FA-FR-001 through FA-FR-007:

1. **Edge:** Next.js `ate-dashboard` `/wafer-analysis` screen with wafer yield charts and radial maps  
2. **API:** FastAPI routers under `/api/v1/wafer-analysis`  
3. **Application:** WaferAnalysisService orchestrates yield → radial → edge-center → wafer health  
4. **Domain:** Yield calculators, radial bin analyzers, edge-center comparators, wafer health scorers  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for analysis cache  

Architecture decision: wafer yield = passing_dies / total_dies × 100. Radial analysis bins dies by distance from wafer center. Edge-center compares outer ring vs inner core failure rates.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (read-only lineage) |
| Cache | Redis (wafer analysis job status) |
| AI | Deterministic analytics; no LLM |
| Testing | Pytest, wafer map benchmark fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 through FA-FR-007 completion  
- Compute wafer yield from die pass/fail aggregates  
- Analyze radial failure patterns by distance bins  
- Compare edge vs center failure rates  
- Compute wafer health metric (0–100)  
- Persist wafer_* tables (wafer_analysis, wafer_yield, wafer_radial_patterns, wafer_edge_center, wafer_health_metrics)  
- Expose REST APIs and `/wafer-analysis` dashboard  

**Exclusions:**
- Die-level hotspot/clustering (FA-FR-007)  
- Fault prediction (FA-FR-009)  
- Report generation (FA-FR-010)  

---

## 7. Functional Requirements

### FR ID
FA-FR-008

### Description
The agent shall perform wafer-level yield computation, radial pattern analysis, and edge-center failure distribution from die analysis results, producing wafer health metrics for downstream prediction and reporting.

### Priority
**High / P1** — enables fault prediction and reporting.

### Inputs
- `die_analysis_run_id` or `wafer_id` or `lot_id`  
- Optional radial bin count (default 5)  
- Optional edge ring fraction (default 0.15)  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- Wafer yield percentage per wafer  
- Radial pattern bins with failure rates  
- Edge vs center comparison with bias flag  
- Wafer health metric (0–100)  
- Wafer analysis run metadata  

### Processing Logic
1. Verify FA-FR-001 through FA-FR-007 gates  
2. Load die health scores and pass/fail for scope wafers  
3. Compute yield = passing_dies / total_dies × 100  
4. Bin dies radially; compute per-bin failure rates  
5. Compare edge ring vs center core failure rates  
6. Flag radial/edge-center bias when ratio &gt; 1.5× uniform  
7. Compute wafer health metric per BR-004  
8. Persist wafer_* entities  

### Dependencies
- FA-FR-001 through FA-FR-007  
- PostgreSQL, Redis  
- Downstream: FA-FR-009, FA-FR-010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Analysis &lt; 3 min per wafer; lot batch &lt; 10 min for 25 wafers |
| Scalability | Batch wafer processing; indexed wafer lookups |
| Availability | API N≥2; PostgreSQL HA |
| Logging | JSON with wafer_analysis_run_id, wafers_analyzed, duration_ms |
| Security | RBAC for analysis trigger |
| Maintainability | Configurable radial bins and edge fraction |
| Reliability | Deterministic yield and health formulas |
| Monitoring | Low yield wafer alerts |

---

## 9. AI Behavior Specification

### Role
Deterministic wafer analytics — yield, radial, edge-center are formula-based.

### Reasoning Strategy
Die aggregation → yield → radial bins → edge-center ratio → wafer health score.

### Workflow
Gate → Aggregate → Yield → Radial → Edge-Center → Health → Persist → Expose.

### Decision Logic
Radial bias flagged when any bin failure rate &gt; 1.5× wafer average. Edge-center bias when edge_rate / center_rate &gt; 1.5.

### Confidence Handling
Bias confidence from sample size per bin/zone. Minimum 10 dies per bin for radial confidence.

### Limitations
Requires die coordinates for radial/edge-center. Yield computable from pass/fail alone.

### Fallback Behaviour
Missing coordinates → yield only, radial/edge-center marked UNAVAILABLE.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| die_analysis_run_id | UUID | Yes (or wafer_id) | FA-FR-007 completed | `d1i2e3a4-n5a6-7890-abcd-ef1234567890` |
| wafer_id | string | Alt scope | Non-empty | `WAFER-LOT0412-05` |
| lot_id | string | No | Non-empty | `LOT-2026-0412` |
| radial_bins | integer | No | 3–20, default 5 | `5` |
| edge_fraction | float | No | 0.05–0.30, default 0.15 | `0.15` |
| bias_threshold | float | No | Default 1.5 | `1.5` |
| X-User-Id | string | Prod | Non-empty | `yield-engineer-05` |

---

## 11. Output Specification

### Schema (wafer analysis success — conceptual)
`wafer_analysis_run.id`, `status`, `wafers_analyzed`, `wafer_results[]`

### JSON Example

```json
{
  "wafer_analysis_run": {
    "id": "w1a2f3e4-r5a6-7890-abcd-ef1234567890",
    "die_analysis_run_id": "d1i2e3a4-n5a6-7890-abcd-ef1234567890",
    "status": "completed",
    "wafers_analyzed": 25
  },
  "wafer_results": [
    {
      "wafer_id": "WAFER-LOT0412-05",
      "yield_pct": 91.5,
      "wafer_health": 72,
      "radial_bias_detected": true,
      "edge_center_bias_detected": true,
      "edge_center_ratio": 2.1,
      "radial_bins": [
        {"bin": 1, "distance_pct": 20, "failure_rate_pct": 4.2},
        {"bin": 5, "distance_pct": 100, "failure_rate_pct": 12.8}
      ]
    }
  ]
}
```

### Engineering Report
Wafer analysis section in FA-FR-010 cites yield, radial bias, edge-center ratio.

### Dashboard Output
`/wafer-analysis` yield chart, radial profile, edge-center comparison, wafer health table.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Wafer analysis requires FA-FR-001 through FA-FR-007 completed. |
| BR-002 | Yield = (passing_dies / total_dies) × 100; zero dies yields null. |
| BR-003 | Radial bias when any bin failure rate &gt; bias_threshold × wafer average (default 1.5×). |
| BR-004 | Wafer health = weighted average of die health scores for wafer. |
| BR-005 | Edge-center bias when edge_failure_rate / center_failure_rate &gt; bias_threshold. |
| BR-006 | Edge ring = outer edge_fraction (default 15%) of wafer radius. |
| BR-007 | Minimum 10 dies per radial bin for confidence; else bin marked LOW_SAMPLE. |
| BR-008 | Each analysis run persists immutable wafer_analysis metadata. |

---

## 13. Key Engineering Rules

1. Never fabricate die pass/fail counts.  
2. Always validate upstream gate chain.  
3. Yield formula is deterministic.  
4. Radial bins computed from die distance to wafer center.  
5. Preserve semiconductor terminology (yield, edge exclusion, radial profile).  
6. Edge-center zones defined by configurable edge_fraction.  
7. Persist radial_bins and edge_fraction on every run.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 through FA-FR-007 |
| Latency | &lt; 3 min per wafer |
| Radial bins | 3–20, default 5 |
| Edge fraction | 0.05–0.30, default 0.15 |
| Bias threshold | Default 1.5× |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/wafer-analysis/analyze`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with die_analysis_run_id or wafer_id/lot_id, optional radial and edge params.

### Response
200 wafer analysis run + wafer_results array.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Upstream gate failed |
| 500 | Unexpected |

### Validation Errors
`UPSTREAM_GATE_FAILED`, `DIE_ANALYSIS_RUN_NOT_FOUND`, `WAFER_NOT_FOUND`, `ZERO_DIE_COUNT`.

Additional endpoints: `GET /api/v1/wafer-analysis`, `GET /api/v1/wafer-analysis/{wafer_id}`, `GET /api/v1/wafer-analysis/yield`, `GET /api/v1/wafer-analysis/radial/{wafer_id}`, `GET /api/v1/wafer-analysis/edge-center/{wafer_id}`, `GET /api/v1/wafer-analysis/runs/{run_id}`.

---

## 16. Database Design

### Tables
`wafer_analysis`, `wafer_analysis_runs`, `wafer_yield`, `wafer_radial_patterns`, `wafer_edge_center`, `wafer_health_metrics`

### Columns (representative — `wafer_yield`)
`id` (PK UUID), `wafer_analysis_run_id`, `wafer_id`, `lot_id`, `total_dies`, `passing_dies`, `failing_dies`, `yield_pct`, `created_at`

### Primary Keys
UUID PKs on all wafer_* tables.

### Foreign Keys
All wafer_* tables reference `wafer_analysis_runs.id`; wafer_id links to die health scores.

### Indexes
`(wafer_id)`, `(lot_id, yield_pct)`, `(wafer_analysis_run_id)`, `(radial_bias_detected)` partial.

### Relationships
One wafer analysis run → many wafer yield/radial/edge-center/health rows per wafer.

### ER Explanation
Wafer analysis aggregates FA-FR-007 die results into wafer-scale metrics consumed by FA-FR-009 prediction and FA-FR-010 reports.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/wafer-analysis`, `/wafer-analysis/{wafer_id}`, `/wafer-analysis/yield` |
| User Actions | Trigger analysis, select lot, view radial profile, export yield |
| Charts | Yield bar by wafer, radial line chart, edge-center comparison (Recharts) |
| Tables | Wafer health ranked, bias flags, yield summary |
| Filters | Lot, yield range, bias detected, date |
| Downloads | Yield CSV, radial profile export |
| Notifications | Toast on low yield; React Query polling |

---

## 18. AI Workflow

1. User triggers wafer analysis on `/wafer-analysis` after die analysis.  
2. API verifies FA-FR-001 through FA-FR-007 gates.  
3. Die health scores aggregated per wafer.  
4. Yield computed from pass/fail counts.  
5. Radial bins and edge-center zones analyzed.  
6. Bias flags set when thresholds exceeded.  
7. Wafer health metrics persisted.  
8. FA-FR-009 consumes wafer health for fault prediction context.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | Prior modules incomplete | Missing FA-FR-001–007 | Complete upstream | High |
| `DIE_ANALYSIS_RUN_NOT_FOUND` | Invalid run id | Missing entity | Verify ID | Medium |
| `WAFER_NOT_FOUND` | Invalid wafer_id | Typo | Verify wafer | Medium |
| `ZERO_DIE_COUNT` | No dies on wafer | Empty wafer | Informational null yield | Low |
| `RADIAL_UNAVAILABLE` | Missing coordinates | No die x/y | Yield only path | Medium |
| `LOW_SAMPLE_BIN` | &lt; 10 dies in bin | Small wafer | Flag bin | Low |
| `YIELD_COMPUTE_ERROR` | Division issue | Zero total | Null yield | Low |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** wafer_analysis_run_id, wafers_analyzed, avg_yield, duration_ms  
- **Audit Logging:** wafer_analysis_runs append-only  
- **Performance Metrics:** wafers/s, elapsed_ms  
- **Health Checks:** die analysis dependency status  
- **Prometheus Metrics:** `fa_wafer_analysis_runs_total`, `fa_wafer_avg_yield_pct`, `fa_radial_bias_wafers_total`  
- **Alerts:** yield below threshold, edge-center bias spike  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: analyze trigger, viewer read |
| Input Validation | Pydantic; bin/fraction range checks |
| Encryption | TLS; PostgreSQL at-rest |
| Secrets Management | Env/vault |
| OWASP | ORM queries |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-008-01 | Wafer yield computation | POST analyze on die data | 200 completed | yield_pct accurate |
| TC-008-02 | Radial bias detection | Wafer with edge failures | radial_bias_detected=true | bin rate &gt; 1.5× avg |
| TC-008-03 | Edge-center bias | Edge-heavy wafer | edge_center_bias_detected=true | ratio &gt; 1.5 |
| TC-008-04 | Wafer health metric | Analyze wafer | health in [0,100] | die health average |
| TC-008-05 | Upstream gate reject | POST without FA-FR-007 | 424 | UPSTREAM_GATE_FAILED |
| TC-008-06 | Zero die wafer | Empty wafer | null yield | ZERO_DIE_COUNT info |

---

## 23. Acceptance Criteria

1. Analysis executes only after FA-FR-001 through FA-FR-007 complete.  
2. Yield matches die pass/fail aggregation.  
3. Radial bias flagged when bin rate exceeds threshold.  
4. Edge-center bias flagged when ratio exceeds threshold.  
5. Wafer health metric computed for every analyzed wafer.  
6. Dashboard `/wafer-analysis` displays yield and radial charts.  
7. Downstream FA-FR-009 can query wafer health metrics.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Missing die coordinates limits radial | Yield-only fallback |
| Business | Edge exclusion zones vary by fab | Configurable edge_fraction |
| Assumption | Die health scores from FA-FR-007 | Gate dependency |
| Assumption | Wafer center defined consistently | Document coordinate origin |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001 through FA-FR-007 |
| External APIs | None |
| Database | PostgreSQL |
| Infrastructure | Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-008 | This document | `/api/v1/wafer-analysis/*` | wafer_* | TC-008-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] Yield formula documented  
- [ ] Radial and edge-center thresholds specified  
- [ ] FA-FR-001–007 gate chain enforced  
- [ ] Wafer health metric formula documented  
- [ ] Test cases cover yield, radial, edge-center  
- [ ] No placeholders remain  
- [ ] Coordinate system for radial bins documented  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-008 |
