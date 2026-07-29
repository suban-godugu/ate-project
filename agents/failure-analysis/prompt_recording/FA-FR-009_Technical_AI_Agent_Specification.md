# FA-FR-009 Technical AI Agent Specification — Fault Prediction Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-009  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-009 Technical AI Agent Specification — Fault Prediction Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Fault Prediction Engine |
| FR ID | FA-FR-009 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-009 generates PROBABLE fault predictions — not definitive root-cause assignments — by synthesizing upstream analytics from ingestion through wafer analysis, optionally enriched with OpenAI GPT narrative explanations for engineering review.

**Scope:** Fault prediction API, prediction models, confidence scoring, PROBABLE fault labeling, optional OpenAI narrative, dashboard at `/fault-prediction`.  
**Stakeholders:** Failure Analysis Engineers, Yield Engineering, Fab Management, Data Science, Platform/DevOps.  
**Out of scope for this agent:** Definitive root-cause assignment, pattern detection (FA-FR-002), report PDF generation (FA-FR-010). Predictions are PROBABLE only.

---

## 3. Business Objective

**Problem:** Engineers manually synthesize data from multiple FA tools to hypothesize likely fault causes. This is time-consuming, inconsistent, and lacks confidence attribution or auditable prediction lineage.

**Expected outcome:** Automated PROBABLE fault predictions with confidence scores, prediction method attribution, and optional GPT narrative explanations, completing within minutes of wafer analysis. All outputs explicitly labeled PROBABLE, never definitive root cause.

**KPIs:**
- Prediction generation &lt; 5 min per lot  
- 100% of predictions labeled PROBABLE (never DEFINITIVE)  
- Confidence scores on every prediction (0.0–1.0)  
- Optional OpenAI narrative for top-N predictions  
- Prediction accuracy tracked against engineer-confirmed outcomes (feedback loop)  

---

## 4. Technical Overview

FA-FR-009 implements a hybrid prediction pipeline gated on FA-FR-001 through FA-FR-008:

1. **Edge:** Next.js `ate-dashboard` `/fault-prediction` screen with PROBABLE fault cards  
2. **API:** FastAPI routers under `/api/v1/fault-prediction`  
3. **Application:** FaultPredictionService orchestrates feature assembly → ML/rules inference → confidence → optional GPT narrative  
4. **Domain:** Feature builders, prediction models, confidence calibrators, GPT prompt templates  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for prediction cache; OpenAI GPT for optional narratives  

Architecture decision: predictions are explicitly PROBABLE. UI and API responses include mandatory disclaimer. GPT generates narrative only; never overrides prediction logic.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (model artifacts) |
| Cache | Redis (prediction job status) |
| AI | OpenAI GPT (optional narrative); rules + ML for prediction logic |
| Testing | Pytest, prediction benchmark fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 through FA-FR-008 completion  
- Assemble feature vectors from all upstream analytics  
- Generate PROBABLE fault predictions with confidence scores  
- Persist `fault_predictions`, prediction metadata tables  
- Optionally generate OpenAI GPT narrative for top-N predictions  
- Enforce PROBABLE labeling on all outputs (never DEFINITIVE)  
- Expose REST APIs and `/fault-prediction` dashboard  
- Support engineer feedback on prediction accuracy  

**Exclusions:**
- Definitive root-cause assignment  
- Modification of upstream analytics data  
- Report PDF generation (FA-FR-010)  

---

## 7. Functional Requirements

### FR ID
FA-FR-009

### Description
The agent shall generate PROBABLE fault predictions by synthesizing upstream FA analytics, assign confidence scores, optionally produce OpenAI narrative explanations, and persist auditable prediction records with mandatory PROBABLE labeling.

### Priority
**High / P1** — final analytics gate before reporting.

### Inputs
- `wafer_analysis_run_id` or `lot_id` or `dataset_id`  
- Optional `top_n_predictions` (default 10)  
- Optional `include_narrative` (default true if OpenAI available)  
- Optional `confidence_min` (default 0.50)  
- Feedback: `prediction_id`, `engineer_verdict` (confirmed/rejected/modified)  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `fault_predictions` with PROBABLE label, confidence, method, features_used  
- Optional GPT narrative text per prediction  
- Prediction run metadata  
- Engineer feedback records  

