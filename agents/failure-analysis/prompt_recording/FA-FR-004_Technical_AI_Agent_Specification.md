# FA-FR-004 Technical AI Agent Specification — Fault Classification Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-004  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-004 Technical AI Agent Specification — Fault Classification Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Fault Classification Engine |
| FR ID | FA-FR-004 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-004 classifies detected faults into engineering taxonomies using a hybrid pipeline of deterministic rules, ML classifiers, and optional LLM-assisted disambiguation, producing labeled fault records for recurrence, correlation, and reporting modules.

**Scope:** Classification API (API-first UI), hybrid rules/ML/LLM pipeline, classification runs, classified fault persistence, confidence and method attribution.  
**Stakeholders:** Failure Analysis Engineers, Test Operations, Data Science, Yield Engineering, Platform/DevOps.  
**Out of scope for this agent:** Pattern detection (FA-FR-002), rate formulas (FA-FR-003), recurrence tracking (FA-FR-005), correlation (FA-FR-006), spatial analytics (FA-FR-007/008), prediction (FA-FR-009), report generation (FA-FR-010).

---

## 3. Business Objective

**Problem:** Fault labeling is inconsistent across engineers and shifts. Manual classification of thousands of failures per lot is slow, non-auditable, and lacks confidence attribution for disputed labels.

**Expected outcome:** Automated hybrid classification with method attribution (rule, ML, LLM), confidence scores, and engineer override capability, completing within minutes of failure rate computation.

**KPIs:**
- Classification throughput &lt; 5 min for 50k faults  
- Rule-path classification accuracy ≥90% on benchmark taxonomy  
- 100% of classified faults retain classification method and confidence  
- Engineer override audit trail for disputed labels  
- API-first: all UI actions backed by REST endpoints  

---

## 4. Technical Overview

FA-FR-004 implements a hybrid classification pipeline gated on FA-FR-001 through FA-FR-003:

1. **Edge:** API-first; optional Next.js classification panels embedded in existing dashboards  
2. **API:** FastAPI routers under `/api/v1/classification`  
3. **Application:** ClassificationService orchestrates rule → ML → LLM cascade with confidence arbitration  
4. **Domain:** Taxonomy registry, rule matchers, ML model inference, LLM disambiguation prompts  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for model cache; OpenAI GPT for LLM tier  

Architecture decision: classification cascade is explicit — rules first (deterministic), ML second (probabilistic), LLM third (assistive disambiguation only when rule+ML disagree below confidence threshold).

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts (API-first UI) |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (model artifact storage) |
| Cache | Redis (taxonomy cache, ML model hot load) |
| AI | OpenAI GPT (LLM disambiguation tier); scikit-learn/onnx ML models; deterministic rules |
| Testing | Pytest, taxonomy benchmark fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 ingestion, FA-FR-002 patterns, FA-FR-003 rates  
- Execute hybrid classification cascade: rules → ML → LLM  
- Persist `classification_runs` and `classified_faults` with method attribution  
- Support engineer override with audit trail  
- Expose REST APIs for classification trigger, results, and override  
- Provide API-first UI components for classification review  

**Exclusions:**
- Pattern detection (FA-FR-002)  
- Rate computation (FA-FR-003)  
- Recurrence analysis (FA-FR-005)  
- Definitive root-cause assignment (reserved for FA-FR-009 PROBABLE only)  
- Modification of source records  

---

## 7. Functional Requirements

### FR ID
FA-FR-004

### Description
The agent shall classify semiconductor faults into engineering taxonomies using a hybrid rules/ML/LLM pipeline, persist classified results with confidence and method attribution, and support engineer override via API-first interfaces.

### Priority
**High / P1** — enables recurrence and correlation modules.

### Inputs
- `dataset_id`, `detection_run_id`, or `computation_run_id`  
- Optional `taxonomy_version` (defaults to active)  
- Optional scope filters: `lot_id`, `pattern_id`, `confidence_min`  
- Override payload: `fault_id`, `new_classification`, `override_reason`  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `classification_runs` with run metadata and counts  
- `classified_faults` with taxonomy label, confidence, method (rule/ml/llm/override)  
- Method distribution statistics  
- Structured error envelopes  

