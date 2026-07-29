# FA-FR-002 Technical AI Agent Specification — Pattern Detection Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-002  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-002 Technical AI Agent Specification — Pattern Detection Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Pattern Detection Engine |
| FR ID | FA-FR-002 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-002 is the pattern detection agent that consumes normalized records from FA-FR-001, applies rule-library and statistical matchers against STIL-derived signatures, ranks detected failure patterns, and persists confidence-scored occurrences for downstream rate, classification, and correlation modules.

**Scope:** Pattern detection API, rule library management, occurrence aggregation, confidence scoring, detection history, statistics, dashboard visualization.  
**Stakeholders:** Failure Analysis Engineers, Test Operations, Yield Engineering, Data Science, Platform/DevOps.  
**Out of scope for this agent:** Failure rate formulas (FA-FR-003), fault taxonomy assignment (FA-FR-004), recurrence tracking (FA-FR-005), spatial die/wafer analytics (FA-FR-007/008), predictive modeling (FA-FR-009), report composition (FA-FR-010).

---

## 3. Business Objective

**Problem:** Engineers manually scan thousands of STIL patterns and log entries to identify recurring failure signatures. Manual detection is slow, inconsistent across shifts, and lacks auditable confidence metrics.

**Expected outcome:** Automated, repeatable pattern detection with ≥95% accuracy against the validated golden rule library, producing ranked pattern lists with occurrence counts and confidence scores within minutes of ingestion completion.

**KPIs:**
- Pattern detection accuracy ≥95% against benchmark rule library  
- Detection run completion &lt; 5 min for 100k normalized records  
- 100% of detected patterns linked to source `upload_id` / `dataset_id` lineage  
- Confidence scores exposed for every detected pattern  
- Zero silent drops of matched occurrences  

---

## 4. Technical Overview

FA-FR-002 implements a rule-driven pattern detection pipeline gated on FA-FR-001 completion:

1. **Edge:** Next.js `ate-dashboard` `/patterns` screen with detection triggers and results tables  
2. **API:** FastAPI routers under `/api/v1/patterns`  
3. **Application:** PatternDetectionService orchestrates rule evaluation → occurrence extraction → confidence scoring → statistics  
4. **Domain:** RuleLibrary, PatternMatcher strategies, confidence calculators, occurrence aggregators  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; Redis for detection job status cache; read-only access to `normalized_records`  

Architecture decision: detection is idempotent per `(dataset_id, rule_library_version)` tuple. Historical detection runs are append-only in `detection_history`.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (read-only reference to raw STIL via FA-FR-001 URIs) |
| Cache | Redis (detection job status, rule library hot cache) |
| AI | OpenAI GPT (assistive rule explanation only); primary matching via deterministic rules |
| Testing | Pytest, golden-fixture accuracy benchmarks |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 completed ingestion (`status=completed`, integrity acceptable)  
- Load and version the rule library from `rule_library`  
- Execute pattern matchers against normalized records and STIL metadata  
- Persist `detected_patterns`, `pattern_occurrences`, `pattern_statistics`, `pattern_confidence`  
- Append immutable entries to `detection_history`  
- Expose REST APIs for detection runs, results, and statistics  
- Render pattern charts and tables on `/patterns` dashboard  

**Exclusions:**
- Failure rate computation (FA-FR-003)  
- Fault classification taxonomy (FA-FR-004)  
- Recurrence and hotspot analysis (FA-FR-005)  
- Statistical correlation (FA-FR-006)  
- Modification of raw STIL bytes or normalized records  

---

## 7. Functional Requirements

### FR ID
FA-FR-002

### Description
The agent shall detect semiconductor failure patterns from ingested normalized records using a versioned rule library, compute confidence scores, aggregate occurrences, and persist ranked results with full audit lineage for downstream FA modules.

### Priority
**Critical / P0** — first analytics gate after ingestion; blocks FA-FR-003 through FA-FR-010.

### Inputs
- `dataset_id` or `upload_id` referencing FA-FR-001 completed ingestion  
- Optional `rule_library_version` (defaults to active)  
- Optional detection filters: `test_stage`, `lot_id`, `date_range`  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `detected_patterns` ranked list with pattern_id, signature, rank  
- `pattern_occurrences` per record/die/wafer linkage  
- `pattern_statistics` aggregate counts and rates  
- `pattern_confidence` scores per detection  
- `detection_history` run metadata  
- Structured error envelopes on gate failure  

