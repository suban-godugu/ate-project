# VERILUMEN / COMPTY — Frontend Presentation Guide

**Product:** ATE Intelligence Enterprise Platform  
**Type:** Semiconductor Test Intelligence Dashboard  
**Version:** 0.1.0  
**Dev URL:** http://localhost:3000/dashboard  
**Repository:** `c1-com/ate-dashboard` (primary) · `bd-1/dashboard` (synced copy)

---

## 1. Executive Summary (Slide 1 — Title)

**One-liner:**  
Enterprise-grade web platform for semiconductor ATE (Automated Test Equipment) yield optimization, scan chain analysis, memory/logic BIST, wafer defect intelligence, cost analytics, and AI-driven test recommendations.

**Target users:** Test engineers, yield engineers, DFT teams, fab operations, test program managers.

**Comparable platforms:** Synopsys Tessent, Siemens EDA, Advantest V93000 analytics, Teradyne UltraFLEX reporting — delivered as a unified modern SaaS dashboard.

---

## 2. Technology Stack (Slide 2)

| Layer | Technology | Purpose |
|---|---|---|
| Framework | **Next.js 16** (App Router) | Routing, SSR-ready architecture |
| Language | **TypeScript 5** | End-to-end type safety |
| Styling | **Tailwind CSS v4** | Utility-first responsive design |
| UI Library | **shadcn/ui** | Buttons, dialogs, selects, badges |
| Charts | **Recharts 3** | Line, bar, pie, area, scatter charts |
| Icons | **Lucide React** | 200+ consistent icons |
| Animation | **Framer Motion 12** | KPI entrance, hover, count-up |
| State | **Zustand 5** | Filters, uploads, notifications, theme |
| Data Fetch | **TanStack React Query 5** | Cache + filter invalidation |
| Upload UX | **react-dropzone** | Drag-and-drop file upload |
| Export | **html2canvas** | PNG page capture export |

**Scale:** ~187 React components · 165 in `/components` · 9 mock data modules · 9 Zustand stores

---

