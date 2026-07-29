# FA-FR-006 Technical AI Agent Specification — Correlation Analysis Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-006  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-006 Technical AI Agent Specification — Correlation Analysis Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Correlation Analysis Engine |
| FR ID | FA-FR-006 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-006 computes statistical correlations between failure patterns, classifications, and recurrence signatures using phi coefficient and chi-square tests, identifying co-occurring failure modes for die analysis and reporting modules.

**Scope:** Correlation API, phi/chi-square computation, failure-pattern correlation matrices, significance testing, dashboard at `/correlation`.  
**Stakeholders:** Failure Analysis Engineers, Data Science, Yield Engineering, Test Operations, Platform/DevOps.  
**Out of scope for this agent:** Pattern detection (FA-FR-002), rate formulas (FA-FR-003), classification (FA-FR-004), recurrence detection (FA-FR-005), die spatial clustering (FA-FR-007), wafer analytics (FA-FR-008), prediction (FA-FR-009), report generation (FA-FR-010).

---

## 3. Business Objective

**Problem:** Engineers manually cross-tabulate failure modes to find co-occurring patterns. Manual correlation analysis is error-prone, lacks significance testing, and cannot scale to thousands of pattern-classification pairs.

**Expected outcome:** Automated phi and chi-square correlation analysis with significance flags, ranked correlation pairs, and matrix visualization within minutes of recurrence analysis completion.

**KPIs:**
- Correlation computation &lt; 3 min for 500 pattern-classification pairs  
- Phi/chi-square results match scipy reference implementations  
- Significance threshold p &lt; 0.05 enforced and flagged  
- 100% lineage to recurrence_run and classification_run  
- Correlation matrix exportable for FA-FR-010 reports  

---

## 4. Technical Overview

FA-FR-006 implements a statistical correlation pipeline gated on FA-FR-001 through FA-FR-005:

1. **Edge:** Next.js `ate-dashboard` `/correlation` screen with correlation matrix heatmap  
2. **API:** FastAPI routers under `/api/v1/correlation`  
3. **Application:** CorrelationService orchestrates contingency tables → phi → chi-square → significance  
4. **Domain:** Contingency builders, phi calculators, chi-square testers, significance evaluators  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for computation cache  

Architecture decision: correlation pairs are (entity_a, entity_b) where entities are patterns, classifications, or recurrence signatures. Sparse matrices stored efficiently with significance flags.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic, scipy |
| Database | PostgreSQL |
| Object Storage | MinIO (read-only lineage) |
| Cache | Redis (correlation job status) |
| AI | Deterministic statistics only; no LLM |
| Testing | Pytest, scipy reference fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 through FA-FR-005 completion  
- Build contingency tables from patterns, classifications, recurrence signatures  
- Compute phi coefficient and chi-square statistic per pair  
- Evaluate significance at p &lt; 0.05  
- Persist `failure_pattern_correlations`, correlation metadata tables  
- Expose REST APIs and `/correlation` dashboard heatmap  

**Exclusions:**
- Pattern detection (FA-FR-002)  
- Rate computation (FA-FR-003)  
- Classification (FA-FR-004)  
- Recurrence detection (FA-FR-005)  
- Die/wafer spatial analytics (FA-FR-007/008)  
- Causal inference (correlation ≠ causation)  

---

## 7. Functional Requirements

### FR ID
FA-FR-006

### Description
The agent shall compute phi and chi-square correlations between failure patterns, classifications, and recurrence signatures, flag statistically significant pairs, and persist correlation matrices for downstream FA modules.

### Priority
**High / P1** — enables die analysis and reporting.

### Inputs
- `recurrence_run_id` or `classification_run_id` or `dataset_id`  
- Optional entity types: `pattern`, `classification`, `recurrence_signature`  
- Optional `significance_level` (default 0.05)  
- Optional `min_co_occurrence` (default 5)  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `failure_pattern_correlations` with phi, chi_square, p_value, significant flag  
- Correlation metadata (pair counts, contingency tables)  
- Ranked significant pairs  
- Computation run metadata  

### Processing Logic
1. Verify FA-FR-001 through FA-FR-005 gates  
2. Load entities (patterns, classifications, recurrence signatures)  
3. Build contingency tables for all valid pairs  
4. Filter pairs with co-occurrence &lt; min_co_occurrence  
5. Compute phi coefficient and chi-square per pair  
6. Flag significant pairs where p_value &lt; significance_level  
7. Persist correlation rows and metadata  
8. Return ranked significant pairs and matrix summary  

### Dependencies
- FA-FR-001 through FA-FR-005  
- PostgreSQL, Redis, scipy  
- Downstream: FA-FR-007, FA-FR-008, FA-FR-010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Computation &lt; 3 min for 500 pairs; matrix API &lt; 600 ms |
| Scalability | Sparse matrix storage; batch pair evaluation |
| Availability | API N≥2; PostgreSQL HA |
| Logging | JSON with correlation_run_id, pairs_computed, significant_count |
| Security | RBAC for compute trigger |
| Maintainability | Configurable significance and min_co_occurrence |
| Reliability | Deterministic scipy-backed results |
| Monitoring | Significant pair count drift alerts |

