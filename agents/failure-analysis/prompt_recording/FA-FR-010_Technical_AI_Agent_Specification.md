# FA-FR-010 Technical AI Agent Specification — Reporting Engine

**Template:** Technical AI Agent Specification Template  
**Project:** Semiconductor Failure Analysis AI Agent  
**FR ID:** FA-FR-010  
**Version:** 1.0  
**Date:** 2026-07-17  

---

## 1. Document Information

| Attribute | Value |
|-----------|-------|
| Document Title | FA-FR-010 Technical AI Agent Specification — Reporting Engine |
| Project | Semiconductor Failure Analysis AI Agent |
| Agent Name | Reporting Engine |
| FR ID | FA-FR-010 |
| Version | 1.0 |
| Status | Released for Review |
| Author | Principal Enterprise AI Architect |
| Reviewer | Technical Design Review Board |
| Date | 2026-07-17 |
| Classification | Internal — Engineering |
| Related Template | Technical_AI_Agent_Specification_Template.docx |

---

## 2. Project Overview

The Semiconductor Failure Analysis AI Agent automates engineering analysis of STIL pattern files and semiconductor tester logs. FA-FR-010 is the terminal reporting agent that composes multi-module engineering reports from FA-FR-001 through FA-FR-009 outputs, exporting in PDF, XLSX, HTML, CSV, and JSON formats with benchmark results and full audit lineage.

**Scope:** Report generation API, multi-format export, report templates, benchmark results, report history, dashboard at `/reports`.  
**Stakeholders:** Failure Analysis Engineers, Yield Engineering, Fab Management, Test Operations, Executive Review, Platform/DevOps.  
**Out of scope for this agent:** Re-computation of upstream analytics; all data sourced read-only from FA-FR-001…009.

---

## 3. Business Objective

**Problem:** Engineers manually compile findings from multiple FA tools into reports for management and customers. Manual report assembly is slow, inconsistent, and lacks standardized sections, benchmark comparisons, and export format options.

**Expected outcome:** Automated engineering report generation composing all FA module results into standardized sections, exportable in five formats (PDF, XLSX, HTML, CSV, JSON), with benchmark comparisons, within minutes of fault prediction completion.

**KPIs:**
- Report generation &lt; 3 min for standard lot report  
- All five export formats functional (PDF, XLSX, HTML, CSV, JSON)  
- Report includes sections from all completed upstream modules  
- Benchmark results compared against historical baselines  
- 100% report lineage to upstream run IDs  

---

## 4. Technical Overview

FA-FR-010 implements a report composition pipeline gated on FA-FR-001 through FA-FR-009:

1. **Edge:** Next.js `ate-dashboard` `/reports` screen with report builder and download  
2. **API:** FastAPI routers under `/api/v1/reports`  
3. **Application:** ReportService orchestrates section assembly → template render → format export → persist  
4. **Domain:** Report templates, section composers, format exporters (WeasyPrint/reportlab PDF, openpyxl XLSX, Jinja2 HTML, CSV, JSON)  
5. **Infrastructure:** SQLAlchemy async → PostgreSQL; MinIO for generated report artifacts  

Architecture decision: reports are read-only compositions of upstream data. No upstream tables modified. Generated artifacts stored in MinIO with PostgreSQL metadata.

---

## 5. Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, ShadCN UI, React Query, Zustand, Framer Motion, Recharts |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.x, AsyncIO, Pydantic v2, Alembic |
| Database | PostgreSQL |
| Object Storage | MinIO (generated report artifacts) |
| Cache | Redis (report generation job status) |
| AI | OpenAI GPT (optional executive summary narrative); deterministic report composition |
| Testing | Pytest, report format validation fixtures |
| Deployment | Docker, Kubernetes, GitHub Actions |

---

## 6. Agent Responsibilities