### Processing Logic
1. Verify FA-FR-001 gate: ingestion completed, integrity ≥ threshold  
2. Load rule library version; cache in Redis  
3. Fetch normalized records for scope  
4. Apply rule matchers (exact, regex, statistical threshold)  
5. Aggregate occurrences; compute confidence per BR-003  
6. Rank patterns by occurrence count × confidence  
7. Persist all entities; append detection_history  
8. Return ranked results with statistics summary  

### Dependencies
- FA-FR-001 completed ingestion (`normalized_records`, uploads)  
- PostgreSQL, Redis  
- Rule library seed data and benchmark fixtures  
- Downstream consumers: FA-FR-003…010 (read-only on detection outputs)  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Detection run &lt; 5 min for 100k records; API list response &lt; 500 ms |
| Scalability | Stateless API replicas; batch rule evaluation; indexed occurrence lookups |
| Availability | API N≥2 behind LB; PostgreSQL HA |
| Logging | Structured JSON with `detection_run_id`, `dataset_id`, rule_version, match counts |
| Security | RBAC for detection trigger; read-only on ingestion tables |
| Maintainability | Versioned rule library; Alembic migrations; YAML rule import |
| Reliability | Idempotent re-runs; append-only detection_history |
| Monitoring | Detection accuracy drift alerts; p95 latency; match rate metrics |

---

## 9. AI Behavior Specification

### Role
Deterministic pattern matcher with optional GPT-assisted rule documentation — AI never overrides rule match results.

### Reasoning Strategy
Rule library evaluation first → statistical confidence → rank aggregation. GPT may generate human-readable pattern descriptions for dashboard tooltips only.

### Workflow
Gate → Load Rules → Match → Score → Rank → Persist → Expose.

### Decision Logic
If ingestion gate fails → reject with `INGESTION_GATE_FAILED`. If no rules match → return empty set with zero-count statistics, not an error.

### Confidence Handling
Confidence = f(rule_weight, match_strength, occurrence_support). Scores 0.0–1.0 stored in `pattern_confidence`. Accuracy benchmark ≥95% against golden library.

### Limitations
Novel patterns not in rule library are not detected until rules are added. LLM does not invent patterns.

### Fallback Behaviour
Rule parse error → skip rule, log warning, continue run. Redis unavailable → direct DB rule load with increased latency.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| dataset_id | UUID | Yes (or upload_id) | Must reference completed ingestion | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| upload_id | UUID | Alt to dataset_id | Completed status | `11987939-bb26-4d5b-90c8-9ba611633319` |
| rule_library_version | string | No | Must exist in rule_library | `v2.4.1` |
| test_stage | string | No | Enum from normalized records | `SCAN` |
| lot_id | string | No | Non-empty if provided | `LOT-2026-0412` |
| date_range | object | No | ISO8601 start/end | `{"start":"2026-07-01","end":"2026-07-17"}` |
| X-User-Id | string | Prod | Non-empty | `fa-engineer-12` |
| X-Role | string | Prod | Enum roles | `failure_engineer` |

---

## 11. Output Specification

### Schema (detection success — conceptual)
`detection_run.id`, `status`, `patterns_detected`, `accuracy_pct`, `detected_patterns[]`, `pattern_statistics`, `processing_duration_ms`

### JSON Example

```json
{
  "detection_run": {
    "id": "d4e5f6a7-b8c9-0123-def4-567890abcdef",
    "dataset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "completed",
    "patterns_detected": 14,
    "accuracy_pct": 96.2,
    "rule_library_version": "v2.4.1",
    "processing_duration_ms": 8420
  },
  "detected_patterns": [
    {
      "pattern_id": "PAT-STUCK-AT-1000",
      "rank": 1,
      "occurrence_count": 847,
      "confidence": 0.97,
      "signature": "STUCK_AT pattern index 1000"
    }
  ]
}
```

### Engineering Report
Pattern detection section in FA-FR-010 cites top patterns, confidence distribution, and detection run accuracy.

### Dashboard Output
`/patterns` ranked table, occurrence bar chart, confidence histogram, detection history timeline.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Detection shall not execute unless FA-FR-001 ingestion status is `completed`. |
| BR-002 | Quarantined records from FA-FR-001 are excluded from pattern matching. |
| BR-003 | Confidence score = rule_weight × match_strength × min(1.0, occurrence_support / support_threshold). |
| BR-004 | Pattern detection accuracy against golden benchmark shall be ≥95%. |
| BR-005 | Each detection run appends an immutable row to `detection_history`. |
| BR-006 | Re-running detection with same `(dataset_id, rule_library_version)` is idempotent. |
| BR-007 | Rule library changes require version bump; prior versions remain queryable. |
| BR-008 | Detected patterns must retain `upload_id` and `dataset_id` lineage. |

