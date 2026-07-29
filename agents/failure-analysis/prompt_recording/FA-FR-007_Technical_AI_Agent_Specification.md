# FA-FR-007 Technical AI Agent Specification — Die Analysis Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-007  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-007 Technical AI Agent Specification — Die Analysis Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Die Analysis Engine |
| FR ID | FA-FR-007 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-007 performs die-level spatial analysis including hotspot detection, die clustering, and health scoring, leveraging correlation and recurrence data to identify spatially concentrated failure modes at individual die granularity.

**Scope:** Die analysis API, die hotspots, die clusters, die health scores, spatial aggregation, dashboard at `/die-analysis`.  
**Stakeholders:** Failure Analysis Engineers, Yield Engineering, Fab Management, Test Operations, Platform/DevOps.  
**Out of scope for this agent:** Pattern detection (FA-FR-002), rate formulas (FA-FR-003), classification (FA-FR-004), recurrence (FA-FR-005), correlation (FA-FR-006), wafer-level analytics (FA-FR-008), prediction (FA-FR-009), report generation (FA-FR-010).

---

## 3. Business Objective

**Problem:** Die-level failure spatial patterns are analyzed manually with wafer maps and spreadsheets. Engineers lack automated die hotspot detection, clustering, and health scoring integrated with upstream correlation and recurrence data.

**Expected outcome:** Automated die-level spatial analysis with hotspot maps, die clusters, health scores (0–100), and correlation-informed prioritization within minutes of correlation analysis completion.

**KPIs:**
- Die analysis completion &lt; 4 min for 10k dies  
- Hotspot detection precision ≥80% against engineer-validated maps  
- Health scores computed for 100% of dies with failure data  
- Die clusters identified with spatial adjacency criteria  
- 100% lineage to correlation_run and recurrence_run  

---

## 4. Technical Overview

FA-FR-007 implements a die-level spatial analysis pipeline gated on FA-FR-001 through FA-FR-006:

1. **Edge:** Next.js `ate-dashboard` `/die-analysis` screen with die map visualization  
2. **API:** FastAPI routers under `/api/v1/die-analysis`  
3. **Application:** DieAnalysisService orchestrates spatial aggregation → hotspot → cluster → health score  
4. **Domain:** Die coordinate mappers, hotspot detectors, DBSCAN/k-means clusterers, health scorers  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for analysis cache  

Architecture decision: die coordinates derived from normalized_records die_id and wafer map metadata. Health score = f(failure_count, classification severity, correlation weight, recurrence flag).

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic, scikit-learn |
| Database | PostgreSQL |
| Object Storage | MinIO (read-only lineage) |
| Cache | Redis (die analysis job status) |
| AI | Deterministic spatial algorithms; no LLM |
| Testing | Pytest, die map benchmark fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 through FA-FR-006 completion  
- Aggregate failures at die level with spatial coordinates  
- Detect die hotspots by concentration threshold  
- Cluster adjacent failing dies (DBSCAN spatial)  
- Compute die health scores (0–100)  
- Persist `die_analysis`, `die_hotspots`, `die_clusters`, `die_health_scores`, die metadata tables  
- Expose REST APIs and `/die-analysis` dashboard die map  

**Exclusions:**
- Wafer-level yield/radial analysis (FA-FR-008)  
- Pattern detection (FA-FR-002)  
- Correlation computation (FA-FR-006)  
- Fault prediction (FA-FR-009)  

---

## 7. Functional Requirements

### FR ID
FA-FR-007

### Description
The agent shall perform die-level spatial analysis including hotspot detection, die clustering, and health scoring from upstream failure data, correlation pairs, and recurrence signatures.

### Priority
**High / P1** — enables wafer analysis and reporting.

### Inputs
- `correlation_run_id` or `recurrence_run_id` or `dataset_id`  
- Optional scope: `wafer_id`, `lot_id`, `health_score_min`  
- Optional cluster parameters: `eps`, `min_samples`  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `die_analysis` run metadata  
- `die_hotspots` with coordinates and concentration  
- `die_clusters` with member die lists  
- `die_health_scores` per die (0–100)  
- Ranked unhealthy dies  

