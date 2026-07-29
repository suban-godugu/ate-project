# COMPTY Production Cleanup & Verification Audit

**Project:** COMPTY (ATE Intelligence Platform)  
**Audit date:** 2026-07-10  
**Scope:** `dashboard/`, `backend/`, root docs, CI, Docker, configs  
**Mode:** Read-only — **no files deleted or modified** (except this report + prompt archive)  
**Auditor:** Cursor Agent automated scan + import/reference verification  

---

## Executive Summary

| Metric | Value |
|--------|------:|
| Dashboard `src/` files scanned | 324 |
| Backend `app/` Python files scanned | 64 |
| Backend `tests/` files | 25 |
| Mock / synthetic data modules | 20+ |
| Junk / cache artifacts on disk | ~10,000+ (`.next/` build output) |
| Verified unused source files | 2 |
| Deprecated wrappers (still referenced) | 3 |
| Duplicate doc sets | 2 (root + `backend/`) |
| Empty source files | 0 |
| **`shared/` folder** | Does not exist |
| **Production Readiness Score** | **56 / 100** |

### Verdict

COMPTY has a **complete enterprise UI** and a **dual-mode architecture** (`mock` | `live`). The frontend defaults to **mock mode** (`NEXT_PUBLIC_API_MODE=mock`). The backend provides real auth, uploads, dashboard routes, and KPI workspace APIs, but **KPI workspace synthesis**, **dedicated drill builders**, and **Scan Coverage drill** remain mock-only. **Do not delete mock modules** until live replacements are verified end-to-end.

### Critical production blockers

1. `NEXT_PUBLIC_API_MODE=mock` in `.env.local` (defaults to mock if unset)
2. `buildKpiWorkspace.ts` + `kpi_workspace_service.py` still synthesize drill data
3. Scan Coverage drill (`lib/mock/scanCoverage.ts`) has **no live API path**
4. Six dedicated `*DrillData.ts` builders have **no live API path**
5. Backend `JWT_SECRET`, MinIO credentials use dev defaults unless overridden
6. `seed.py` creates `alex@verilumen.ai` / `changeme123` — must not run in production
7. `pytest` in production `requirements.txt` (bloats Docker image)
8. No dashboard Dockerfile (frontend deploy config incomplete)

---

## 1. Mock Data Report

### 1.1 Primary frontend mock datasets

| File path | Mock type | Production replacement | Status | Dependency impact |
|-----------|-----------|------------------------|--------|-------------------|
| `dashboard/src/lib/dummyData.ts` | Executive KPIs, patterns, cost trend, wafer heat generator | `GET /api/v1/dashboard/executive` | Replace with API | `usePlatformData`, executive page, search index |
| `dashboard/src/lib/scanChainData.ts` | Full scan-chain dataset (~1,156 lines) | `GET /api/v1/dashboard/scan-chain/{tab}` | Replace with API | All scan-chain tabs, drill builders |
| `dashboard/src/lib/waferData.ts` | Wafer analysis mock + SVG URIs | `GET /api/v1/dashboard/wafer-analysis/*` | Replace with API | Wafer module, 10 tabs |
| `dashboard/src/lib/recommendationData.ts` | Agent KPIs, recommendations | `GET /api/v1/dashboard/recommendation-analysis/{agent}` | Replace with API | Recommendation center |
| `dashboard/src/lib/mbistData.ts` | MBIST module data | `GET /api/v1/dashboard/mbist/{tab}` | Replace with API | MBIST tabs |
| `dashboard/src/lib/lbistData.ts` | LBIST module data | `GET /api/v1/dashboard/lbist/{tab}` | Replace with API | LBIST tabs |
| `dashboard/src/lib/costIntelligenceData.ts` | Cost intelligence mock | `GET /api/v1/dashboard/cost-intelligence/{tab}` | Replace with API | Cost module |
| `dashboard/src/lib/alertsData.ts` | Alerts feed mock | `GET /api/v1/dashboard/alerts/{tab}` | Replace with API | Alerts module |
| `dashboard/src/lib/uploadData.ts` | Upload history seeds + display helpers | `GET /api/v1/uploads` | Keep helpers; remove seeds in live | Upload modals |
| `dashboard/src/lib/kpiDrillDown/buildKpiWorkspace.ts` | Full KPI workspace builder (~1,326 lines) | `GET /api/v1/kpi/{id}/workspace` | Replace with API (partial exists) | Generic KPI modals |
| `dashboard/src/lib/kpiDrillDown/kpiProfiles.ts` | Widget profile config | `backend/app/data/kpi_profiles.py` | Keep as config (dedupe) | KPI widgets |
| `dashboard/src/lib/searchIndex.ts` | Client search index from mock | `GET /api/v1/search?q=` | Replace with API | Global search (live path exists) |
| `dashboard/src/lib/heatmapUtils.ts` | Seeded deterministic heat values | Real die/defect coordinates from DB | Replace with API | Wafer/scan heatmaps |
| `dashboard/src/lib/filterEngine.ts` | Client-side filter on mock rows | Server-side filter query params | Replace with API | Executive + filtered hooks |

