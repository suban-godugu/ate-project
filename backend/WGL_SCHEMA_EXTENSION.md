# WGL Parser — Schema Extension Candidates

**Date:** 2026-07-06  
**Status:** Prompt 28 confirmed — **no migration generated**

---

## Current storage (sufficient for Prompt 26)

| Data | Storage |
|------|---------|
| Pattern / pin / scan counts | `ai_log_summaries` columns + `raw_summary_json` |
| Full WGL parse | MinIO `{job_id}/metadata.json` |
| Waveform timing metadata | MinIO `{job_id}/waveforms.json` |
| Scan structure | MinIO `{job_id}/scan-chains.json` |
| Search | `build_search_index()` from `raw_summary_json` |

---

## Future relational candidates (only if SQL analytics required)

| Table | Purpose |
|-------|---------|
| `waveform_definitions` | WFT name, period, drive/compare states per upload |
| `wgl_pattern_catalog` | Pattern name, vector count, timeplate link |
| `wgl_scan_chain_defs` | Chain topology from WGL scanChain blocks |

**Recommendation:** Continue using JSON in MinIO + summary columns until dashboard tabs require JOINs across uploads.

---

## Out of scope

- Raw vector storage (object storage only if ever needed)  
- Test result inference (STDF/log)  
- AI embeddings (Stage 8+)
