# FA-FR-005 Technical AI Agent Specification — Recurrence Analysis Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-005  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-005 Technical AI Agent Specification — Recurrence Analysis Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Recurrence Analysis Engine |
| FR ID | FA-FR-005 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-005 identifies recurring failure signatures across lots, wafers, and time windows, performs hotspot analysis, generates engineering recommendations, and maintains audit logs for recurrence tracking consumed by correlation, spatial, and reporting modules.

**Scope:** Recurrence API, recurring failure detection, hotspot analysis, engineering recommendations, audit logs, dashboard at `/recurrence`.  
**Stakeholders:** Failure Analysis Engineers, Yield Engineering, Fab Management, Test Operations, Platform/DevOps.  
**Out of scope for this agent:** Pattern detection (FA-FR-002), rate formulas (FA-FR-003), classification (FA-FR-004), statistical correlation (FA-FR-006), die/wafer spatial (FA-FR-007/008), prediction (FA-FR-009), report PDF (FA-FR-010).

---

## 3. Business Objective

**Problem:** Recurring failures are discovered late through manual lot-to-lot comparison. Engineers lack automated recurrence scoring, hotspot maps, and actionable recommendations tied to classified fault history.

**Expected outcome:** Automated recurrence detection with ranked recurring failures, hotspot coordinates, engineering recommendations, and full audit trail within minutes of classification completion.

**KPIs:**
- Recurrence analysis completion &lt; 4 min for 50k classified faults  
- Hotspot identification accuracy ≥85% against engineer-validated baselines  
- 100% of recurrence events linked to classification_run lineage  
- Engineering recommendations generated for top-N recurring failures  
- Audit log for every recurrence analysis run  

---

## 4. Technical Overview

FA-FR-005 implements a recurrence detection pipeline gated on FA-FR-001 through FA-FR-004:

1. **Edge:** Next.js `ate-dashboard` `/recurrence` screen with recurrence tables and hotspot maps  
2. **API:** FastAPI routers under `/api/v1/recurrence`  
3. **Application:** RecurrenceService orchestrates signature grouping → temporal recurrence → hotspot → recommendations  
4. **Domain:** Recurrence matchers, hotspot aggregators, recommendation generators  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for analysis job cache  

Architecture decision: recurrence signatures are composite keys of (classification, pattern_id, spatial_bucket). Historical comparison spans configurable lookback windows.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (read-only lineage) |
| Cache | Redis (recurrence job status, lookback cache) |
| AI | OpenAI GPT (optional recommendation narrative); deterministic recurrence logic |
| Testing | Pytest, recurrence benchmark fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 through FA-FR-004 completion  
- Detect recurring failures across lots, wafers, and time windows  
- Persist `recurring_failures`, recurrence metadata tables, `hotspot_analysis`  
- Generate `engineering_recommendations` for top recurring signatures  
- Append `recurrence_audit_logs` for every run  
- Expose REST APIs and `/recurrence` dashboard  

**Exclusions:**
- Pattern detection (FA-FR-002)  
- Rate computation (FA-FR-003)  
- Classification (FA-FR-004)  
- Phi/chi-square correlation (FA-FR-006)  
- Die-level spatial clustering (FA-FR-007)  

---

## 7. Functional Requirements

### FR ID
FA-FR-005

### Description
The agent shall identify recurring semiconductor failure signatures from classified faults, perform hotspot analysis, generate engineering recommendations, and persist auditable recurrence records for downstream FA modules.

### Priority
**High / P1** — enables correlation and spatial analytics.

### Inputs
- `classification_run_id` or `dataset_id`  
- Optional `lookback_days` (default 90)  
- Optional scope: `lot_id`, `classification`, `min_recurrence_count`  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `recurring_failures` ranked by recurrence score  
- Recurrence metadata (occurrence windows, lot spread)  
- `hotspot_analysis` spatial/temporal hotspots  
- `engineering_recommendations` actionable text  
- `recurrence_audit_logs` run metadata  

