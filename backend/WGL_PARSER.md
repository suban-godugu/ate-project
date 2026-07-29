# WGL Parser (Waveform Generation Language)

**Module:** `app/parsers/wgl_parser.py`  
**Detection:** `DetectedFormat.wgl` in `file_detection.py`  
**Worker:** `parse_worker.py` routes WGL uploads to `parse_wgl_bytes()`  
**Fixture:** `tests/fixtures/sample.wgl` via `python scripts/build_wgl_fixture.py`

Grammar reference: TSSI Waveform Generation Language (TDS Languages Guide) — `waveform` … `end` program structure.

---

## Supported grammar

| Block | Extracted metadata |
|-------|-------------------|
| `waveform` program wrapper | Program validity |
| `!` / `#` comments | Header: Title, Device, Tester, Pattern-Group, etc. |
| `signal` … `end` | Pin name, direction (input/output/bidir/mux) |
| `timeplate` … `end` | Name, period, drive/compare edge states, frequency estimate |
| `pattern` … `end` | Name, vector count, cycle count, timeplate reference |
| `scanChain` … `end` | Chain name, members, scan in/out |
| `pingroup`, `subroutine` | Group names, procedure names (presence) |

---

## Unsupported / vendor extensions

Unknown or vendor blocks (e.g. `CTLMode`, `EdtRules`) are **logged as warnings**, skipped, and listed in `unsupported_extensions`. Parsing **continues** for supported blocks (unlike STIL vendor blocks which fail hard).

---

## Extracted metadata (not inferred)

- Pattern name, group, category, vector/cycle counts  
- Waveform tables, periods, timing sets  
- Pin/signal definitions, clock/reset/enable classification  
- Scan chain structure (not test failures)  

**Not extracted:** yield, pass/fail, diagnosis, confidence, root cause.

---

## Pipeline flow

```
.wgl / .wgl.gz upload
  → detect_file_format (extension + `waveform` header, not STIL)
  → parse_wgl_bytes
  → ai_log_summaries (patterns_found, scan_chains, raw_summary_json)
  → MinIO: summary.json, scan-chains.json, metadata.json, waveforms.json
  → Redis progress + parser_warning events
  → Cache: dash:*, dash:scan-chain*, search:index:v1
  → Search: pattern names, waveforms, pins, scan chains
```

No `scan_chain_failures` rows — WGL defines waveforms/patterns, not test outcomes.

---

## Known limitations

- Vector bit data is counted, not stored.  
- Nested subroutines inside patterns are not fully interpreted.  
- Vendor dialects beyond TSSI core blocks may appear only in warnings.  
- Equation-specific blocks (`equationsheet`, `pmode`) are recognized but minimally parsed.

---

## Schema

See [`WGL_SCHEMA_EXTENSION.md`](WGL_SCHEMA_EXTENSION.md). No migration required for Prompt 26.

---

## Testing

```bash
python scripts/build_wgl_fixture.py
python -m pytest tests/test_wgl_parser.py -v
```
