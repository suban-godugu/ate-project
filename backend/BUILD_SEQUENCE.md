# VERILUMEN — Unified Build Sequence

> Reconciles a second opinion you got elsewhere against this tracker. It agreed with the chart/analytics gap already flagged here (folded in as Stage 7) and made a fair point about schema depth — but its schema-completion prompt has a real bug risk, flagged below. Don't run that prompt as written.
>
> Since then, a session with direct repo access verified this tracker line-by-line and converged on the same picture — good sign, not more to referee. Alert CRUD is confirmed missing (exact file/line locations below). SSE auth (P2-12) is confirmed **done**. A properly-scoped six-table candidate list replaced the vague "whatever the parser needs" placeholder. Updated below.
>
> One more round argued for parser-first over the P1-8-first call from last turn — and on reconsideration, that one's right, revised below. Even with P1-8 shipped, live mode is still just seeded rows through real plumbing, not real product value, until something has actually parsed a real file. The 65–70%-overall / per-module-percentage table that came with it is the same fabricated-precision problem as the 88–90% one from earlier — still not measurement, regardless of how many rounds repeat it.
>
> Parser shipped (STDF + LOG, scoped as specified, no new tables, `stdf-tamer`). That flips the priority: **P1-8 moves to the top now**, since it's the direct verification that the parser's real output actually surfaces on the dashboard instead of still being shadowed by mock fallback.

Single source of truth for what is done, what is next, and what **not** to run blindly.

**Do not run** the enterprise parser prompt, master cursor prompt, or Stage 4→9 one-shot. Use [`ALL_PROMPTS.md`](ALL_PROMPTS.md) — one prompt at a time.

---

## On the second opinion's schema-first prompt — don't run it as-is

It tells an agent to create `user`, `alert`, `upload`, `notification` as new tables. Your schema already has `users`, `alerts`, `upload_jobs`, `notifications` — live, working, referenced everywhere. Its own rule is "don't remove existing tables, only extend" — followed literally, that creates duplicate, disconnected tables next to the real ones, not an extension of them. `recommendation_feedback` in its list is also one you already have. It wasn't working from the actual schema, just guessing plausible names from a domain list. If you use any of that prompt's table list, rename those four first and have whichever agent runs it check `\d <table>` before creating anything.

Six parser-table candidates (when extraction confirms need): `pattern_results`, `scan_chain_results`/`scan_cells`, `mbist_failures`, `lbist_sessions`, `die_results`, `test_cost_events` — in `002_parser_facts.py`, not upfront.

**Interim bridge:** `module_fact_rows` (`002_module_fact_rows.py`) until parser fact tables exist.

---

## What's actually left, in order

0. ~~**Manually verify the parser (P21)**~~ — ✅ **done** (2026-07-06): **17/17** checks pass. See [`backend/PARSER_VERIFICATION_REPORT.md`](backend/PARSER_VERIFICATION_REPORT.md). Upload audit + theme sync completed in **Prompt 32**.
1. ~~STDF/LOG parser~~ — ✅ **done**. **STIL** (P25) + **WGL** (P26) + **PAT framework** (P27) added. Vendor PAT grammar awaits real sample.
2. ~~**Parser-driven schema review (P28)**~~ — ✅ **done** (2026-07-06): no migration required; see [`backend/PARSER_SCHEMA_ANALYSIS.md`](backend/PARSER_SCHEMA_ANALYSIS.md) + [`backend/DATABASE_SCHEMA.md`](backend/DATABASE_SCHEMA.md).
3. ~~**Frontend: stop silent mock fallback (P1-8)**~~ — ✅ **done**.
4. ~~SSE auth (P2-12)~~ — ✅ **done**.
5. **Live analytics (Stage 7)** — ✅ **complete** (P30): deep analytics via `deep_analytics.py`; real SQL trends/distributions; blocked states for die maps, embeddings, graphs. See [`backend/DEEP_ANALYTICS.md`](backend/DEEP_ANALYTICS.md).
6. ~~Alert CRUD (P2-13)~~ — ✅ **done**.
7. ~~Parser extensions — STIL, WGL, PAT framework~~ — ✅ **done** (P25–P27); vendor PAT grammar awaits real sample.
8. **AI recommendation + cost engines (Stage 8)** — RL scoring shipped; **Cost Intelligence engine** (P29) aggregates real LOG/STDF cost data via `cost_engine.py`.
9. Hygiene — grouped migrations, per-module live toggle, final mock-import audit, Stage 9 hardening.

