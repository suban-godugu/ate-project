# FA-FR-001 Technical AI Agent Specification — Test Data Ingestion Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-001  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-001 Technical AI Agent Specification — Test Data Ingestion Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Test Data Ingestion Engine |
| FR ID | FA-FR-001 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-001 is the foundational agent that admits raw artifacts into the platform, validates integrity, parses heterogeneous formats, normalizes records into a canonical schema, and persists lineage-ready data in PostgreSQL with object storage for raw bytes.

**Scope:** Upload API, dataset scan, parser factory/adapters, validation/quarantine, normalized persistence, ingestion statistics, audit trail.  
**Stakeholders:** Test Operations, Data Engineering, FA Engineers, Yield Engineering, Platform/DevOps.  
**Out of scope for this agent:** Pattern scoring, rate formulas, classification taxonomy application, spatial analytics, report composition (FA-FR-002…010).

---

## 3. Business Objective

**Problem:** Fab and ATE environments produce multi-format, multi-GB STIL and log artifacts. Manual ingestion is error-prone, non-auditable, and blocks downstream FA automation.

**Expected outcome:** Trusted, validated, normalized test records available within seconds to minutes of upload, with full auditability and quarantine of malformed records without losing the lot.

**KPIs:**
- Upload acknowledge (async path) &lt; 2 s  
- Integrity percentage tracked per upload  
- Quarantine rate monitored; zero silent data loss of accepted records  
- 100k+ record batch ingest capability  
- 100% of production uploads associated with `upload_id` / `dataset_id` lineage  

---

## 4. Technical Overview

FA-FR-001 implements a Clean Architecture ingestion pipeline:

1. **Edge:** Next.js `ate-dashboard` multipart upload / dataset scan UI  
2. **API:** FastAPI routers under `/api/v1` (`uploads`, `datasets`, `ingestion/statistics`)  
3. **Application:** Upload/dataset services orchestrate validation → parse → persist  
4. **Domain:** Parser strategies (STIL, CSV, LOG, adapter plugins), validation rules, canonical `TestRecord` fields  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; MinIO/filesystem for raw objects; Redis for rate limits  

Architecture decision: raw bytes are immutable; analytics never rewrite originals. Deterministic `record_key` / checksums support dedupe policies.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, react-dropzone |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (S3 API) / controlled filesystem |
| Cache | Redis |
| AI (assistive only here) | Optional format hints via rules; no generative rewrite of STIL |
| Testing | Pytest / unittest, benchmark timings on audits |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Accept multipart uploads and server-side dataset scans  
- Detect format via factory/registry (MIME, extension, content sniff)  
- Parse STIL and tester logs into normalized records  
- Validate schema, integrity, size, path safety  
- Quarantine invalid records with structured issues  
- Persist uploads, metadata, validation results, normalized records, statistics, audits  
- Expose retrieval APIs for records and ingestion statistics  

**Exclusions:**
- Failure pattern ranking (FA-FR-002)  
- Rate computation, classification, recurrence, correlation, die/wafer, prediction, reporting  
- Destructive mutation of raw STIL/log bytes  

---

## 7. Functional Requirements

### FR ID
FA-FR-001

### Description
The agent shall ingest semiconductor STIL files and tester log files, validate them, parse supported formats, normalize to a canonical record model, and store results with full audit lineage for downstream FA-FR modules.

### Priority
**Critical / P0** — blocks entire pipeline.

### Inputs
- Multipart file upload (STIL, CSV, LOG, allowed JSON/XML)  
- Dataset folder scan requests  
- Optional flags: `allow_duplicate`, recursive scan  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `upload` / `dataset` entities with status  
- `normalized_records` set  
- `validation_results` and quarantine counts  
- `ingestion_statistics`  
- Structured error envelopes on rejection  

