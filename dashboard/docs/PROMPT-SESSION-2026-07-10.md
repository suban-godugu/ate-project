# VERILUMEN — Session Prompts (2026-07-10)

Archive of all prompts from the 2026-07-10 Cursor session (dashboard Git push, build fixes, hydration, Overall Scan Health drill-down).

---

## Session 29 — Push Dashboard to GitHub

**Date:** 2026-07-10

### Prompt

```text
Push COMPTY Dashboard code to https://github.com/Verilumen-Labss/dashboard.git

The local repository was stuck in a git rebase (local main at 9281d6a, remote at 98cf49d).
Fix: git rebase --abort, git checkout main, git reset --hard 9281d6a, git push --force-with-lease origin main.
```

**Outcome:** Dashboard `main` force-pushed successfully; local and remote synced at `9281d6a`.

---

## Session 30 — Build Error: apiRequest Export

**Date:** 2026-07-10

### Prompt

```text
Build Error: Export apiRequest doesn't exist in target module
./src/lib/api/kpi.ts imports apiRequest from @/lib/api/client but client exports apiFetch.
```

**Fix:** Use `apiFetch` + `buildQuery` in `kpi.ts`. Additional TypeScript fixes in WaferHeatmap, useLiveModuleCharts, scanChain types, useCostIntelligenceData, useScanChainData.

---

## Session 31 — Hydration Mismatch (fdprocessedid)

**Date:** 2026-07-10

### Prompt

```text
Console Error: Hydration mismatch on Scan Chain OverviewTab buttons — fdprocessedid attribute on <button> elements in RecommendationActionButtons and View Details buttons.
```

**Fix:** Add `suppressHydrationWarning` to shared `Button` component (browser extension injects `fdprocessedid` before React hydrates). Test in incognito to confirm.

---

## Session 32 — Overall Scan Health KPI Drill-Down

**Date:** 2026-07-10

### Prompt

```text
PROMPT: Overall Scan Health KPI Drill-Down Card — dedicated component only for overall-health KPI.
Three sections: Executive Summary (6 cards), Health Score Breakdown (table + final score), Healthy vs Failing Chains (3 cards).
Props-driven, no generic KpiDrillDownModal. See docs/PROMPT-OVERALL-SCAN-HEALTH-KPI-DRILLDOWN.md for full specification.
```

**Files:** `OverallScanHealthDrillCard.tsx`, `OverallScanHealthDrillDownModal.tsx`, `overallScanHealthDrillData.ts`, `ExecutiveOverviewKPIGrid.tsx`

---

## Session 33 — Save All Prompts

**Date:** 2026-07-10

### Prompt

```text
need to save all prompt for this all
```

**Archive targets:** `prompts.csv` (STEP 72–77), `docs/PROMPT-SESSION-2026-07-10.md`, `docs/PROMPT-OVERALL-SCAN-HEALTH-KPI-DRILLDOWN.md`, `docs/VERILUMEN-ALL-PROMPTS.md`, `ALL_PROMPTS.md`

---

## Session 34 — Total Scan Chains KPI Drill-down

**Date:** 2026-07-10

### Prompt

```text
Dedicated Total Scan Chains KPI drill card modal for total-chains KPI — distribution, status donut, breakdown, chain diagnosis. Props-driven component wired in ExecutiveOverviewKPIGrid.
```

**Files:** `TotalScanChainsDrillCard.tsx`, `TotalScanChainsDrillDownModal.tsx`, `totalScanChainsDrillData.ts`

---

## Session 35 — Healthy Chains KPI Drill-down

**Date:** 2026-07-10

### Prompt

```text
Dedicated Healthy Chains KPI drill card modal — executive summary, distribution bars, status donut, breakdown, health diagnosis.
```

**Files:** `HealthyChainsDrillCard.tsx`, `HealthyChainsDrillDownModal.tsx`, `healthyChainsDrillData.ts`

---

## Session 36 — Failing Chains KPI Drill-down

