# STIL Parser (IEEE 1450)

**Module:** `app/parsers/stil_parser.py`  
**Detection:** `app/parsers/file_detection.py` → `DetectedFormat.stil`  
**Worker routing:** `app/workers/parse_worker.py`  
**Fixture:** `tests/fixtures/sample.stil` (generate via `python scripts/build_stil_fixture.py`)

---

## Supported grammar (IEEE Std 1450-1999 / STIL 1.0)

| Block | Extracted metadata |
|-------|-------------------|
| `STIL version;` | Version string (1.x) |
| `Header { }` | Title, Date, Source, other quoted fields |
| `Signals { }` | Signal name, direction (In/Out/InOut/Supply/Pseudo), optional width |
| `SignalGroups { }` | Group name → expression |
| `Timing { WaveformTable … }` | Waveform table name, Period, clock frequency estimate |
| `ScanStructures { … }` | Chain name, ScanLength, ScanIn/Out/Enable, compression, order |
| `Pattern <name> { }` | Pattern name, WFT reference, vector/cycle counts |
| `PatternBurst`, `PatternExec` | Named burst/exec blocks |
| `MacroDefs`, `Procedures` | Macro/procedure names |
| `Spec`, `Core` | Block presence counted (minimal body parsing) |

Named block form is supported: `Pattern core_scan_pat { … }`.

---

## Unsupported grammar

| Construct | Behaviour |
|-----------|-----------|
| Vendor blocks (`CTLMode`, `EdtRules`, `SVF`, `Tessent`, …) | **Error:** `StilUnsupportedExtension` — logged warning, parse fails |
| STIL 1.1 blocks (`Environment`, `Selector`, …) in 1.0 files | Warning logged; block skipped |
| STIL 2.x / unknown major version | **Error:** `StilUnsupportedVersion` |
| Missing `STIL x.x;` header | **Error:** `StilMalformedGrammar` |
| Unclosed `{` / invalid structure | **Error:** `StilMalformedGrammar` |
| Invalid `.stil.gz` payload | **Error:** `StilCorruptedFile` |

---

## Extracted fields (not inferred)

**Pattern metadata:** name, timing WFT, vector count, cycle count, pattern length  
**Scan information:** chain name, length, scan in/out/enable, compression, order, capture/shift cycles (when present)  
**Signals:** names, direction, width; classified clock/reset/control lists  
**Timing:** waveform tables, period, estimated clock frequency  

**Explicitly NOT extracted (STDF domain):** pass, fail, yield, failures, root cause, die results.

---

## Parser flow

```
Upload (.stil / .stil.gz)
    → file_detection (extension + STIL header signature)
    → parse_worker: validate → parse → extract → ai → store
    → stil_parser.parse_stil_bytes()
    → ai_log_summaries (patterns_found, scan_chains, raw_summary_json)
    → MinIO: summary.json, scan-chains.json (structure metadata), metadata.json (full parse)
    → Redis: progress + parser_warning events
    → Cache: dash:*, dash:scan-chain*, search:index:v1
    → Search index: pattern names, scan chains, signals from STIL summaries
```

No `scan_chain_failures` rows are created for STIL — pattern files define structure, not test outcomes.

---

## File detection

| Input | Method |
|-------|--------|
| `.stil` | Extension + `STIL x.x;` header or IEEE block signature |
| `.stil.gz` | Gzip decompress → inner `.stil` rules |
| Content | Must match `STIL version;` — never guessed from extension alone for ambiguous types |

---

## Known limitations

- Vector **data** is counted, not stored (avoids large MinIO payloads and fake vectors).
- STIL 1.1-only constructs are warned/skipped, not fully parsed.
- `Spec` / `Core` blocks are recognized but not deeply interpreted.
- Deeply nested vendor grammar inside standard blocks is not validated.

---

## Schema extension candidates

See [`STIL_SCHEMA_EXTENSION.md`](STIL_SCHEMA_EXTENSION.md). No migration is created automatically — current storage uses `ai_log_summaries.raw_summary_json` and MinIO `metadata.json`.

---

## Testing

```bash
python scripts/build_stil_fixture.py
python -m pytest tests/test_stil_parser.py -v
```

---

## Verification checklist (live stack)

1. Upload `tests/fixtures/sample.stil` via presign → complete  
2. Job status `Completed`, `file_type=stil`  
3. MinIO parsed: `summary.json`, `scan-chains.json`, `metadata.json`  
4. `ai_log_summaries.patterns_found = 1`, `scan_chains = 1`  
5. Dashboard/search cache invalidated  
6. Audit events written (Prompt 32)  
7. `GET /search` includes pattern `core_scan_pat`
