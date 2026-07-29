# STIL Parser — Schema Extension Candidates

**Date:** 2026-07-06  
**Status:** Prompt 28 confirmed — **no migration generated**

---

## Current storage (sufficient for Prompt 25)

| Data | Storage |
|------|---------|
| Pattern names, counts | `ai_log_summaries.patterns_found`, `raw_summary_json` |
| Scan structure metadata | `ai_log_summaries.scan_chains`, MinIO `scan-chains.json` |
| Full STIL parse tree | MinIO `{job_id}/metadata.json` |
| Search | `build_search_index()` reads STIL `raw_summary_json` |

Existing tables **`upload_jobs`**, **`ai_log_summaries`**, and MinIO parsed buckets accommodate all fields extracted today.

---

## Fields with no dedicated relational home (future candidates)

If relational querying or JOINs are required later, consider:

| Candidate table | Would store | Trigger |
|-----------------|-------------|---------|
| `pattern_definitions` | pattern name, vector count, WFT, source upload_job_id, module | Dashboard pattern-agent tab needs SQL filters across uploads |
| `scan_structure_defs` | chain name, length, scan in/out pins, compression | Cross-lot scan structure comparison |
| `timing_waveform_sets` | WFT name, period, signal waveform refs | Timing analysis dashboards |
| `stil_signal_catalog` | signal name, direction, width, groups | Signal-level search at scale |

**Not needed for Prompt 25** — JSON in MinIO + summary columns is enough for ingest, cache invalidation, and search.

---

## Explicitly out of scope

- Vector bit patterns (too large; belongs in object storage if ever persisted)
- Pass/fail/yield (STDF / log domain)
- Pattern embeddings / AI features (Stage 8+)

---

## Recommendation

Ship with existing schema. Revisit `002_parser_facts.py` only when a dashboard tab requires SQL aggregation over STIL fields that JSON extraction cannot serve efficiently.