### 1.2 KPI drill mock builders (mock-only — no `isLiveApi()` branch)

| File path | Mock type | Production replacement | Status | Dependency impact |
|-----------|-----------|------------------------|--------|-------------------|
| `dashboard/src/lib/mock/scanCoverage.ts` | Scan Coverage drill payload | New `GET /api/v1/kpi/scan-coverage/workspace` or dedicated endpoint | **Keep temporarily** | Modal + optional page route |
| `dashboard/src/lib/scan-chain/totalScanChainsDrillData.ts` | Total chains drill props | KPI workspace or dedicated drill API | **Keep temporarily** | `TotalScanChainsDrillDownModal` |
| `dashboard/src/lib/scan-chain/healthyChainsDrillData.ts` | Healthy chains drill | Same | **Keep temporarily** | `HealthyChainsDrillDownModal` |
| `dashboard/src/lib/scan-chain/failingChainsDrillData.ts` | Failing chains drill | Same | **Keep temporarily** | `FailingChainsDrillDownModal` |
| `dashboard/src/lib/scan-chain/overallScanHealthDrillData.ts` | Overall health drill | Same | **Keep temporarily** | `OverallScanHealthDrillDownModal` |
| `dashboard/src/lib/scan-chain/avgDiagnosisConfidenceDrillData.ts` | Avg diagnosis confidence data | `buildKpiWorkspace` live + conditionals | **Keep temporarily** | `KpiDrillDownWorkspace` when `avg-diagnosis-confidence` |
| `dashboard/src/lib/scan-chain/avgTestTimeDrillData.ts` | Avg test time data | Same | **Keep temporarily** | `KpiDrillDownWorkspace` when `avg-test-time` |

### 1.3 Backend mock / synthetic

| File path | Mock type | Production replacement | Status | Dependency impact |
|-----------|-----------|------------------------|--------|-------------------|
| `backend/app/services/kpi_workspace_service.py` | `_hash_seed()`, synthetic sparklines/tables | DB aggregates from `KpiSnapshot`, failures, patterns | **Replace with API** | `GET /kpi/{id}/workspace` |
| `backend/scripts/seed_data.py` | Rows mirroring frontend mock | One-time staging seed only | **Keep** (dev/staging) | `seed.py` |
| `backend/scripts/seed.py` | Dev user + seed runner | Production provisioning (not seed script) | **Keep** (dev only) | Local dev |
| `backend/app/services/filters.py` | `fake_filters` test helper | Request-scoped filters | Review usage | Dimension resolution |

### 1.4 Test fixtures (keep — not runtime)

| Path | Purpose |
|------|---------|
| `backend/tests/fixtures/sample.pat` | PAT parser tests |
| `backend/tests/fixtures/sample.wgl` | WGL parser tests |
| `backend/tests/fixtures/sample.stil` | STIL parser tests |
| `backend/tests/fixtures/sample_ate.log` | Upload pipeline tests |
| `backend/scripts/build_*_fixture.py` | Regenerate test fixtures |