### Processing Logic
1. Verify FA-FR-001 through FA-FR-006 gates  
2. Load die records with coordinates from normalized_records  
3. Enrich with classification, correlation, recurrence weights  
4. Detect hotspots where die failure density exceeds threshold  
5. Cluster adjacent failing dies via DBSCAN  
6. Compute health score per die per BR-003  
7. Persist all entities  
8. Return ranked unhealthy dies and hotspot map data  

### Dependencies
- FA-FR-001 through FA-FR-006  
- PostgreSQL, Redis, scikit-learn  
- Downstream: FA-FR-008, FA-FR-009, FA-FR-010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Analysis &lt; 4 min for 10k dies; die map API &lt; 800 ms |
| Scalability | Spatial indexing; batch die processing |
| Availability | API N≥2; PostgreSQL HA |
| Logging | JSON with die_analysis_run_id, dies_analyzed, hotspots, duration_ms |
| Security | RBAC for analysis trigger |
| Maintainability | Configurable cluster and hotspot thresholds |
| Reliability | Deterministic health score formula |
| Monitoring | Unhealthy die count alerts |

---

## 9. AI Behavior Specification

### Role
Deterministic spatial analytics engine — DBSCAN clustering and formula-based health scoring.

### Reasoning Strategy
Spatial aggregation → density hotspot → DBSCAN cluster → weighted health score.

### Workflow
Gate → Aggregate → Hotspot → Cluster → Score → Persist → Expose.

### Decision Logic
Hotspot when local failure density &gt; 3× wafer average. Health score 0 = worst, 100 = no failures.

### Confidence Handling
Hotspot confidence from sample size and concentration ratio. Cluster confidence from silhouette score when ≥2 clusters.

### Limitations
Requires die coordinates in normalized_records. Missing coordinates → die excluded with flag.

### Fallback Behaviour
Insufficient dies for clustering → clusters marked SINGLE_DIE. Missing correlation data → health score uses failure count only.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| correlation_run_id | UUID | Yes (or alt ids) | FA-FR-006 completed | `c0r1r2u3-n4n5-6789-abcd-ef1234567890` |
| wafer_id | string | No | Non-empty | `WAFER-LOT0412-05` |
| lot_id | string | No | Non-empty | `LOT-2026-0412` |
| health_score_min | integer | No | 0–100 | `50` |
| eps | float | No | DBSCAN epsilon, default 2.0 | `2.0` |
| min_samples | integer | No | DBSCAN min, default 3 | `3` |
| dataset_id | UUID | Alt scope | Upstream gates passed | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| X-User-Id | string | Prod | Non-empty | `yield-engineer-05` |

---

## 11. Output Specification

### Schema (die analysis success — conceptual)
`die_analysis_run.id`, `status`, `dies_analyzed`, `hotspots_found`, `clusters_found`, `die_health_scores[]`

### JSON Example

```json
{
  "die_analysis_run": {
    "id": "d1i2e3a4-n5a6-7890-abcd-ef1234567890",
    "correlation_run_id": "c0r1r2u3-n4n5-6789-abcd-ef1234567890",
    "status": "completed",
    "dies_analyzed": 847,
    "hotspots_found": 12,
    "clusters_found": 4
  },
  "die_hotspots": [
    {
      "hotspot_id": "HS-001",
      "center_x": 45,
      "center_y": 32,
      "die_count": 18,
      "concentration_ratio": 4.2,
      "wafer_id": "WAFER-LOT0412-05"
    }
  ],
  "die_health_scores": [
    {
      "die_id": "DIE-045-032",
      "health_score": 23,
      "failure_count": 7,
      "cluster_id": "CLU-002",
      "hotspot_id": "HS-001"
    }
  ]
}
```

### Engineering Report
Die analysis section in FA-FR-010 cites hotspot count, worst health scores, cluster summary.