### Processing Logic
1. Verify FA-FR-001/002/003 gates  
2. Load taxonomy version  
3. For each fault candidate: apply rule matchers  
4. If rule confidence &lt; threshold → ML inference  
5. If ML confidence &lt; threshold → LLM disambiguation (OpenAI)  
6. Persist classified_faults with method and confidence  
7. Append classification_run metadata  
8. Return summary with method distribution  

### Dependencies
- FA-FR-001, FA-FR-002, FA-FR-003  
- PostgreSQL, Redis, OpenAI API (LLM tier)  
- ML model artifacts in MinIO  
- Downstream: FA-FR-005…010  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Classification &lt; 5 min for 50k faults; API single-fault &lt; 200 ms |
| Scalability | Batch inference; async LLM calls with rate limiting |
| Availability | API N≥2; graceful LLM degradation to ML-only |
| Logging | JSON with classification_run_id, method counts, LLM token usage |
| Security | RBAC for override; LLM prompts sanitized (no raw secrets) |
| Maintainability | Versioned taxonomy and ML models; Alembic migrations |
| Reliability | Idempotent re-runs; override audit immutable |
| Monitoring | Method distribution drift; LLM latency and cost |

---

## 9. AI Behavior Specification

### Role
Hybrid classifier — rules authoritative, ML probabilistic, LLM assistive disambiguator only.

### Reasoning Strategy
Cascade: Rule match (confidence ≥0.85) → accept. Else ML (confidence ≥0.75) → accept. Else LLM with structured prompt → accept if confidence ≥0.60. Else mark UNCLASSIFIED.

### Workflow
Gate → Load Taxonomy → Rule → ML → LLM → Persist → Expose.

### Decision Logic
Rule and ML agree → boost confidence. Disagree → LLM tiebreaker with explicit method=llm.

### Confidence Handling
Each tier produces 0.0–1.0 confidence. Final confidence = max(tier_confidence) with method attribution. Override sets confidence=1.0, method=override.

### Limitations
LLM does not invent taxonomy categories outside registered taxonomy. UNCLASSIFIED is valid output.

### Fallback Behaviour
OpenAI unavailable → skip LLM tier; mark UNCLASSIFIED if rule+ML insufficient. ML model missing → rule-only path with warning.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| dataset_id | UUID | Yes (or run ids) | Upstream gates passed | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| taxonomy_version | string | No | Must exist | `tax-v3.1` |
| confidence_min | float | No | 0.0–1.0 | `0.75` |
| lot_id | string | No | Non-empty | `LOT-2026-0412` |
| fault_id | UUID | Yes (override) | Must exist | `f1a2u3l4-t5i6-7890-abcd-ef1234567890` |
| new_classification | string | Yes (override) | Valid taxonomy code | `STUCK_AT_LOGIC` |
| override_reason | string | Yes (override) | Non-empty | `Visual die inspection confirmed` |
| X-User-Id | string | Prod | Non-empty | `fa-engineer-12` |

---

## 11. Output Specification

### Schema (classification success — conceptual)
`classification_run.id`, `status`, `faults_classified`, `method_distribution`, `classified_faults[]`

### JSON Example

```json
{
  "classification_run": {
    "id": "c1l2a3s4-s5i6-7890-abcd-ef1234567890",
    "dataset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "faults_classified": 3847,
    "unclassified_count": 42,
    "method_distribution": {
      "rule": 2100,
      "ml": 1200,
      "llm": 489,
      "override": 58
    }
  },
  "classified_faults": [
    {
      "fault_id": "f1a2u3l4-t5i6-7890-abcd-ef1234567890",
      "classification": "STUCK_AT_LOGIC",
      "confidence": 0.92,
      "method": "rule",
      "taxonomy_version": "tax-v3.1"
    }
  ]
}
```

