# COMPTY / VERILUMEN — UI Module Documentation

**Audience:** Product, design, and engineering documentation  
**Scope:** Dashboard · Scan Chain Analysis · Wafer Analysis · Recommendation Analysis  
**Date:** 2026-07-14  
**Source of truth:** Live UI components + mock data in `dashboard/src`

---

## Contents

1. [Executive Dashboard](#1-executive-dashboard)
2. [Scan Chain Analysis](#2-scan-chain-analysis)
3. [Wafer Analysis](#3-wafer-analysis)
4. [Recommendation Analysis](#4-recommendation-analysis)

**All KPIs only:** [`KPI-COMPLETE-LIST.md`](./KPI-COMPLETE-LIST.md)

---

# 1. Executive Dashboard

| Property | Value |
|----------|-------|
| **Route** | `/dashboard` |
| **Title** | Executive Dashboard |
| **Primary action** | AI Optimize |
| **Page shell** | Sidebar + Top Navbar + `LiveModuleGate` |

### Layout (top → bottom)

1. KPI grid (6 cards)  
2. Wafer Cost Heatmap  
3. Cost Trend Chart | Pattern Analysis Table (2 columns)  
4. Optimization Engine | Optimization Results (2 columns)

---

## 1.1 KPIs

| ID | Title | Example value | Change | Meaning |
|----|-------|---------------|--------|---------|
| `total-test-cost` | Total Test Cost | `$2.4M` | −4.2% | Lower is better |
| `cost-per-wafer` | Cost per Wafer | `$184` | −2.8% | Lower is better |
| `cost-per-die` | Cost per Die | `$0.018` | −5.1% | Lower is better |
| `test-time` | Test Time | `42.6s` | −3.2% | Lower is better |
| `yield` | Yield | `94.2%` | +1.8% | Higher is better |
| `roi-improvement` | ROI Improvement | `+18.4%` | +6.2% | Higher is better |

**Card features:** Icon, large value, % change badge, 7-point sparkline, hover lift.  
**Drill-down:** None on this page (cards are display-only).

---

## 1.2 Charts & Heatmaps

### Wafer Cost Heatmap

| Property | Detail |
|----------|--------|
| Title | Wafer Cost Heatmap (Spatial AI) |
| Type | Canvas spatial heatmap (40×40 circular wafer) |
| Subtitle | Interactive spatial cost analysis across wafer surface |
| Overlay modes | Fail Density · Yield · **Cost** (default) |
| Controls | Pan, Zoom (up to 3×), Reset, Fullscreen |
| Tooltip | Die `[row, col]` + metric % |
| Legend | Green → Yellow → Orange → Red (Low → High Cost) |

### Cost Trend Analysis

| Property | Detail |
|----------|--------|
| Title | Cost Trend Analysis |
| Type | Dual-axis line chart (Recharts) |
| Subtitle | Daily total cost and cost per wafer — 7 days |
| Series | Total Cost ($K) purple · Cost per Wafer ($) cyan |
| Range | Mon–Sun |

---

## 1.3 Tables

### Pattern Analysis Table

| Property | Detail |
|----------|--------|
| Subtitle | Enterprise test pattern performance and recommendations |
| Row count (mock) | 8 (`PAT-001` … `PAT-008`) |
| Page size | 5 |
| Features | Search by Pattern ID, column sort, pagination |

| Column | Format |
|--------|--------|
| Pattern ID | Monospace (e.g. `PAT-001`) |
| Test Time | seconds |
| Cost | `$` |
| Fail Rate | `%` |
| Detect Power | `%` |
| ROI Score | number |
| Recommendation | Badge: Keep / Review / Remove |

---

## 1.4 Other sections

### Test Optimization Engine

| Slider | Default | Range |
|--------|---------|-------|
| Maximum Cost | `$2,500` | $1,000–$5,000 |
| Yield Target | `95%` | 85–99% |
| Maximum Test Time | `45s` | 20–120s |

**CTA:** Run AI Optimization (simulated ~1.8s)

### Optimization Results

| Metric | Example |
|--------|---------|
| Estimated Cost Reduction | 18.4% |
| Estimated Time Savings | 12.6s |
| Projected Yield | 95.8% |
| Patterns Reduced | 14 |
| Total Savings | $284K |

**CTA:** View Optimized Pattern Set

### Global chrome (affects this page)

- Sidebar Quick Filters: Date · Fab · Tester · Product · Lot · Wafer  
- Navbar: Search · Calendar · Notifications · Upload Data · Upload Log · Export · AI Optimize

---

# 2. Scan Chain Analysis

| Property | Value |
|----------|-------|
| **Route** | `/dashboard/scan-chain` |
| **Title** | Scan Chain Analysis |
| **Primary action** | AI Diagnose |
| **Tabs (4)** | Overview · Pattern Analysis · Failure Analysis · Scan Diagnosis |

---

## 2.1 Overview Tab

### Executive KPIs (7)

| ID | Title | Example | Subtitle |
|----|-------|---------|----------|
| `overall-health` | Overall Scan Health | 77.9% | Healthy vs total chain ratio |
| `total-chains` | Total Scan Chains | 2,933 | Active chains across all modules |
| `healthy-chains` | Healthy Chains | 2,284 | Passing verification & diagnosis |
| `failing-chains` | Failing Chains | 142 | Require debug or repair action |
| `scan-coverage` | Scan Coverage | 96.8% | Fault coverage across patterns |
| `avg-diagnosis-confidence` | Average Diagnosis Confidence | 91% | AI flop-level localization accuracy |
| `avg-test-time` | Average Test Time | 18.4s | Mean pattern execution runtime |

**Drill-downs (dedicated modals):**

| KPI | Modal |
|-----|-------|
| Overall Scan Health | `OverallScanHealthDrillDownModal` |
| Total Scan Chains | `TotalScanChainsDrillDownModal` |
| Healthy Chains | `HealthyChainsDrillDownModal` |
| Failing Chains | `FailingChainsDrillDownModal` |
| Scan Coverage | `ScanCoverageDrillDownModal` (8 sections) |
| Avg Diagnosis Confidence / Avg Test Time | Generic enterprise KPI workspace |

---

### Charts & visualizations

| Title | Type | Subtitle / notes |
|-------|------|------------------|
| Scan Chain Health | Donut | Healthy · Warning · Failing · Unknown (center: Total Chains) |
| Top 10 Failing Chips | Horizontal bar | Ranked by fail count |
| Top 10 Failing Scan Chains | Horizontal bar | Ranked by failure frequency |
| Top 10 Patterns by Failures | Horizontal bar | Patterns linked to most failures |
| Failure Trend | Line | Last 7 periods |
| Pattern Growth | Line | Last 7 periods |
| Coverage Trend | Line | Last 7 periods |
| Diagnosis Trend | Line | Last 7 periods |
| Yield Trend | Line | Last 7 periods |
| Chain Growth | Line | Last 7 periods |
| Recurring Failure Trend | Line | Last 7 periods |
| Repair Success Trend | Line | Last 7 periods |
| Scan Chain Heatmap | Grid heatmap 16×24 | Spatial failure density |
| Failure Density Heatmap | Spatial 20×20 | Wafer-level failure density |
| Die Failure Heatmap | Spatial 16×16 | Die-level hotspots |
| Scan Chain Topology Viewer | Topology graph | Broken chains, failing cells, debug locations |

**Health donut segments (example):** Healthy 2,284 · Warning 421 · Failing 142 · Unknown 86 · Total 2,933

---

### Summary mini-KPI sections

**Pattern Analysis Summary**

| Label | Value |
|-------|-------|
| Pattern Files Ingested | 2,846 |
| Pattern Coverage | 98.42% |
| Pattern Clusters | 126 |
| Redundant Patterns | 38 |
| Metadata Extracted | 2,846 |
| Embeddings Generated | 2,846 |

**Failure Analysis Summary**

| Label | Value |
|-------|-------|
| Overall Failure Rate | 2.84% |
| Failing Test Patterns | 1,246 |
| Root Cause Confidence | 94% |
| Recurring Failures | 183 |
| Lot Failure Rate | 3.11% |
| Wafer Failure Rate | 2.43% |

**Scan Diagnosis Summary**

| Label | Value |
|-------|-------|
| Failing Scan Chains | 14 |
| Failing Scan Cells | 73 |
| Chain Breaks Detected | 9 |
| Average Diagnosis Confidence | 91% |
| Diagnosis Reports | 4 |
| Diagnoses Pending Review | 6 |

*(Section links navigate to Pattern Analysis / Failure Analysis / Scan Diagnosis tabs.)*

---

### Tables

| Title | Columns |
|-------|---------|
| Latest Uploads | Latest Upload · Patterns Parsed · Chains Parsed · Failures Found · Parser · Upload Time · Status |

Page size: 5 · searchable

---

### Other sections

| Section | Details |
|---------|---------|
| **AI Executive Summary** | Most Critical Chain/Pattern · Highest Failure Lot/Wafer · Most Common Root Cause · Confidence 91% · Estimated Saving $284K/quarter · Priority Recommendation · CTA: Run AI Diagnosis |
| **Recommendation Preview** | Up to 4 cards (DX-001…DX-004) with confidence, saving, status, approve/reject, View Details |
| **Alerts Preview** | Critical 1 · High 2 · Warning 1 + alert list · link to `/dashboard/alerts` |
| **Recent Upload Activity** | Latest Uploads table |

---

## 2.2 Pattern Analysis Tab

### KPIs (11)

| ID | Title | Example | Status / subtitle |
|----|-------|---------|-------------------|
| `files-ingested` | Pattern Files Ingested | 2,846 | 100% Imported · STIL • WGL • PAT |
| `vectors-parsed` | Scan Vectors Parsed | 99.7% | SLA Met · 2.8M Scan Vectors |
| `file-integrity` | File Integrity | 100% | PASS |
| `pattern-coverage-kpi` | Pattern Coverage | 98.42% | +0.2% ATPG Delta |
| `metadata-extracted` | Metadata Extracted | 2,846 | Complete |
| `embeddings-generated` | Embeddings Generated | 2,846 | 100% |
| `pattern-clusters` | Pattern Clusters | 126 | Threshold 0.87 |
| `redundant-patterns` | Redundant Patterns | 38 | 94% Confidence |
| `similarity-analyses` | Similarity Analyses | 2,846 | 182 ms |
| `pass-fail-linked` | Pass / Fail Linked | 2,741 / 2,846 | 96.3% |
| `quality-reports` | Quality Reports | 24 | PDF • Excel • HTML |

**Grid:** 4 columns @ xl · each card opens enterprise KPI drill-down workspace.

---

### Charts (4)

| Title | Type | Subtitle |
|-------|------|----------|
| Pattern Import Trend | Dual line | Weekly imported vs. validated files |
| Pattern Coverage Trend | Line | ATPG fault coverage over time |
| Pattern Cluster Distribution | Pie / donut | AI cluster: Stuck-At · Transition · Bridging · Timing · Other |
| Pattern Similarity | Scatter | Coverage vs. similarity score by cluster |

---

### Tables

| Title | Columns |
|-------|---------|
| Pattern Analysis Table | Pattern ID · Pattern Name · File Type · Status · Recommendation |

*(Full data also includes Coverage, Compression, Vectors, Cluster, Similarity, Redundancy, Quality.)*  
Page size: 6 · search · sort · pagination

**Other:** No AI summary card, no header action bar (removed by design).

---

## 2.3 Failure Analysis Tab

### KPIs (9)

| ID | Title | Example | Status / subtitle |
|----|-------|---------|-------------------|
| `imported-files` | Imported Test Files | 248 | Validated · STDF + Tester Logs |
| `overall-failure-rate` | Overall Failure Rate | 2.84% | Within Target |
| `failing-patterns` | Failing Test Patterns | 1,246 | Active · 286 Recurring |
| `die-failure-rate` | Die Failure Rate | 1.92% | Open Heatmap · 48,320 Dies |
| `wafer-failure-rate` | Wafer Failure Rate | 2.43% | Open Heatmap · 112 Wafers |
| `lot-failure-rate` | Lot Failure Rate | 3.11% | Monitor · 14 / 236 Lots |
| `fault-categories` | Fault Categories | 5 | Classified · 2 Unknown |
| `root-cause-confidence` | Root Cause Confidence | 94% | High Confidence · Bridge Fault |
| `recurring-failures` | Recurring Failures | 183 | Tracked · 37 Lots |

Each KPI opens enterprise KPI drill-down workspace.

---

### Charts (4)

| Title | Type | Subtitle |
|-------|------|----------|
| Overall Failure Trend | Dual line | Total failures vs. resolved |
| Failure Rate Trend | Line | Aggregate failure rate over time |
| Failure Distribution | Pie | Stuck-at · Bridging · Transition Delay · Cell-Aware · Scan Fault · Unknown |
| Failure by Lot | Horizontal bar | Top lots by failure count |

---

### Tables

| Title | Columns |
|-------|---------|
| Failure Analysis Table | Failure ID · Pattern ID · Lot ID · Wafer ID · Die ID · Fault Category · Root Cause · Confidence · Severity · Status · Recommendation · Timestamp |

Page size: 6 · **Export** button

---

## 2.4 Scan Diagnosis Tab

### KPIs (12) — 3 sections

#### Detection & Identification

| ID | Title | Example | Status |
|----|-------|---------|--------|
| `sd-failing-chains` | Failing Scan Chains | 14 | Detected from Failure Logs |
| `sd-failing-cells` | Failing Scan Cells | 73 | Confidence Score Available |
| `sd-chain-breaks` | Chain Breaks Detected | 9 | Topology View Available |
| `sd-shift-capture` | Shift / Capture Issues | 21 | Shift 13 · Capture 8 |

#### Topology & Ranking

| ID | Title | Example | Status |
|----|-------|---------|--------|
| `sd-topology-chains` | Chains in Topology | 128 | Loaded & Visualized |
| `sd-chains-ranked` | Chains Ranked | 14 | Failure Frequency Ranking |
| `sd-failure-correlations` | Failure Correlations | 61 | Failure-to-Chain Mapping |
| `sd-top-failing-chain` | Top Failing Chain | SC_14 | 38 Failures Across 5 Lots |

#### Diagnosis & Reporting

| ID | Title | Example | Status |
|----|-------|---------|--------|
| `sd-diagnosis-reports` | Diagnosis Reports | 4 | Generated Today |
| `sd-debug-locations` | Debug Locations | 31 | Supporting Evidence Available |
| `sd-avg-confidence` | Average Diagnosis Confidence | 91% | All Results Scored |
| `sd-pending-review` | Diagnoses Pending Review | 6 | Low Confidence 4 · Ambiguous 2 |

Each KPI opens topology-first KPI drill-down workspace.

---

### Charts (3)

| Title | Type | Subtitle |
|-------|------|----------|
| Failure Localization Distribution | Donut | Broken Chains · Shift · Capture · Cell Failures · Unknown |
| Chain Failure Ranking | Horizontal bar | Top 10 failing scan chains |
| Diagnosis Confidence Trend | Line | Last 30 days |

### Tables

None on this tab.

### Other sections

| Section | Details |
|---------|---------|
| **Scan Diagnosis Workflow** | Failure Logs → Pattern Correlation → Topology Analysis → Scan Diagnosis Engine → Root Cause Detection → Debug Recommendation → Engineer Review → Validation |
| **Action bar** | View Topology · Export PDF · Export Excel · Generate Debug Report · Approve Diagnosis |

---

# 3. Wafer Analysis

| Property | Value |
|----------|-------|
| **Route** | `/dashboard/wafer-analysis` |
| **Title** | Wafer Analysis |
| **Subtitle** | AI-powered wafer defect classification, yield analysis, hotspot detection and spatial intelligence |
| **Primary action** | Generate Yield Analysis |
| **Tabs (10)** | Overview · Centre · Donut · Edge-Ring · Scratch · Near-Full · Normal · Edge-Loc · Local · Random |

---

## 3.1 Overview Tab

### KPIs — Input & Die Statistics (5)

| Title | Example |
|-------|---------|
| Number of Wafers | 1,248 |
| Number of Dies | 992,640 |
| Good Dies | 931,284 |
| Bad Dies | 61,356 |
| Defect Clusters | 342 |

### Defect Classification cards (9 — clickable → open defect tab)

| Title | Primary | Subtitle |
|-------|---------|----------|
| Centre | 88% | 42 wafers · 78% confidence |
| Donut | 89.4% | 38 wafers · 80% confidence |
| Edge-Ring | 90.8% | 56 wafers · 82% confidence |
| Scratch | 92.2% | 24 wafers · 84% confidence |
| Near-Full | 93.6% | 12 wafers · 86% confidence |
| Normal | 88% | 312 wafers · 88% confidence |
| Edge-Loc | 89.4% | 48 wafers · 90% confidence |
| Local | 90.8% | 36 wafers · 78% confidence |
| Random | 92.2% | 280 wafers · 80% confidence |

### Charts

| Title | Type | Detail |
|-------|------|--------|
| Positive / Negative Yield | Donut | Positive 93.8% · Negative 6.2% · center Net Yield 93.8% |

### Gallery — Wafer Defect Classification Gallery (9 cards)

Each card shows:

- Wafer / overlay / density thumbnails  
- Label badge  
- Avg Yield · Confidence · Good Dies · Bad Dies · total dies  
- CTA: **View analysis** → defect tab  

### Upload Workflow (8 steps)

1. Upload Wafer Image  
2. AI Classification  
3. Overlay Generation  
4. Fail Density Generation  
5. Defect Classification  
6. Yield Calculation  
7. Recommendation Engine  
8. Save Analysis  

### Bottom Summary Bar

| Label | Value |
|-------|-------|
| Total Wafers | 1,248 |
| Total Dies | 992,640 |
| Good Dies | 931,284 |
| Bad Dies | 61,356 |
| Average Yield | 93.8% |
| Estimated Savings | $284K |
| AI Confidence | 91.4% |

---

## 3.2 Defect Class Tabs (shared layout × 9)

All nine defect tabs use the same structure; only KPI values and descriptions change.

### Common sections (top → bottom)

1. **Header card** — `{Label} Defect Analysis` + class description  
2. **KPI grid** — 8 KPIs  
3. **Upload History** — selectable table (10 uploads)  
4. **Wafer Analysis Views** — 2 canvas maps  
5. **Analysis Information** — info panel  
6. **Analysis Workflow** — 8-step pipeline  

### Shared KPI titles (every defect tab)

| # | Title |
|---|-------|
| 1 | Total Wafers |
| 2 | Good Dies |
| 3 | Bad Dies |
| 4 | Average Yield |
| 5 | Average Confidence |
| 6 | Total Dies |
| 7 | Defect Severity |
| 8 | Estimated Yield Loss |

### KPI values by tab

| KPI | Centre | Donut | Edge-Ring | Scratch | Near-Full | Normal | Edge-Loc | Local | Random |
|-----|--------|-------|-----------|---------|-----------|--------|----------|-------|--------|
| Total Wafers | 42 | 38 | 56 | 24 | 12 | 312 | 48 | 36 | 280 |
| Good Dies | 748 | 744 | 740 | 736 | 732 | 728 | 724 | 720 | 716 |
| Bad Dies | 48 | 54 | 60 | 66 | 72 | 78 | 84 | 90 | 96 |
| Average Yield | 88% | 89.4% | 90.8% | 92.2% | 93.6% | 88% | 89.4% | 90.8% | 92.2% |
| Average Confidence | 78% | 80% | 82% | 84% | 86% | 88% | 90% | 78% | 80% |
| Total Dies | 796 | 796 | 796 | 796 | 796 | 796 | 796 | 796 | 796 |
| Defect Severity | High | High | High | Medium | Medium | Medium | Low | Low | Low |
| Estimated Yield Loss | 12.0% | 10.6% | 9.2% | 7.8% | 6.4% | 12.0% | 10.6% | 9.2% | 7.8% |

### Tab descriptions

| Tab | Description |
|-----|-------------|
| **Centre** | Centre defect patterns with localized die failures in the wafer core region |
| **Donut** | Ring-shaped annular failure band between centre and edge zones |
| **Edge-Ring** | Peripheral edge ring defects (handling, chucking, edge bead) |
| **Scratch** | Linear scratch signatures (probe card or transport damage) |
| **Near-Full** | Near full-wafer failure with catastrophic yield loss |
| **Normal** | Baseline maps with random defect scatter and healthy yield |
| **Edge-Loc** | Localized edge clusters at specific quadrants / flat zones |
| **Local** | Compact local clusters (process excursion / reticle anomalies) |
| **Random** | Stochastic scatter without dominant spatial signature |

### Upload History table

| Columns |
|---------|
| Thumbnail · Wafer · Lot · Upload Date · Confidence · Action (Delete) |

### Canvas maps

| View | Detail |
|------|--------|
| **Overlay Analytics** | Die fail overlay (pass=teal / fail=yellow) + cyan cluster boxes |
| **Fail Density Map** | Blurred density heatmap + crosshair + X·Y hotspot tooltip |

### Analysis Information panel

Defect Type · Assigned Lot · Confidence · Good Dies · Bad Dies · Total Dies · Yield · Average Cost · Recommendation

### Analysis Workflow

Same 8 steps as Overview Upload Workflow (title: Analysis Workflow).

**No charts beyond canvases · No action bar · No AI summary card** on defect tabs.

---

# 4. Recommendation Analysis

| Property | Value |
|----------|-------|
| **Route** | `/dashboard/recommendation-analysis` |
| **Title** | Recommendation Analysis |
| **Primary action** | Generate AI Recommendations |
| **Tabs (3)** | Pattern Recommendation Agent · Scan Debug Recommendation Agent · Test Optimization Recommendation Agent |

---

## 4.1 Pattern Recommendation Agent

**Header:** ATPG pattern optimization, redundancy removal, ordering, coverage, low-power.

### KPIs (10 — flat grid)

| # | Title | Value | Subtitle / Status |
|---|-------|-------|-------------------|
| 1 | Redundant Patterns | 34 / 342 | 94% AI Confidence |
| 2 | Removal Recommended | 28 | 12.4% Test Time Reduction |
| 3 | Removal Confidence | 92% | High Confidence |
| 4 | Reorder Recommendations | 42 | 5.8% Fault Escape Reduction |
| 5 | ATPG Additions Suggested | 18 | Coverage Improvement |
| 6 | Fault Models Targeted | 4 | SA • TD • Bridging • Cell-Aware |
| 7 | Low-Power Sets | 12 | 18% Switching Reduction |
| 8 | Estimated Power Saving | 21.6% | — |
| 9 | Coverage Delta | 98.1% → 99.3% | +1.2% Gain |
| 10 | Total Recommendations | 104 | Remove • Reorder • Add • Low Power |

### Charts (4)

| Title | Type | Detail |
|-------|------|--------|
| Recommendation Distribution | Pie | Remove 28 · Reorder 42 · ATPG 18 · Low Power 16 |
| Coverage Improvement Trend | Line | Current vs Projected |
| Power Saving Trend | Line | Current vs Optimized |
| Pattern Cluster Analysis | Pie | Cluster A–D |

### Table — Pattern Recommendation Table

| Columns |
|---------|
| Recommendation ID · Pattern ID · Recommendation · Priority · Confidence · Coverage Gain · Power Saving · Status · Action |

Rows: `PAT-REC-001` … `PAT-REC-006`

### AI Summary

| Metric | Value |
|--------|-------|
| Patterns to Remove | 28 |
| Patterns to Reorder | 42 |
| New ATPG Patterns | 18 |
| Coverage Gain | +1.2% |
| Power Saving | 21.6% |
| Test Time Reduction | 12.4% |

### Other

| Section | Detail |
|---------|--------|
| Workflow | None on this tab |
| Action bar | Approve · Reject · Apply · Export PDF · Export Excel · Generate ATPG Script · Export Report |

---

## 4.2 Scan Debug Recommendation Agent

**Header:** Failure diagnosis & debug for scan chain testing.

### KPIs (15) — 5 sections

#### Scan Chain Debug

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Broken Chains Detected | 7 | 3 Critical Priority |
| Debug Recommendations | 14 | Isolation • Bypass • Re-Stitch |
| Average Confidence | 88% | Above 85% Threshold |

#### ATPG Constraint Review

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Constraint Violations | 23 | Across 6 Constraint Files |
| Review Recommendations | 19 | Relax • Tighten • Remove |
| Coverage Impact | +1.8% | Projected After Applying Recommendations |

#### Timing Debug

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Timing Violations | 11 | Setup 8 · Hold 3 |
| Timing Debug Recommendations | 16 | At-Speed • Launch • Capture |
| Worst Slack | −42 ps | Critical Path Flagged |

#### Power Related Debug

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Power Violations | 9 | IR Drop 5 · EM 4 |
| Power Debug Recommendations | 12 | Clock Gating • Domain Isolation |
| Peak Switching Activity | 74% | Exceeds 65% Budget |

#### Physical Defect Investigation

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Defect Suspects | 31 | Across 4 Wafers |
| Investigation Recommendations | 18 | SEM • FIB • X-Ray • E-Beam |
| Defect Localization Accuracy | 91% | Average Across Suspects |

### Charts (3)

| Title | Type | Detail |
|-------|------|--------|
| Failure Root Cause Distribution | Donut | Broken Chain · Timing · Power · ATPG Constraint · Physical Defect · Unknown |
| Debug Recommendation Priority | Vertical bar | Critical / High / Medium / Low |
| Recommendation Trend | Line | Last 30 days |

### Table — Top Scan Debug Recommendations

| Columns |
|---------|
| Recommendation ID · Category · Scan Chain · Root Cause · Recommendation · Priority · Confidence · Engineer · Status · Expected Impact · Action |

Rows: `DBG-REC-001` … `DBG-REC-008`

### AI Debug Executive Summary

| Metric | Value |
|--------|-------|
| Broken Chains | 7 |
| Timing Issues | 11 |
| Power Issues | 9 |
| Constraint Violations | 23 |
| Physical Defects | 31 |
| Coverage Improvement | +1.8% |
| Estimated Yield Improvement | +1.2% |
| Expected Debug Time Reduction | 18.4 hrs |
| AI Confidence | 88% |

### Debug Workflow (7 steps)

1. Failure Logs  
2. Diagnosis Engine  
3. Root Cause Analysis  
4. Scan Debug Recommendation Agent  
5. Engineer Review  
6. Implementation  
7. Validation  

### Action bar

Approve · Reject · Apply · Export PDF · Export Excel · Generate Debug Report

---

## 4.3 Test Optimization Recommendation Agent

**Header:** Adaptive testing, yield, cost, production strategy.

### KPIs (19) — 7 sections

#### Adaptive Testing

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Adaptive Recommendations | 22 | Flow • Sequence • Bin Adjustment |
| Test Time Reduction | 18% | Projected if Fully Applied |
| Flow Variants Evaluated | 8 | Best Variant Selected |

#### Test Stop Optimization

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Stop Recommendations | 17 | Hard Stop 6 · Soft Stop 11 |
| Escapes Prevented | 43 | Expected with Stop Rules |
| Active Stop Rules | 9 | Lot • Wafer • Site • Bin |

#### Risk-Based Testing

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| High-Risk Devices | 58 | Critical 12 · High 46 |
| Risk Recommendations | 24 | Prioritize • Skip • Resample |
| Average Risk Score | 0.74 | Above 0.65 Threshold |

#### Yield Optimization

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Current Yield | 87.4% | +1.2% vs Last Lot |
| Yield Recommendations | 21 | Bin • Limit • Retest Strategy |
| Projected Yield Gain | +3.1% | 87.4% → 90.5% |

#### Cost Reduction

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Estimated Cost Saving | $48K | If Fully Applied |
| Cost Recommendations | 16 | Handler • Probe • Retest |
| Cost Per Device | $0.38 | −$0.07 vs Last Lot |

#### Multi-Site Optimization

| Title | Value | Status / subtitle |
|-------|-------|-------------------|
| Active Test Sites | 16 | 16 of 16 Configured |
| Site Recommendations | 11 | Load Balance • Disable • Reassign |
| Site Correlation Delta | ±2.3% | 3 Sites Outside ±1.5% |

#### Summary

| Title | Value | Subtitle |
|-------|-------|----------|
| Total Recommendations | 111 | Adaptive 22 · Stop 17 · Risk 24 · Yield 21 · Cost 16 · Site 11 |

### Charts (6)

| Title | Type | Detail |
|-------|------|--------|
| Adaptive Testing Distribution | Donut | Adaptive · Stop · Risk · Yield · Cost · Site (center Total 111) |
| Optimization Priority | Vertical bar | Critical / High / Medium / Low |
| Recommendation Trend | Line | 30 days |
| Yield Improvement Trend | Line | Current vs Projected |
| Cost Reduction Trend | Area | Optimized cost series |
| Site Utilization | 4×4 heatmap | Sites 1–16 |

### Table — Optimization Recommendation Table

| Columns |
|---------|
| Recommendation ID · Optimization Type · Current Value · Optimized Value · Estimated Benefit · Priority · Confidence · Status · Assigned Engineer · Action |

Rows: `OPT-REC-001` … `OPT-REC-008`

### Executive AI Summary

| Metric | Value |
|--------|-------|
| Adaptive Testing | 22 recs |
| Yield Improvement | +3.1% |
| Test Time Reduction | 18% |
| Cost Savings | $48K |
| Risk Reduction | 43 escapes |
| Multi-Site Efficiency | ±2.3% delta |
| Overall ROI | 3.8x |
| AI Confidence | 92.4% |

### Optimization Workflow (8 steps)

1. Production History  
2. Yield Analytics  
3. ATE Logs  
4. AI Optimization Engine  
5. Test Optimization Recommendation Agent  
6. Engineer Approval  
7. Optimized Test Flow  
8. Production Validation  

### Action bar

Approve · Reject · Apply Optimization · Export PDF · Export Excel · Generate Optimization Report

---

# Quick reference — section counts

| Module / Tab | KPIs | Charts / maps | Tables | Other |
|--------------|-----:|--------------:|-------:|-------|
| **Dashboard** | 6 | 2 (heatmap + cost) | 1 | Optimization engine + results |
| **Scan Chain · Overview** | 7 exec + mini summaries | 16 viz | 1 | AI summary · recs · alerts |
| **Scan Chain · Pattern** | 11 | 4 | 1 | KPI drill-downs |
| **Scan Chain · Failure** | 9 | 4 | 1 | KPI drill-downs · Export |
| **Scan Chain · Diagnosis** | 12 | 3 | 0 | Workflow · action bar |
| **Wafer · Overview** | 5 + 9 defect cards | 1 donut + gallery | 0 | Workflow · summary bar |
| **Wafer · Defect tabs (×9)** | 8 each | 2 canvas maps | Upload History | Info panel · workflow |
| **Rec · Pattern Agent** | 10 | 4 | 1 | AI summary · action bar |
| **Rec · Scan Debug Agent** | 15 | 3 | 1 | AI summary · workflow · actions |
| **Rec · Test Opt Agent** | 19 | 6 | 1 | AI summary · workflow · actions |

---

*This document reflects the current UI implementation. Example values come from mock data and may change in live API mode.*
