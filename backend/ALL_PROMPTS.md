# VERILUMEN — All Prompts (Single Master File)

**Last updated:** 2026-07-06  
**Purpose:** One file containing every build prompt for the VERILUMEN ATE Intelligence Platform.  
**How to use:** Run **one prompt at a time** in Cursor. Do not paste the entire file or the "Do Not Run" section as a single task.

---

## Quick status

| Range | Area | Done | Remaining | 
|-------|------|------|-----------|
| STEP 1–39 | Frontend UI (dashboard modules) | ✅ All | — |
| STEP 40–53 | Full-stack integration | ✅ Most | STEP 53 hardening |
| Phase 1–9 | Backend infrastructure | ✅ Most | Phase 9 Tier 3 |
| P0–P16 | Live demo + core product | ✅ All | — |
| P17–P20 | Hardening + RL + tests | ⬜ Open | 4 prompts |
| P21–P32 | Parser verify + extensions + analytics | ✅ Most | PAT vendor grammar |

**Next recommended:** P18 (RL consumer) → P19 (tests) → P20 (Tier 3 hardening) → PAT vendor sample.

---

## Global rules (apply to every prompt)

1. Inspect the codebase before creating anything.
2. **Extend** existing tables: `users`, `alerts`, `upload_jobs`, `notifications`, `recommendation_feedback` — never duplicate as `user`, `alert`, `upload`, `notification`.
3. No placeholder parsers, no fake KPI defaults, no silent mock fallbacks in **live mode**.
4. Monolithic FastAPI + routers is correct — do not split into microservices.
5. Structured data → PostgreSQL · files → MinIO · cache/sessions/jobs → Redis.
6. Parser-driven schema only — add tables when parser output has nowhere to go.

**Candidate parser tables (when confirmed):** `pattern_results`, `scan_chain_results`, `scan_cells`, `mbist_failures`, `lbist_sessions`, `die_results`, `test_cost_events`.

---

# PART A — Frontend UI Prompts (STEP 1–39)

> Source: `dashboard/prompts.csv` · Date: 2026-06-29 · Status: ✅ **All implemented**

### STEP 1 — Project Setup ✅
**Prompt:** Create Next.js app with TypeScript Tailwind ESLint App Router src directory. Install recharts framer-motion react-icons lucide-react react-query clsx tailwind-merge. Init shadcn and add button card table dropdown-menu input select slider avatar badge.

### STEP 2 — Folder Structure ✅
**Prompt:** Define src folder structure for dashboard components layout cards charts tables filters optimization results lib types hooks styles.

### STEP 3 — Layout (Cursor Prompt 1) ✅
**Prompt:** Premium enterprise dashboard layout: 280px sidebar 72px navbar 24px padding/gap CSS Grid glassmorphism purple accent dark theme responsive. Background #090B12 Cards #111827 Border #2D3748 Accent #7C3AED Rounded 20px.

### STEP 4 — Sidebar (Cursor Prompt 2) ✅
**Prompt:** 280px sidebar #0A1020 background. Header ATE Intelligence Enterprise Platform. Navigation: Dashboard Scan Chain Analysis MBIST LBIST Wafer Analysis Cost Intelligence Alerts Settings. Active menu purple gradient rounded-xl glow. Icons for every menu. Quick Filters: Date Range Fab Tester Product Reset Filters. Alerts badge 5. Sidebar fixed.

### STEP 5 — Top Navbar (Cursor Prompt 3) ✅
**Prompt:** 72px sticky navbar. Left page title Executive Dashboard. Center large search bar. Right Calendar Notifications Profile Export Report AI Optimize. User Alex Johnson Admin. Notification badge 12. Glass backdrop blur.

### STEP 6 — Executive KPI Cards (Cursor Prompt 4) ✅
**Prompt:** Six KPI cards in 6-column grid. Each card: icon title large value weekly trend sparkline hover animation. Metrics: Total Test Cost Cost per Wafer Cost per Die Test Time Yield ROI Improvement. Recharts AreaChart sparklines Framer Motion entrance. Glass card gradient border.

### STEP 7 — Wafer Heatmap (Cursor Prompt 5) ✅
**Prompt:** Wafer Cost Heatmap canvas 40x40 circular wafer grid. Pan zoom reset fullscreen. Overlay dropdown fail density yield cost. Color legend green yellow orange red. Tooltip on hover. Spatial AI analysis.