### Processing Logic
1. Authenticate/authorize request  
2. Sanitize filename; enforce allow-list and size caps  
3. Store raw object (MinIO/FS) with checksum  
4. Select parser via ParserFactory / adapter registry  
5. Parse → validate each record  
6. Accept or quarantine; compute integrity %  
7. Persist metadata + records + audit + statistics  
8. Return completed payload with preview  

### Dependencies
- PostgreSQL, MinIO/FS, Redis (rate limit)  
- Config: upload limits, adapter YAML  
- Downstream consumers: FA-FR-002…010 (read-only on completed ingestion)  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Upload ACK &lt; 2 s (async); validation typically &lt; 5 s for standard files; batch 100k+ records |
| Scalability | Stateless API replicas; batch inserts; object store horizontal scale |
| Availability | API N≥2 behind LB; PostgreSQL HA; MinIO erasure coding in prod |
| Logging | Structured JSON logs with `upload_id`, `execution_id`, parser_id, counts |
| Security | Path traversal blocked; MIME allow-list; RBAC; secrets in env/vault |
| Maintainability | Factory/Strategy parsers; Alembic migrations; versioned adapter configs |
| Reliability | Append-only audits; idempotent dedupe options; quarantine without lot wipe |
| Monitoring | RED metrics; ingest throughput; quarantine rate; disk/object errors |

---

## 9. AI Behavior Specification

### Role
Format-aware ingestion guardian — deterministic first; AI may only assist classification of unknown formats in future adapters, never rewrite content.

### Reasoning Strategy
Rule-based detection → strategy parse → schema validation. No LLM authority over accepted bits.

### Workflow
Detect → Parse → Validate → Persist → Audit.

### Decision Logic
If parser missing → reject/quarantine file. If record invalid → quarantine record, continue lot when policy allows.

### Confidence Handling
Integrity % = accepted / (accepted + quarantined). Exposed in upload response.

### Limitations
Full parse of multi-hundred-MB STIL may be deferred by size thresholds in evaluation paths; production should stream or raise limits deliberately.

### Fallback Behaviour
Unknown format → structured error `UNSUPPORTED_FORMAT`. Partial success → status completed with quarantine details.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| file | multipart binary | Yes (upload) | Allow-list ext/MIME; max bytes; sanitized name | `Production_SCAN_stuck_at_1000pat.stil` |
| allow_duplicate | boolean | No | Default false | `true` |
| path / scan root | string | Yes (scan) | Must be under allowed roots | `C:\data\generated_logs 1000 patterns` |
| recursive | boolean | No | Default false | `true` |
| X-User-Id | string | Prod | Non-empty | `fa-engineer-12` |
| X-Role | string | Prod | Enum roles | `failure_engineer` |

Canonical normalized fields (minimum): `lot_id`, `wafer_id`, `die_id`, `test_stage`, `tester_id`, `pass_fail`, `timestamp`, `source_file`, `adapter_id`.

---

## 11. Output Specification

### Schema (upload success — conceptual)
`upload.id`, `status`, `parser_id`, `records_accepted`, `records_quarantined`, `integrity_pct`, `validation_report`, `processing_statistics`, `parsed_dataset_preview[]`

### JSON Example

```json
{
  "duplicate": false,
  "upload": {
    "id": "11987939-bb26-4d5b-90c8-9ba611633319",
    "original_filename": "csv_die_results_sample.csv",
    "status": "completed",
    "parser_id": "csv_die_results",
    "records_accepted": 2,
    "records_quarantined": 0,
    "integrity_pct": 100.0
  }
}
```

### Engineering Report
Ingestion section in FA-FR-010 cites upload integrity, parser id, STIL pattern counts when available.

### Dashboard Output
`/upload` queue status; `/datasets` explorer; `/stats` parser statistics charts.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Raw STIL/log bytes are immutable after storage. |
| BR-002 | Accepted records must satisfy mandatory canonical fields. |
| BR-003 | Path traversal and absolute escape paths are rejected. |
| BR-004 | Files exceeding `MAX_UPLOAD_BYTES` are rejected before parse. |
| BR-005 | Quarantined records never enter FA-FR-002 source sets. |
| BR-006 | Duplicate uploads require explicit `allow_duplicate=true`. |
| BR-007 | Every completed upload writes an audit log entry. |

