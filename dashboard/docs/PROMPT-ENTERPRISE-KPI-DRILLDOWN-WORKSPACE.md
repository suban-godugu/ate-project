# Cursor Prompt — Enterprise KPI Drill-down Analytics Workspace

> **Module:** Scan Chain Analysis · Executive Dashboard (extensible)  
> **Trigger:** Click any `ExecutiveKPICard` on Scan Chain Overview  
> **Stack:** Next.js App Router · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Recharts · React Query (API-ready)

---

## Objective

Redesign the KPI drill-down popup.

The current popup is too simple and looks like documentation.

When an engineer clicks a KPI card, the popup must become a **complete analytics workspace**, similar to Synopsys Tessent, Siemens EDA, Advantest SmarTest, Teradyne IGXL, or KLA analytics dashboards.

**DO NOT** create a documentation modal.  
**DO NOT** display long text explanations.  
**DO NOT** make the popup look like a help page.

Every section must contain **interactive engineering analytics**.

---

## Layout

| Property | Value |
|---|---|
| Modal width | **90vw** |
| Modal height | **90vh** |
| Theme | Dark enterprise only |
| Effects | Rounded corners · glass effect · blur overlay |
| Structure | Sticky header · scrollable content · sticky footer |
| Animation | Smooth Framer Motion entry |

---

## Header

Display:

- KPI Icon
- KPI Name
- Current KPI Value
- Status Badge
- Trend Indicator
- Last Updated
- Risk Level
- Export Button
- Refresh Button
- Close Button

**Below the header** — active filter chips:

Fab · Tester · Product · Lot · Wafer

---

## ROW 1 — Executive Summary

Display **6 summary cards**:

1. Current Value  
2. Target Value  
3. Delta  
4. Trend  
5. Business Impact  
6. Operational Impact  

Each card contains: **Icon · Value · Mini sparkline**

---

## ROW 2 — Historical Trend

Large interactive chart.

**Tabs:** 24 Hours · 7 Days · 30 Days · 90 Days · Compare Previous Lot · Compare Previous Release

**Support:** Zoom · Tooltip · Download

---

## ROW 3 — Engineering Analytics

Dynamically render widgets from **API JSON payload** — no hardcoded KPI layouts.

**Supported widgets:**

Line Chart · Bar Chart · Area Chart · Scatter Plot · Gauge · Heatmap · Treemap · Histogram · Pareto · Radar · Bubble Chart · Similarity Matrix · Correlation Matrix · Network Graph · Timeline · Wafer Map · Cluster Visualization

Each KPI can have **different widget combinations**.

---

## ROW 4 — Breakdown Analysis

Display breakdown by (each **clickable**):

Fab · Tester · Product · Lot · Wafer · Module · Pattern · Scan Chain · Vector

---

## ROW 5 — Root Cause Analysis

**AI Diagnosis Card** displaying:

- Most Probable Root Cause
- Confidence %
- Affected Modules
- Affected Patterns
- Affected Chains
- Affected Lots
- Affected Wafers
- Severity
- Risk
- Expected Yield Impact

---

## ROW 6 — Recommendation Engine

Interactive recommendations. Each recommendation has:

- Priority
- Estimated Improvement
- Estimated Runtime Saving
- Estimated Cost Saving
- Actions: Retry Parsing · Re-run ATPG · Repair Metadata · Remove Redundant Patterns · Optimize Scan Chains · Regenerate STIL · Regenerate WGL

---

## ROW 7 — Engineering Timeline

Timeline events (each **clickable**):

Upload → Parsing → Validation → Embedding → AI Analysis → Recommendation → Report Generation → Export

---

## ROW 8 — Raw Engineering Data

Enterprise data grid with:

Search · Sort · Filter · Pagination · Column Chooser · Freeze Columns · CSV Export · Excel Export

---

## ROW 9 — Related Modules

Navigation cards (click opens module **without closing modal**):

Pattern Analysis · Failure Analysis · Scan Diagnosis · Recommendation Analysis · Wafer Analysis · Cost Intelligence · Yield Dashboard · Alerts · Reports

---

## ROW 10 — AI Copilot

Floating AI Assistant. Engineers can ask:

- Why did coverage drop?
- Why did the parser fail?
- Compare previous lot
- Show similar failures
- Predict next failure
- Recommend optimization

---

## Footer

Display:

Record Count · Parser Version · AI Model Version · Backend Status · Database Status · API Latency · Last Refresh

---

## Semiconductor Data

When applicable display:

Pattern ID · Vector ID · Scan Chain ID · Scan Cell · Flop ID · Compression Ratio · ATPG Version · Tester · Program Version · Fail Bin · Defect Class · Clock Domain · Fault Model · Coverage · Diagnosis Confidence

---

## Visual Design

- VERILUMEN design system
- Dark background · purple accents · soft borders
- Professional typography · hover animations · interactive charts
- Sticky header · scrollable sections · loading skeletons
- **No placeholder text · no documentation blocks · no long paragraphs**

---

## Technical Requirements

| Requirement | Detail |
|---|---|
| Framework | React 19 · TypeScript · Next.js App Router |
| Styling | Tailwind CSS · shadcn/ui |
| Data | React Query · dynamic widget rendering from API |
| Motion | Framer Motion |
| Charts | Recharts |
| Architecture | Each KPI receives JSON payload and renders its own dashboard |
| States | Loading · empty · error |
| Features | Export · refresh · keyboard accessibility · responsive layout |

The final experience should feel like opening an **engineering workspace**, not a popup.

---

## Implementation (Completed)

| Layer | Files |
|---|---|
| Types | `src/types/kpiDrillDown.ts` |
| API builder | `src/lib/kpiDrillDown/buildKpiWorkspace.ts` |
| KPI profiles | `src/lib/kpiDrillDown/kpiProfiles.ts` |
| Hook | `src/hooks/useKpiDrillDownWorkspace.ts` |
| Workspace UI | `src/components/common/kpi-drilldown/KpiDrillDownWorkspace.tsx` |
| Sections | `src/components/common/kpi-drilldown/KpiWorkspaceSections.tsx` |
| Widgets | `src/components/common/kpi-drilldown/KpiWidgetRenderer.tsx` |
| Copilot | `src/components/common/kpi-drilldown/KpiCopilotPanel.tsx` |
| Modal shell | `src/components/common/ExecutiveKPIDrillDownModal.tsx` |
| KPI cards | `src/components/common/ExecutiveKPICard.tsx` |
| Grid | `src/components/scan-chain/overview/ExecutiveOverviewKPIGrid.tsx` |
| Wiring | `src/components/scan-chain/tabs/OverviewTab.tsx` |

**Live API:** Replace `buildKpiWorkspace()` call in hook with `useQuery` → `GET /api/v1/kpi/:id/workspace?filters=...`

---

## Related STEPs

- **STEP 53** — Executive KPI Card (premium card + click trigger)
- **STEP 56** — Enterprise KPI Drill-down Analytics Workspace (this prompt)
- **STEP 57** — Executive KPI typography visibility fix
- **STEP 58** — Hydration UI primitive fix
- **STEP 59** — Prompt archive update