## 3. Application Architecture (Slide 3)

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (Next.js App Router)                               │
├──────────────┬──────────────────────────────────────────────┤
│  Sidebar     │  Top Navbar (Search · Calendar · Upload ·      │
│  280px       │  Notifications · Export · Primary Action)    │
│  Navigation  ├──────────────────────────────────────────────┤
│  + Quick     │  Module Tabs (keep-alive TabPanelHost)       │
│  Filters     │  KPI Grids · Charts · Tables · Canvas Maps   │
└──────────────┴──────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   Zustand Stores      Mock Data Layer (src/lib/*.ts)
   filterStore         + React Query hooks (live-ready)
   uploadStore
   notificationStore
   themeStore
```

**Design pattern:** Module-based dashboards with shared shell (`DashboardLayout`), shared KPI design system, and per-module tab navigation with lazy-mounted keep-alive panels.

---

## 4. Design System (Slide 4)

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| App background | `#090B12` | Page shell |
| Card surface | `#111827` | KPI cards, chart cards |
| Executive card | `#121826` | Premium executive KPIs |
| Border | `#2D3748` | Cards, tables |
| Primary purple | `#7C3AED` | Accent, active nav, charts |
| Secondary purple | `#8B5CF6` | Sparklines, glow |
| Success green | `#10B981` | Positive trends |
| Danger red | `#EF4444` | Negative trends |
| Muted text | `#64748B` | Subtitles |
| Secondary text | `#94A3B8` | KPI titles |

### Layout Constants

| Element | Size |
|---|---|
| Sidebar width | 280px (collapsible) |
| Top navbar height | 72px sticky |
| Content padding | 24px |
| Section gap | 24px |
| KPI card height | 220px |
| KPI card padding | 22px |
| KPI card radius | 18px |
| KPI grid gap | 24px |
| KPI grid columns | xl:4 · md:2 · sm:1 |

### KPI Design System

Two tier system:
- **`EnterpriseKPICard`** — used across all modules (Dashboard, Scan Chain, MBIST, LBIST, Wafer, Cost, Alerts, Recommendation)
- **`ExecutiveKPICard`** — premium variant for Scan Chain Overview with drill-down modal

Typography: Title 16px · Value 44–48px bold · Subtitle 14px · Trend 15px · Badge 12px

### Visual Effects

- Glassmorphism cards with backdrop blur
- Purple gradient active navigation
- Hover lift + glow on KPI cards
- Framer Motion staggered entrance animations
- Sparkline draw animations on KPI cards

---

## 5. Navigation & Modules (Slide 5)

### Sidebar Modules (8 + Settings)

| # | Module | Route | Tabs |
|---|---|---|---|
| 1 | **Executive Dashboard** | `/dashboard` | Single page |
| 2 | **Scan Chain Analysis** | `/dashboard/scan-chain` | 4 tabs |
| 3 | **MBIST Analysis** | `/dashboard/mbist` | 5 tabs |
| 4 | **LBIST Analysis** | `/dashboard/lbist` | 5 tabs |
| 5 | **Wafer Analysis** | `/dashboard/wafer-analysis` | 10 tabs |
| 6 | **Cost Intelligence** | `/dashboard/cost-intelligence` | 6 tabs |
| 7 | **Recommendation Analysis** | `/dashboard/recommendation-analysis` | 3 AI agents |
| 8 | **Alerts** | `/dashboard/alerts` | 7 tabs |
| — | **Settings** | `/dashboard/settings` | Theme + Account |

**Total module tabs:** 40+ analytical views

---

## 6. Module Details (Slides 6–13)

### 6.1 Executive Dashboard

**Purpose:** C-level overview of test cost, yield, and optimization ROI.

| Section | Components |
|---|---|
| KPI Row | 6 cards — Total Test Cost, Cost/Wafer, Cost/Die, Test Time, Yield, ROI |
| Wafer Heatmap | Interactive 40×40 canvas — pan, zoom, overlay modes (yield/fail/cost) |
| Analytics Row | Cost Trend Chart + Pattern Analysis Table |
| Optimization | AI Optimization Engine (sliders) + Results panel |

**Primary action:** AI Optimize

---

### 6.2 Scan Chain Analysis (4 tabs)

| Tab | KPIs | Key Visualizations |
|---|---|---|
| **Overview** | 7 executive KPIs + drill-down mini KPIs | Health donut, failing chips/chains bar charts, trend analytics, AI executive summary, spatial heatmaps, alerts & recommendations preview |
| **Pattern Analysis** | 11 KPIs | Import trend, coverage trend, cluster pie, similarity scatter, pattern table (12 columns) |
| **Failure Analysis** | 10 KPIs | Failure trend, type distribution, by-lot chart, failure table, wafer/die heatmaps |
| **Scan Diagnosis** | Sectioned KPIs (3-col grid) | Diagnosis timeline, chain connectivity graph, topology viewer, diagnosis table |

**Primary action:** AI Diagnose  
**Special:** Overview → tab drill-down navigation · Executive KPI click → 1400px drill-down modal

---

### 6.3 MBIST Analysis (5 tabs)

Memory Built-In Self-Test analytics.

| Tab | Focus |
|---|---|
| Overview | 6 KPIs, memory health donut, failure heatmap, AI diagnosis |
| Memory Health | Utilization, temperature, access density KPIs + charts |
| Failure Analysis | Failure trends, type distribution, bank heatmap |
| Diagnosis | Timeline, correlation graphs, root cause analysis |
| AI Recommendation | Risk cards + recommendations table |

---

### 6.4 LBIST Analysis (5 tabs)

Logic Built-In Self-Test analytics — mirrors MBIST structure for logic domains.

| Tab | Focus |
|---|---|
| Overview | 6 KPIs, coverage donut, module heatmap |
| Coverage Analysis | Block efficiency, detection coverage |
| Failure Analysis | Spatial failure density |
| Diagnosis | Logic connectivity + root cause graphs |
| AI Recommendation | Logic repair recommendations |

---

### 6.5 Wafer Analysis (10 tabs)

AI-powered wafer defect classification and spatial intelligence.

| Tab | Focus |
|---|---|
| Overview | Input die statistics, 9 defect class KPIs, yield donut, gallery, workflow |
| 9 Defect Classes | Centre, Donut, Edge-Ring, Scratch, Near-Full, Normal, Edge-Loc, Local, Random |

**Each defect tab includes:**
- 8 KPI cards
- Upload history panel (selectable wafer list)
- Overlay analytics canvas (teal/gold fail map)
- Fail density heatmap canvas
- Info panel with wafer metadata

**Primary action:** Generate Yield Analysis

---

### 6.6 Cost Intelligence (6 tabs)

Cross-module test cost optimization.

| Tab | Focus |
|---|---|
| Overview | 6 KPIs, cost contribution donut, breakdown bar, monthly trend |
| Scan Chain / MBIST / LBIST / Wafer Cost | Module-specific cost KPIs + charts |
| AI Cost Optimization | Recommendation table + enterprise summary |

**Primary action:** Generate Cost Optimization

---

### 6.7 Recommendation Analysis (3 AI Agents)

Centralized AI recommendation engine — single page, 3 agent tabs.

| Agent | KPIs | Sections |
|---|---|---|
| **Pattern Recommendation** | 11 KPIs | Remove/reorder/ATPG/low-power recommendations, charts, table, AI summary |
| **Scan Debug Recommendation** | 15 KPIs in 5 sections | Debug queue, constraints, timing, power, defect investigation |
| **Test Optimization** | 19 KPIs in 7 sections | Adaptive testing, stop rules, risk, yield, cost, site optimization |

**Primary action:** Generate AI Recommendations

---

### 6.8 Alerts (7 tabs)

Real-time monitoring center consolidating all module alerts.

| Tab | Focus |
|---|---|
| Overview | 6 KPIs, severity distribution, trend, recent alerts table |
| Scan Chain / MBIST / LBIST / Wafer / Cost / AI Rec Alerts | Module-specific alert KPIs + tables |

**Primary action:** Mark All as Read

---

### 6.9 Settings

| Panel | Features |
|---|---|
| Theme Settings | Accent color, card style (glass/solid/minimal), border radius, font size, density, sidebar style, animations |
| Account Presets | Profile, role, department, language, timezone, notifications |
| Live Preview | Mini KPI preview reflecting theme tokens |

Persisted to `localStorage` via Zustand + ThemeContext.

---

## 7. Global Platform Features (Slide 14)

| Feature | Component | Status |
|---|---|---|
| **Global Search** | `GlobalSearch` | Client-side index across all modules |
| **Quick Filters** | Sidebar panel | Fab, Tester, Product, Lot, Wafer, Date Range |
| **Date Range Picker** | Top navbar calendar | Presets + custom range |
| **Notifications** | Bell dropdown | Grouped, mark read, unread badge |
| **Upload Data** | Modal | STDF/STIL/WGL/CSV/XLSX/ZIP up to 10GB (simulated) |
| **Upload Log File** | Modal | ATE logs, 5-step pipeline, AI summary (simulated) |
| **Export Report** | Dropdown | CSV, Excel, PDF, PNG (client-side) |
| **Primary Actions** | Per-page button | AI Optimize / Diagnose / Generate (simulated 1.8s) |
| **Filter Engine** | `filterEngine.ts` | Adjusts KPI values, sparklines, table rows by filters |
| **Tab Performance** | `TabPanelHost` | Lazy mount + keep-alive (no re-render on switch) |
| **Responsive Layout** | CSS Grid | Desktop 4-col KPI · Tablet 2-col · Mobile 1-col |

---

## 8. Reusable Component Library (Slide 15)

| Component | Path | Used By |
|---|---|---|
| `EnterpriseKPICard` | `components/common/` | All modules |
| `ExecutiveKPICard` | `components/common/` | Scan Chain Overview |
| `EnterpriseKPIGrid` | `components/common/` | All KPI grids |
| `ChartCard` | `components/scan-chain/` | All chart wrappers |
| `DataTable` | `components/scan-chain/` | All searchable tables |
| `DashboardLayout` | `components/layout/` | Every page |
| `TabPanelHost` | `components/platform/` | All tabbed modules |
| `UploadDataModal` | `components/upload/` | Global navbar |
| `ExportMenu` | `components/platform/` | Global navbar |
| `WaferHeatmap` | `components/charts/` | Executive Dashboard |

**Total KPI cards in application:** 150+ across all modules

---

## 9. Data Layer (Slide 16)

| File | Module | Contents |
|---|---|---|
| `dummyData.ts` | Executive Dashboard | KPIs, patterns, cost trend, wafer heatmap |
| `scanChainData.ts` | Scan Chain | 11 pattern KPIs, 10 failure KPIs, diagnosis sections, overview data |
| `mbistData.ts` | MBIST | Memory KPIs, charts, tables |
| `lbistData.ts` | LBIST | Logic KPIs, charts, tables |
| `waferData.ts` | Wafer | Defect classes, gallery, upload history, canvas data |
| `costIntelligenceData.ts` | Cost | Module cost KPIs, trends |
| `recommendationData.ts` | Recommendation | 3 agent datasets, 45+ KPIs |
| `alertsData.ts` | Alerts | Module alert KPIs, alert rows |
| `uploadData.ts` | Upload | Supported formats, validation rules |

**Current mode:** Mock JSON (fully functional UI)  
**Live-ready:** API client + React Query hooks scaffolded (`NEXT_PUBLIC_API_MODE=mock|live`)

---

## 10. State Management (Slide 17)

| Store | Purpose |
|---|---|
| `filterStore` | Global fab/tester/product/lot/wafer/date filters |
| `uploadStore` | Upload history, progress, file cache |
| `notificationStore` | Alert notifications, read/unread |
| `themeStore` | Theme preferences |
| `uiStore` | Sidebar collapse, active recommendation agent tab |
| `actionStore` | Primary action results (AI optimize/diagnose) |
| `recommendationStore` | Recommendation apply/reject state |
| `userStore` | Session display name (auth-ready) |

All persisted to `localStorage` where appropriate.

---

## 11. Presentation Demo Flow (Slide 18)

**Recommended 10-minute demo script:**

1. **Login → Executive Dashboard** (30s)  
   Show 6 KPIs, wafer heatmap pan/zoom, cost trend, run AI Optimize

2. **Scan Chain → Overview** (2 min)  
   Executive KPIs, click card for drill-down modal, scroll to health summary + trends

3. **Scan Chain → Pattern Analysis** (1.5 min)  
   11 KPIs, import/coverage charts, pattern table search

4. **Scan Chain → Failure + Diagnosis** (1 min)  
   Failure heatmaps, diagnosis topology

5. **Wafer Analysis → Overview + Defect tab** (2 min)  
   Defect class KPIs, select wafer, overlay + density canvas

6. **Recommendation Analysis → Scan Debug Agent** (1.5 min)  
   15 sectioned KPIs, recommendation table

7. **Cost Intelligence + Alerts** (1 min)  
   Cost breakdown, alert severity overview

8. **Settings → Theme toggle** (30s)  
   Live preview, accent color change

9. **Upload Data modal** (30s)  
   Drag-drop, progress animation

10. **Export + Filters** (30s)  
    Change fab filter, export CSV

---

## 12. Key Metrics for Stakeholders (Slide 19)

| Metric | Value |
|---|---|
| Application modules | **9** |
| Analytical tab views | **40+** |
| KPI cards (total) | **150+** |
| Chart types | Line, Bar, Pie, Donut, Area, Scatter, Heatmap, Canvas |
| Data tables | **20+** searchable/sortable |
| React components | **187** TSX files |
| TypeScript coverage | 100% |
| Responsive breakpoints | Mobile / Tablet / Desktop / XL (1920px) |
| Build prompts documented | **54 STEPs** in `prompts.csv` |
| Enterprise KPI design system | Unified across all modules |

---

## 13. Competitive Positioning (Slide 20)

| Capability | Traditional EDA Tools | VERILUMEN Platform |
|---|---|---|
| Unified dashboard | Separate tools per domain | Single platform, 9 modules |
| Modern UX | Desktop-native, dated UI | Web SaaS, glassmorphism, animations |
| AI recommendations | Batch/offline | Real-time agent tabs with KPI impact |
| Wafer spatial analysis | External tools | Built-in canvas overlay + density |
| Cost + Yield + Test | Siloed reports | Cross-module Cost Intelligence |
| Customization | Limited | Theme engine, filters, export |
| Deployment | On-premise installs | Next.js — cloud or on-prem ready |

---

## 14. Roadmap / Integration Status (Slide 21)

| Layer | Status |
|---|---|
| UI / UX | ✅ Complete |
| Mock data layer | ✅ Complete |
| KPI design system | ✅ Unified |
| Client-side filters/search/export | ✅ Complete |
| Backend API (FastAPI) | 🔄 In progress (`bd-1/backend`) |
| Live PostgreSQL analytics | 🔄 Scaffolded |
| Real STDF/LOG parser | 🔄 In progress |
| Authentication | 🔄 Login page scaffolded |

---

## 15. File Locations for Presenters

| Resource | Path |
|---|---|
| This guide | `docs/FRONTEND-PRESENTATION.md` |
| All prompts archive | `docs/VERILUMEN-ALL-PROMPTS.pdf` |
| Pattern Analysis prompt | `docs/PROMPT-SCAN-CHAIN-PATTERN-ANALYSIS.md` |
| Prompt history | `prompts.csv` (STEP 1–54) |
| Dev server | `npm run dev` → localhost:3000 |

---

*Generated for VERILUMEN / COMPTY ATE Intelligence Enterprise Platform presentation.*
