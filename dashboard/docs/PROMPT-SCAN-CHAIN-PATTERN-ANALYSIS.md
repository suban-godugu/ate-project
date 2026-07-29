# Cursor AI Prompt — Scan Chain Analysis → Pattern Analysis (Production Ready)

> **Module:** Scan Chain Analysis  
> **Tab:** Pattern Analysis  
> **Route:** `/dashboard/scan-chain` → tab `pattern-analysis`  
> **Stack:** Next.js 15+ · TypeScript · Tailwind CSS v4 · shadcn/ui · Recharts · Framer Motion · Lucide React

---

## Context

You are continuing development of the **VERILUMEN / COMPTY ATE Intelligence Enterprise Platform**.

The **Pattern Analysis** tab is the scan-pattern intelligence workspace for semiconductor test engineers. It must match the visual quality of Synopsys Tessent, Siemens EDA, Advantest V93000, and Teradyne UltraFLEX dashboards.

**IMPORTANT**
- Continue from the existing implementation — do **NOT** rebuild the app shell, sidebar, or top navbar.
- Reuse existing components: `EnterpriseKPICard`, `EnterpriseKPIGrid`, `ChartCard`, `DataTable`, `TrendLineChart`, `DistributionPie`.
- Do **NOT** re-add removed sections (Upload/Export header actions, AI Summary card, Redundancy Heatmap, Similarity Matrix) unless explicitly requested.
- Match the enterprise KPI design system used across Dashboard, Overview, MBIST, LBIST, Wafer, Cost Intelligence, Alerts.

---

## Objective

Build a **production-ready Pattern Analysis tab** with:

1. **11 enterprise KPI cards** (fixed grid, identical dimensions)
2. **4 analytics charts** (import trend, coverage trend, cluster distribution, similarity scatter)
3. **1 searchable data table** (pattern-level detail rows)
4. **Optional:** KPI drill-down modal on card click (Pattern-specific variant)
5. **Responsive layout** — desktop-first, tablet 2-col, mobile 1-col

---

## Page Layout (Top → Bottom)

```
┌─────────────────────────────────────────────────────────────┐
│  KPI GRID — 11 cards · 4 columns @ xl · 24px gap            │
├──────────────────────────┬──────────────────────────────────┤
│  Pattern Import Trend    │  Pattern Coverage Trend          │
├──────────────────────────┼──────────────────────────────────┤
│  Pattern Cluster Pie     │  Pattern Similarity Scatter      │
├─────────────────────────────────────────────────────────────┤
│  Pattern Analysis Table (search · sort · pagination)        │
└─────────────────────────────────────────────────────────────┘
```

**Spacing:** `dashboard-content` gap **24px** between sections.

---

## KPI Cards (11 Required — Keep Exactly These)

Use **`EnterpriseKPIGrid`** with `variant="overview"` (4 columns @ xl).

| ID | Title | Example Value | Subtitle / Status | Icon |
|---|---|---|---|---|
| `files-ingested` | Pattern Files Ingested | 2,846 | STIL • WGL • PAT | layers |
| `vectors-parsed` | Scan Vectors Parsed | 99.7% | 2.8M Scan Vectors | scan |
| `file-integrity` | File Integrity | 100% | PASS | shield-check |
| `pattern-coverage-kpi` | Pattern Coverage | 98.42% | +0.2% ATPG Delta | target |
| `metadata-extracted` | Metadata Extracted | 2,846 | Complete | file-stack |
| `embeddings-generated` | Embeddings Generated | 2,846 | 100% | sparkles |
| `pattern-clusters` | Pattern Clusters | 126 | Threshold 0.87 | git-branch |
| `redundant-patterns` | Redundant Patterns | 38 | 94% Confidence | alert-triangle |
| `similarity-analyses` | Similarity Analyses | 2,846 | 182 ms | crosshair |
| `pass-fail-linked` | Pass / Fail Linked | 2,741 | of 2,846 total | check-circle |
| `quality-reports` | Quality Reports | 24 | PDF • Excel • HTML | file-text |

**Data source:** `src/lib/scanChainData.ts` → `patternAnalysisKPIs`

---

## KPI Card Design System

Use shared **`EnterpriseKPICard`** (`src/components/common/EnterpriseKPICard.tsx`).

| Property | Value |
|---|---|
| Height | **220px** fixed |
| Width | **100%** responsive (`w-full h-full`) |
| Padding | **22px** |
| Border radius | **18px** |
| Background | `#111827` |
| Border | `rgba(124,58,237,0.25)` |
| Grid gap | **24px** |
| xl (≥1280px) | **4 columns** |
| md (≥768px) | **2 columns** |
| sm | **1 column** |

### Typography

| Element | Spec |
|---|---|
| Title | 16px · Medium (500) · `#94A3B8` |
| Value | 44px · Bold (700) · line-height 48px · `#FFFFFF` |
| Subtitle | 14px · Regular (400) · `#64748B` |
| Trend | 15px · SemiBold (600) · `#10B981` / `#EF4444` |
| Status badge | 12px · SemiBold · height 26px · padding 6×12px · rounded-full |

### Layout (inside card)

- **Top-left:** 48×48 icon circle, purple tint
- **Top-right:** status badge (e.g. `100% Imported`, `SLA Met`, `PASS`)
- **Title** → **Value** → **Subtitle OR trend**
- **Bottom:** 44px sparkline area (purple gradient fill, no axes)

### Value normalization

- Bullet lists → count + subtitle
- `2,741 / 2,846` → value `2,741`, subtitle `of 2,846 total`
- `98.1% → 99.3%` → value `99.3%`, subtitle `from 98.1%`
- Truncate all long text — no overflow, no clipped digits