---

## 13. Key Engineering Rules

1. Never hallucinate pattern signatures not supported by rule library matches.  
2. Always validate ingestion gate before any rule evaluation.  
3. Maintain deterministic match outputs for identical records + rule version.  
4. Never modify normalized records or raw STIL content.  
5. Preserve semiconductor terminology (STIL, pattern index, stuck-at, transition).  
6. Prefer explicit empty results over fabricated pattern detections.  
7. Persist `rule_library_version` on every detection run for replay.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 completed ingestion only |
| Accuracy floor | ≥95% against benchmark rule library |
| Latency | &lt; 5 min for 100k records |
| Memory | Stream records in batches; avoid full in-memory load |
| Concurrency | One active detection run per dataset_id (mutex via Redis) |
| SQLite | Not supported for production API |

---

## 15. API Specification

### Endpoint
`POST /api/v1/patterns/detect`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role` (production); `Content-Type: application/json`

### Request
JSON body with `dataset_id` or `upload_id`, optional filters and `rule_library_version`.

### Response
200 JSON detection run entity + ranked detected_patterns + statistics.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 409 | Detection already in progress |
| 424 | Ingestion gate failed (FA-FR-001) |
| 429 | Rate limited |
| 500 | Unexpected |

### Validation Errors
Structured `{ "detail": { "code", "message", "issues": [...] } }` e.g. `INGESTION_GATE_FAILED`, `DATASET_NOT_FOUND`, `RULE_VERSION_INVALID`.

### Example Payload
JSON body per §10; response example in §11.

Additional endpoints: `GET /api/v1/patterns`, `GET /api/v1/patterns/{pattern_id}`, `GET /api/v1/patterns/runs/{run_id}`, `GET /api/v1/patterns/statistics`, `GET /api/v1/patterns/rule-library`, `GET /api/v1/patterns/history`.

---

## 16. Database Design

### Tables
`detected_patterns`, `pattern_occurrences`, `pattern_statistics`, `pattern_confidence`, `detection_history`, `rule_library`

### Columns (representative — `detected_patterns`)
`id` (PK UUID), `detection_run_id`, `pattern_id`, `signature`, `rank`, `occurrence_count`, `dataset_id`, `upload_id`, `rule_library_version`, `created_at`

### Primary Keys
UUID PKs on all entity tables.

### Foreign Keys
`pattern_occurrences.detected_pattern_id` → `detected_patterns.id`; `pattern_confidence.detected_pattern_id` → `detected_patterns.id`; `detection_history.dataset_id` references FA-FR-001 datasets.

### Indexes
`(dataset_id, rule_library_version)`, `(pattern_id, rank)`, `(detection_run_id)`, GIN on `signature` for search.

### Relationships
One detection run → many detected_patterns; one detected_pattern → many pattern_occurrences and one pattern_confidence row.

### ER Explanation
Pattern detection reads FA-FR-001 lineage and writes analytics tables consumed by FA-FR-003 onward. No writes to ingestion tables.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/patterns`, `/patterns/{pattern_id}`, `/patterns/history` |
| User Actions | Trigger detection, filter by lot/stage, drill into occurrences, export CSV |
| Charts | Top patterns bar chart, confidence distribution, detection timeline (Recharts) |
| Tables | Ranked patterns, occurrence detail, rule library version |
| Filters | Dataset, lot, test stage, date range, confidence threshold |
| Downloads | Pattern list CSV, occurrence detail export |
| Notifications | Toast on detection complete; polling via React Query |

---

## 18. AI Workflow