---

## 13. Key Engineering Rules

1. Never hallucinate missing lot/wafer/die identifiers.  
2. Always validate inputs at API and parser boundaries.  
3. Maintain deterministic parser outputs for identical bytes + config version.  
4. Never modify raw STIL or log content.  
5. Preserve semiconductor engineering terminology (STIL, die, wafer, lot, ATE).  
6. Prefer quarantine over silent coercion of invalid values.  
7. Persist `config_version` / parser metadata for replay.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Formats | `.stil`, `.log`, `.txt`, `.csv`, configured JSON/XML |
| Max file size | `MAX_UPLOAD_BYTES` (multi-GB capable; env-configured) |
| Latency | ACK &lt; 2 s async; sync small files interactive |
| Memory | Stream large files; avoid full in-memory STIL when over threshold |
| Concurrency | Rate-limited per client; pool-sized DB connections |
| SQLite | Not supported for production API |

---

## 15. API Specification

### Endpoint
`POST /api/v1/uploads`

### Method
POST (multipart/form-data)

### Headers
`X-User-Id`, `X-Role` (production); `Content-Type: multipart/form-data`

### Request
Form field `file`; query `allow_duplicate` optional.

### Response
200 JSON upload entity + validation + preview.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 409 | Duplicate rejected |
| 413 | Too large |
| 429 | Rate limited |
| 500 | Unexpected |

### Validation Errors
Structured `{ "detail": { "code", "message", "issues": [...] } }` e.g. `UNSUPPORTED_FORMAT`, `PATH_TRAVERSAL`, `EMPTY_FILE`.

### Example Payload
Multipart file attach; response example in §11.

Additional endpoints: `GET /api/v1/uploads`, `GET /api/v1/uploads/{id}`, `GET /api/v1/uploads/{id}/records`, `POST /api/v1/datasets/upload`, `POST /api/v1/datasets/scan`, `GET /api/v1/ingestion/statistics`.

---

## 16. Database Design

### Tables
`uploads`, `upload_history`, `parser_metadata`, `validation_results`, `normalized_records`, `audit_logs`, `ingestion_statistics`, `ingestion_datasets`

### Columns (representative — `uploads`)
`id` (PK UUID), `original_filename`, `storage_uri`, `checksum`, `status`, `parser_id`, `records_accepted`, `records_quarantined`, `integrity_pct`, `created_at`, `completed_at`

### Primary Keys
UUID PKs on all entity tables.

### Foreign Keys
`normalized_records.upload_id` → `uploads.id`; validation/history → upload/dataset.

### Indexes
`(status, created_at)`, `checksum`, `upload_id` on records, `(dataset_id)`.

### Relationships
One upload → many normalized_records; one dataset → many uploads/files.