### Animation

- Card entrance: fade-up 0.4s, staggered by index
- Sparkline: draw animation left-to-right
- Hover: subtle lift, purple border glow, `cursor: pointer` if clickable

---

## Charts Section

### Row 1 — Trend Charts (2 columns @ lg)

**Chart 1 — Pattern Import Trend**
- Subtitle: *Weekly imported vs. validated files*
- Data: `patternImportTrend`
- Lines: Imported `#7C3AED`, Validated `#06B6D4`
- Component: `TrendLineChart` inside `ChartCard`

**Chart 2 — Pattern Coverage Trend**
- Subtitle: *ATPG fault coverage over time*
- Data: `patternAnalysisCoverageTrend`
- Line: Coverage `#22C55E`
- Component: `TrendLineChart` inside `ChartCard`

### Row 2 — Distribution + Scatter (2 columns @ lg)

**Chart 3 — Pattern Cluster Distribution**
- Subtitle: *AI cluster classification*
- Data: `patternClusterDistribution`
- Donut segments: Stuck-At, Transition, Bridging, Timing, Other
- Component: `DistributionPie` inside `ChartCard`

**Chart 4 — Pattern Similarity**
- Subtitle: *Coverage vs. similarity score by cluster*
- Data: `patternScatterData`
- Clusters A/B/C/D with distinct colors
- Component: `PatternScatterChart` inside `ChartCard`

**Chart styling:** dark glass card, `#111827` surface, `#2D3748` border, 20px radius, Recharts tooltips dark theme.

---

## Pattern Analysis Table

**Title:** Pattern Analysis Table  
**Subtitle:** Imported patterns with coverage, clustering, and AI quality scores  
**Data:** `patternAnalysisRows`  
**Page size:** 6  
**Search keys:** patternId, patternName, fileType, cluster, status, recommendation

| Column | Render |
|---|---|
| Pattern ID | monospace white |
| Pattern Name | text |
| File Type | STIL / WGL / PAT |
| Coverage | `%` suffix |
| Compression | 2 decimal places |
| Vectors | locale string |
| Cluster | CL-A12 etc. |
| Similarity | 2 decimal places |
| Redundancy | None / Low / Medium / High |
| Quality | `%` suffix |
| Status | badge: Active=success, Review=warning, Redundant=danger |
| Recommendation | Keep / Review / Merge / Remove |

**Table features:** sticky header, pagination, search, row hover highlight.

---

## Optional — KPI Drill-Down Modal

On KPI card click, open **Pattern KPI Drill-down Modal** (1400px max-width):

1. Executive Summary  
2. KPI Trend (sparkline expanded to line chart)  
3. Pattern Type Distribution  
4. Redundancy / Similarity Insights  
5. Top Contributing Patterns  
6. Detailed Pattern Table (filtered by KPI)  
7. AI Pattern Recommendations  
8. Export PDF  
9. Open Pattern Recommendation Agent  

Wire navigation to Recommendation Analysis → Pattern Agent tab where relevant.

---

## Files to Use / Modify

```
src/components/scan-chain/tabs/PatternAnalysisTab.tsx      ← main tab layout
src/components/scan-chain/pattern/PatternKPIGrid.tsx       ← KPI grid wrapper
src/components/common/EnterpriseKPICard.tsx                  ← shared KPI card
src/lib/scanChainData.ts                                     ← patternAnalysisKPIs, charts, rows
src/types/scanChain.ts                                       ← PatternAnalysisKPI, PatternAnalysisRow
src/styles/globals.css                                       ← .kpi-grid responsive rules
```

**Do NOT create duplicate KPI components.** Extend `EnterpriseKPICard` only.

---

## Color System

| Token | Hex |
|---|---|
| Background | `#090B12` |
| Card | `#111827` |
| Border | `#2D3748` |
| Primary purple | `#7C3AED` |
| Accent purple | `#8B5CF6` |
| Success green | `#10B981` / `#22C55E` |
| Warning amber | `#F59E0B` |
| Danger red | `#EF4444` |
| Muted text | `#64748B` |
| Secondary text | `#94A3B8` |
| White | `#FFFFFF` |

---

## Quality Checklist

- [ ] All 11 KPI cards identical height (220px) and width (100% of grid cell)
- [ ] No fixed pixel card widths
- [ ] Titles and values aligned consistently across all cards
- [ ] Sparklines render on every KPI (placeholder if empty)
- [ ] 4 charts render without layout shift
- [ ] Table search and pagination work
- [ ] Responsive: 4 → 2 → 1 columns for KPI grid
- [ ] No console errors, TypeScript passes
- [ ] Matches enterprise polish of Scan Chain Overview executive KPIs
- [ ] Respects global Quick Filters (fab, lot, tester, product) when wired to live API

---

## Out of Scope (Do NOT Add)

- Upload / Export / Generate AI header action bar on this tab
- AI Recommendation Summary card (removed in STEP 26)
- Redundancy Heatmap matrix
- Similarity Matrix heatmap
- Duplicate KPI card implementations

---

## Acceptance Criteria

The Pattern Analysis tab is **production-ready** when:

1. An engineer can assess pattern ingestion health from the 11 KPIs in under 5 seconds  
2. Import and coverage trends show clear week-over-week direction  
3. Cluster distribution and similarity scatter reveal redundancy hotspots  
4. The pattern table supports finding any pattern by ID or cluster in one search  
5. Visual design is indistinguishable in quality from top-tier EDA/analytics platforms  

---

*Paste this entire prompt into Cursor inside `c1-com/ate-dashboard` or `bd-1/dashboard`.*