### Processing Logic
1. Verify FA-FR-001 through FA-FR-004 gates  
2. Load classified faults and upstream lineage  
3. Group by recurrence signature (classification + pattern + bucket)  
4. Compare against historical recurrence within lookback window  
5. Score recurrence frequency and lot spread  
6. Identify hotspots (die/wafer/lot concentrations)  
7. Generate recommendations for top-N signatures  
8. Persist all entities; append audit log  

### Dependencies
- FA-FR-001, FA-FR-002, FA-FR-003, FA-FR-004  
- PostgreSQL, Redis, OpenAI (optional narratives)  
- Downstream: FA-FR-006…010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Analysis &lt; 4 min for 50k faults; API list &lt; 500 ms |
| Scalability | Batch grouping; indexed lookback queries |
| Availability | API N≥2; PostgreSQL HA |
| Logging | JSON with recurrence_run_id, signatures found, duration_ms |
| Security | RBAC for analysis trigger |
| Maintainability | Configurable lookback and min_recurrence thresholds |
| Reliability | Append-only audit logs; idempotent re-runs |
| Monitoring | Recurrence rate drift; hotspot alert thresholds |

---

## 9. AI Behavior Specification

### Role
Deterministic recurrence detector with optional GPT-generated recommendation narratives.

### Reasoning Strategy
Signature grouping → temporal comparison → hotspot aggregation → rule-based recommendations. GPT may enrich recommendation text only.

### Workflow
Gate → Group → Compare → Hotspot → Recommend → Persist → Expose.

### Decision Logic
Recurrence score = occurrence_count × lot_spread_factor × temporal_cluster_weight. Top-N by score receive recommendations.

### Confidence Handling
Recurrence confidence based on sample size and lot spread per BR-004. Hotspot confidence from concentration ratio.

### Limitations
No recurrence detected if lookback window has insufficient history. GPT does not alter recurrence scores.

### Fallback Behaviour
OpenAI unavailable → recommendations use template strings. Insufficient history → informational flag, partial results.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| classification_run_id | UUID | Yes (or dataset_id) | FA-FR-004 completed | `c1l2a3s4-s5i6-7890-abcd-ef1234567890` |
| dataset_id | UUID | Alt scope | Upstream gates passed | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| lookback_days | integer | No | 1–365, default 90 | `90` |
| min_recurrence_count | integer | No | ≥2, default 3 | `3` |
| lot_id | string | No | Non-empty | `LOT-2026-0412` |
| classification | string | No | Valid taxonomy code | `STUCK_AT_LOGIC` |
| top_n_recommendations | integer | No | 1–50, default 10 | `10` |
| X-User-Id | string | Prod | Non-empty | `fa-engineer-12` |

---

## 11. Output Specification

### Schema (recurrence success — conceptual)
`recurrence_run.id`, `status`, `recurring_count`, `hotspots_found`, `recurring_failures[]`, `engineering_recommendations[]`

### JSON Example

```json
{
  "recurrence_run": {
    "id": "r1e2c3u4-r5e6-7890-abcd-ef1234567890",
    "classification_run_id": "c1l2a3s4-s5i6-7890-abcd-ef1234567890",
    "status": "completed",
    "recurring_count": 18,
    "hotspots_found": 5,
    "lookback_days": 90
  },
  "recurring_failures": [
    {
      "signature": "STUCK_AT_LOGIC|PAT-STUCK-AT-1000|WAFER-CENTER",
      "recurrence_score": 0.89,
      "occurrence_count": 12,
      "lot_spread": 4,
      "first_seen": "2026-04-01T08:00:00Z",
      "last_seen": "2026-07-15T14:30:00Z"
    }
  ],
  "engineering_recommendations": [
    {
      "signature": "STUCK_AT_LOGIC|PAT-STUCK-AT-1000|WAFER-CENTER",
      "priority": "high",
      "recommendation": "Investigate scan chain integrity on lots LOT-2026-0412 through LOT-2026-0418; center wafer bias suggests reticle defect."
    }
  ]
}
```

### Engineering Report
Recurrence section in FA-FR-010 cites top recurring signatures and recommendations.