---

## 2. Junk File Report

| Path | Type | Recommendation | Safe to delete? | Notes |
|------|------|----------------|-----------------|-------|
| `dashboard/.next/` | Next.js build output | **Ignore** (gitignored) | Yes (regenerated) | ~9,900+ files on disk |
| `dashboard/tsconfig.tsbuildinfo` | TS incremental cache | **Ignore** | Yes | Gitignored |
| `dashboard/next-env.d.ts` | Auto-generated | **Ignore** | Yes | Gitignored |
| `backend/.pytest_cache/` | Pytest cache | **Ignore** | Yes | Gitignored |
| `backend/PARSER_VERIFICATION_REPORT.json` | Generated report | **Move to .gitignore** | Maybe | Committed artifact |
| `dashboard/prompts.csv` | Dev prompt archive | **Exclude from prod image** | N/A | Not runtime |
| `dashboard/docs/PROMPT-*.md` | Dev specs | **Exclude from prod image** | N/A | Not runtime |
| Root `ALL_PROMPTS.md`, `MASTER_CURSOR_PROMPT.md`, etc. | Dev docs | **Exclude from prod image** | Yes from deploy | Keep in repo |
| Duplicate `backend/ALL_PROMPTS.md`, etc. | Copy of root docs | **Consolidate** | Yes (one copy) | No runtime impact |
| `.cursor/hooks/.session-state.json` | Hook state | **Ignore** | Yes | Gitignored |

**Not found:** `.bak`, `.tmp`, `.old`, screenshot images, sample uploads outside `tests/fixtures/`.

---

## 3. Unused File Report

Verified via import graph, grep for path strings, and dynamic import patterns.

| File path | Reason | References | Safe to delete? | Dependency impact |
|-----------|--------|------------|-----------------|-------------------|
| `dashboard/src/components/platform/UnifiedKPICard.tsx` | Deprecated re-export barrel | **0 imports** (only self + comment in `types/kpi.ts`) | **Yes** | Update `types/kpi.ts` comment |
| `dashboard/src/components/common/KPICard.tsx` | Deprecated re-export to `EnterpriseKPICard` | **0 direct imports**; module `KPICard.tsx` files import `EnterpriseKPICard` directly | **Yes** (verify dynamic imports) | None expected |
| `dashboard/src/lib/api/index.ts` | **Missing** — referenced in docs only | N/A | **Create or remove doc refs** | Broken if imported |

### Files to keep (not unused)

| Path | Reason |
|------|--------|
| `dashboard/src/app/scan-chain/page.tsx` (×8 legacy redirects) | Backward-compatible URL redirects |
| `dashboard/src/app/dashboard/scan-chain/drill/scan-coverage/page.tsx` | Optional deep-link route; modal is primary |
| `dashboard/src/components/common/ExecutiveKPIDrillDownModal.tsx` | Still used as fallback in `ExecutiveOverviewKPIGrid` |
| All 9 Zustand stores | Verified imported across hooks/components |

---

## 4. Duplicate Code Report

| Duplicate | Locations | Consolidation recommendation |
|-----------|-----------|------------------------------|
| Module `KPICard.tsx` wrappers | `scan-chain/`, `mbist/`, `lbist/`, `wafer/`, `cost-intelligence/`, `alerts/`, `recommendation/` | Single `ModuleKPICard` with `variant` prop |
| `globals.css` | `src/app/globals.css` + `src/styles/globals.css` (both imported in `layout.tsx`) | Merge into one file |
| KPI profile maps | `kpiProfiles.ts` ↔ `backend/app/data/kpi_profiles.py` | Shared JSON or codegen |
| Prompt archives | Root + `backend/` + `dashboard/docs/` | Single canonical `docs/` location |
| Drill data builders | 6× `*DrillData.ts` with identical patterns | Shared `buildDrillFromApi()` mapper |
| `ExecutiveKPIDrillDownModal` vs `KpiDrillDownModal` | Deprecated wrapper | Remove after all KPIs have dedicated modals |
| Legacy + dashboard routes | 9 redirect stubs | Keep for URL compat or configure nginx redirects |

