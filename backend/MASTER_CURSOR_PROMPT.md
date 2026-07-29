# VERILUMEN — Master Cursor Prompt (REFERENCE ONLY)

> **All prompts are in one file:** [`ALL_PROMPTS.md`](ALL_PROMPTS.md)  
> **Do not paste this entire file or ALL_PROMPTS.md into an agent as one task.**

---

## Rules (always apply)

- Inspect codebase before creating anything
- **Extend** `users`, `alerts`, `upload_jobs`, `notifications`, `recommendation_feedback` — never duplicate
- No placeholder parsers, no fake KPI defaults, no silent mock fallbacks in live mode
- Monolithic FastAPI + routers is correct — do not split into microservices

---

## Stage overview

| Stage | Topic | Prompts in ALL_PROMPTS.md |
|-------|-------|---------------------------|
| 0–3 | Foundations, auth, dashboard | STEP 40–47, Phase 1–7 |
| 4 | Real file parser | P7, P25–P27 |
| 5–6 | Notifications, recommendations | STEP 50–51, P12–P16 |
| 7 | Live analytics | P30 |
| 8 | AI + cost engines | P29, P18 (open) |
| 9 | Production hardening | P20, STEP 53 (open) |

See [`BUILD_SEQUENCE.md`](BUILD_SEQUENCE.md) for done/next tracker.