### Processing Logic
1. Verify FA-FR-001 through FA-FR-008 gates  
2. Assemble feature vector from patterns, rates, classifications, recurrence, correlation, die/wafer metrics  
3. Apply prediction model (rules + ML ensemble)  
4. Filter predictions below confidence_min  
5. Label all outputs PROBABLE per BR-001  
6. Optionally invoke OpenAI GPT for top-N narrative  
7. Persist fault_predictions and prediction metadata  
8. Return ranked PROBABLE predictions with disclaimer  

### Dependencies
- FA-FR-001 through FA-FR-008  
- PostgreSQL, Redis, OpenAI API (optional)  
- ML model artifacts in MinIO  
- Downstream: FA-FR-010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Prediction &lt; 5 min per lot; single prediction API &lt; 300 ms |
| Scalability | Batch feature assembly; async GPT calls |
| Availability | Graceful GPT degradation; predictions without narrative |
| Logging | JSON with prediction_run_id, predictions_count, GPT tokens |
| Security | RBAC; sanitized GPT prompts; PROBABLE disclaimer enforced |
| Maintainability | Versioned prediction models; feedback loop for retraining |
| Reliability | Idempotent re-runs; feedback immutable |
| Monitoring | Prediction confidence drift; GPT cost; feedback rate |

---

## 9. AI Behavior Specification

### Role
PROBABLE fault predictor — rules + ML for predictions; OpenAI GPT for optional narrative only.

### Reasoning Strategy
Feature assembly → rules check → ML ensemble → confidence calibration → PROBABLE label → optional GPT narrative.

### Workflow
Gate → Features → Predict → Label PROBABLE → Narrate (optional) → Persist → Expose.

### Decision Logic
All predictions receive label=PROBABLE. Confidence ≥ confidence_min included in results. GPT narrative describes reasoning; never changes prediction or confidence.

### Confidence Handling
Ensemble confidence calibrated 0.0–1.0. Low confidence predictions included if above min threshold with explicit low-confidence flag.

### Limitations
PROBABLE only — never definitive root cause. Engineers must validate. GPT narrative is assistive text, not authoritative.

### Fallback Behaviour
OpenAI unavailable → predictions without narrative. ML model missing → rules-only path with reduced confidence cap (0.75).

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| wafer_analysis_run_id | UUID | Yes (or lot_id) | FA-FR-008 completed | `w1a2f3e4-r5a6-7890-abcd-ef1234567890` |
| lot_id | string | Alt scope | Non-empty | `LOT-2026-0412` |
| top_n_predictions | integer | No | 1–50, default 10 | `10` |
| include_narrative | boolean | No | Default true | `true` |
| confidence_min | float | No | 0.0–1.0, default 0.50 | `0.50` |
| prediction_id | UUID | Yes (feedback) | Must exist | `p1r2e3d4-i5c6-7890-abcd-ef1234567890` |
| engineer_verdict | string | Yes (feedback) | confirmed/rejected/modified | `confirmed` |
| X-User-Id | string | Prod | Non-empty | `fa-engineer-12` |

---

## 11. Output Specification

### Schema (prediction success — conceptual)
`prediction_run.id`, `status`, `predictions_count`, `disclaimer`, `fault_predictions[]`

### JSON Example

```json
{
  "disclaimer": "All predictions are PROBABLE only. Not definitive root cause. Engineer validation required.",
  "prediction_run": {
    "id": "p1r2u3n4-r5u6-7890-abcd-ef1234567890",
    "wafer_analysis_run_id": "w1a2f3e4-r5a6-7890-abcd-ef1234567890",
    "status": "completed",
    "predictions_count": 8,
    "model_version": "pred-v2.1"
  },
  "fault_predictions": [
    {
      "prediction_id": "p1r2e3d4-i5c6-7890-abcd-ef1234567890",
      "label": "PROBABLE",
      "predicted_fault": "SCAN_CHAIN_STUCK_AT",
      "confidence": 0.78,
      "method": "ml_ensemble",
      "features_used": ["recurrence_score", "correlation_phi", "edge_center_bias", "die_health_min"],
      "narrative": "Based on recurring stuck-at pattern PAT-STUCK-AT-1000 across 4 lots with edge-center bias ratio 2.1, scan chain integrity issue is the most probable cause. Recommend physical probe of scan chain on edge dies."
    }
  ]
}
```