**Responsibilities:**
- Gate on FA-FR-001 through FA-FR-009 completion (partial reports allowed with section skip flags)  
- Compose standardized report sections from all upstream modules  
- Generate reports in PDF, XLSX, HTML, CSV, JSON formats  
- Include benchmark_results against historical baselines  
- Persist `reports`, report metadata, report_sections, benchmark_results  
- Expose REST APIs and `/reports` dashboard  
- Store generated artifacts in MinIO with download URLs  

**Exclusions:**
- Re-computation of upstream analytics  
- Modification of any FA-FR-001…009 data  
- Definitive root-cause statements (FA-FR-009 predictions cited as PROBABLE only)  

---

## 7. Functional Requirements

### FR ID
FA-FR-010

### Description
The agent shall compose engineering reports from all upstream FA module outputs, export in PDF/XLSX/HTML/CSV/JSON formats, include benchmark comparisons, and persist report metadata with full lineage.

### Priority
**High / P1** — terminal deliverable for engineering and management review.

### Inputs
- `dataset_id` or `lot_id` with upstream run IDs  
- `report_template` (standard/executive/detailed/custom)  
- `export_formats[]` (pdf, xlsx, html, csv, json)  
- Optional `include_sections[]` to select modules  
- Optional `benchmark_period` (default 90 days)  
- Identity headers: `X-User-Id`, `X-Role`  

### Outputs
- `reports` entity with status, formats, storage URIs  
- Report sections per upstream module  
- `benchmark_results` comparison data  
- Download URLs for each format  
- Report generation metadata  

### Processing Logic
1. Verify FA-FR-001 through FA-FR-009 gates (partial allowed with skip flags)  
2. Load upstream data for each completed module  
3. Compose sections: ingestion, patterns, rates, classification, recurrence, correlation, die, wafer, prediction  
4. Include PROBABLE disclaimer for prediction section per BR-005  
5. Compute benchmark_results against historical baselines  
6. Render each requested export format  
7. Store artifacts in MinIO; persist report metadata  
8. Return report entity with download URLs  

### Dependencies
- FA-FR-001 through FA-FR-009 (read-only)  
- PostgreSQL, MinIO, Redis  
- PDF/XLSX rendering libraries  
- Downstream: none (terminal module)  

---

## 8. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| Performance | Report generation &lt; 3 min standard; format render &lt; 30 s each |
| Scalability | Async report jobs; MinIO horizontal scale |
| Availability | API N≥2; MinIO erasure coding in prod |
| Logging | JSON with report_id, formats, sections, duration_ms |
| Security | RBAC for report generation and download; artifact access tokens |
| Maintainability | Versioned report templates; Jinja2/HTML separation |
| Reliability | Idempotent re-generation; artifact checksums |
| Monitoring | Report generation latency; format failure rate |

---

## 9. AI Behavior Specification

### Role
Deterministic report composer with optional GPT executive summary — AI never alters upstream data values.

### Reasoning Strategy
Section assembly from upstream queries → template render → format export. GPT may generate executive summary prose from section data only.

### Workflow
Gate → Load Sections → Compose → Benchmark → Render → Store → Expose.

### Decision Logic
Missing upstream module → section marked SKIPPED with reason, not error. All formats requested are generated independently.

### Confidence Handling
Benchmark comparison includes confidence intervals where upstream modules provide them. Prediction section always includes PROBABLE disclaimer.

### Limitations
Report reflects upstream data at generation time; not live-updated until re-generated.

### Fallback Behaviour
PDF renderer unavailable → HTML + print CSS fallback. GPT unavailable → template executive summary without AI prose.

---

## 10. Input Specification