---

## 5. Dependency Report

### Dashboard (`dashboard/package.json`)

| Package | Used? | Recommendation |
|---------|-------|----------------|
| `next`, `react`, `react-dom` | ✅ | Keep |
| `@tanstack/react-query` | ✅ | Keep |
| `recharts`, `framer-motion`, `lucide-react` | ✅ | Keep |
| `zustand` | ✅ | Keep |
| `@base-ui/react` | ✅ (shadcn primitives) | Keep |
| `class-variance-authority`, `clsx`, `tailwind-merge` | ✅ | Keep |
| `html2canvas` | ✅ (`exportUtils.ts`) | Keep if PNG export required |
| `react-dropzone` | ✅ (`UploadDropzone.tsx`) | Keep |
| `tw-animate-css` | ✅ (CSS) | Keep |
| **`react-icons`** | ❌ **Zero imports in `src/`** | **Remove from dependencies** |
| **`shadcn`** (npm package) | ❌ **Not imported at runtime** | **Move to devDependencies** or remove |

### Backend (`backend/requirements.txt`)

| Package | Used? | Recommendation |
|---------|-------|----------------|
| `fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `alembic` | ✅ | Keep |
| `redis`, `arq`, `minio` | ✅ | Keep |
| `python-jose`, `passlib`, `pydantic-settings` | ✅ | Keep |
| `stdf-tamer` | ✅ (parsers) | Keep |
| `reportlab` | ✅ (PDF export) | Keep |
| **`pytest`, `pytest-asyncio`** | Tests only | **Move to `requirements-dev.txt`** |

---

## 6. Debug & Development Code

| Area | Finding | Action |
|------|---------|--------|
| `dashboard/src/**` | No `console.log/warn/error` | ✅ Clean |
| `dashboard/src/**` | No `TODO`, `FIXME`, `HACK` | ✅ Clean |
| `backend/app/**` | No debug `print()` | ✅ Clean |
| `backend/scripts/**` | CLI `print()` in seed/backup/verify | ✅ Keep (scripts only) |
| `KpiDrillDownWorkspace.tsx` | `dataSource="mock"` default prop | Config — set via env in prod |
| README / docs | References "simulated" features | Documentation only |

---

## 7. Production Configuration Audit

### Frontend (`dashboard/.env.local`)

| Variable | Current / default | Production requirement |
|----------|-------------------|------------------------|
| `NEXT_PUBLIC_API_MODE` | `mock` | **Must be `live`** |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Production API URL + HTTPS |

### Backend (`backend/.env.example`)

| Variable | Risk | Production requirement |
|----------|------|------------------------|
| `JWT_SECRET` | `CHANGE_ME` placeholder | **Must rotate** |
| `MINIO_SECRET_KEY` | `CHANGE_ME` | **Must rotate** |
| `DATABASE_URL` | Local dev default | Production Postgres URL |
| `CORS_ORIGINS` | `localhost:3000` only | Add production dashboard origin |
| `ENVIRONMENT` | `development` | Set `production` |
| `ENABLE_HSTS` | `false` | Enable behind TLS |

### Docker

| Item | Status |
|------|--------|
| `backend/Dockerfile` | ✅ Exists (Python 3.12-slim) |
| `backend/docker-compose.yml` | ✅ Postgres, Redis, MinIO, API, worker |
| Dashboard Dockerfile | ❌ **Missing** |
| `docker-compose` dev mounts | `.:/app` volume — **remove for prod** |
| API `--reload` in compose | Dev only — **remove for prod** |

### CI (`.github/workflows/ci.yml`)

| Job | Status |
|-----|--------|
| Backend unit tests | ✅ Postgres + Redis services |
| Frontend lint + vitest + build | ✅ |
| E2E Playwright | ❌ Not in CI (script exists: `npm run test:e2e`) |
| Security scan | ❌ Not configured |

### Authentication

| Item | Status |
|------|--------|
| Backend JWT auth | ✅ Real (`auth.py`) |
| Frontend `AuthGuard` | ✅ Live mode |
| Mock mode | Skips auth — **disable mock in prod** |
| Seed credentials | ⚠️ `changeme123` — never seed in prod |

---

## 8. Live API Migration Status

| Module | Hook / source | Live API endpoint | Migration status |
|--------|---------------|-------------------|------------------|
| Executive dashboard | `usePlatformData` | `GET /dashboard/executive` | ⚠️ **Dual** — mock fallback always available |
| Scan Chain | `useScanChainData` | `GET /dashboard/scan-chain/{tab}` | ⚠️ **Dual** |
| MBIST | `useMbistData` | `GET /dashboard/mbist/{tab}` | ⚠️ **Dual** |
| LBIST | `useLbistData` | `GET /dashboard/lbist/{tab}` | ⚠️ **Dual** |
| Wafer Analysis | `useWaferData` | `GET /dashboard/wafer-analysis/*` | ⚠️ **Dual** |
| Recommendation | `useRecommendationData` | `GET /dashboard/recommendation-analysis/{agent}` | ⚠️ **Dual** |
| Cost Intelligence | `useCostIntelligenceData` | `GET /dashboard/cost-intelligence/{tab}` | ⚠️ **Dual** |
| Alerts | `useAlertsData` | `GET /dashboard/alerts/{tab}` | ⚠️ **Dual** |
| Generic KPI drill | `useKpiDrillDownWorkspace` | `GET /kpi/{id}/workspace` | ⚠️ **Dual** — API returns synthetic data |
| Overall Scan Health drill | `overallScanHealthDrillData.ts` | None | ❌ **Mock only** |
| Total Scan Chains drill | `totalScanChainsDrillData.ts` | None | ❌ **Mock only** |
| Healthy Chains drill | `healthyChainsDrillData.ts` | None | ❌ **Mock only** |
| Failing Chains drill | `failingChainsDrillData.ts` | None | ❌ **Mock only** |
| Scan Coverage drill | `mock/scanCoverage.ts` | None | ❌ **Mock only** |
| Avg Diagnosis Confidence | `avgDiagnosisConfidenceDrillData.ts` + workspace | Partial via workspace API | ⚠️ **Hybrid** |
| Avg Test Time | `avgTestTimeDrillData.ts` + workspace | Partial via workspace API | ⚠️ **Hybrid** |
| Global search | `useGlobalSearch` | `GET /search?q=` | ⚠️ **Dual** |
| Notifications | `useNotifications` | Notifications API | ⚠️ **Dual** |
| Upload history | `useUploadHistory` | Uploads API | ⚠️ **Dual** |
| Upload flow | `uploadFlow.ts` | Presign + MinIO + SSE | ✅ **Live path exists** |
| Auth | `auth.ts` | `POST /auth/login` | ✅ **Live** |
| Audit logs | `useAuditLogs` | Audit API | ✅ **Live only** |
| Primary actions | `usePrimaryAction` | Actions SSE API | ⚠️ **Dual** |
| Theme sync | `useThemePreferencesSync` | User prefs API | ⚠️ **Live when authenticated** |

**Legend:** ⚠️ Dual = works in live mode but mock builder still ships in bundle. ❌ Mock only = no live branch.

---

## 9. Safe Removal Plan

### Phase 1 — Safe (no runtime impact)

| Action | Items | Verification |
|--------|-------|--------------|
| Delete build cache | `dashboard/.next/`, `tsconfig.tsbuildinfo` | Regenerated by `npm run build` |
| Remove unused npm package | `react-icons` | `grep -r react-icons src/` → 0 matches |
| Move CLI package | `shadcn` → devDependencies | Not imported in `src/` |
| Split Python deps | `pytest*` → `requirements-dev.txt` | CI installs both files |
| Delete deprecated wrappers | `UnifiedKPICard.tsx`, `common/KPICard.tsx` | Zero import grep |
| Gitignore generated report | `PARSER_VERIFICATION_REPORT.json` | Regenerated by script |
| Consolidate duplicate docs | `backend/ALL_PROMPTS.md` etc. | Keep root or `dashboard/docs/` copy |
| Exclude from prod Docker image | `prompts.csv`, `docs/PROMPT-*`, `.cursor/` | Build-stage `.dockerignore` |

### Phase 2 — Requires verification before removal

| Action | Items | Verification steps |
|--------|-------|-------------------|
| Remove scan-coverage page route | `app/dashboard/scan-chain/drill/scan-coverage/page.tsx` | Confirm no bookmarks/links; grep route string |
| Remove `ExecutiveKPIDrillDownModal` | After all KPIs have dedicated modals | Grep `ExecutiveKPIDrillDownModal` usage |
| Merge duplicate CSS | `app/globals.css` + `styles/globals.css` | Visual regression on all pages |
| Create `lib/api/index.ts` barrel | Or remove README references | Typecheck |

### Phase 3 — Replace first (do NOT delete until live verified)

| Keep until replaced | Live replacement | Verification |
|--------------------|------------------|--------------|
| All `src/lib/*Data.ts` files | Dashboard tab APIs return full payloads | E2E per module with `API_MODE=live` |
| `buildKpiWorkspace.ts` | KPI workspace API returns real DB data | Compare modal data vs DB |
| `*DrillData.ts` + `mock/scanCoverage.ts` | Dedicated drill endpoints | Wire hooks with `isLiveApi()` |
| `searchIndex.ts` mock branch | Search API indexed data | Search returns same routes |
| `seed_data.py` | Production data ingestion pipeline | N/A for runtime |

---

## 10. Production Readiness Score

### Score breakdown

| Category | Weight | Score | Weighted |
|----------|-------:|------:|---------:|
| Mock data removal / live wiring | 25 | 8 | 8.0 |
| Dead code & duplicate cleanup | 15 | 12 | 12.0 |
| Dependency health | 15 | 13 | 13.0 |
| Code quality (debug, types, lint) | 15 | 14 | 14.0 |
| API integration completeness | 15 | 6 | 6.0 |
| Security & configuration | 10 | 4 | 4.0 |
| Build & deployment readiness | 5 | 2 | 2.0 |
| **Total** | **100** | — | **56 / 100** |

### Issue priority matrix

#### Critical

- `NEXT_PUBLIC_API_MODE=mock` in production deploy
- Default JWT / MinIO secrets if not rotated
- `seed.py` with default password runnable in production
- KPI workspace API still synthesizes fake analytics

#### High

- Six dedicated drill cards + Scan Coverage are mock-only
- No dashboard production Dockerfile / deploy config
- `pytest` in production Python requirements
- `react-icons` unused dependency in bundle lockfile

#### Medium

- Duplicate `globals.css` imports
- Duplicate prompt/doc archives (root + backend)
- `PARSER_VERIFICATION_REPORT.json` committed
- E2E tests not in CI pipeline
- Mobile sidebar has no hamburger menu

#### Low

- Deprecated `UnifiedKPICard.tsx` / `KPICard.tsx` barrels
- Optional standalone scan-coverage page route redundant with modal
- README length / outdated "mock only" sections in UI matrix

---

## Appendix A — Repository layout

```
bd-1/
├── dashboard/          # Next.js 16 frontend (separate git repo)
├── backend/            # FastAPI backend (nested .git)
├── .github/workflows/  # Monorepo CI
├── ALL_PROMPTS.md        # Dev archive
├── APPLICATION_STATUS.md
├── BUILD_SEQUENCE.md
└── MASTER_CURSOR_PROMPT.md
```

**No `shared/` directory exists.**

---

## Appendix B — Files scanned summary

| Area | File count |
|------|----------|
| `dashboard/src/` | 324 |
| `dashboard/src/lib/` (mock-heavy) | ~45 |
| `dashboard/src/hooks/` | ~30 |
| `dashboard/src/components/` | ~230 |
| `backend/app/` | 64 |
| `backend/tests/` | 25 |
| `backend/scripts/` | 10 |

---

*This audit is read-only. No application code was modified. Re-run after each migration phase to update scores.*
 