### Engineering Report
Classification section in FA-FR-010 cites taxonomy distribution and override count.

### Dashboard Output
API-first panels: classification summary, method pie chart, override queue, fault detail drawer.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Classification requires FA-FR-001, FA-FR-002, FA-FR-003 completed. |
| BR-002 | Rule tier: confidence ≥0.85 → accept without ML/LLM. |
| BR-003 | ML tier: invoked only when rule confidence &lt; 0.85; accept if ML confidence ≥0.75. |
| BR-004 | LLM tier: invoked only when rule+ML disagree or both below thresholds; accept if ≥0.60. |
| BR-005 | LLM may only assign labels from registered taxonomy; no invented categories. |
| BR-006 | Engineer override requires reason and sets method=override, confidence=1.0. |
| BR-007 | Each classification run appends immutable metadata to classification_runs. |
| BR-008 | UNCLASSIFIED is a valid output, not an error. |

---

## 13. Key Engineering Rules

1. Never hallucinate taxonomy labels outside registered taxonomy.  
2. Always attribute classification method (rule/ml/llm/override).  
3. LLM prompts include only sanitized fault context, no secrets.  
4. Never modify source records or upstream analytics tables.  
5. Preserve semiconductor fault terminology (stuck-at, transition, bridging).  
6. Engineer override is auditable and immutable.  
7. Persist taxonomy_version and model_version on every run.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 through FA-FR-003 |
| LLM dependency | Optional; graceful degradation |
| Latency | &lt; 5 min for 50k faults |
| LLM rate limit | Configurable tokens/min via Redis |
| API-first | All UI actions have REST equivalents |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/classification/run`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with dataset_id or run ids, optional taxonomy_version and filters.

### Response
200 classification run + classified_faults summary.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Upstream gate failed |
| 503 | LLM unavailable (partial if ML completed) |
| 500 | Unexpected |

### Validation Errors
`UPSTREAM_GATE_FAILED`, `TAXONOMY_VERSION_INVALID`, `FAULT_NOT_FOUND`, `INVALID_TAXONOMY_CODE`.

Additional endpoints: `GET /api/v1/classification/runs`, `GET /api/v1/classification/runs/{run_id}`, `GET /api/v1/classification/faults`, `GET /api/v1/classification/faults/{fault_id}`, `PUT /api/v1/classification/faults/{fault_id}/override`, `GET /api/v1/classification/taxonomy`.

---

## 16. Database Design

### Tables
`classification_runs`, `classified_faults`

### Columns (representative — `classified_faults`)
`id` (PK UUID), `classification_run_id`, `fault_id`, `source_record_id`, `classification`, `confidence`, `method`, `taxonomy_version`, `model_version`, `override_reason`, `override_by`, `dataset_id`, `created_at`

### Primary Keys
UUID PKs on both tables.

### Foreign Keys
`classified_faults.classification_run_id` → `classification_runs.id`; fault_id references upstream pattern/rate entities.

### Indexes
`(classification_run_id)`, `(classification, confidence)`, `(method)`, `(dataset_id)`, `(fault_id)` unique per run.

### Relationships
One classification_run → many classified_faults. Override updates classified_faults row with audit fields.

### ER Explanation
Classification reads upstream analytics and writes labeled faults consumed by FA-FR-005 recurrence and FA-FR-006 correlation modules.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | API-first panels embedded in `/patterns`, `/failure-rates`; dedicated classification API views |
| User Actions | Trigger classification, review UNCLASSIFIED, override label, export |
| Charts | Method distribution pie, confidence histogram, taxonomy bar chart |
| Tables | Classified faults, override queue, UNCLASSIFIED list |
| Filters | Dataset, taxonomy, method, confidence range |
| Downloads | Classification CSV export |
| Notifications | Toast on run complete; React Query polling |

---

## 18. AI Workflow

1. API client triggers classification on gated dataset.  
2. Taxonomy and ML model loaded from cache/MinIO.  
3. Rule matchers evaluate each fault candidate.  
4. ML inference for sub-threshold rule matches.  
5. OpenAI LLM disambiguates remaining low-confidence faults.  
6. Results persisted with method attribution.  
7. Engineer reviews UNCLASSIFIED and overrides via API.  
8. FA-FR-005 consumes classified faults for recurrence analysis.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UPSTREAM_GATE_FAILED` | Prior modules incomplete | Missing FA-FR-001/002/003 | Complete upstream | High |
| `TAXONOMY_VERSION_INVALID` | Unknown taxonomy | Bad version string | Use active version | Medium |
| `ML_MODEL_UNAVAILABLE` | Model artifact missing | MinIO/FS issue | Rule-only fallback | Medium |
| `LLM_UNAVAILABLE` | OpenAI API down | Network/key issue | ML-only; UNCLASSIFIED remainder | Medium |
| `LLM_RATE_LIMITED` | Token budget exceeded | High volume | Retry with backoff | Low |
| `INVALID_TAXONOMY_CODE` | Override bad label | Typo | Use valid code | Medium |
| `FAULT_NOT_FOUND` | Invalid fault_id | Missing entity | Verify ID | Medium |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** classification_run_id, method counts, LLM tokens, duration_ms  
- **Audit Logging:** override actions with user, reason, timestamp  
- **Performance Metrics:** faults/s, tier latency breakdown  
- **Health Checks:** taxonomy load, ML model availability, OpenAI connectivity  
- **Prometheus Metrics:** `fa_classification_runs_total`, `fa_classified_by_method`, `fa_llm_tokens_used`  
- **Alerts:** UNCLASSIFIED rate spike, LLM cost threshold, ML model stale  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: classify trigger, override requires engineer role |
| Input Validation | Taxonomy enum validation; sanitized LLM prompts |
| Encryption | TLS; OpenAI API key in vault |
| Secrets Management | OpenAI key never in logs or prompts |
| OWASP | No prompt injection from raw user text; structured prompts only |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-004-01 | Rule classification | Run on known rule-match faults | method=rule | confidence ≥0.85 |
| TC-004-02 | ML fallback | Run on ambiguous faults | method=ml | ML invoked when rule low |
| TC-004-03 | LLM disambiguation | Force rule+ML disagree | method=llm | LLM label in taxonomy |
| TC-004-04 | Engineer override | PUT override endpoint | method=override | reason persisted |
| TC-004-05 | Upstream gate reject | Run without FA-FR-003 | 424 | UPSTREAM_GATE_FAILED |
| TC-004-06 | LLM degradation | Mock OpenAI down | 200 partial | UNCLASSIFIED for remainder |