---

## Stage 0 — Foundations ✅ done (both sides)

- **[Backend Phase 1]** Infra alignment — done
- **[Frontend STEP 40]** Environment & typed API client — done: `.env.local`, `src/lib/api/{client,dashboard,uploads,auth,notifications,actions}.ts`
- **[Frontend STEP 42]** Consolidate data access behind hooks — done: 7 module hooks, 0 components still import raw `*Data.ts`

## Stage 1 — Data, storage, cache layer 🟡 partial (backend only)

- **[Backend Phase 2]** Database schema — 18+ tables live; **Prompt 28 confirmed no parser migration** — see [`PARSER_SCHEMA_ANALYSIS.md`](backend/PARSER_SCHEMA_ANALYSIS.md). Future candidates (`die_results`, `pattern_definitions`, …) only when SQL analytics require them.
- **[Backend Phase 3]** Storage layer (MinIO) — done
- **[Backend Phase 4]** Cache layer (Redis) — done, rate limiting wired

## Stage 2 — Auth ✅ done (both sides)

- **[Backend Phase 5]** Auth — done, incl. `GET /users/me/preferences`
- **[Frontend STEP 41]** Auth pages + wiring — done: login, `AuthGuard`, session in `userStore`, real `uploadedBy`

## Stage 3 — Core dashboard read path 🟡 partial

- **[Backend Phase 7]** Dashboard query endpoints — done, `GET /search` now live (confirmed via frontend integration)
- **[Backend, extends Phase 7]** Alert CRUD — **confirmed missing**: only reads exist, in `app/routers/dashboard.py` + `app/services/dashboard_service.py`; needs `POST /alerts`, `PATCH /alerts/{id}`, `DELETE /alerts/{id}` + `dash:alerts:*`/`notif:*` invalidation
- **[Frontend STEP 43]** Live-wire dashboards — partial: KPIs + rows are live; overview charts partially live (Stage 7); sub-tab charts/heatmaps still mock — P1-9
- **[Frontend STEP 44]** Wire quick filters + search — done

## Stage 4 — Uploads 🟡 parser done, manual verify pending

- **[Backend Phase 6]** Uploads — presign → complete → SSE fully live; **parser now real for STDF + LOG** — `app/parsers/{file_detection,stdf_parser,log_parser}.py`, writes real `scan_chain_failures` + `ai_log_summaries` rows, no new tables, `stdf-tamer` (Apache 2.0). STIL/WGL/PAT still a follow-up pass, not urgent. **Not yet manually verified with a real upload in live mode** — do that before treating it as fully closed.
- **[Backend, extends Phase 6]** SSE auth on `GET /uploads/{job_id}/status` — ✅ done (`Depends(get_current_user)` + ownership check added)
- **[Frontend STEP 45]** Real upload flow — done, and now backed by genuinely real parsed data instead of a stub

## Stage 5 — Notifications ✅ done (both sides)

- **[Backend Phase 8]** Notifications — done
- **[Frontend STEP 46]** Notifications live wiring — done

## Stage 6 — Recommendations, RL feedback, export 🟡 feedback bug in live mode