### STEP 8 — Pattern Analysis Table (Cursor Prompt 6) ✅
**Prompt:** Enterprise table columns: Pattern ID Test Time Cost Fail Rate Detect Power ROI Score Recommendation. Badges Keep Review Remove. Sticky header pagination search sorting hover row highlight.

### STEP 9 — Cost Trend Chart (Cursor Prompt 7) ✅
**Prompt:** Recharts line chart Total Cost and Cost per Wafer over 7 days Mon-Sun. Smooth animated lines dark theme legend. Glass card wrapper.

### STEP 10 — Optimization Engine (Cursor Prompt 8) ✅
**Prompt:** Three sliders Maximum Cost Yield Target Maximum Test Time with live values. Run AI Optimization purple button with sparkle icon animated loading state.

### STEP 11 — Optimization Results (Cursor Prompt 9) ✅
**Prompt:** Result card after optimization: cost reduction time savings projected yield patterns reduced total savings. Green positive values. View Optimized Pattern Set button hover animation.

### STEP 12 — Final Polish (Cursor Prompt 10) ✅
**Prompt:** Inter font glassmorphism gradient borders hover lift responsive desktop tablet mobile. Integrate all components dummy JSON production ready enterprise SaaS quality comparable to Synopsys Siemens NVIDIA Intel dashboards.

### SETTINGS — Settings Page ✅
**Prompt:** Theme Settings: appearance accent sidebar card font compact animations reset. Account Presets: profile role department dashboard language timezone notifications save. Persist to localStorage. Live theme preview.

### INTEGRATION — Dashboard Page Integration ✅
**Prompt:** Wire all components into main dashboard page with shared dummy data and responsive grid layout. Redirect root / to /dashboard.

### STEP 13 — Scan Chain Analysis Dashboard ✅
**Prompt:** Create premium enterprise Scan Chain Analysis dashboard for ATE Intelligence Enterprise Platform. Stack: Next.js 15 TypeScript TailwindCSS shadcn/ui Framer Motion Recharts Lucide. Theme: Background #090B12 Cards #111827 Border #2D3748 Accent #7C3AED Rounded 20px Glass Effect smooth animations responsive. Tabs: Overview Pattern Analysis Failure Analysis Scan Diagnosis. Full KPI/chart/table layout per tab. Enterprise SaaS quality.

### STEP 14 — Record All Prompts ✅
**Prompt:** Record the all prompt in csv and readme file.

### STEP 15 — Automatic Prompt Recording ✅
**Prompt:** Make the automatic record the prompt in csv and readme file.

### STEP 16 — Recommendation Analysis Sidebar ✅
**Prompt:** Add Recommendation Analysis to sidebar between Cost Intelligence and Alerts. Sparkles icon route /dashboard/recommendation-analysis. Purple gradient active state hover scale accessibility. Do not redesign sidebar.

### STEP 17 — MBIST Analysis Dashboard ✅
**Prompt:** Create premium enterprise MBIST Analysis dashboard. Tabs: Overview Memory Health Failure Analysis Diagnosis AI Recommendation. Route /mbist. Dark enterprise glassmorphism theme.

### STEP 18 — LBIST Analysis Dashboard ✅
**Prompt:** Create premium enterprise LBIST Analysis dashboard. Tabs: Overview Coverage Analysis Failure Analysis Diagnosis AI Recommendation. Route /lbist.

### STEP 19 — Recommendation Analysis Dashboard ✅
**Prompt:** Create premium enterprise Recommendation Analysis dashboard. Route /recommendation-analysis. Tabs Overview Scan Chain MBIST LBIST Wafer Analysis. Priority badges Critical High Medium Low.

### STEP 20 — Cost Intelligence Dashboard ✅
**Prompt:** Create premium enterprise Cost Intelligence dashboard. Route /cost-intelligence. Tabs Overview Scan Chain Cost MBIST Cost LBIST Cost Wafer Cost AI Cost Optimization.

### STEP 21 — Alerts Dashboard ✅
**Prompt:** Create premium enterprise Alerts dashboard. Route /alerts. Tabs Overview Scan Chain MBIST LBIST Wafer Cost AI Recommendation Alerts. Severity badges Critical High Medium Low.

### STEP 22 — Upload Test Data ✅
**Prompt:** Add enterprise Upload Test Data feature top navbar UploadCloud button purple gradient modal drag-drop react-dropzone dataset category metadata progress upload history. Supported STDF STIL WGL CSV XLSX JSON ZIP XML max 10GB.

