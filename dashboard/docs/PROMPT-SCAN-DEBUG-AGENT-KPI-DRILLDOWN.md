# Cursor Prompt — Scan Debug Recommendation Agent KPI Drill-down

> **Module:** Recommendation Analysis · Scan Debug Recommendation Agent Tab  
> **Trigger:** Click any Scan Debug KPI card (15 KPIs across 5 sections)  
> **Stack:** Next.js App Router · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Recharts · React Query (API-ready)

---

## Objective

Redesign every KPI drill-down inside the **Scan Debug Recommendation Agent**.

Each KPI opens an **AI-assisted Scan Debug Decision Console** — not documentation, not a generic chart dashboard.

Engineers should immediately understand:

- What failed and why AI generated this recommendation
- Which scan chains and patterns are affected
- Expected improvement, confidence, and risk
- How to approve and apply the fix

**Split-view centerpiece:** Left 40% AI explanation + confidence + approval · Right 60% interactive engineering visualization (topology, wafer map, heatmap, timing path).

Design inspiration: Synopsys Tessent Diagnosis · Siemens Tessent Shell · KLA Yield Explorer · Advantest SmarTest.

---

## Layout

| Property | Value |
|---|---|
| Modal width | **95vw** |
| Modal height | **92vh** |
| Layout preset | `debug` |
| Module | `scanDebug` |
| Theme | Dark enterprise · glass cards · purple accents |

---

## Workspace Rows

1. **Executive Summary** — 12 cards: current, target, rec count, affected chains/patterns/wafers/lots, coverage, runtime, power, cost, business impact
2. **AI Debug Decision — Review & Visualize** — Split panel (40/60): AI overview + root cause + quick actions | topology / wafer map / heatmap hero
3. **Engineering Analytics** — Remaining KPI-specific dynamic widgets
4. **Breakdown** — Tester, lot, wafer, pattern, scan chain, module, clock domain, fault model, power domain
5. **Engineering Impact** — Coverage, yield, power, runtime, memory, cost, pattern reduction
6. **Action Center** — Approve, reject, modify, assign, Jira, report, ATPG script, export
7. **Engineering Timeline** — Generated → Review → Approval → Pattern Update → Validation → Regression → Production
8. **Raw Engineering Data** — Pattern, chain, cell, vector, clock, fault model, coverage, power, runtime, rec score, confidence
9. **AI Copilot** — Why generated? Similar debug cases. Compare lot. Estimate runtime/coverage. Alternative fix.

---

## 15 KPI-Specific Workspaces

| KPI ID | Widget Focus |
|---|---|
| `broken-chains` | Chain topology graph, broken locations, dependency graph, failure frequency, health score |
| `debug-recs` | Priority ranking, AI ranking, categories, historical success, estimated improvement |
| `avg-confidence` | Confidence gauge, trend, manual validation, approval %, calibration |
| `constraint-violations` | Constraint hierarchy, ATPG tree, severity, violation heatmap, suggested fixes |
| `review-recs` | Pending reviews, assignments, approval workflow, status timeline |
| `coverage-impact` | Before/after coverage, heatmap, module comparison, gain waterfall |
| `timing-violations` | Setup/hold histogram, timing path graph, critical path, clock domains |
| `timing-debug-recs` | Optimization ranking, recommended fixes, timing gain, clock tree comparison |
| `worst-slack` | Slack trend, critical paths, timing hierarchy, worst path explorer |
| `power-violations` | IR drop heatmap, switching activity, dynamic/leakage power, hotspots |
| `power-debug-recs` | Before/after power, optimization actions, savings, domain analysis |
| `peak-switching` | Activity timeline, peak windows, switching heatmap, clock domain activity |
| `defect-suspects` | Wafer defect map, XY coordinates, suspect ranking, failure clustering |
| `investigation-recs` | Investigation workflow, priority, confidence, similar cases, resolution history |
| `defect-localization` | Localization accuracy gauge, predicted vs actual, wafer comparison, validation |

---

## Implementation Files

```
src/types/kpiDrillDown.ts                          — scanDebug module, debug layout, SCAN_DEBUG_BREAKDOWN_DIMENSIONS
src/lib/kpiDrillDown/kpiDrillDownUtils.ts          — SCAN_DEBUG_AGENT_KPI_IDS (15 KPIs)
src/lib/kpiDrillDown/kpiProfiles.ts                — 15 widget profiles + custom titles
src/lib/kpiDrillDown/buildKpiWorkspace.ts          — scan debug AI decision, impact, approval, table
src/components/common/kpi-drilldown/KpiScanDebugDecisionPanel.tsx  — 40/60 split decision panel
src/components/common/kpi-drilldown/KpiDrillDownWorkspace.tsx
src/components/recommendation/SectionedKPIGrid.tsx — wired via CenterKPIGrid
src/components/recommendation/tabs/ScanDebugAgentTab.tsx
```

---

## Four Decision Questions (Every KPI)

1. **What failed?** — Executive Summary + hero visualization
2. **Why did AI recommend this?** — Split panel AI overview + root cause
3. **What improves if applied?** — Engineering Impact cards
4. **Should the engineer approve?** — Action Center + confidence/risk badges
