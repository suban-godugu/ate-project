# Cursor Prompt — Scan Diagnosis KPI Drill-down

> **Module:** Scan Chain Analysis · Scan Diagnosis Tab  
> **Trigger:** Click any Scan Diagnosis KPI card (12 KPIs across 3 sections)  
> **Stack:** Next.js App Router · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Recharts · React Query (API-ready)

---

## Objective

Redesign the KPI drill-down for the **Scan Diagnosis** module.

Create an enterprise diagnosis workspace similar to Synopsys Tessent Diagnosis, Siemens Tessent Shell, Advantest SmarTest, Teradyne IGXL, and KLA Yield Explorer.

Engineers must investigate scan failures from KPI level down to the exact failing scan cell.

**Never** create documentation-style layouts or large text explanation blocks.

Every section must help debug silicon failures.

**Topology-first:** Chain Topology Graph is the centerpiece for topology-focused KPIs.

---

## Layout

| Property | Value |
|---|---|
| Modal width | **95vw** |
| Modal height | **92vh** |
| Theme | Dark enterprise · glass cards · purple accents |
| Structure | Sticky header · scrollable body · animated open/close |

---

## Workspace Rows

1. **Executive Summary** — Current KPI, Target, Affected Chains/Patterns/Wafers/Lots, Diagnosis Confidence, Est. Yield Loss, Business Impact, Trend (10 cards + sparklines)
2. **Failure Trend** — 24h, 7d, 30d, Previous Lot, Previous Wafer, Release Comparison
3. **Scan Diagnosis** — Dynamic engineering widgets (topology-first)
4. **Failure Traceability** — Fab → Tester → Lot → Wafer → Die → Pattern → Scan Chain → Scan Cell → Flop → Failure Bit → Diagnosis (clickable)
5. **Root Cause Analysis** — Root cause, confidence, failure type, scan cells, clock/shift/capture, fault model, compression, physical region
6. **Topology View** — Interactive chain graph with broken chains, failing cells, zoom/pan/search
7. **AI Recommendation Engine** — Repair chain, re-run ATPG, reduce compression, regenerate pattern, repair clock/shift timing
8. **Raw Engineering Data** — Chain ID, Pattern, Vector, Flop, Cell, Cycle, Clock, Fail Count, Diagnosis
9. **Timeline** — Upload → Parsing → Diagnosis → AI Analysis → Root Cause → Recommendation → Report
10. **AI Copilot** — Why did Chain 14 fail? Compare previous lot. Show similar failures. Predict recurring failures. Suggest ATPG improvements.

---

## 12 KPI-Specific Dashboards

| KPI ID | Widget Focus |
|---|---|
| `sd-failing-chains` | Chain topology graph, top failing chains, heatmap, ranking, timeline |
| `sd-failing-cells` | Cell density heatmap, histogram, clock domain, ranking, dependency graph |
| `sd-chain-breaks` | Topology graph, break location, frequency, shift direction, repair suggestions |
| `sd-shift-capture` | Shift vs capture, timing histogram, clock analysis, cycle distribution, failure density |
| `sd-topology-chains` | Interactive topology, connected graph, fan-in/fan-out, clock domains, path explorer |
| `sd-chains-ranked` | Ranking table, frequency, severity, trend, historical comparison |
| `sd-failure-correlations` | Correlation matrix, pattern similarity, clusters, wafer correlation |
| `sd-top-failing-chain` | Chain topology, chain/pattern history, timeline, affected lots |
| `sd-diagnosis-reports` | Report history, versions, downloads, review status, timeline |
| `sd-debug-locations` | Die map, XY coordinates, wafer map, hotspots, physical layout |
| `sd-avg-confidence` | Confidence gauge, trend, AI score history, manual validation, accuracy |
| `sd-pending-review` | Pending list, engineer assignment, priority, confidence, SLA timer |

---

## Implementation Files

```
src/lib/kpiDrillDown/kpiProfiles.ts           — 12 scan diagnosis widget profiles
src/lib/kpiDrillDown/buildKpiWorkspace.ts       — traceability, topology, diagnosis table
src/lib/kpiDrillDown/kpiDrillDownUtils.ts       — SCAN_DIAGNOSIS_KPI_IDS, layout preset
src/components/common/kpi-drilldown/KpiTraceabilityPath.tsx
src/components/common/kpi-drilldown/KpiTopologyPanel.tsx
src/components/scan-chain/diagnosis/ScanDiagnosisSectionedGrid.tsx
```