### STEP 23 — Upload Log File ✅
**Prompt:** Add enterprise Upload Log File button beside Upload Data. ATE log upload log source tester metadata validation progress 5-step pipeline AI log summary upload history actions. Supported STDF STIL WGL LOG TXT CSV JSON XML ZIP GZ max 5GB.

### STEP 24 — Complete Remaining Platform Functionality ✅
**Prompt:** Complete remaining frontend functionality. Zustand stores filters user uploads notifications settings. Route migration to /dashboard/* with redirects and wafer-analysis page. Global search calendar notifications export responsive nav sidebar. Filter engine primary actions AI diagnosis apply recommendation. Upload persistence profile loading empty error states accessibility. Do not redesign page shell.

### STEP 25 — Pattern Analysis KPI Dashboard ✅
**Prompt:** Scan Chain Pattern Analysis tab enterprise KPI dashboard. 11 KPIs PA-001 to PA-011. Charts: Pattern Import Trend Pattern Coverage Trend Pattern Cluster Distribution donut Pattern Similarity Scatter. Table with Pattern ID Category Coverage Efficiency Runtime Redundancy Similarity Cluster Recommendation Priority Status.

### STEP 26 — Pattern Analysis Tab Refinement ✅
**Prompt:** Remove from Scan Chain Pattern Analysis tab: header action box Upload Export Generate AI buttons AI Recommendation Summary section Redundancy Heatmap Similarity Matrix. Keep 11 KPIs import/coverage trend charts cluster pie scatter chart pattern table.

### STEP 27 — Failure Analysis KPI Dashboard ✅
**Prompt:** Scan Chain Failure Analysis tab enterprise KPI dashboard. 12 KPIs FA-FR-001 to FA-FR-012. Charts: Failure Trend Failure Type Distribution Failure by Lot Failure Density. Table: Failure ID Pattern ID Chip Fail Type Root Cause Severity Status Repair Action Priority.

### STEP 28 — Failure Analysis Tab Refinement ✅
**Prompt:** Remove from Scan Chain Failure Analysis tab: header action box Upload Export Generate AI buttons AI Recommendation Summary Wafer Die heatmaps Correlation Matrix Root Cause Analysis section. Keep 12 KPIs failure trend charts distribution by-lot charts failure table.

### STEP 29 — Recommendation Analysis AI Agent Center ✅
**Prompt:** Redesign Recommendation Analysis page as single AI Recommendation Center without module tabs. Three agent sections: Pattern Recommendation Agent Scan Debug Recommendation Agent Test Optimization Recommendation Agent.

### STEP 30 — Recommendation Analysis AI Agent Tabs ✅
**Prompt:** Redesign Recommendation Analysis with 3 AI Agent tabs persisted in uiStore. Animated tab switching Framer Motion. Route /dashboard/recommendation-analysis.

### STEP 31 — Scan Debug Recommendation Agent Tab ✅
**Prompt:** Scan Debug Recommendation Agent tab full enterprise dashboard. 15 KPIs in 5 sections. Charts: root cause donut priority bar 30-day trend. Table: Recommendation ID Category Priority Expected Impact Action Status. AI Debug Executive Summary 9 cards. Debug workflow diagram action bar.

### STEP 32 — Test Optimization Recommendation Agent Tab ✅
**Prompt:** Test Optimization Recommendation Agent tab full enterprise dashboard. 19 KPIs in 7 sections. Charts: priority donut priority bar 30-day trend yield line cost area site utilization heatmap 16 sites. Table: Recommendation ID Category Priority Confidence Assigned Engineer Expected Impact Action Status.

### STEP 33 — Record All Prompts (Session Update) ✅
**Prompt:** Have upload all prompt to csv and readme file.

### STEP 34 — Wafer Analysis Module (All Tabs) ✅
**Prompt:** Create premium enterprise Wafer Analysis module. Route /dashboard/wafer-analysis. 10 tabs TabPanelHost keep-alive: Overview Centre Donut Edge-Ring Scratch Near-Full Normal Edge-Loc Local Random. Overview + DefectClassTab with canvas heatmaps and upload history.

### STEP 35 — Wafer Analysis Images in Data ✅
**Prompt:** Update wafer data to include wafer images in waferData.ts not separate asset system. WaferImages interface wafer overlay density SVG data URIs via buildWaferImages buildWaferImageUri.

### STEP 36 — Wafer Analysis UI Refinement ✅
**Prompt:** Overview remove Yield Trend Yield Distribution Defect Class Breakdown Recent Wafer Yield Top Defect Wafers table. Defect tabs: Upload History single selectable list drives canvas maps. Overlay Analytics canvas and Fail Density canvas.

### STEP 37 — Wafer Analysis Records Removal ✅
**Prompt:** Remove Wafer Analysis Records table from all defect class tabs. Remove analysisRows from defect bundle and buildAnalysisRows from waferData.

### STEP 38 — Platform Tab Performance Optimization ✅
**Prompt:** Improve tab and section response time without UI visual changes. TabPanelHost lazy mount keep-alive hidden inactive tabs. Remove artificial setTimeout delays in usePlatformData. React Query cache defaults refetchOnWindowFocus false staleTime 60s. Apply TabPanelHost to all module pages.

### STEP 39 — Record All Prompts (Full Platform Update) ✅
**Prompt:** Update all prompts to prompts.csv and README.md including Wafer Analysis module all tabs data images UI refinements performance optimization and current platform state.

---

# PART B — Full-Stack Integration Prompts (STEP 40–53)

> Source: `dashboard/prompts-frontend-integration.csv` · Date: 2026-07-03

### STEP 40 — Infra Foundation ✅
**Prompt:** Extend docker-compose postgres redis minio minio-init worker. Env MINIO_* REDIS_* JWT_*. Dependencies fastapi uvicorn sqlalchemy asyncpg alembic redis arq minio python-jose passlib pydantic-settings.

### STEP 41 — Consolidate Data Hooks ✅
**Prompt:** Add useFiltered<Module>Data() hooks next to usePlatformData.ts reading useFilterStore returning kpis rows isLoading. Repoint 49 components from raw *Data.ts imports to hooks.

### STEP 42 — API Client Scaffold ✅
**Prompt:** NEXT_PUBLIC_API_URL and NEXT_PUBLIC_API_MODE=mock in .env.local. src/lib/api/client.ts fetch wrapper auth headers typed errors. Stubs for dashboard uploads auth notifications actions matching backend endpoints.

### STEP 43 — Database Schema Reconciliation ✅
**Prompt:** Alembic migrations for dims auth uploads analytics recommendations feedback indexes. Match 39-table schema or add missing. One migration per logical group per spec.

### STEP 44 — Storage and Cache Clients ✅
**Prompt:** minio_client presign put/get bytes. redis_client filter_cache_key session jwt blacklist dash keys job status events ratelimit notif unread search index.

### STEP 45 — Auth ✅
**Prompt:** Backend JWT login refresh logout me preferences. Frontend userStore session login page AuthGuard in DashboardLayout replace hardcoded Alex Johnson in uploads.

### STEP 46 — Dashboard Search Filters Actions ✅
**Prompt:** GET dashboard/* endpoints GlobalFilters cached Redis. GET search GET filters/options. POST actions/primary POST ai-diagnosis GET actions/{id}/status SSE.

### STEP 47 — Live-wire Dashboards ✅
**Prompt:** Swap hook internals: mock useMemo vs live useQuery on NEXT_PUBLIC_API_MODE. searchPlatform → GET /search. Flip per module as endpoints land.

### STEP 48 — Uploads ✅
**Prompt:** Backend presign complete SSE ARQ parse_worker. Frontend performFileUpload presign PUT complete SSE. Drop fileCache useQuery history presigned download in live modals.

### STEP 49 — AI Actions ✅
**Prompt:** ai_worker primary action and AI diagnosis. Replace usePrimaryAction setTimeout with POST + SSE mapping to existing UI steps.

### STEP 50 — Notifications ✅
**Prompt:** Backend notifications CRUD + Redis cache. Frontend useNotifications hook React Query replacing seed data in live mode.

### STEP 51 — Recommendation Feedback ✅
**Prompt:** POST /recommendations/{id}/feedback → recommendation_feedback reward_value. Frontend RecommendationActionButtons calls API in live mode.

### STEP 52 — Export PDF ✅
**Prompt:** CSV Excel PNG client-side unchanged. exportPDF → POST /export/pdf reportlab MinIO presigned URL in live mode.

### STEP 53 — Production Hardening ⬜ NOT STARTED (Tier 3)
**Prompt:** Postgres PITR MinIO replication Redis policy vault secrets rate limit RLS ClamAV OpenTelemetry — deferred checklist. See `backend/PRODUCTION_HARDENING.md`.

---

# PART C — Backend Phase Prompts

> Source: `backend/prompts-backend.csv` + `backend/prompts-database.csv` · Date: 2026-07-03

### Phase 1 — Infra Alignment ✅
**Prompt:** Extend docker-compose.yml merge don't replace. Confirm postgres redis minio. Add minio-init one-shot creating verilumen-raw-uploads verilumen-parsed verilumen-wafer-images verilumen-exports verilumen-ai-artifacts. Add worker service (same image as api command arq app.workers.WorkerSettings). Env: MINIO_* REDIS_URL REDIS_PREFIX JWT_* in .env.

### Phase 2.1 — Dimension Tables ✅
**Prompt:** For each dimension table confirm an equivalent already exists or add via Alembic. Tables: fabs, testers, products, lots, wafers.

### Phase 2.2 — Auth/Users ✅
**Prompt:** Confirm users user_preferences audit_logs exist or add via Alembic.

### Phase 2.3 — Upload Pipeline ✅
**Prompt:** CREATE upload_jobs upload_pipeline_steps ai_log_summaries with upload_status and upload_kind enums.

### Phase 2.4 — Module Analytics ✅
**Prompt:** Add kpi_snapshots scan_chain_failures wafer_defect_uploads alerts recommendations notifications if missing.

### Phase 2.5 — RL Feedback Loop ✅
**Prompt:** CREATE TABLE recommendation_feedback for Pattern Scan Debug Test Optimization agents.

### Phase 2.6 — Migration Strategy ⬜ PARTIAL
**Prompt:** Write all schema changes as Alembic migrations one per logical group not raw SQL. **Still monolithic 001_initial_schema.py — see P17.**

### Phase 3 — Storage Layer MinIO ✅
**Prompt:** app/storage/minio_client.py wrap minio SDK: get_presigned_put_url get_presigned_get_url put_object_bytes get_object_bytes. Object keys: raw-uploads/{kind}/{yyyy}/{mm}/{job_id}/{filename}; parsed/{job_id}/summary.json.

### Phase 4 — Cache Layer Redis ✅
**Prompt:** app/cache/redis_client.py wrap redis.asyncio. Keys: session jwt blacklist dash job events ratelimit notif unread search index. filter_cache_key helper.

### Phase 5 — Auth ✅
**Prompt:** POST /auth/login /auth/refresh /auth/logout GET /auth/me PATCH /users/me/preferences. JWT python-jose bcrypt. Access 15min refresh 7d.

### Phase 6 — Uploads Presigned Flow + Worker ✅
**Prompt:** POST /uploads/presign → upload_jobs queued presigned PUT. Frontend PUT to MinIO. POST /uploads/{id}/complete → parsing → ARQ parse_worker. GET status SSE via job:{id}:events. Worker: GET MinIO parse STDF/LOG PUT parsed JSON INSERT facts DEL cache.

### Phase 7 — Dashboard Query Endpoints ✅
**Prompt:** GlobalFilters: date_preset fab tester product lot wafer. Cached reads via filter_cache_key. Endpoints: GET /dashboard/executive scan-chain/{tab} mbist/{tab} lbist/{tab} wafer-analysis/* recommendation-analysis/{agent} cost-intelligence/{tab} alerts/{tab} search filters/options.

### Phase 7+ — AI Actions ✅
**Prompt:** POST /actions/primary/{page_id} POST /ai-diagnosis/{module} GET /actions/{job_id}/status SSE. ai_worker run_primary_action run_ai_diagnosis.

### Phase 7+ — Recommendation Feedback ✅
**Prompt:** POST /recommendations/{id}/feedback {action_taken outcome_metric outcome_value} → recommendation_feedback reward_value.

### Phase 7+ — Export PDF ✅
**Prompt:** POST /export/pdf {title lines} → reportlab PDF → verilumen-exports MinIO → presigned URL.

### Phase 8 — Notifications ✅
**Prompt:** Postgres notifications table + notif:unread:{user_id} Redis cache. GET /notifications PATCH /notifications/read-all PATCH /notifications/{id}/read.

### Phase 9 — Production Checklist ⬜ NOT STARTED (Tier 3)
**Prompt:** Postgres PITR; MinIO versioning replication; Redis AOF policy; secrets vault; RLS multi-tenant; ClamAV upload scan; OpenTelemetry Grafana.

---

# PART D — Finish-the-Build Prompts (P0–P20)

> These take live mode from "technically works" to production-ready. Run in order within each tier.

## P0 — Unblocks a real live demo ✅ DONE (2026-07-06)

### P1 — Expand seed data for every module ✅
**Prompt:** `scripts/seed.py` currently seeds executive + scan-chain KPIs, 2 scan failures, 1 alert, 1 recommendation — everything else is empty. Add realistic rows (10–20 each) for MBIST, LBIST, Wafer Analysis, Cost Intelligence, and Recommendation Analysis, matching the shapes in `src/types/*.ts`.

### P2 — Implement `_fetch_module_rows()` for missing modules ✅
**Prompt:** Only scan-chain and alerts are implemented; mbist, lbist, wafer-analysis, cost-intelligence, and recommendation-analysis return empty rows despite the routes existing. Write the real queries for each, reusing the scan-chain pattern. For recommendation-analysis: verify `RecommendationActionButtons` sends feedback against the real `recommendations.id`, not a mock ID.

### P3 — Real executive KPIs, no fake defaults ✅
**Prompt:** `build_executive_payload()` returns `patterns: []`, `costTrend: []`; `_default_kpis()` returns fake `"42"`/`"8"` when the DB is empty. Compute real aggregates from seeded tables; return explicit empty/no-data state instead of fabricated numbers.

### P4 — Apply date filtering in backend SQL ✅
**Prompt:** `date_preset`, `custom_date_from`, `custom_date_to` exist in `GlobalFilters` and get sent from the frontend, but nothing filters by them. Add the date range to every module's query.

### P5 — Frontend: token refresh + session restore ✅
**Prompt:** `apiFetch` never calls `/auth/refresh` — access tokens expire after 15 minutes and the user gets logged out mid-session. On a 401, refresh and retry once before forcing logout. Call `GET /auth/me` on app load so a persisted session actually restores.

### P6 — Frontend: invalidate dashboard queries after upload completes ✅
**Prompt:** When the SSE stream reports `completed`, invalidate that module's query keys too. Format upload processing time as `"2m 4s"` instead of `"1234ms"`.

---

## P1 — Core product value

### P7 — Real STDF + LOG parser ✅
**Prompt:** Implement real parsers in `app/parsers/{file_detection,stdf_parser,log_parser}.py`. Write to `scan_chain_failures` + `ai_log_summaries`. Use `stdf-tamer` (Apache 2.0). No new DB tables. Cache invalidation including `search:index:v1`. Fixtures: `tests/fixtures/sample.stdf`, `sample_ate.log`. Do not touch frontend hooks, alert CRUD, or SSE auth in this pass.

**Shipped files:** `app/parsers/file_detection.py`, `stdf_parser.py`, `log_parser.py`, `app/services/metadata_upsert.py`, `app/workers/parse_worker.py`, `tests/test_parsers.py`.

### P8 — Frontend: stop the silent mock fallback ✅
**Prompt:** Live mode uses `emptyLiveShell` + `useLiveModuleCharts` — no `{ ...mock, kpis: api.kpis }` blend. Mock mode unchanged.

### P9 — Frontend: per-tab live queries ✅
**Prompt:** `ModuleTabProvider` on module pages; hooks query `/dashboard/{module}/{activeTab}` via `useModuleDashboard`.

### P10 — Settings ↔ backend preferences sync ✅
**Prompt:** Settings page loads/saves `account_json` via `/users/me/preferences` in live mode.

### P11 — Dynamic filter options ✅
**Prompt:** `GET /filters/options` queries fabs/testers/products/lots/wafers from PostgreSQL.

---

## P2 — Hardening & polish

### P12 — Upload SSE auth ✅
**Prompt:** `GET /uploads/{job_id}/status` had no auth check. Add `Depends(get_current_user)` + `uploaded_by == user.id`.

### P13 — Alert CRUD + cache invalidation ✅
**Prompt:** `POST/PATCH/DELETE /dashboard/alerts` + `dash:alerts:*` / `notif:*` / `search:index:v1` invalidation.

### P14 — Audit log writes ✅
**Prompt:** Login, recommendation feedback, export PDF → `audit_logs`.

### P15 — Refresh token rotation ✅
**Prompt:** Previous refresh JTI blacklisted on each `/auth/refresh`.

### P16 — Search index + cache ✅
**Prompt:** Upload jobs indexed; parse worker invalidates `search:index:v1`.

### P17 — Grouped Alembic migrations ⬜ NOT STARTED
**Prompt:** Split the single `001_initial_schema.py` into one migration per logical group (dims/auth, uploads, analytics, recommendations+feedback).

### P18 — RL training consumer ⬜ NOT STARTED
**Prompt:** Build the consumer that turns applied/rejected/ignored `recommendation_feedback` rows into training signal for the Pattern / Scan-Debug / Test-Optimization agents. Build the consumer plus **one working recommendation type per agent** first:

- **Pattern:** removal, ordering, coverage improvement, ATPG recommendation, low-power optimization
- **Scan Debug:** broken chains, constraint review, timing/power debug, physical investigation
- **Test Optimization:** adaptive testing, test-stop, risk-based testing, yield/cost optimization, multi-site optimization

### P19 — Automated tests ⬜ PARTIAL
**Prompt:** Backend + frontend coverage for upload, auth, and dashboard happy paths at minimum. Backend has ~104 unit tests; frontend has 5 hook test files. Add E2E upload → dashboard flow.

### P20 — Production hardening checklist ⬜ PARTIAL (Tier 1–2 done, Tier 3 open)
**Prompt:** Update `PRODUCTION_HARDENING.md`. Then: Postgres backups + PITR, MinIO versioning, Redis persistence policy, secrets in a vault, row-level security if multi-tenant, ClamAV on uploads, OpenTelemetry → Grafana.

---

# PART E — Extended Backend Prompts (P21–P32)

> Added after the original 20-prompt plan. Parser extensions, verification, analytics engines.

### P21 — Manual Parser Verification ✅
**Prompt:** Manually verify the STDF + LOG parser end-to-end in live mode. Upload `tests/fixtures/sample.stdf` and `sample_ate.log` through presign → MinIO → ARQ worker → PostgreSQL → dashboard APIs. Confirm cache invalidation, search index refresh, and dashboard row updates. Document results in `backend/PARSER_VERIFICATION_REPORT.md`. Run `backend/scripts/verify_parser_e2e.py`.

**Result:** 17/17 checks pass.

### P24 — Production Readiness Tier 1 & 2 ✅
**Prompt:** Implement operational visibility and backup/security baseline: structured JSON logging, request ID middleware, health/ready/live/metrics endpoints, audit query API, worker heartbeat, Postgres backup/restore scripts, security headers, CI pipeline. Document in `backend/PRODUCTION_HARDENING.md` and `backend/PRODUCTION_READINESS_REPORT.md`. Tier 3 (OTel, ClamAV, Vault, K8s) deferred.

### P25 — STIL Parser (IEEE 1450) ✅
**Prompt:** Implement `app/parsers/stil_parser.py` for IEEE Std 1450-1999 STIL 1.0. Extract: Header, Signals, SignalGroups, Timing/WaveformTable, ScanStructures, Pattern blocks. Store parsed JSON in MinIO + summary in `ai_log_summaries`. Route in `parse_worker.py`. Fail gracefully on vendor extensions (CTLMode, Tessent, etc.) with `StilUnsupportedExtension`. Fixture: `tests/fixtures/sample.stil`. No new DB tables unless schema review requires. Docs: `backend/STIL_PARSER.md`.

### P26 — WGL Parser ✅
**Prompt:** Implement `app/parsers/wgl_parser.py` for Waveform Generation Language files. Extract pattern/scan/signal metadata. Store parsed JSON in MinIO + summary fields. Route in `parse_worker.py`. Fixture: `tests/fixtures/sample.wgl`. Docs: `backend/WGL_PARSER.md`, `backend/WGL_SCHEMA_EXTENSION.md`.

### P27 — PAT Parser Framework ✅ (vendor grammar pending)
**Prompt:** Implement PAT file detection and framework in `app/parsers/pat_parser.py`. PAT is vendor-specific (Teradyne, Advantest) — **do not invent grammar**. Detect `.pat`/`.pat.gz` via content signatures. Return `unsupported_pat_format` until a real vendor sample is registered via `register_pat_vendor_parser()`. Docs: `backend/PAT_PARSER.md`, `backend/PAT_SCHEMA_EXTENSION.md`.

### P28 — Parser-Driven Schema Review ✅
**Prompt:** Analyze STDF, LOG, STIL, WGL, PAT parser output against existing PostgreSQL schema. Create migration **only if required**. Document field mapping, deferred tables, and MinIO JSON storage strategy. Output: `backend/PARSER_SCHEMA_ANALYSIS.md`, `backend/DATABASE_SCHEMA.md`. Tests: `tests/test_schema_extensions.py`.

**Result:** No migration required. Future candidates: `die_results`, `pattern_definitions`, `mbist_failures`, `lbist_sessions`.

### P29 — Enterprise Cost Intelligence Engine ✅
**Prompt:** Build `app/services/cost_engine.py` aggregating real cost data from `ai_log_summaries.estimated_cost`, `estimated_savings`, `scan_chain_failures`, `upload_jobs.processing_ms`. Wire to `GET /dashboard/cost-intelligence/{tab}` and executive `costTrend`. Document formulas. Evaluate cost alerts on parse. Frontend: use live cost hooks. Tests: `tests/test_cost_engine.py`. Docs: `backend/COST_ENGINE.md`.

### P30 — Enterprise Deep Analytics (Stage 7) ✅
**Prompt:** Build `app/services/deep_analytics.py` extending all dashboard module charts with SQL aggregation, tab-specific rows, and `_meta` blocked markers for unavailable analytics (die heatmaps, embeddings, connectivity graphs). Wire via `chart_aggregation.py`. Frontend: `useLiveModuleCharts`, `AnalyticsChartEmpty`. Tests: `tests/test_chart_aggregation.py`. Docs: `backend/DEEP_ANALYTICS.md`.

### P32 — Upload Audit + Theme Preferences Sync ✅
**Prompt:** Write upload and parser lifecycle events to `audit_logs` via `upload_audit.py`. Sync theme preferences: backend `theme_json` in `user_preferences`, frontend `useThemePreferencesSync` hook. Ensure `QueryProvider` wraps `ThemeProvider` in `layout.tsx` (React Query dependency). Re-run P21 verification for 17/17 pass.

---

# PART F — DO NOT RUN (reference only)

### Enterprise all-formats parser (DO NOT RUN AS-IS)
**Why:** Asks for STDF + STIL + WGL + PAT + LOG + CSV + TXT + XML, die coordinates, MBIST/LBIST/wafer/cost/AI embeddings, 10 GB streaming, and speculative tables in a single pass. Will stall, duplicate tables, or reintroduce placeholder data.

**Use instead:** P7 (STDF+LOG) → P25–P27 (one format at a time) → P28 (schema review).

**Never create:** `user`, `alert`, `upload`, `notification` (duplicates of live tables).

### Master Cursor one-shot (DO NOT RUN AS-IS)
**Why:** Scope spans Stage 4 → Stage 9 with "zero placeholders anywhere" — too large for one agent session.

**Vision rules preserved above in Global rules.** Implementation order: P0 → P7 → P25–P30 → P18 → P19 → P20.

---

# PART G — Remaining work summary

| Item | Prompt | Blocker |
|------|--------|---------|
| PAT vendor grammar | P27 follow-up | Real Teradyne/Advantest `.pat` sample |
| RL recommendation generation | P18 | Parse data + feedback loop |
| Grouped migrations | P17 | Hygiene, not blocking |
| E2E tests | P19 | — |
| Tier 3 hardening | P20 / STEP 53 | OTel, ClamAV, Vault, K8s |
| Executive AI Optimize mock | — | Wire to real cost/rec engine or empty state |
| `die_results` schema | P28 follow-up | STDF die map extraction |

---

## Local run commands

```powershell
# backend
cd backend
# start PostgreSQL, Redis, and MinIO locally first
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000
arq app.workers.WorkerSettings   # separate terminal

# frontend — dashboard/.env.local
NEXT_PUBLIC_API_MODE=live
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Login: `alex@verilumen.ai` / `changeme123`

---

## Related implementation docs (not prompts — output artifacts)

| Doc | Purpose |
|-----|---------|
| `backend/STIL_PARSER.md` | STIL grammar reference |
| `backend/WGL_PARSER.md` | WGL grammar reference |
| `backend/PAT_PARSER.md` | PAT framework reference |
| `backend/PARSER_SCHEMA_ANALYSIS.md` | Schema review results |
| `backend/COST_ENGINE.md` | Cost formulas + API |
| `backend/DEEP_ANALYTICS.md` | Analytics architecture |
| `backend/PRODUCTION_HARDENING.md` | Hardening checklist |
| `backend/GAP_REPORT.md` | Backend gap tracker |
| `dashboard/FRONTEND_GAP_REPORT.md` | Frontend gap tracker |

---

*This file supersedes scattered prompt files. Historical CSV archives remain in `dashboard/prompts.csv`, `backend/prompts-backend.csv` for machine-readable backup.*