### Engineering Report
Prediction section in FA-FR-010 cites top PROBABLE faults with disclaimer.

### Dashboard Output
`/fault-prediction` PROBABLE fault cards, confidence bars, narrative expand, feedback buttons, disclaimer banner.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | All predictions MUST be labeled PROBABLE; DEFINITIVE root cause is forbidden. |
| BR-002 | Prediction requires FA-FR-001 through FA-FR-008 completed. |
| BR-003 | Confidence scores range 0.0–1.0; predictions below confidence_min excluded. |
| BR-004 | GPT narrative is optional; never modifies prediction or confidence values. |
| BR-005 | Disclaimer text mandatory in every API response and dashboard view. |
| BR-006 | Engineer feedback (confirmed/rejected/modified) is auditable and immutable. |
| BR-007 | Feature vector must include at least 3 upstream signal types. |
| BR-008 | Prediction model version persisted on every run. |
| BR-009 | Rules-only fallback caps confidence at 0.75 when ML unavailable. |

---

## 13. Key Engineering Rules

1. NEVER label predictions as DEFINITIVE root cause.  
2. Always include PROBABLE disclaimer in API and UI.  
3. GPT generates narrative only; no prediction authority.  
4. Feature assembly from real upstream data only; no fabrication.  
5. Preserve semiconductor fault terminology.  
6. Engineer feedback loop for model improvement.  
7. Persist model_version and feature list on every prediction.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 through FA-FR-008 |
| Label constraint | PROBABLE only; DEFINITIVE forbidden |
| Latency | &lt; 5 min per lot |
| Confidence min | Default 0.50 |
| GPT dependency | Optional; graceful degradation |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/fault-prediction/predict`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with wafer_analysis_run_id or lot_id, optional top_n and narrative flag.

### Response
200 prediction run + fault_predictions with mandatory disclaimer.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Upstream gate failed |
| 503 | GPT unavailable (predictions without narrative) |
| 500 | Unexpected |

### Validation Errors
`UPSTREAM_GATE_FAILED`, `WAFER_ANALYSIS_RUN_NOT_FOUND`, `INSUFFICIENT_FEATURES`, `MODEL_UNAVAILABLE`.

Additional endpoints: `GET /api/v1/fault-prediction`, `GET /api/v1/fault-prediction/{prediction_id}`, `GET /api/v1/fault-prediction/runs/{run_id}`, `POST /api/v1/fault-prediction/{prediction_id}/feedback`, `GET /api/v1/fault-prediction/accuracy`.

---

## 16. Database Design

### Tables
`fault_predictions`, `prediction_runs`, `prediction_features`, `prediction_narratives`, `prediction_feedback`, `prediction_model_versions`

### Columns (representative — `fault_predictions`)
`id` (PK UUID), `prediction_run_id`, `label` (always PROBABLE), `predicted_fault`, `confidence`, `method`, `model_version`, `lot_id`, `wafer_id`, `features_json`, `created_at`

### Primary Keys
UUID PKs on all prediction tables.

### Foreign Keys
`fault_predictions.prediction_run_id` → `prediction_runs.id`; `prediction_narratives.prediction_id` → `fault_predictions.id`; `prediction_feedback.prediction_id` → `fault_predictions.id`.

### Indexes
`(lot_id, confidence DESC)`, `(label)`, `(prediction_run_id)`, `(predicted_fault)`.

### Relationships
One prediction run → many fault_predictions; one prediction → optional narrative and feedback rows.

### ER Explanation
Predictions synthesize all upstream FA analytics; consumed by FA-FR-010 reporting with PROBABLE disclaimer.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/fault-prediction`, `/fault-prediction/{prediction_id}`, `/fault-prediction/accuracy` |
| User Actions | Trigger prediction, read narrative, submit feedback, export |
| Charts | Confidence distribution, prediction accuracy over time, feedback pie |
| Tables | PROBABLE predictions ranked, feedback history |
| Filters | Lot, confidence range, predicted fault type |
| Downloads | Prediction CSV with disclaimer header |
| Notifications | PROBABLE disclaimer banner always visible; toast on complete |

---

## 18. AI Workflow

