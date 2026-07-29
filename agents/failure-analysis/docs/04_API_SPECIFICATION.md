# 04 — API Specification

**Related:** [01 System Architecture](01_SYSTEM_ARCHITECTURE.md) · [02 Software Design](02_SOFTWARE_DESIGN_SPECIFICATION.md) · [07 Security](07_SECURITY_ARCHITECTURE.md) · [10 User Guide](10_USER_GUIDE.md)

Interactive OpenAPI: `http://localhost:8000/docs` (when API is running). Base prefix: `/api/v1`.

---

## 1. Conventions

| Topic | Convention |
|-------|------------|
| Content type | `application/json` (multipart for uploads) |
| Auth (production) | Gateway headers `X-User-Id`, `X-Role` (see [07](07_SECURITY_ARCHITECTURE.md)) |
| Errors | `{ "detail": { "code", "message", "issues": [...] } }` |
| Async | Many POST endpoints accept `async_execution` / background processing |
| Legacy | Upload-only or older prefixes; prefer production paths |

## 2. Health

| Method | Path | Response |
|--------|------|----------|
| GET | `/health` | `{ "status": "ok", "service": "failure-analysis-api" }` |

## 3. Production Pipeline Endpoints

### FA-FR-001 Ingestion — `/api/v1`

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/uploads` | Upload file |
| GET | `/uploads`, `/uploads/{id}` | List / detail |
| GET | `/uploads/{id}/metadata`, `/uploads/{id}/records` | Metadata / records |
| DELETE | `/uploads/{id}` | Soft/hard delete per policy |
| POST | `/datasets/upload`, `/datasets/scan` | Dataset upload / server scan |
| GET | `/datasets`, `/datasets/{id}` | Dataset list / detail |
| GET | `/ingestion/statistics` | Parser/ingestion stats |

### FA-FR-002 Patterns — `/api/v1/patterns`

| Method | Path |
|--------|------|
| POST | `/detect` (production), `/analyze` (legacy-compatible) |
| GET | `/`, `/statistics`, `/history`, `/top`, `/{pattern_row_id}` |

### FA-FR-003 Failure rates — `/api/v1/failure-rate`

| Method | Path |
|--------|------|
| POST | `/compute` |
| GET | `/`, `/trends`, `/statistics`, `/history`, `/{pattern_id}` |

### FA-FR-004 Classification — `/api/v1/classification`

| Method | Path |
|--------|------|
| POST | `/analyze` |
| GET | `/`, `/statistics`, `/{fault_id}` |

### FA-FR-005 Recurrence — `/api/v1/recurrence`

| Method | Path |
|--------|------|
| POST | `/analyze` |
| GET | `/`, `/trends`, `/hotspots`, `/history`, `/statistics`, `/{recurrence_id}` |

### FA-FR-006 Correlation — `/api/v1/correlation`

| Method | Path |
|--------|------|
| POST | `/analyze` |
| GET | `/`, `/history`, `/statistics`, `/trends`, `/matrix`, `/network`, `/{correlation_id}` |
| POST | `/legacy/analyze` (compatibility) |

### FA-FR-007 Die — `/api/v1/die-analysis`

| Method | Path |
|--------|------|
| POST | `/analyze` (`legacy=true` supported) |
| GET | `/`, `/hotspots`, `/clusters`, `/statistics`, `/{die_result_id}` |

### FA-FR-008 Wafer — `/api/v1/wafer-analysis`

| Method | Path |
|--------|------|
| POST | `/analyze` (`legacy=true` supported) |
| GET | `/`, `/hotspots`, `/statistics`, `/yield`, `/{wafer_result_id}` |

### FA-FR-009 Fault prediction — `/api/v1/fault-prediction`

| Method | Path |
|--------|------|
| POST | `/predict`, `/feedback` |
| GET | `/`, `/history`, `/statistics`, `/{prediction_id}` |

### FA-FR-010 Reports — `/api/v1/reports`

| Method | Path |
|--------|------|
| POST | `/generate`, `/export` |
| GET | `/`, `/history`, `/templates`, `/{report_id}` |
| GET | `/download/{pdf\|excel\|json\|html\|csv}` |

## 4. Legacy Compatibility Prefixes

| Prefix | Notes |
|--------|-------|
| `/api/v1/failure-rates` | Older rate calculate / dashboard |
| `/api/v1/recurring` | Older recurrence |
| `/api/v1/die`, `/api/v1/wafer` | Older spatial APIs |
| `/api/v1/root-cause` | Older prediction |

Use production prefixes for new integrations.

## 5. Evaluation & Workbench

| Prefix | Purpose |
|--------|---------|
| `/api/v1/evaluation` | Datasets, run evaluation, download reports |
| `/api/v1/workbench` | Overview, improvements, logs, visualizations, health |

## 6. Typical Request Shape (production analyze)

```json
{
  "dataset_id": "optional-uuid",
  "upload_id": "optional-uuid",
  "async_execution": false,
  "thresholds": {}
}
```

Provide exactly one of `dataset_id` or `upload_id` where required. Incomplete upstream lineage → `422` with issue codes such as `INVALID_*_SOURCE`.

## 7. Typical Success Shape

```json
{
  "status": "completed",
  "analysis_id": "...",
  "execution_id": "...",
  "results": {},
  "benchmarks": {
    "processing_ms": 0,
    "api_sla_met": true
  }
}
```

Exact fields vary by module; see OpenAPI schemas and Pydantic models under each package’s `schemas.py`.

## 8. Error Codes (common)

| Code pattern | Meaning |
|--------------|---------|
| `*_ACCESS_DENIED` | RBAC failure |
| `INVALID_*_SOURCE` | Missing/incomplete lineage |
| `RATE_LIMITED` | Too many requests |
| `NOT_FOUND` | Unknown id |
| `VALIDATION_ERROR` | Payload/schema issues |

## 9. Cross-References

- DTOs & services → [02](02_SOFTWARE_DESIGN_SPECIFICATION.md)
- RBAC headers → [07](07_SECURITY_ARCHITECTURE.md)
- Dashboard consumption → [10](10_USER_GUIDE.md)
