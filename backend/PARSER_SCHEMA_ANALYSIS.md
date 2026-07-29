# Parser-Driven Schema Analysis (Prompt 28)

**Date:** 2026-07-06  
**Decision:** **No migration required** — all implemented parser output fits existing tables and MinIO JSON artifacts.

---

## Method

1. Inspected `app/parsers/{stdf,log,stil,wgl,pat}_parser.py` result types and `to_summary_dict()` / `to_metadata_dict()` output.
2. Traced `parse_worker.py` writes to PostgreSQL and MinIO.
3. Compared against SQLAlchemy models and Alembic migrations `001`–`003`.
4. Ran fixtures (`tests/fixtures/sample.{stdf,stil,wgl,pat,ate.log}`) to confirm real field shapes.

**Note:** The prompt example referenced `pattern` and `scan_chain` tables — those **do not exist** in this repository. Pattern and scan *definitions* from STIL/WGL/PAT are stored in MinIO JSON; pattern *identifiers* from STDF/LOG failures go to `scan_chain_failures.pattern_id`.

Migration `003` is already **`003_rl_training.py`**. A future parser migration would be **`004_parser_schema_extensions.py`**, not `003`.

---

## Summary table

| Parser | Extracted fields (representative) | Current destination | Needs new table? | Reason |
|--------|--------------------------------|---------------------|------------------|--------|
| **STDF** | `lot_id`, `product_code`, `tester_code`, `test_program` | `lots`, `products`, `testers`, `upload_jobs` (via metadata upsert) | **No** | Core dimension tables |
| STDF | `wafer_results` (yield, part counts) | `wafers` | **No** | Upserted per wafer |
| STDF | `yield_pct`, `patterns` (set), record counts | `ai_log_summaries` | **No** | Summary columns + `raw_summary_json` |
| STDF | `failures[]` (chain, pattern, cycle, root cause) | `scan_chain_failures` | **No** | Relational failure rows |
| **LOG** | lot/wafer/tester/product, counts, yield, cost | `lots`, `wafers`, … + `ai_log_summaries` | **No** | Same pattern as STDF summary path |
| LOG | `failures[]` | `scan_chain_failures` | **No** | Same as STDF failures |
| **STIL** | pattern/scan/signal counts, names | `ai_log_summaries.patterns_found`, `scan_chains`, `raw_summary_json` | **No** | Summary + searchable JSON |
| STIL | signals, waveform_tables, timing_sets, scan_structures, patterns (full) | MinIO `{job_id}/metadata.json`, `scan-chains.json` | **No** | Object storage by design |
| **WGL** | pattern/pin/waveform counts, names | `ai_log_summaries` + `raw_summary_json` | **No** | Same as STIL summary path |
| WGL | pins, waveforms, timing_sets, scan_chains (full) | MinIO `metadata.json`, `waveforms.json`, `scan-chains.json` | **No** | Object storage by design |
| **PAT** | *(none — framework only)* | `upload_jobs.error_message`, audit logs on failure | **No** | No successful parse yet |

**Migration required:** **NO**

---

## Per-parser field mapping

### STDF (`StdfParseResult`)

| Field | Destination | Migration |
|-------|-------------|-----------|
| `lot_id` | `lots.lot_code` | No |
| `product_code` | `products.code` | No |
| `tester_code` | `testers.code`, `fabs` (via upsert) | No |
| `wafer_results[]` | `wafers` (yield, good/bad/total dies) | No |
| `yield_pct`, `patterns`, `raw_record_counts` | `ai_log_summaries` | No |
| `failures[]` | `scan_chain_failures` | No |

### LOG (`LogParseResult`)

| Field | Destination | Migration |
|-------|-------------|-----------|
| Context IDs + counts | metadata upsert + `ai_log_summaries` | No |
| `estimated_cost`, `estimated_savings` | `ai_log_summaries` | No |
| `failures[]` | `scan_chain_failures` | No |
| `raw_fields` | `ai_log_summaries.raw_summary_json` | No |

### STIL (`StilParseResult`)

