# VERILUMEN — Real Parser Build Prompt (Prompt 7, scoped: STDF + LOG)

> **Status: DONE (2026-07-06)**  
> **Full prompt archive:** [`../ALL_PROMPTS.md`](../ALL_PROMPTS.md) — see **P7**, **P25–P27**, **P28**

---

## What shipped

| Component | Path |
|---|---|
| File-type detection | `app/parsers/file_detection.py` |
| STDF parser (stdf-tamer, Apache 2.0) | `app/parsers/stdf_parser.py` |
| LOG parser (regex, vendor-tolerant) | `app/parsers/log_parser.py` |
| STIL parser | `app/parsers/stil_parser.py` (P25) |
| WGL parser | `app/parsers/wgl_parser.py` (P26) |
| PAT framework | `app/parsers/pat_parser.py` (P27) |
| Metadata upsert | `app/services/metadata_upsert.py` |
| Parse worker | `app/workers/parse_worker.py` |
| Fixtures | `tests/fixtures/sample.stdf`, `sample_ate.log`, `sample.stil`, `sample.wgl` |
| Tests | `tests/test_parsers.py`, `tests/test_pat_parser.py` |

**No new DB tables** — uses existing `scan_chain_failures`, `ai_log_summaries`, dimension tables.

## Verify locally

```powershell
cd backend
pip install -r requirements.txt
python scripts/build_stdf_fixture.py   # if sample.stdf missing
python -m pytest tests/test_parsers.py -v
```