| Field | Type | Required | Validation | Example |
|-------|------|----------|------------|---------|
| dataset_id | UUID | Yes (or lot_id) | Upstream data exists | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| lot_id | string | Alt scope | Non-empty | `LOT-2026-0412` |
| report_template | string | No | standard/executive/detailed/custom | `standard` |
| export_formats | string[] | Yes | Subset of pdf,xlsx,html,csv,json | `["pdf","xlsx","html"]` |
| include_sections | string[] | No | Module names | `["ingestion","patterns","prediction"]` |
| benchmark_period | integer | No | Days, default 90 | `90` |
| include_executive_summary | boolean | No | Default true | `true` |
| X-User-Id | string | Prod | Non-empty | `fa-engineer-12` |

---

## 11. Output Specification

### Schema (report success — conceptual)
`report.id`, `status`, `formats_generated`, `sections[]`, `benchmark_results`, `download_urls{}`

### JSON Example

```json
{
  "report": {
    "id": "r1e2p3o4-r5t6-7890-abcd-ef1234567890",
    "dataset_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "lot_id": "LOT-2026-0412",
    "status": "completed",
    "report_template": "standard",
    "formats_generated": ["pdf", "xlsx", "html", "csv", "json"],
    "sections_included": 9,
    "sections_skipped": 0,
    "processing_duration_ms": 12400
  },
  "download_urls": {
    "pdf": "https://minio.example.com/reports/r1e2p3o4/report.pdf",
    "xlsx": "https://minio.example.com/reports/r1e2p3o4/report.xlsx",
    "html": "https://minio.example.com/reports/r1e2p3o4/report.html",
    "csv": "https://minio.example.com/reports/r1e2p3o4/report.csv",
    "json": "https://minio.example.com/reports/r1e2p3o4/report.json"
  },
  "benchmark_results": {
    "yield_vs_baseline_pct": -2.3,
    "failure_rate_vs_baseline_pct": 1.8,
    "benchmark_period_days": 90
  }
}
```

### Engineering Report
Self-referential: this module produces the report artifact itself.

### Dashboard Output
`/reports` report list, preview HTML, download buttons per format, benchmark comparison chart.

---

## 12. Business Rules

| ID | Rule |
|----|------|
| BR-001 | Report generation requires at least FA-FR-001 completed; other sections skipped if upstream incomplete. |
| BR-002 | All five export formats (PDF, XLSX, HTML, CSV, JSON) must be supported. |
| BR-003 | Report data is read-only from upstream modules; no re-computation. |
| BR-004 | Generated artifacts stored in MinIO with checksum and storage URI. |
| BR-005 | Prediction section MUST include PROBABLE disclaimer from FA-FR-009. |
| BR-006 | Benchmark results compare current lot against historical baseline for benchmark_period. |
| BR-007 | Each report generation appends immutable metadata to reports table. |
| BR-008 | Report templates are versioned; report metadata stores template_version. |

---

## 13. Key Engineering Rules

1. Never modify upstream FA-FR-001…009 data during report generation.  
2. Always include PROBABLE disclaimer in prediction section.  
3. All five formats generated from same section data (consistency).  
4. Artifact checksums verified on storage.  
5. Preserve semiconductor engineering terminology throughout.  
6. Skipped sections documented with reason, not silent omission.  
7. Persist all upstream run IDs in report lineage metadata.  

---

## 14. Constraints

| Constraint | Value / Policy |
|------------|----------------|
| Gate dependency | FA-FR-001 minimum; FA-FR-001–009 for full report |
| Export formats | PDF, XLSX, HTML, CSV, JSON (all five required) |
| Latency | &lt; 3 min standard report |
| Artifact storage | MinIO with SSE in prod |
| Template versions | Immutable once report generated |
| SQLite | Not supported for production |

---

## 15. API Specification

### Endpoint
`POST /api/v1/reports/generate`

### Method
POST (application/json)

### Headers
`X-User-Id`, `X-Role`; `Content-Type: application/json`

### Request
JSON with dataset_id or lot_id, export_formats, optional template and sections.

### Response
200 report entity + download_urls + benchmark_results.

