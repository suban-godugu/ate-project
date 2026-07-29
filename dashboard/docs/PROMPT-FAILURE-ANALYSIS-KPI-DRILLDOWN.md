# Cursor Prompt — Failure Analysis KPI Drill-down

> **Module:** Scan Chain Analysis · Failure Analysis Tab  
> **Trigger:** Click any Failure Analysis KPI card  
> **Stack:** Next.js App Router · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Recharts · React Query (API-ready)

---

## Objective

Redesign the KPI drill-down modal for the **Failure Analysis** module.

The current popup is too generic and documentation-like.

Every KPI should open a **unique engineering analytics dashboard**.

The drill-down must help semiconductor test engineers **investigate failures** instead of only displaying metric descriptions.

**DO NOT** use long text explanations.  
**DO NOT** display formula cards as the primary content.

Instead build an **interactive enterprise analytics workspace**.

---

## Layout

| Property | Value |
|---|---|
| Modal width | **95vw** |
| Modal height | **92vh** |
| Theme | Dark enterprise only |
| Effects | Rounded corners · glass effect · blur overlay |
| Structure | Sticky header · scrollable content · sticky footer |
| Animation | Smooth Framer Motion entry |

---

## Header

Display:

- KPI Icon · KPI Name · Current Value · Status · Last Updated · Trend % · Severity
- Export · Refresh · Close
- Active filters: Fab · Tester · Product · Lot · Wafer · Time Range

---

## Row 1 — Executive Summary

Current KPI · Target · Delta · Trend · Risk · Business Impact · Yield Impact · Cost Impact  
Mini sparklines on each card.

---

## Row 2 — Trend Analytics

Interactive chart with tabs: **24 Hours · 7 Days · 30 Days · 90 Days · Previous Lot · Previous Release**  
Zoom · Tooltip · Export

---

## Row 3 — Engineering Analytics

Render widgets dynamically per KPI:

Line · Area · Bar · Heatmap · Treemap · Gauge · Scatter · Histogram · Pareto · Bubble · Timeline · Correlation Matrix · Wafer Map · Similarity Matrix

---

## Row 4 — Breakdown

Drill-down dimensions: Tester · Lot · Wafer · Module · Die · Pattern · Scan Chain · Failure Bin · Root Cause

---

## Row 5 — AI Root Cause

Most Probable Root Cause · Confidence · Affected Modules · Wafers · Lots · Patterns · Severity · Priority · Expected Yield Loss · Cost Impact

---

## Row 6 — Recommendations

Interactive cards: Priority · Expected Improvement · Runtime Saving · Cost Saving  
Actions: Retry Test · Re-run ATPG · Repair Pattern · Repair Scan Chain · Optimize Test Program

---

## Row 7 — Event Timeline

Upload → Execution → Failure Detection → Diagnosis → AI Analysis → Recommendation → Report

---

## Row 8 — Raw Data Table

Search · Sort · Filter · Pagination · Export · Freeze Columns

---

## Row 9 — Related Modules

Pattern Analysis · Scan Diagnosis · Wafer Analysis · Recommendation Engine · Yield Dashboard · Cost Intelligence · Alerts · Reports

---

## Row 10 — AI Copilot

Suggested prompts:

- Why did failures increase?
- Show similar lots
- Compare previous wafer
- Predict next failure
- Suggest optimization

---

## KPI-Specific Dashboards (9 unique profiles)

### 1. Imported Test Files
Upload trend · File type distribution · Validation status · Failed imports · Recent uploads

### 2. Overall Failure Rate
Failure trend · Wafer heatmap · Failure by tester · Failure by product · Failure Pareto

### 3. Failing Test Patterns
Top failing patterns · Pattern frequency · Pattern timeline · Pattern heatmap · ATPG relationship

### 4. Die Failure Rate
Wafer map · Die density · XY coordinate map · Defect clusters · Failure histogram

### 5. Wafer Failure Rate
Wafer comparison · Edge vs Center · Wafer heatmap · Yield trend · Wafer ranking

### 6. Lot Failure Rate
Lot comparison · Historical lots · Failure timeline · Tester distribution · Product comparison

### 7. Fault Categories
Pie chart · Pareto · Root cause tree · Category trend · Severity distribution

### 8. Root Cause Confidence
Confidence gauge · AI confidence history · Root cause frequency · Similar historical failures · Resolution success rate

### 9. Recurring Failures
Recurring pattern trend · Top recurring failures · Timeline · Affected wafers · Cost impact

---

## Visual Design

VERILUMEN Design System · Purple accents · Dark background · Rounded cards · Animated charts · Interactive hover · Enterprise typography

No documentation sections. No static explanation cards. Every KPI gets its own widget dashboard.

---

## Implementation Files

```
src/lib/kpiDrillDown/kpiProfiles.ts          — 9 failure KPI widget profiles
src/lib/kpiDrillDown/buildKpiWorkspace.ts    — failure root cause, timeline, table, breakdowns
src/lib/kpiDrillDown/kpiDrillDownUtils.ts     — FAILURE_ANALYSIS_KPI_IDS, layout preset
src/components/scan-chain/failure/FailureKPIGrid.tsx — KpiDrillDownGrid wiring
src/components/common/kpi-drilldown/*          — shared workspace shell (95vw × 92vh for failure)
```