### Dashboard Output
`/die-analysis` wafer die map, hotspot overlay, health score heatmap, cluster legend.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Die analysis requires FA-FR-001 through FA-FR-006 completed. |
| BR-002 | Hotspot flagged when local failure density &gt; 3× wafer average. |
| BR-003 | Health score = 100 − min(100, failure_count × severity_weight × correlation_weight × recurrence_weight). |
| BR-004 | DBSCAN clustering with configurable eps and min_samples. |
| BR-005 | Dies without coordinates excluded with MISSING_COORDINATES flag. |
| BR-006 | Health score range 0–100; 0 = worst, 100 = no failures. |
| BR-007 | Each analysis run persists immutable die_analysis metadata. |
| BR-008 | Correlation significant pairs boost health score penalty weight. |

---

## 13. Key Engineering Rules

1. Never fabricate die coordinates.  
2. Always validate upstream gate chain.  
3. Health score formula is deterministic and versioned.  
4. Spatial clustering uses scikit-learn DBSCAN.  
5. Preserve semiconductor die map terminology (reticle, shot, die X/Y).  
6. Hotspot concentration ratio auditable.  
7. Persist cluster parameters on every run.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 through FA-FR-006 |
| Latency | &lt; 4 min for 10k dies |
| Health score range | 0–100 |
| Hotspot threshold | 3× wafer average density |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/die-analysis/analyze`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with correlation_run_id or alt scope, optional wafer/lot filters and cluster params.

### Response
200 die analysis run + hotspots + clusters + health scores.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Upstream gate failed |
| 500 | Unexpected |

### Validation Errors
`UPSTREAM_GATE_FAILED`, `CORRELATION_RUN_NOT_FOUND`, `MISSING_DIE_COORDINATES`, `INSUFFICIENT_DIES`.

Additional endpoints: `GET /api/v1/die-analysis`, `GET /api/v1/die-analysis/hotspots`, `GET /api/v1/die-analysis/clusters`, `GET /api/v1/die-analysis/health-scores`, `GET /api/v1/die-analysis/map/{wafer_id}`, `GET /api/v1/die-analysis/runs/{run_id}`.

---

## 16. Database Design

### Tables
`die_analysis`, `die_hotspots`, `die_clusters`, `die_health_scores`, `die_cluster_members`, `die_analysis_runs`

### Columns (representative — `die_health_scores`)
`id` (PK UUID), `die_analysis_run_id`, `die_id`, `wafer_id`, `lot_id`, `x_coord`, `y_coord`, `health_score`, `failure_count`, `cluster_id`, `hotspot_id`, `created_at`

### Primary Keys
UUID PKs on all entity tables.

### Foreign Keys
`die_health_scores.die_analysis_run_id` → `die_analysis_runs.id`; `die_cluster_members.cluster_id` → `die_clusters.id`.

### Indexes
`(wafer_id, health_score)`, `(die_id)`, `(hotspot_id)`, `(cluster_id)`, spatial index on (x_coord, y_coord).

### Relationships
One die analysis run → many health scores, hotspots, clusters. One cluster → many cluster members.

### ER Explanation
Die analysis reads correlation and recurrence outputs plus normalized_records coordinates; writes spatial analytics consumed by FA-FR-008 wafer analysis and FA-FR-010 reports.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/die-analysis`, `/die-analysis/map/{wafer_id}`, `/die-analysis/clusters` |
| User Actions | Trigger analysis, select wafer, filter by health score, export map |
| Charts | Die map scatter, health score heatmap, hotspot overlay (Recharts/custom canvas) |
| Tables | Unhealthy dies ranked, hotspot list, cluster members |
| Filters | Wafer, lot, health score range, cluster |
| Downloads | Die health CSV, map PNG export |
| Notifications | Toast on analysis complete; React Query polling |

---

## 18. AI Workflow