**Date:** 2026-07-10

### Prompt

```text
Dedicated Failing Chains KPI drill card modal — failure distribution, status, breakdown, failure diagnosis.
```

**Files:** `FailingChainsDrillCard.tsx`, `FailingChainsDrillDownModal.tsx`, `failingChainsDrillData.ts`

---

## Session 37 — Scan Coverage KPI Drill Card

**Date:** 2026-07-10

### Prompt

```text
Scan Coverage KPI Drill Card — dedicated component with 8 sections: Executive Summary, Coverage Distribution (tabbed horizontal bars), Coverage Status (donut), Coverage Diagnosis, Metadata, Timeline, Raw Coverage Data, Related Modules. Mock-data driven API-ready.
```

**Files:** `src/components/scan-chain/drill/scan-coverage/*`, `src/types/scanCoverage.ts`, `src/lib/mock/scanCoverage.ts`

---

## Session 38 — Average Diagnosis Confidence KPI Drill Card

**Date:** 2026-07-10

### Prompt

```text
Edit existing Average Diagnosis Confidence KPI drill only (91%). Replace Engineering Analytics with Diagnosis Confidence Status donut. Update executive summary, breakdown, Diagnosis Summary, metadata, Raw Diagnosis Data. No new page/route.
```

**Files:** `avgDiagnosisConfidenceDrillData.ts`, `AverageDiagnosisConfidenceDrill.tsx`, `buildKpiWorkspace.ts`, `KpiDrillDownWorkspace.tsx`

---

## Session 39 — Average Test Time KPI Drill Card

**Date:** 2026-07-10

### Prompt

```text
Edit existing Average Test Time KPI drill only (18.4 s). Replace Historical Trend with Test Time Distribution horizontal bars. Replace Engineering Analytics with Test Time Status donut. Test Time Analysis, metadata, Raw Test Time Data. No new page/route.
```

**Files:** `avgTestTimeDrillData.ts`, `AverageTestTimeDrill.tsx`, `buildKpiWorkspace.ts`, `KpiDrillDownWorkspace.tsx`

---

## Session 40 — Scan Coverage KPI Modal Popup

**Date:** 2026-07-10

### Prompt

```text
Scan Coverage KPI card must pop the KPI drill card modal when clicked — not navigate to a separate page route.
```

**Files:** `ScanCoverageDrillDownModal.tsx`, `ScanCoverageDrill.tsx`, `ExecutiveOverviewKPIGrid.tsx`

---

## Session 41 — Save All Prompts (Continuation)

**Date:** 2026-07-10

### Prompt

```text
have u save all promt
```

**Archive targets:** `prompts.csv` (STEP 77–84), `docs/PROMPT-SESSION-2026-07-10.md`, `docs/VERILUMEN-ALL-PROMPTS.md`, `ALL_PROMPTS.md`

---

## Session 42 — COMPTY Production Cleanup & Verification Audit

**Date:** 2026-07-10

### Prompt

```text
Perform complete production cleanup of COMPTY project. Analyze entire repository (dashboard, backend, docs, scripts, CI, Docker, configs). Identify mock data, junk files, unused components, duplicate code, unused dependencies, debug code, production config issues, live API gaps. Do NOT delete automatically. Generate detailed cleanup report with safe removal plan (Phases 1–3) and production readiness score.
```

**Output:** `docs/PRODUCTION-CLEANUP-AUDIT.md` — score **56/100**

---

## Session 43 — Production Cleanup README + Save All Prompts

**Date:** 2026-07-10

### Prompt

```text
Add all cleanup audit details to README file and save all prompts (STEPs 85–86) to prompts.csv, VERILUMEN-ALL-PROMPTS.md, PROMPT-SESSION-2026-07-10.md, ALL_PROMPTS.md.
```

**Files:** `README.md` (Production Cleanup Audit section), `docs/PRODUCTION-CLEANUP-AUDIT.md`, `prompts.csv`, archive docs