---

## 9. AI Behavior Specification

### Role
Pure statistical engine — no AI inference. Phi and chi-square are deterministic scipy computations.

### Reasoning Strategy
Contingency table construction → phi coefficient → chi-square test → p-value → significance flag.

### Workflow
Gate → Build Tables → Compute → Significance → Rank → Persist → Expose.

### Decision Logic
Pair included if co-occurrence ≥ min_co_occurrence. Significant if p_value &lt; significance_level (default 0.05).

### Confidence Handling
Not applicable (deterministic statistics). Significance level is the confidence threshold for inclusion.

### Limitations
Correlation does not imply causation. Documented in dashboard disclaimers.

### Fallback Behaviour
Insufficient co-occurrence → pair excluded with reason, not error. scipy unavailable → hard fail with alert.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| recurrence_run_id | UUID | Yes (or alt ids) | FA-FR-005 completed | `r1e2c3u4-r5e6-7890-abcd-ef1234567890` |
| classification_run_id | UUID | Alt scope | FA-FR-004 completed | `c1l2a3s4-s5i6-7890-abcd-ef1234567890` |
| entity_types | string[] | No | Subset of pattern, classification, recurrence_signature | `["pattern","classification"]` |
| significance_level | float | No | 0.001–0.10, default 0.05 | `0.05` |
| min_co_occurrence | integer | No | ≥2, default 5 | `5` |
| dataset_id | UUID | Alt scope | Upstream gates passed | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| X-User-Id | string | Prod | Non-empty | `data-scientist-03` |

---

## 11. Output Specification

### Schema (correlation success — conceptual)
`correlation_run.id`, `status`, `pairs_computed`, `significant_pairs`, `correlations[]`

### JSON Example

```json
{
  "correlation_run": {
    "id": "c0r1r2u3-n4n5-6789-abcd-ef1234567890",
    "recurrence_run_id": "r1e2c3u4-r5e6-7890-abcd-ef1234567890",
    "status": "completed",
    "pairs_computed": 342,
    "significant_pairs": 28,
    "significance_level": 0.05
  },
  "correlations": [
    {
      "entity_a": "PAT-STUCK-AT-1000",
      "entity_b": "STUCK_AT_LOGIC",
      "entity_a_type": "pattern",
      "entity_b_type": "classification",
      "phi": 0.72,
      "chi_square": 45.3,
      "p_value": 0.0001,
      "co_occurrence_count": 847,
      "significant": true
    }
  ]
}
```

### Engineering Report
Correlation section in FA-FR-010 cites top significant pairs and phi values.

### Dashboard Output
`/correlation` heatmap matrix, significant pair table, phi distribution chart.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Correlation requires FA-FR-001 through FA-FR-005 completed. |
| BR-002 | Phi coefficient computed via scipy for all valid pairs. |
| BR-003 | Chi-square statistic computed via scipy.chi2_contingency. |
| BR-004 | Significant when p_value &lt; significance_level (default 0.05). |
| BR-005 | Pairs with co-occurrence &lt; min_co_occurrence (default 5) are excluded. |
| BR-006 | Correlation ≠ causation; disclaimer required in UI and reports. |
| BR-007 | Each correlation run persists immutable computation metadata. |
| BR-008 | Phi range [-1, 1]; values outside indicate computation error. |

---

## 13. Key Engineering Rules

1. Use scipy reference implementations for phi and chi-square.  
2. Never fabricate contingency table counts.  
3. Always validate upstream gate chain.  
4. Exclude low co-occurrence pairs explicitly, not silently.  
5. Preserve statistical terminology (phi, chi-square, p-value, contingency).  
6. Significance flags are boolean, not subjective.  
7. Persist significance_level and min_co_occurrence on every run.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 through FA-FR-005 |
| Significance default | p &lt; 0.05 |
| Min co-occurrence | Default 5 |
| Latency | &lt; 3 min for 500 pairs |
| Library | scipy required for statistics |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/correlation/compute`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with recurrence_run_id or alt scope, optional entity_types and thresholds.

### Response
200 correlation run + correlations array.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Upstream gate failed |
| 500 | Unexpected |

### Validation Errors
`UPSTREAM_GATE_FAILED`, `RECURRENCE_RUN_NOT_FOUND`, `INSUFFICIENT_PAIRS`, `INVALID_SIGNIFICANCE_LEVEL`.

Additional endpoints: `GET /api/v1/correlation`, `GET /api/v1/correlation/matrix`, `GET /api/v1/correlation/significant`, `GET /api/v1/correlation/runs/{run_id}`, `GET /api/v1/correlation/pair/{entity_a}/{entity_b}`.

---

## 16. Database Design

### Tables
`failure_pattern_correlations`, `correlation_metadata`, `correlation_contingency_tables`, `correlation_runs`

### Columns (representative — `failure_pattern_correlations`)
`id` (PK UUID), `correlation_run_id`, `entity_a`, `entity_b`, `entity_a_type`, `entity_b_type`, `phi`, `chi_square`, `p_value`, `co_occurrence_count`, `significant`, `created_at`

### Primary Keys
UUID PKs on all entity tables.

### Foreign Keys
`failure_pattern_correlations.correlation_run_id` → `correlation_runs.id`; contingency tables reference correlation id.

### Indexes
`(correlation_run_id)`, `(significant)` partial, `(entity_a, entity_b)`, `(phi DESC)`.

### Relationships
One correlation run → many failure_pattern_correlations; one correlation → one contingency table row.

### ER Explanation
Correlation reads recurrence and classification outputs; writes statistical pairs consumed by FA-FR-007 die analysis and FA-FR-010 reports.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/correlation`, `/correlation/matrix`, `/correlation/significant` |
| User Actions | Trigger compute, filter significant only, drill pair detail, export matrix |
| Charts | Correlation heatmap (Recharts), phi distribution, significant count bar |
| Tables | Significant pairs ranked by |phi|, full pair list |
| Filters | Entity type, significance, min phi, date range |
| Downloads | Matrix CSV, significant pairs export |
| Notifications | Toast on compute complete; correlation ≠ causation disclaimer |

