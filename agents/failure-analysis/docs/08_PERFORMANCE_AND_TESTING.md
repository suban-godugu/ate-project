# 08 — Performance and Testing

**Related:** [01 System Architecture](01_SYSTEM_ARCHITECTURE.md) · [05 AI Architecture](05_AI_ARCHITECTURE.md) · [09 Deployment](09_DEPLOYMENT_GUIDE.md)

---

## 1. Purpose

Define performance targets, scalability approach, benchmarking fields, and the test strategy for FA-FR-001→010.

## 2. Performance Targets

| Scenario | Target |
|----------|--------|
| Upload acknowledge (async process) | &lt; 2s |
| Validation (typical files) | &lt; 5s |
| Retrieval APIs (p95) | &lt; 2s |
| Heavy analytics | Prefer async / background |
| Report generation | &lt; 10s or queued |
| Batch ingestion | 100k+ records (set-based inserts) |
| Max file size | Up to multi-GB (`MAX_UPLOAD_BYTES`) |

## 3. Scalability

| Dimension | Strategy |
|-----------|----------|
| API | Stateless horizontal replicas behind LB |
| Workers | Scale on queue depth / CPU |
| PostgreSQL | Vertical scale + read replicas + partition audits at volume |
| Objects | MinIO distributed / S3 |
| UI | CDN for static assets; Next.js replicas |
| Algorithms | Set-based aggregation; avoid dense matrices unless needed |

Module independence allows separate worker pools (e.g. reporting vs spatial) as load grows. See [02 Software Design](02_SOFTWARE_DESIGN_SPECIFICATION.md) for queue/worker design.

## 4. Benchmarking

Production audits persist benchmark payloads, commonly including:

- `processing_ms`, load / compute / persist timings  
- Throughput (records/s)  
- CPU / memory samples (where collected)  
- `api_sla_met`  
- Completeness / consistency scores (reports)  
- Precision / recall / F1 when ground truth is supplied (evaluation / prediction)

Surface benchmarks in module history APIs and FA-FR-010 `benchmark_results`.

## 5. Testing Strategy

| Layer | Scope |
|-------|-------|
| Unit | Engines (deterministic scoring, clustering, rates) |
| API | FastAPI route contracts, RBAC, 422 lineage gates |
| Integration | Alembic schema + repository persist |
| Evaluation | Metrics harness in `evaluation/` |
| E2E | Playwright (`ate-dashboard/e2e/`) |

### Primary test modules

| Area | Tests (examples) |
|------|------------------|
| Ingestion | `tests/test_fa_fr_001_ingestion.py`, `test_phase1_ingestion.py`, `test_phase7_ingestion_api.py` |
| Patterns | `tests/test_fa_fr_002_pattern_detection.py`, `test_phase8_pattern_detection.py` |
| Rates | `tests/test_fa_fr_003_failure_rates.py`, `test_phase9_failure_rates.py` |
| Recurrence | `tests/test_fa_fr_005_recurrence.py` (and related phase tests) |
| Correlation | `tests/test_fa_fr_006_correlation.py`, `test_phase12_correlation.py` |
| Die / Wafer | `tests/test_fa_fr_007_die_analysis.py`, `tests/test_fa_fr_008_wafer_analysis.py` |
| Prediction | `tests/test_fa_fr_009_fault_prediction.py` |
| Reporting | `tests/test_fa_fr_010_reporting.py`, `test_phase16_reporting.py` |
| CLI phases | `test_phase2_analytics.py`, `test_phase3_die_wafer.py`, … |

### Commands

```powershell
# Ensure schema
$env:PYTHONPATH = (Get-Location).Path
python -m alembic upgrade head

# Module / phase tests
python -m unittest tests.test_fa_fr_001_ingestion -v
python -m unittest tests.test_fa_fr_010_reporting tests.test_phase16_reporting -v

# Evaluation
python -m evaluation.cli --discover-only

# Dashboard E2E (from ate-dashboard)
npm run test:e2e
```

## 6. Quality Metrics (AI / analytics)

- Classification / prediction: accuracy, precision, recall, F1, top-k  
- Correlation / hotspot / cluster accuracy vs fixtures  
- Report completeness and consistency scores  
- Ops: error rate, queue lag, DB p95  

Regression gates should fail CI when critical SLAs or metric floors regress.

## 7. Cross-References

- Observability → [01](01_SYSTEM_ARCHITECTURE.md)
- AI evaluation → [05](05_AI_ARCHITECTURE.md)
- Deploy sizing → [09](09_DEPLOYMENT_GUIDE.md)