### Dashboard Output
`/recurrence` ranked table, hotspot map, recommendation cards, audit timeline.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Recurrence analysis requires FA-FR-001 through FA-FR-004 completed. |
| BR-002 | Recurrence signature = classification + pattern_id + spatial_bucket. |
| BR-003 | Minimum recurrence count default 3; configurable via min_recurrence_count. |
| BR-004 | Recurrence confidence = min(1.0, occurrence_count / confidence_threshold) × lot_spread_factor. |
| BR-005 | Hotspot flagged when concentration ratio exceeds 3× uniform distribution. |
| BR-006 | Engineering recommendations generated for top-N by recurrence_score. |
| BR-007 | Every analysis run appends immutable row to recurrence_audit_logs. |
| BR-008 | Lookback window default 90 days; configurable 1–365. |

---

## 13. Key Engineering Rules

1. Never invent recurrence signatures without classified fault evidence.  
2. Always validate upstream gate chain before analysis.  
3. Hotspot coordinates derived from die/wafer metadata, not fabricated.  
4. GPT enriches recommendation text only; scores remain deterministic.  
5. Preserve semiconductor terminology (lot, wafer, die, reticle, scan chain).  
6. Audit logs are append-only.  
7. Persist lookback_days and threshold config on every run.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 through FA-FR-004 |
| Lookback | 1–365 days, default 90 |
| Latency | &lt; 4 min for 50k faults |
| Min recurrence | ≥2 occurrences |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/recurrence/analyze`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with classification_run_id or dataset_id, optional lookback and filters.

### Response
200 recurrence run + recurring_failures + recommendations.

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
`UPSTREAM_GATE_FAILED`, `CLASSIFICATION_RUN_NOT_FOUND`, `INSUFFICIENT_HISTORY`, `INVALID_LOOKBACK`.

Additional endpoints: `GET /api/v1/recurrence`, `GET /api/v1/recurrence/{signature}`, `GET /api/v1/recurrence/hotspots`, `GET /api/v1/recurrence/recommendations`, `GET /api/v1/recurrence/audit-logs`, `GET /api/v1/recurrence/runs/{run_id}`.

---

## 16. Database Design

### Tables
`recurring_failures`, `recurrence_metadata`, `recurrence_occurrences`, `hotspot_analysis`, `recurrence_audit_logs`, `engineering_recommendations`

### Columns (representative — `recurring_failures`)
`id` (PK UUID), `recurrence_run_id`, `signature`, `classification`, `pattern_id`, `spatial_bucket`, `recurrence_score`, `occurrence_count`, `lot_spread`, `confidence`, `first_seen`, `last_seen`, `created_at`

### Primary Keys
UUID PKs on all entity tables.

### Foreign Keys
`recurrence_occurrences.recurring_failure_id` → `recurring_failures.id`; `engineering_recommendations.recurring_failure_id` → `recurring_failures.id`; audit logs reference recurrence_run.

### Indexes
`(signature)`, `(recurrence_score DESC)`, `(classification_run_id)`, `(created_at)`.

### Relationships
One recurrence run → many recurring_failures; one recurring_failure → many occurrences and one recommendation.

### ER Explanation
Recurrence reads classified faults and upstream lineage; writes analytics consumed by FA-FR-006 correlation and FA-FR-007 die analysis.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/recurrence`, `/recurrence/hotspots`, `/recurrence/recommendations` |
| User Actions | Trigger analysis, filter by classification, drill hotspots, export |
| Charts | Recurrence score bar, lot spread scatter, hotspot heatmap (Recharts) |
| Tables | Recurring failures, recommendations, audit log |
| Filters | Lookback, classification, lot, min score |
| Downloads | Recurrence CSV, recommendation PDF snippet |
| Notifications | Toast on analysis complete; React Query polling |

---

## 18. AI Workflow