- **[Backend, extends Phase 7]** `POST /recommendations/{id}/feedback` — live (confirmed via frontend integration; already exists, don't recreate it)
- **[Frontend STEP 47]** Recommendation feedback → RL signal — **broken in live mode until P1-8**: rows carry mock IDs like `"REC-001"` when recommendation-analysis returns empty or mock-blended rows; fix with Prompt 2 + Prompt 8 in [`PROMPTS_20.md`](PROMPTS_20.md)
- **[Backend, extends Phase 7]** Export — live, but shipped as `POST /export/pdf` specifically rather than the generic `GET /export/{format}` originally speced. Fine for PDF; if CSV/Excel/PNG is wanted later, decide then whether to add sibling routes or refactor to the generic form
- **[Frontend STEP 48]** Export Report — done

## Stage 7 — Live analytics ✅ complete (P30)

- **[Backend]** `chart_aggregation.py` + `deep_analytics.py` — SQL aggregation for all modules; `_meta` blocked markers for unavailable analytics
- **[Frontend]** `useLiveModuleCharts`, `AnalyticsChartEmpty`, no dummy wafer heatmap in live mode without data
- **Blocked until parser/schema:** die heatmaps (`die_results`), pattern similarity (embeddings), MBIST address maps, connectivity graphs

Depends on Stage 4 parser output — satisfied for STDF/LOG/STIL/WGL.

## Stage 8 — AI recommendation + cost engines ⬜ not started

- Real RL-driven recommendation scoring feeding the recommendation tables — ties to the Pattern / Scan-Debug / Test-Optimization agents (agent-specific responsibility breakdown in Prompt 18 of [`PROMPTS_20.md`](PROMPTS_20.md))
- Real cost aggregation from actual module costs, replacing whatever currently backs Cost Intelligence

## Stage 9 — Hardening ⬜ not started

- **[Backend Phase 9]** Production checklist — documented in [`backend/PRODUCTION_HARDENING.md`](backend/PRODUCTION_HARDENING.md), not built

---

## Confirmed gaps (exact locations)

### Alert CRUD — **NOT done**

- **Exists:** `GET /dashboard/alerts/{tab}`
- **Missing:** `POST`/`PATCH`/`DELETE` + `dash:alerts:*` / `notif:*` invalidation
- **Location:** `app/routers/dashboard.py`, `app/services/dashboard_service.py`

### Upload SSE auth — **DONE** (P2-12)

- **Was:** `GET /uploads/{job_id}/status` — no auth
- **Now:** `Depends(get_current_user)` + `uploaded_by == user.id`

---

## Running it locally right now

```powershell
# backend
cd backend
# start PostgreSQL, Redis, and MinIO as native local services/processes first
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
arq app.workers.WorkerSettings   # separate terminal

# frontend — dashboard/.env.local
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Login as `alex@verilumen.ai` / `changeme123`. Mock mode stays the safe default (`NEXT_PUBLIC_API_MODE=mock`), so nothing breaks if the backend isn't running.

---

## Documentation state

- **All prompts (single file):** [`ALL_PROMPTS.md`](ALL_PROMPTS.md) — STEP 1–53, Phase 1–9, P0–P32
- **Stage tracker:** this file
- **Implementation docs:** [`backend/PARSER_SCHEMA_ANALYSIS.md`](backend/PARSER_SCHEMA_ANALYSIS.md), [`backend/DATABASE_SCHEMA.md`](backend/DATABASE_SCHEMA.md), [`backend/GAP_REPORT.md`](backend/GAP_REPORT.md), [`dashboard/FRONTEND_GAP_REPORT.md`](dashboard/FRONTEND_GAP_REPORT.md)
- **CSV backups (historical):** `dashboard/prompts.csv`, `backend/prompts-backend.csv`, `dashboard/prompts-frontend-integration.csv`
- **Short pointers only:** [`PROMPTS_20.md`](PROMPTS_20.md), [`MASTER_CURSOR_PROMPT.md`](MASTER_CURSOR_PROMPT.md), [`backend/PROMPT_7_PARSER.md`](backend/PROMPT_7_PARSER.md)
