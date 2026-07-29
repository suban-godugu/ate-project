# VERILUMEN — Enterprise Parser Prompts (DO NOT RUN AS-IS)

> **Full prompt archive:** [`../ALL_PROMPTS.md`](../ALL_PROMPTS.md) — see **PART F — DO NOT RUN**

Do not paste the "P1-7 Enterprise File Parser" or "REAL ENTERPRISE FILE PARSER" prompts as one task.

## What to use instead

| Step | Location in ALL_PROMPTS.md |
|---|---|
| Scoped parser (STDF + LOG) | **P7** — done |
| STIL / WGL / PAT | **P25–P27** — done (PAT vendor grammar pending) |
| Schema review | **P28** — done |
| Incremental finish plan | **P0–P20** |
| Stage tracker | [`../BUILD_SEQUENCE.md`](../BUILD_SEQUENCE.md) |

## Never create speculatively

Duplicate tables: `user`, `alert`, `upload`, `notification`  
Use existing: `users`, `alerts`, `upload_jobs`, `notifications`