### HTTP Codes
| Code | Meaning |
|------|---------|
| 200 | Success |
| 202 | Accepted (async large report) |
| 400/422 | Validation failure |
| 403 | RBAC denied |
| 424 | Minimum gate failed (no FA-FR-001) |
| 500 | Unexpected |

### Validation Errors
`MINIMUM_GATE_FAILED`, `DATASET_NOT_FOUND`, `INVALID_FORMAT`, `TEMPLATE_NOT_FOUND`, `RENDER_FAILURE`.

Additional endpoints: `GET /api/v1/reports`, `GET /api/v1/reports/{report_id}`, `GET /api/v1/reports/{report_id}/download/{format}`, `GET /api/v1/reports/templates`, `GET /api/v1/reports/benchmarks`, `DELETE /api/v1/reports/{report_id}` (soft delete).

---

## 16. Database Design

### Tables
`reports`, `report_sections`, `report_artifacts`, `report_templates`, `benchmark_results`, `report_generation_history`

### Columns (representative — `reports`)
`id` (PK UUID), `dataset_id`, `lot_id`, `report_template`, `template_version`, `status`, `formats_generated`, `storage_base_uri`, `checksum`, `upstream_run_ids_json`, `created_by`, `created_at`, `completed_at`

### Primary Keys
UUID PKs on all report tables.

### Foreign Keys
`report_sections.report_id` → `reports.id`; `report_artifacts.report_id` → `reports.id`; `benchmark_results.report_id` → `reports.id`.

### Indexes
`(dataset_id, created_at)`, `(lot_id)`, `(status)`, `(created_by)`.

### Relationships
One report → many sections, artifacts (one per format), one benchmark_results row.

### ER Explanation
Reports are terminal read-only compositions referencing all upstream module run IDs. Artifacts in MinIO; metadata in PostgreSQL.

---

## 17. Dashboard Integration

| Element | Detail |
|---------|--------|
| Screens | `/reports`, `/reports/{report_id}`, `/reports/templates`, `/reports/benchmarks` |
| User Actions | Generate report, select formats, preview HTML, download, compare benchmarks |
| Charts | Benchmark comparison bar, section completion status, format availability |
| Tables | Report history, section summary, download links |
| Filters | Lot, date range, template, status |
| Downloads | PDF, XLSX, HTML, CSV, JSON per report |
| Notifications | Toast on generation complete; async job polling |

---

## 18. AI Workflow

1. User configures report on `/reports` with lot and format selection.  
2. API verifies minimum FA-FR-001 gate; checks upstream module completion.  
3. Section composers load data from each completed FA module.  
4. Benchmark results computed against historical baseline.  
5. Templates rendered to PDF, XLSX, HTML, CSV, JSON.  
6. Artifacts stored in MinIO; metadata persisted.  
7. Optional GPT executive summary appended.  
8. User downloads report in preferred format.  

---

## 19. Error Handling

| Error Code | Description | Cause | Recovery | Severity |
|------------|-------------|-------|----------|----------|
| `MINIMUM_GATE_FAILED` | No FA-FR-001 data | No ingestion | Run ingestion first | High |
| `DATASET_NOT_FOUND` | Invalid dataset_id | Missing entity | Verify ID | Medium |
| `INVALID_FORMAT` | Unknown export format | Bad input | Use pdf/xlsx/html/csv/json | Medium |
| `TEMPLATE_NOT_FOUND` | Unknown template | Bad template name | Use standard | Medium |
| `RENDER_FAILURE` | PDF/XLSX render error | Library issue | Retry; HTML fallback | Medium |
| `STORAGE_ERROR` | MinIO upload fail | Infra issue | Retry | Critical |
| `SECTION_DATA_MISSING` | Upstream incomplete | Module not run | Section SKIPPED | Low |
| `DB_PERSIST_ERROR` | Commit failed | DB down | Retry | Critical |

---

## 20. Logging & Monitoring