1. User triggers recurrence analysis on `/recurrence` after classification.  
2. API verifies FA-FR-001 through FA-FR-004 gates.  
3. Classified faults grouped by recurrence signature.  
4. Historical comparison within lookback window.  
5. Hotspots identified by concentration ratio.  
6. Recommendations generated (GPT optional narrative).  
7. Results persisted; audit log appended.  
8. FA-FR-006 consumes recurrence data for correlation analysis.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | Prior modules incomplete | Missing FA-FR-001–004 | Complete upstream | High |
| `CLASSIFICATION_RUN_NOT_FOUND` | Invalid run id | Missing entity | Verify ID | Medium |
| `INSUFFICIENT_HISTORY` | Lookback too short | New deployment | Reduce lookback or wait | Low |
| `INVALID_LOOKBACK` | lookback_days out of range | Bad input | Use 1–365 | Medium |
| `NO_RECURRENCES_FOUND` | Zero signatures | Clean data | Informational, not error | Low |
| `HOTSPOT_COMPUTE_ERROR` | Missing spatial metadata | Incomplete die/wafer fields | Partial results | Medium |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |
| `LLM_NARRATIVE_FAILED` | GPT unavailable | API issue | Template recommendations | Low |

---

## 20. Logging & Monitoring

- **Structured Logging:** recurrence_run_id, signatures_found, hotspots, duration_ms  
- **Audit Logging:** recurrence_audit_logs append-only  
- **Performance Metrics:** faults/s, signatures/s, elapsed_ms  
- **Health Checks:** lookback query performance  
- **Prometheus Metrics:** `fa_recurrence_runs_total`, `fa_recurring_failures_total`, `fa_hotspots_found_total`  
- **Alerts:** recurrence spike, hotspot concentration breach  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: analyze trigger, viewer read |
| Input Validation | Pydantic; lookback range checks |
| Encryption | TLS; PostgreSQL at-rest |
| Secrets Management | OpenAI key in vault |
| OWASP | ORM queries; sanitized GPT prompts |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-005-01 | Detect recurring failures | POST analyze on classified dataset | 200 completed | recurring_count &gt; 0 |
| TC-005-02 | Upstream gate reject | POST without FA-FR-004 | 424 | UPSTREAM_GATE_FAILED |
| TC-005-03 | Hotspot identification | Analyze with spatial data | hotspots_found &gt; 0 | concentration &gt; 3× uniform |
| TC-005-04 | Recommendations generated | Analyze with top_n=5 | 5 recommendations | priority assigned |
| TC-005-05 | Insufficient history | lookback_days=1 on new data | 200 with flag | INSUFFICIENT_HISTORY info |
| TC-005-06 | Audit log persistence | Run analysis | audit row exists | immutable entry |

---

## 23. Acceptance Criteria

1. Analysis executes only after FA-FR-001 through FA-FR-004 complete.  
2. Recurring failures ranked by recurrence_score.  
3. Hotspots identified when concentration exceeds threshold.  
4. Engineering recommendations generated for top-N signatures.  
5. Audit log records every analysis run.  
6. Dashboard `/recurrence` displays results and hotspots.  
7. Downstream FA-FR-006 can query recurrence data.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Sparse spatial metadata limits hotspots | Graceful partial results |
| Business | False recurrence from classification errors | Surface classification confidence |
| Assumption | Sufficient historical data in lookback | Configurable window |
| Assumption | Die/wafer fields populated by FA-FR-001 | Schema contract |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001, FA-FR-002, FA-FR-003, FA-FR-004 |
| External APIs | OpenAI GPT (optional recommendation narrative) |
| Database | PostgreSQL |
| Infrastructure | Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-005 | This document | `/api/v1/recurrence/*` | recurring_failures, recurrence_*, hotspot_analysis, recurrence_audit_logs, engineering_recommendations | TC-005-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] Recurrence signature formula documented  
- [ ] Hotspot threshold defined  
- [ ] FA-FR-001–004 gate chain enforced  
- [ ] Audit log immutability specified  
- [ ] Test cases cover recurrence, hotspot, audit  
- [ ] No placeholders remain  
- [ ] Lineage to classification_run documented  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-005 |