---

## 23. Acceptance Criteria

1. Classification executes only after FA-FR-001 through FA-FR-003 complete.  
2. Hybrid cascade applies rules → ML → LLM in order.  
3. Every classified fault has method and confidence attribution.  
4. Engineer override is auditable with reason.  
5. LLM assigns only registered taxonomy labels.  
6. API-first: all operations available via REST.  
7. Downstream FA-FR-005 can query classified faults.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | LLM cost at scale | Rate limits; rule+ML first |
| Technical | ML model drift | Versioned models; benchmark CI |
| Business | Override abuse | RBAC + audit trail |
| Assumption | Taxonomy maintained by FA team | Versioned registry |
| Assumption | OpenAI available for LLM tier | Graceful degradation |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001, FA-FR-002, FA-FR-003 |
| External APIs | OpenAI GPT (LLM tier) |
| Database | PostgreSQL |
| Infrastructure | Redis, MinIO, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, scikit-learn/onnx, OpenAI SDK, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-004 | This document | `/api/v1/classification/*` | classification_runs, classified_faults | TC-004-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] Hybrid cascade logic documented  
- [ ] LLM constraints and fallback documented  
- [ ] API-first UI approach verified  
- [ ] Override audit trail specified  
- [ ] Test cases cover all three AI tiers  
- [ ] No placeholders remain  
- [ ] Upstream gate chain documented  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-004 |