1. User triggers prediction on `/fault-prediction` after wafer analysis.  
2. API verifies FA-FR-001 through FA-FR-008 gates.  
3. Feature vector assembled from all upstream modules.  
4. ML ensemble + rules generate PROBABLE predictions.  
5. OpenAI GPT optionally generates narrative for top-N.  
6. Results persisted with PROBABLE label and disclaimer.  
7. Engineer reviews and submits feedback.  
8. FA-FR-010 includes PROBABLE predictions in engineering reports.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | Prior modules incomplete | Missing FA-FR-001–008 | Complete upstream | High |
| `WAFER_ANALYSIS_RUN_NOT_FOUND` | Invalid run id | Missing entity | Verify ID | Medium |
| `INSUFFICIENT_FEATURES` | &lt; 3 signal types | Sparse upstream | Partial prediction warning | Medium |
| `MODEL_UNAVAILABLE` | ML artifact missing | MinIO issue | Rules-only fallback | Medium |
| `LLM_NARRATIVE_FAILED` | GPT unavailable | API issue | Predictions without narrative | Low |
| `DEFINITIVE_LABEL_FORBIDDEN` | Attempt definitive RC | Code bug | Reject; alert | Critical |
| `FEEDBACK_ALREADY_SUBMITTED` | Duplicate feedback | Re-submit | Return existing | Low |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** prediction_run_id, predictions_count, avg_confidence, GPT tokens  
- **Audit Logging:** prediction_feedback append-only  
- **Performance Metrics:** predictions/s, feature assembly ms, GPT latency  
- **Health Checks:** model availability, OpenAI connectivity  
- **Prometheus Metrics:** `fa_prediction_runs_total`, `fa_probable_predictions_total`, `fa_prediction_feedback_confirmed_rate`  
- **Alerts:** confidence drift, GPT cost threshold, zero predictions on rich data  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: predict trigger, feedback requires engineer role |
| Input Validation | Pydantic; verdict enum validation |
| Encryption | TLS; OpenAI key in vault |
| Secrets Management | OpenAI key never in logs or narratives |
| OWASP | Sanitized GPT prompts; no user text injection into prediction logic |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-009-01 | Generate PROBABLE predictions | POST predict on wafer data | 200 with disclaimer | all labels=PROBABLE |
| TC-009-02 | No DEFINITIVE labels | Inspect all predictions | label=PROBABLE only | BR-001 enforced |
| TC-009-03 | GPT narrative optional | include_narrative=true | narrative present | text non-empty |
| TC-009-04 | GPT degradation | Mock OpenAI down | 200 without narrative | predictions still returned |
| TC-009-05 | Engineer feedback | POST feedback confirmed | feedback persisted | audit immutable |
| TC-009-06 | Upstream gate reject | POST without FA-FR-008 | 424 | UPSTREAM_GATE_FAILED |

---

## 23. Acceptance Criteria

1. Predictions execute only after FA-FR-001 through FA-FR-008 complete.  
2. All predictions labeled PROBABLE; DEFINITIVE forbidden.  
3. Disclaimer present in every API response and dashboard view.  
4. Confidence scores on every prediction (0.0–1.0).  
5. Optional GPT narrative does not alter predictions.  
6. Engineer feedback auditable and immutable.  
7. Downstream FA-FR-010 includes PROBABLE predictions with disclaimer.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Business | Engineers treat PROBABLE as definitive | Mandatory disclaimer; UI banner |
| Technical | ML model drift | Feedback loop; versioned models |
| Technical | GPT cost at scale | Optional narrative; top-N only |
| Assumption | Sufficient upstream features | Minimum 3 signal types |
| Assumption | OpenAI available for narrative | Graceful degradation |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001 through FA-FR-008 |
| External APIs | OpenAI GPT (optional narrative) |
| Database | PostgreSQL |
| Infrastructure | Redis, MinIO, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, OpenAI SDK, scikit-learn/onnx, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-009 | This document | `/api/v1/fault-prediction/*` | fault_predictions, prediction_* | TC-009-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] PROBABLE-only labeling enforced  
- [ ] DEFINITIVE root cause forbidden  
- [ ] Disclaimer in API and UI specified  
- [ ] GPT narrative optional and non-authoritative  
- [ ] FA-FR-001–008 gate chain enforced  
- [ ] Feedback loop documented  
- [ ] No placeholders remain  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-009 |