1. User triggers die analysis on `/die-analysis` after correlation.  
2. API verifies FA-FR-001 through FA-FR-006 gates.  
3. Die records loaded with coordinates.  
4. Hotspots detected by density threshold.  
5. DBSCAN clusters adjacent failing dies.  
6. Health scores computed with correlation/recurrence weights.  
7. Results persisted; die map rendered.  
8. FA-FR-008 consumes die health scores for wafer-level aggregation.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | Prior modules incomplete | Missing FA-FR-001–006 | Complete upstream | High |
| `CORRELATION_RUN_NOT_FOUND` | Invalid run id | Missing entity | Verify ID | Medium |
| `MISSING_DIE_COORDINATES` | No x/y on dies | Incomplete ingestion | Fix FA-FR-001 data | Medium |
| `INSUFFICIENT_DIES` | Too few for cluster | Small wafer | Partial results | Low |
| `DBSCAN_FAILED` | Clustering error | Bad parameters | Adjust eps/min_samples | Medium |
| `WAFER_NOT_FOUND` | Invalid wafer_id | Typo | Verify wafer | Medium |
| `HEALTH_SCORE_OUT_OF_RANGE` | Score ∉ [0,100] | Formula bug | Alert engineering | Critical |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** die_analysis_run_id, dies_analyzed, hotspots, clusters, duration_ms  
- **Audit Logging:** die_analysis_runs append-only  
- **Performance Metrics:** dies/s, elapsed_ms  
- **Health Checks:** scikit-learn availability  
- **Prometheus Metrics:** `fa_die_analysis_runs_total`, `fa_die_hotspots_total`, `fa_unhealthy_dies_total`  
- **Alerts:** unhealthy die spike, missing coordinates rate  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: analyze trigger, viewer read |
| Input Validation | Pydantic; coordinate range checks |
| Encryption | TLS; PostgreSQL at-rest |
| Secrets Management | Env/vault |
| OWASP | ORM queries; no user-supplied clustering code |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-007-01 | Die analysis on valid wafer | POST analyze with correlation data | 200 completed | dies_analyzed &gt; 0 |
| TC-007-02 | Hotspot detection | Wafer with known cluster | hotspots_found &gt; 0 | concentration &gt; 3× |
| TC-007-03 | Health score range | Analyze failing dies | scores in [0,100] | BR-006 enforced |
| TC-007-04 | DBSCAN clustering | Adjacent failing dies | clusters_found ≥ 1 | members grouped |
| TC-007-05 | Upstream gate reject | POST without FA-FR-006 | 424 | UPSTREAM_GATE_FAILED |
| TC-007-06 | Missing coordinates | Dies without x/y | excluded with flag | MISSING_COORDINATES |

---

## 23. Acceptance Criteria

1. Analysis executes only after FA-FR-001 through FA-FR-006 complete.  
2. Hotspots detected when density exceeds 3× wafer average.  
3. Health scores computed for all dies with coordinates (0–100).  
4. DBSCAN clusters adjacent failing dies.  
5. Dashboard `/die-analysis` renders die map with hotspots.  
6. Correlation weights applied to health score penalty.  
7. Downstream FA-FR-008 can query die health scores by wafer.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Missing die coordinates | Flag and exclude; surface in UI |
| Technical | DBSCAN parameter sensitivity | Configurable eps/min_samples |
| Assumption | Die x/y in normalized_records | FA-FR-001 schema contract |
| Assumption | Wafer map orientation consistent | Document coordinate system |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001 through FA-FR-006 |
| External APIs | None |
| Database | PostgreSQL |
| Infrastructure | Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, scikit-learn, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-007 | This document | `/api/v1/die-analysis/*` | die_analysis, die_hotspots, die_clusters, die_health_scores, die_* | TC-007-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] Health score formula documented  
- [ ] Hotspot threshold (3×) specified  
- [ ] DBSCAN parameters configurable  
- [ ] FA-FR-001–006 gate chain enforced  
- [ ] Die map coordinate system documented  
- [ ] No placeholders remain  
- [ ] Test cases cover hotspot, cluster, health score  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-007 |
