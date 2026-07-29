# PAT Parser — Schema Extension Candidates

**Date:** 2026-07-06  
**Status:** Prompt 28 confirmed — **no migration** (PAT still produces no DB writes)

---

## Current state (Prompt 27)

No PAT vendor parser is registered. **No database writes** occur on PAT upload failure.

Existing tables suffice for the framework:

| Need | Storage |
|------|---------|
| Failed upload diagnostics | `upload_jobs.error_message`, audit logs |
| Future PAT metadata | `ai_log_summaries.raw_summary_json`, MinIO `metadata.json` |

---

## Candidates after real vendor PAT parsing (Prompt 28+)

| Table | When needed |
|-------|-------------|
| `pattern_definitions` | SQL filters across PAT uploads by pattern name/group |
| `vendor_pat_catalog` | Track vendor, version, generator per upload |
| `pat_scan_chain_defs` | Relational scan chain queries |

**Do not create until** STIL + WGL + PAT parsers produce fields that JSON/MinIO cannot serve.

---

## Out of scope

- Vector bit storage  
- Test result inference (STDF)  
- Speculative columns before parser validation
