# PAT Parser (Vendor-Specific Pattern Files)

**Module:** `app/parsers/pat_parser.py`  
**Status:** Framework ready — **no vendor grammar registered**  
**Fixture:** `tests/fixtures/sample.pat` (detection-only, not a supported vendor format)

---

## Important

PAT is **not** a universal standard unlike STDF, STIL, or WGL. Pattern files vary by:

- Teradyne (IG-XL, UltraFlex, J750)
- Advantest (V93000, SmarTest)
- Customer proprietary generators

**No vendor PAT sample exists in this repository.** The parser framework detects PAT-like files and returns `unsupported_pat_format` with diagnostics instead of inventing grammar or placeholder metadata.

---

## Supported vendors

| Vendor | Version | Status |
|--------|---------|--------|
| *(none)* | — | Awaiting real `.pat` sample + validated grammar |

Register parsers via `register_pat_vendor_parser()` after Prompt 28 schema review.

---

## File detection

| Input | Rule |
|-------|------|
| `.pat` / `.pat.gz` | Extension + content signature (never extension alone) |
| Text signatures | `PAT_FILE`, `PATTERN`, `PAT_HEADER`, `VECTOR`, vendor markers (IG-XL, V93000, …) |
| Binary PAT | `.pat` extension + binary ratio heuristic, not STDF magic |

Rejected if content matches STDF, STIL, WGL, or ATE log markers.

---

## Parser behavior (current)

```
parse_pat_bytes()
  → identify vendor hint (diagnostics only)
  → if vendor in _SUPPORTED_PARSERS → vendor parser (none registered)
  → else PatUnsupportedFormat("PAT sample required …")
```

Error codes: `unsupported_pat_format`, `unsupported_vendor`, `malformed_grammar`, `corrupted_file`, `encoding_error`

---

## Extracted metadata (when vendor parser added)

Pattern name/id/revision, vector counts, scan chains, pins, timing — **only from real vendor grammar**, never inferred.

**Never extracted:** yield, failures, diagnosis, confidence, recommendations.

---

## Pipeline integration

- `file_detection.py` → `DetectedFormat.pat`
- `parse_worker.py` → routes PAT; fails at parse step with `PAT unsupported_pat_format: …`
- Audit: `parser_failed` / `upload_failed` via existing `_fail_job`
- Search: indexes PAT summaries when `format=pat` in `raw_summary_json` (future successful parses)
- MinIO: `metadata.json` when vendor parser succeeds (not written on unsupported failure)

---

## Verification (no vendor sample)

```bash
python scripts/build_pat_fixture.py
python -m pytest tests/test_pat_parser.py -v
```

Expected:

- Framework ready ✓  
- Detection routes `.pat` with `PAT_FILE` signature ✓  
- Parse returns `unsupported_pat_format` ✓  
- No fabricated pattern metadata ✓  

---

## Known limitations

- Zero vendor grammars implemented  
- Binary PAT formats only detected, not parsed  
- Vendor hint detection is best-effort for error messages only  

---

## Schema

See [`PAT_SCHEMA_EXTENSION.md`](PAT_SCHEMA_EXTENSION.md). Prompt 28 decides migrations based on real parser output.