1. User selects completed dataset from FA-FR-001 on `/patterns`.  
2. API verifies ingestion gate and loads rule library.  
3. Pattern matchers evaluate normalized records in batches.  
4. Occurrences aggregated; confidence scores computed per BR-003.  
5. Results ranked and persisted to PostgreSQL.  
6. Dashboard refreshes with ranked patterns and charts.  
7. FA-FR-003 consumes detected patterns for failure rate computation.  
8. FA-FR-010 later cites pattern detection results in engineering reports.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `INGESTION_GATE_FAILED` | FA-FR-001 not completed | Upload incomplete/quarantined | Complete ingestion first | High |
| `DATASET_NOT_FOUND` | Invalid dataset_id | Missing or deleted | Verify dataset exists | Medium |
| `RULE_VERSION_INVALID` | Unknown rule version | Typo or deprecated | Use active version | Medium |
| `DETECTION_IN_PROGRESS` | Mutex conflict | Concurrent run | Wait or cancel prior run | Low |
| `RULE_PARSE_ERROR` | Malformed rule definition | Bad YAML/JSON rule | Fix rule; re-import | Medium |
| `ACCURACY_BELOW_THRESHOLD` | Benchmark &lt; 95% | Rule drift or bad fixtures | Review rule library | High |
| `DB_PERSIST_ERROR` | Commit failed | DB unavailable | Retry; alert ops | Critical |
| `REDIS_UNAVAILABLE` | Cache miss path | Redis down | Fallback to DB load | Low |

---

## 20. Logging & Monitoring

- **Structured Logging:** JSON with detection_run_id, dataset_id, rule_version, patterns_matched, duration_ms  
- **Audit Logging:** `detection_history` append-only  
- **Performance Metrics:** records/s, match rate, accuracy_pct, elapsed_ms  
- **Health Checks:** `GET /health` includes rule library load status  
- **Prometheus Metrics (target):** `fa_pattern_detection_runs_total`, `fa_patterns_detected_total`, `fa_pattern_accuracy_pct`  
- **Alerts:** accuracy below 95%, detection p95 latency breach, zero-match anomaly on large datasets  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC target; trusted `X-User-Id` |
| Authorization | RBAC: `failure_engineer` trigger; `viewer` read-only |
| Input Validation | Pydantic UUID validation; filter enum checks |
| Encryption | TLS in transit; PostgreSQL encryption at rest (prod) |
| Secrets Management | `.env` / vault; OpenAI key for assistive features only |
| OWASP | Injection prevented via ORM; no dynamic rule eval from user input |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-002-01 | Detect patterns on valid dataset | POST detect with completed dataset_id | 200 completed | patterns_detected &gt; 0, accuracy ≥95% |
| TC-002-02 | Reject incomplete ingestion gate | POST detect with pending upload | 424 | INGESTION_GATE_FAILED |
| TC-002-03 | Idempotent re-run | POST detect twice same params | 200 both | Same pattern counts |
| TC-002-04 | Empty match set | POST detect on clean dataset | 200 completed | patterns_detected = 0, no error |
| TC-002-05 | Rule version override | POST with specific rule_library_version | 200 | Results tagged with version |
| TC-002-06 | Confidence scoring | Verify known pattern | confidence in [0,1] | Matches BR-003 formula |

---

## 23. Acceptance Criteria

1. Pattern detection executes only after FA-FR-001 ingestion completes successfully.  
2. Detection accuracy ≥95% against golden benchmark rule library.  
3. Every detected pattern has confidence score and occurrence count.  
4. Detection history records every run with rule library version.  
5. Dashboard `/patterns` displays ranked results with charts.  
6. Downstream FA-FR-003 can query detected patterns by dataset_id.  
7. Quarantined FA-FR-001 records are excluded from matching.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Rule library drift reduces accuracy | Versioned rules; benchmark CI gate |
| Technical | Large dataset timeout | Batch streaming; async job queue |
| Business | False negatives on novel failures | Rule update workflow; engineer review UI |
| Assumption | FA-FR-001 normalized records contain pattern-relevant fields | Schema contract documented |
| Assumption | Golden benchmark fixtures maintained | CI accuracy test on every rule change |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001 (`normalized_records`, uploads, datasets) |
| External APIs | OpenAI GPT (optional assistive descriptions) |
| Database | PostgreSQL |
| Infrastructure | Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-002 | This document | `/api/v1/patterns/*` | detected_patterns, pattern_occurrences, pattern_statistics, pattern_confidence, detection_history, rule_library | TC-002-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] API contracts match OpenAPI intent  
- [ ] DB tables align with Alembic pattern migrations  
- [ ] FA-FR-001 gate dependency enforced  
- [ ] Accuracy ≥95% benchmark documented  
- [ ] Test cases cover gate, happy path, idempotency  
- [ ] No placeholders remain  
- [ ] Downstream lineage fields documented  

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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-002 |