- **Structured Logging:** report_id, formats, sections, benchmark, duration_ms  
- **Audit Logging:** report_generation_history append-only  
- **Performance Metrics:** render time per format, total generation ms  
- **Health Checks:** MinIO connectivity, PDF renderer availability  
- **Prometheus Metrics:** `fa_reports_generated_total`, `fa_report_render_duration_ms`, `fa_report_format_errors_total`  
- **Alerts:** render failure rate, storage errors, generation latency breach  

---

## 21. Security

| Area | Control |
|------|---------|
| Authentication | Gateway/OIDC; X-User-Id |
| Authorization | RBAC: generate, download, delete (soft) |
| Input Validation | Pydantic; format enum validation |
| Encryption | TLS; MinIO SSE at rest |
| Secrets Management | MinIO credentials in vault |
| OWASP | Download URLs time-limited signed; no path traversal in artifact paths |

---

## 22. Test Cases

| TC ID | Objective | Steps | Expected Result | Pass Criteria |
|-------|-----------|-------|-----------------|---------------|
| TC-010-01 | Generate full report | POST generate all formats | 200 completed | 5 formats in download_urls |
| TC-010-02 | PDF format valid | Download PDF | Valid PDF binary | Opens without error |
| TC-010-03 | XLSX format valid | Download XLSX | Valid XLSX | Sheets per section |
| TC-010-04 | PROBABLE disclaimer | Report with predictions | Disclaimer in PDF/HTML | BR-005 enforced |
| TC-010-05 | Benchmark results | Generate with benchmark_period | benchmark_results present | vs baseline computed |
| TC-010-06 | Partial upstream | Only FA-FR-001 complete | Sections skipped flagged | Not error; partial report |
| TC-010-07 | Minimum gate reject | No ingestion data | 424 | MINIMUM_GATE_FAILED |

---

## 23. Acceptance Criteria

1. Report generation requires at least FA-FR-001 completed.  
2. All five formats (PDF, XLSX, HTML, CSV, JSON) generated successfully.  
3. Report sections compose data from all completed upstream modules.  
4. Prediction section includes PROBABLE disclaimer.  
5. Benchmark results compare against historical baseline.  
6. Artifacts stored in MinIO with download URLs.  
7. Dashboard `/reports` lists reports with download actions.  

---

## 24. Risks & Assumptions

| Type | Item | Mitigation |
|------|------|------------|
| Technical | PDF rendering library compatibility | Pin versions; CI format tests |
| Technical | Large report timeout | Async job with 202 response |
| Business | Partial reports misinterpreted as complete | Section skip flags visible |
| Assumption | MinIO available for artifact storage | Hard dependency |
| Assumption | Upstream modules expose queryable run data | API contract documented |

---

## 25. Dependencies

| Kind | Dependency |
|------|------------|
| Internal | FA-FR-001 through FA-FR-009 (read-only) |
| External APIs | OpenAI GPT (optional executive summary) |
| Database | PostgreSQL |
| Infrastructure | MinIO, Redis, Docker/K8s |
| Libraries | FastAPI, SQLAlchemy, Pydantic, WeasyPrint/reportlab, openpyxl, Jinja2, Alembic, Pytest |

---

## 26. Traceability Matrix

| FR | Prompt / Spec | API | DB | Test Case | Acceptance Criteria |
|----|---------------|-----|----|-----------|---------------------|
| FA-FR-010 | This document | `/api/v1/reports/*` | reports, report_*, benchmark_results | TC-010-01…07 | §23 items 1–7 |

---

## 27. Reviewer Checklist

- [ ] All 28 sections present and non-empty  
- [ ] All five export formats documented  
- [ ] PROBABLE disclaimer in prediction section specified  
- [ ] Read-only upstream data policy enforced  
- [ ] Benchmark comparison logic documented  
- [ ] MinIO artifact storage specified  
- [ ] Test cases cover all formats and partial reports  
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
| 1.0 | 2026-07-17 | Initial Technical AI Agent Specification for FA-FR-010 |