### ER Explanation
Ingestion is the root of lineage. Downstream FA-FR modules reference `upload_id` or `dataset_id` and never mutate these tables’ historical rows.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/upload`, `/datasets`, `/stats`, `/history` |
| User Actions | Drag-drop upload, server scan, refresh status, open dataset |
| Charts | Ingestion volume, integrity %, quarantine rate |
| Tables | Upload list, record preview, validation issues |
| Filters | Status, parser, date range |
| Downloads | Raw file reference; export stats CSV |
| Notifications | Toast on complete/fail; status polling |

---

## 18. AI Workflow

1. User selects STIL/log files or scan path.  
2. API stores raw object and computes checksum.  
3. Factory selects parser/adapter.  
4. Records parsed and validated.  
5. Accepted records normalized and inserted.  
6. Statistics and audit completed.  
7. Downstream agents may begin FA-FR-002 on completed lineage.  
8. FA-FR-010 later cites ingestion integrity in reports.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `UNSUPPORTED_FORMAT` | No parser matched | Unknown extension/content | Use supported format or add adapter | Medium |
| `PATH_TRAVERSAL` | Unsafe filename/path | `..` or absolute escape | Sanitize/reject | High |
| `FILE_TOO_LARGE` | Exceeds max bytes | Oversized artifact | Split or raise limit with approval | Medium |
| `PARSE_FAILURE` | Parser exception | Corrupt content | Quarantine; inspect raw | High |
| `VALIDATION_ERROR` | Schema fail | Missing fields | Fix source data | Medium |
| `DUPLICATE_UPLOAD` | Checksum exists | Re-upload | Set allow_duplicate or reuse id | Low |
| `STORAGE_ERROR` | Object store fail | MinIO/FS issue | Retry; check infra | Critical |
| `DB_PERSIST_ERROR` | Commit failed | DB unavailable | Retry; alert ops | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** JSON with upload_id, parser_id, counts, duration_ms  
- **Audit Logging:** `audit_logs` / upload_history append-only  
- **Performance Metrics:** elapsed_ms, records/s, integrity_pct  
- **Health Checks:** `GET /health` for API process  
- **Prometheus Metrics (target):** `fa_ingest_uploads_total`, `fa_ingest_records_total`, `fa_ingest_quarantine_ratio`  
- **Alerts:** quarantine spike, storage errors, p95 ingest latency breach  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC target; trusted `X-User-Id` |
| Authorization | RBAC roles for upload/delete |
| Input Validation | Pydantic + MIME + size + path sanitize |
| Encryption | TLS in transit; SSE for MinIO at rest (prod) |
| Secrets Management | `.env` / vault; never commit secrets |
| OWASP | Injection prevented via ORM; upload hardening; misconfig CORS restricted in prod |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-001-01 | Valid CSV upload | POST sample CSV | 200 completed | integrity 100%, records &gt; 0 |
| TC-001-02 | Reject path traversal | Upload `../x.stil` name | 4xx | No object written outside root |
| TC-001-03 | Oversize reject | Exceed MAX bytes | 413/422 | No partial corrupt DB state |
| TC-001-04 | STIL parse | Upload small STIL | completed + metadata | parser_id stil; notes present |
| TC-001-05 | Dataset scan | POST scan allowed root | datasets listed | files discovered |
| TC-001-06 | Duplicate policy | Re-upload same checksum | 409 unless allow_duplicate | Rule enforced |

---

## 23. Acceptance Criteria

1. Supported formats parse into normalized records with mandatory fields.  
2. Integrity percentage reported for every completed upload.  
3. Raw object retained and addressable by storage URI.  
4. Audit trail exists for success and failure.  
5. Downstream FA-FR-002 can locate completed upload/dataset.  
6. Upload ACK meets &lt; 2 s on async path under nominal load.  
7. No raw STIL content is altered by the agent.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | Huge STIL OOM | Streaming/threshold parse |
| Technical | Ambiguous log dialects | Adapter YAML + fixtures |
| Business | Incomplete uploads block FA | Clear UI status + quarantine report |
| Assumption | Gateway sets identity headers | Document perimeter trust |
| Assumption | PostgreSQL is available | Hard dependency; no SQLite prod |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | `backend/ingestion/*`, adapters registry, stil parser |
| External APIs | None required for core ingest |
| Database | PostgreSQL |
| Infrastructure | MinIO/FS, Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, Alembic |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-001 | This document | `/api/v1/uploads`, `/datasets/*` | uploads, normalized_records, … | TC-001-01…06 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] API contracts match OpenAPI intent  
- [ ] DB tables align with Alembic ingestion migrations  
- [ ] Security upload controls reviewed  
- [ ] Performance limits realistic  
- [ ] Test cases cover happy path and abuse cases  
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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-001 |
