# Cursor Prompt — Pattern Recommendation Agent KPI Drill-down

> **Module:** Recommendation Analysis · Pattern Recommendation Agent Tab  
> **Trigger:** Click any Pattern Agent KPI card (10 KPIs)  
> **Stack:** Next.js App Router · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Recharts · React Query (API-ready)

---

## Objective

Redesign every KPI drill-down inside the **Pattern Recommendation Agent**.

The current popup is too generic. Each KPI must open an **AI Pattern Optimization Decision Workspace** — not documentation, not a simple analytics dashboard.

Engineers should immediately understand:

- Why the AI generated this recommendation
- Which ATPG patterns and scan chains are affected
- Expected coverage, runtime, power, memory, and cost improvement
- Recommendation confidence and engineering risk
- How to safely approve, reject, or modify the recommendation

**Decision-focused layout:** Before vs After Pattern Optimization comparison.

Design inspiration: Synopsys DSO.ai · Cadence Cerebrus · Siemens Solido AI · Advantest SmarTest · Teradyne IGXL.

---

## Layout

| Property | Value |
|---|---|
| Modal width | **95vw** |
| Modal height | **92vh** |
| Layout preset | `optimization` |
| Theme | Dark enterprise · glass cards · purple accents |
| Structure | Sticky header · scrollable body · sticky footer · animated open/close |

---

## Workspace Rows

1. **Executive Summary** — Current, Target, Pattern Reduction, Coverage Gain, Runtime Reduction, Power Saving, Memory Saving, ATE Cost Saving, Business ROI (9 cards + sparklines)
2. **AI Decision Overview** — Category, reason, optimization goal, historical success, similar cases, engineering/business benefit, confidence, difficulty, risk
3. **Pattern Analytics** — Dynamic engineering widgets (treemap, similarity matrix, heatmap, dependency graph, waterfall, etc.)
4. **Pattern Breakdown** — Interactive drill-down by pattern group, pattern, fault model, coverage, compression, runtime, tester, lot, wafer
5. **AI Explanation** — Recommendation reason, feature importance, similar cases, alternative optimization, risk analysis, expected outcome
6. **Engineering Impact** — Coverage, pattern count, runtime, power, compression, ATE utilization, memory, cost
7. **Approval Center** — Approve, Reject, Modify, Assign, Generate ATPG Script, Export, Report, Change Request
8. **Simulation — Before vs After** — Pattern count, coverage, runtime, memory, power, cost, execution time
9. **Engineering Timeline** — Generated → Review → Simulation → Approval → Pattern Update → Regression → Production
10. **Raw Engineering Data** — Enterprise grid with pattern ID, name, group, fault model, coverage, runtime, power, compression, recommendation score, engineer decision
11. **AI Copilot** — Why was this pattern selected? Show duplicates. Estimate runtime/coverage. Suggest safer optimization.

---

## 10 KPI-Specific Workspaces

| KPI ID | Widget Focus |
|---|---|
| `redundant` | Duplicate pattern clusters, similarity matrix, dependency graph, runtime savings, redundant heatmap |
| `removal` | Removal priority ranking, coverage impact, runtime reduction, risk analysis, AI confidence |
| `removal-conf` | Confidence gauge, historical trend, engineer approval rate, success history, AI calibration |
| `reorder` | Pattern execution flow, before vs after ordering, runtime comparison, dependency graph, AI ranking |
| `atpg` | Coverage gap, suggested patterns, fault coverage, ATPG priority, historical success |
| `fault-models` | Fault model distribution, coverage per model, detection rate, historical comparison, AI recommendation |
| `low-power` | Power before vs after, switching activity, low power pattern list, energy trend, runtime impact |
| `power-saving` | Power waterfall, tester power usage, pattern power ranking, historical savings, AI estimate |
| `coverage-delta` | Coverage trend, heatmap, module comparison, before vs after, historical gain |
| `total` | Recommendation categories, monthly trend, approval rate, success history, AI effectiveness |

---

## Architecture

Configuration-driven drill-down framework — each KPI declares:

- Header metadata (title, icon, badges, recommendation status, priority, AI version)
- Summary metrics (9-card executive summary)
- Widget layout (from `kpiProfiles.ts`)
- AI decision + explanation templates
- Approval actions + simulation metrics
- Data grid schema

**Module:** `recommendation`  
**Layout preset:** `optimization` (95vw × 92vh)

---

## Implementation Files

```
src/types/kpiDrillDown.ts                          — recommendation module types
src/lib/kpiDrillDown/kpiDrillDownUtils.ts          — PATTERN_AGENT_KPI_IDS, toDrillDownKPI
src/lib/kpiDrillDown/kpiProfiles.ts                — 10 pattern-agent widget profiles
src/lib/kpiDrillDown/buildKpiWorkspace.ts          — AI decision, explanation, impact, simulation, approval
src/components/common/kpi-drilldown/KpiRecommendationPanels.tsx
src/components/common/kpi-drilldown/KpiDrillDownWorkspace.tsx  — isRecommendation branch
src/components/common/kpi-drilldown/KpiDrillDownModal.tsx
src/components/recommendation/CenterKPIGrid.tsx      — wired to KpiDrillDownModal
src/components/recommendation/tabs/PatternAgentTab.tsx
```

---

## Four Engineering Questions (Every KPI)

1. **Why did the AI recommend this?** — AI Decision Overview + AI Explanation
2. **What patterns are affected?** — Pattern Breakdown + Raw Data Grid
3. **What is the expected improvement?** — Executive Summary + Engineering Impact + Simulation
4. **Should the engineer approve it?** — Approval Center + confidence/risk badges