| Field | Destination | Migration |
|-------|-------------|-----------|
| `patterns_found`, `scan_chains`, header title/source | `ai_log_summaries` + `raw_summary_json` | No |
| `waveform_tables`, `timing_sets` | MinIO `metadata.json` | No |
| `scan_structures`, `patterns`, `signals` | MinIO `metadata.json` + `scan-chains.json` | No |
| `clock_signals`, `reset_signals`, `control_signals` | MinIO `metadata.json` | No |

### WGL (`WglParseResult`)

| Field | Destination | Migration |
|-------|-------------|-----------|
| Summary counts/names | `ai_log_summaries.raw_summary_json` | No |
| `waveforms`, `timing_sets` | MinIO `waveforms.json` + `metadata.json` | No |
| `scan_chains`, `pins`, `patterns` | MinIO `metadata.json` + `scan-chains.json` | No |

### PAT (`PatParseResult`)

| Field | Destination | Migration |
|-------|-------------|-----------|
| All fields | *(not produced — parse fails with `unsupported_pat_format`)* | No |
| Failure diagnostics | `upload_jobs.error_message`, `audit_logs` | No |

---

## Candidate tables evaluated (Prompt 28 list)

| Candidate | Can existing storage hold it? | Create? | Notes |
|-----------|------------------------------|---------|-------|
| `pattern_results` | Yes — `scan_chain_failures`, `ai_log_summaries.raw_summary_json` | **No** | STDF failures are test results, not pattern defs |
| `scan_cells` | Yes — MinIO `scan-chains.json` | **No** | STIL/WGL scan *definitions*, not die-level cells |
| `die_results` | Partial — `wafers` has aggregate yield only | **Defer** | STDF parser does not emit per-die coordinates today |
| `test_cost_events` | Yes — `ai_log_summaries.estimated_cost` | **No** | LOG only; no event stream needed yet |
| `waveform_metadata` | Yes — MinIO `waveforms.json` | **No** | WGL timing/waveform detail |
| `timing_metadata` | Yes — MinIO `metadata.json` | **No** | STIL/WGL timing_sets |
| `signal_metadata` | Yes — MinIO `metadata.json` | **No** | STIL signals / WGL pins |
| `pattern_vectors` | N/A — not extracted | **No** | Explicitly out of parser scope |
| `mbist_failures` | N/A — not extracted | **No** | LOG mentions block counts only |
| `lbist_sessions` | N/A — not extracted | **No** | Same |
| `wafer_defect_uploads` | Separate upload module | **No** | Not parser output |

**Interim dashboard bridge:** `module_fact_rows` (`002_module_fact_rows.py`) remains for seeded dashboard rows until SQL analytics require normalized fact tables.

---

## When to revisit (future `004_parser_schema_extensions.py`)

Create relational tables **only** when a dashboard or API requirement needs SQL JOINs across uploads that JSONB extraction cannot serve efficiently, for example:

- Cross-lot pattern catalog search with filters on `pattern_group`, `vector_count`, `timing_wft`
- Per-die spatial heatmaps (`die_results` with x/y coordinates from STDF PIR/PRR)
- Cost event timelines with multiple rows per lot

Until then: **MinIO parsed JSON + `ai_log_summaries` + `scan_chain_failures` is sufficient.**

---

## Verification matrix

| Parser | Field | Destination table / store | Migration required |
|--------|-------|---------------------------|--------------------|
| STDF | lot_id | `lots` | NO |
| STDF | pattern_id (failure) | `scan_chain_failures` | NO |
| STDF | yield_pct | `ai_log_summaries`, `wafers` | NO |
| LOG | patterns_found | `ai_log_summaries` | NO |
| STIL | waveform_tables | MinIO `metadata.json` | NO |
| STIL | scan_structures | MinIO `scan-chains.json` | NO |
| WGL | waveforms | MinIO `waveforms.json` | NO |
| WGL | timing_sets | MinIO `metadata.json` | NO |
| PAT | all metadata | *(none yet)* | NO |

---

## Actions taken (Prompt 28)

- Created this report
- Created `DATABASE_SCHEMA.md` (actual schema reference)
- Created `tests/test_schema_extensions.py` (mapping + optional DB round-trip)
- **Did not** create `003_parser_schema_extensions.py` (not needed; `003` is RL training)
- **Did not** modify `metadata_upsert.py` or `parse_worker.py` (no new tables)