---

## 18. AI Workflow

1. User triggers correlation on `/correlation` after recurrence analysis.  
2. API verifies FA-FR-001 through FA-FR-005 gates.  
3. Contingency tables built from upstream entities.  
4. Phi and chi-square computed via scipy.  
5. Significant pairs flagged and ranked.  
6. Results persisted to PostgreSQL.  
7. Dashboard renders heatmap and significant pair table.  
8. FA-FR-007 uses correlation pairs for die hotspot context.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | Prior modules incomplete | Missing FA-FR-001–005 | Complete upstream | High |
| `RECURRENCE_RUN_NOT_FOUND` | Invalid run id | Missing entity | Verify ID | Medium |
| `INSUFFICIENT_PAIRS` | Too few valid pairs | Sparse data | Lower min_co_occurrence | Low |
| `INVALID_SIGNIFICANCE_LEVEL` | Out of range | Bad input | Use 0.001–0.10 | Medium |
| `CONTINGENCY_BUILD_ERROR` | Missing entity data | Upstream gap | Check classification | Medium |
| `SCIPY_COMPUTE_ERROR` | Statistical failure | Degenerate table | Exclude pair | Medium |
| `PHI_OUT_OF_RANGE` | |phi| &gt; 1 | Computation bug | Alert engineering | Critical |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** correlation_run_id, pairs_computed, significant_count, duration_ms  
- **Audit Logging:** correlation_runs append-only  
- **Performance Metrics:** pairs/s, elapsed_ms  
- **Health Checks:** scipy availability  
- **Prometheus Metrics:** `fa_correlation_runs_total`, `fa_significant_pairs_total`, `fa_correlation_compute_duration_ms`  
- **Alerts:** zero significant pairs on large dataset anomaly  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: compute trigger, viewer read |
| Input Validation | Pydantic; significance range checks |
| Encryption | TLS; PostgreSQL at-rest |
| Secrets Management | Env/vault |
| OWASP | ORM queries; no user-supplied statistical formulas |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-006-01 | Compute correlations | POST compute on recurrence data | 200 completed | pairs_computed &gt; 0 |
| TC-006-02 | Phi matches scipy | Known contingency fixture | phi within 0.001 | scipy reference match |
| TC-006-03 | Significance flag | Pair with p &lt; 0.05 | significant=true | BR-004 enforced |
| TC-006-04 | Low co-occurrence excluded | Pair with count &lt; 5 | pair absent | min_co_occurrence enforced |
| TC-006-05 | Upstream gate reject | POST without FA-FR-005 | 424 | UPSTREAM_GATE_FAILED |
| TC-006-06 | Matrix export | GET /correlation/matrix | CSV/JSON matrix | exportable format |

---

## 23. Acceptance Criteria

1. Computation executes only after FA-FR-001 through FA-FR-005 complete.  
2. Phi and chi-square match scipy reference implementations.  
3. Significant pairs flagged at p &lt; 0.05 (configurable).  
4. Low co-occurrence pairs excluded per min_co_occurrence.  
5. Dashboard `/correlation` renders heatmap and significant pairs.  
6. Correlation ≠ causation disclaimer displayed.  
7. Downstream FA-FR-007 can query significant correlation pairs.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Sparse data yields few significant pairs | Adjustable thresholds |
| Business | Misinterpretation as causation | UI/report disclaimers |
| Assumption | Sufficient entity diversity from upstream | Document minimum data requirements |
| Assumption | scipy version pinned in requirements | Lock file in CI |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001 through FA-FR-005 |
| External APIs | None |
| Database | PostgreSQL |
| Infrastructure | Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, scipy, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-006 | This document | `/api/v1/correlation/*` | failure_pattern_correlations, correlation_* | TC-006-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] Phi/chi-square formulas reference scipy  
- [ ] Significance threshold documented  
- [ ] Correlation ≠ causation disclaimer specified  
- [ ] FA-FR-001–005 gate chain enforced  
- [ ] Test cases include scipy reference validation  
- [ ] No placeholders remain  
- [ ] Matrix export format documented  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-006 |
