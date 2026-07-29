# VERILUMEN Database Schema

**Source of truth:** SQLAlchemy models in `app/models/` and Alembic migrations `001`–`003`.  
**Last reviewed:** Prompt 28 (2026-07-06) — parser-driven; no speculative tables.

---

## Migration chain

| Revision | File | Purpose |
|----------|------|---------|
| `001_initial` | `001_initial_schema.py` | Core dimensions, auth, uploads, analytics, recommendations |
| `002_module_fact_rows` | `002_module_fact_rows.py` | Dashboard seed/fact row bridge (`module_fact_rows`) |
| `003_rl_training` | `003_rl_training.py` | RL metrics on `recommendations`, `recommendation_training_runs` |

**Head:** `003_rl_training`  
**Parser extension migration:** Not required as of Prompt 28. Future grouped migration would be `004_parser_schema_extensions.py` if parser output outgrows JSONB/MinIO storage.

---

## Core dimensions

| Table | Key columns | Parser usage |
|-------|-------------|--------------|
| `fabs` | `code`, `name` | STDF/LOG tester-derived fab |
| `testers` | `code`, `name`, `platform`, `fab_id` | STDF/LOG `tester_code` |
| `products` | `code`, `name` | STDF/LOG `product_code` |
| `lots` | `lot_code`, `product_id`, `fab_id` | STDF/LOG `lot_id` |
| `wafers` | `wafer_code`, `lot_id`, yield/die counts | STDF wafer results |

---

## Upload pipeline

| Table | Key columns | Parser usage |
|-------|-------------|--------------|
| `upload_jobs` | status, file metadata, FKs to lot/wafer/… | One row per upload |
| `upload_pipeline_steps` | `step_key`, `status`, `meta` (JSONB) | validate → parse → extract → ai → store |
| `ai_log_summaries` | counts, yield, cost, **`raw_summary_json`** (JSONB) | STDF/LOG/STIL/WGL summaries |

### `ai_log_summaries` parser columns

| Column | STDF | LOG | STIL | WGL |
|--------|------|-----|------|-----|
| `patterns_found` | ✓ | ✓ | ✓ | ✓ |
| `scan_chains` | ✓ (failure count) | ✓ | ✓ | ✓ |
| `wafer_count` | ✓ | ✓ | — | — |
| `defects_found` | ✓ | ✓ | — | — |
| `yield_pct` | ✓ | ✓ | — | — |
| `estimated_cost` / `estimated_savings` | — | ✓ | — | — |
| `raw_summary_json` | ✓ | ✓ | ✓ | ✓ |

Full STIL/WGL/PAT detail (signals, waveforms, timing, scan definitions) lives in **MinIO** parsed bucket:

- `{job_id}/summary.json`
- `{job_id}/scan-chains.json`
- `{job_id}/metadata.json` (STIL, WGL)
- `{job_id}/waveforms.json` (WGL)

---

## Analytics & failures

| Table | Key columns | Parser usage |
|-------|-------------|--------------|
| `scan_chain_failures` | `chain_id`, `pattern_id`, `fail_cycle`, `root_cause`, lot/wafer FKs | STDF + LOG **test failures** (not STIL/WGL scan definitions) |
| `kpi_snapshots` | module KPIs with dimension FKs | Dashboard aggregates |
| `wafer_defect_uploads` | defect class, images | Wafer analysis module (not file parsers) |
| `alerts` | severity, lot/wafer FKs | Dashboard |
| `module_fact_rows` | `module`, `tab`, `row_data` (JSONB) | Interim dashboard facts |

---

## Auth & audit

| Table | Purpose |
|-------|---------|
| `users`, `user_preferences` | Auth + theme/account/filter prefs |
| `audit_logs` | Login, upload, parser, export events |

---

## Recommendations & RL

| Table | Purpose |
|-------|---------|
| `recommendations` | AI recommendation rows (+ RL columns from `003`) |
| `recommendation_feedback` | User apply/reject/ignore |
| `recommendation_training_runs` | RL training run history (`003`) |

---

## Tables that do **not** exist (by design)

These were considered in Prompt 28 and deferred until parser output requires relational storage:

- `pattern` / `pattern_definitions`
- `scan_chain` (definition table — distinct from `scan_chain_failures`)
- `waveform_metadata`, `timing_metadata`, `signal_metadata`
- `pattern_results`, `scan_cells`, `die_results`, `test_cost_events`
- `mbist_failures`, `lbist_sessions`

See [`PARSER_SCHEMA_ANALYSIS.md`](PARSER_SCHEMA_ANALYSIS.md) for the full field-by-field mapping.

---

## Indexes (selected)

| Index | Table |
|-------|-------|
| `idx_upload_jobs_status` | `upload_jobs` |
| `idx_kpi_snapshots_filter` | `kpi_snapshots` |
| `idx_wafer_defect_class` | `wafer_defect_uploads` |
| `idx_alerts_created`, `idx_alerts_lot` | `alerts` |
| `idx_module_fact_rows_module` | `module_fact_rows` |
| `idx_rec_feedback_agent` | `recommendation_feedback` |
| `idx_rec_training_rec` | `recommendation_training_runs` |
