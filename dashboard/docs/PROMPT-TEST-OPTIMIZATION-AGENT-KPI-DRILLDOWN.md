# Cursor Prompt — Test Optimization Recommendation Agent KPI Drill-down

> **Module:** Recommendation Analysis · Test Optimization Recommendation Agent Tab  
> **Trigger:** Click any Test Optimization KPI card (19 KPIs across 7 sections)  
> **Stack:** Next.js App Router · React 19 · TypeScript · Tailwind CSS · shadcn/ui · Framer Motion · Recharts · React Query (API-ready)

---

## Objective

Redesign every KPI drill-down inside the **Test Optimization Recommendation Agent**.

Unlike Pattern and Scan Debug agents, this module is **business optimization focused** — yield, cost, test time, risk, and production efficiency.

Each KPI opens an **AI Test Optimization Decision Center** — not a debugging console, not documentation.

Engineers should immediately understand:

- Why AI generated this recommendation
- Expected yield, cost, test time, power, and ROI improvement
- Engineering risk and confidence
- How to safely approve and apply the recommendation

**Centerpiece:** Simulation Panel comparing **Current State vs Optimized State** (yield, runtime, cost, power, throughput, ROI).

Design inspiration: Synopsys DSO.ai · Siemens Solido AI · Cadence Cerebrus · Advantest SmarTest · Teradyne IGXL.

---

## Layout

| Property | Value |
|---|---|
| Modal width | **95vw** |
| Modal height | **92vh** |
| Layout preset | `optimization` |
| Module | `testOptimization` |
| Theme | Dark enterprise · glass cards · purple accents |

---

## Workspace Rows

1. **Executive Summary** — Current, Target, Expected Gain, Yield, Cost, Runtime, Power, ROI, Business Impact (9 cards)
2. **Optimization Overview** — Category, reason, historical success, business/engineering benefit, confidence, difficulty, risk
3. **Simulation — Current vs Optimized** — Hero centerpiece with before/after metrics
4. **Engineering Analytics** — KPI-specific dynamic widgets
5. **Breakdown Analysis** — Fab, Tester, Site, Lot, Wafer, Product, Package, Device, Test Flow, Test Program
6. **AI Explanation** — Optimization reason, feature importance, similar cases, alternatives, risk
7. **Business Impact** — Yield gain, cost reduction, runtime, power, ATE utilization, throughput, ROI, capacity
8. **Action Center** — Approve, Reject, Modify, Simulate, Generate Test Program, Report, Change Request
9. **Engineering Timeline** — Generated → Review → Simulation → Approval → Validation → Production → Completed
10. **Raw Data** — Enterprise grid with yield, runtime, cost, risk score, ROI, recommendation score
11. **AI Copilot** — Why suggested? Estimate savings. Similar optimizations. Compare lot. Predict ROI.

---

## 19 KPI-Specific Workspaces

| KPI ID | Widget Focus |
|---|---|
| `adaptive-recs` | Recommendation ranking, AI confidence, historical effectiveness, adaptive trend |
| `test-time-red` | Before/after runtime, waterfall, sequence optimization, savings projection |
| `flow-variants` | Flow comparison, variant ranking, success rate, runtime/coverage comparison |
| `stop-recs` | Hard vs soft stop, yield impact, escape analysis, rule effectiveness |
| `escapes-prevented` | Escape categories, defect distribution, prevention timeline, cost avoidance |
| `active-stop-rules` | Rule hierarchy, utilization, trigger frequency, optimization suggestions |
| `high-risk-devices` | Device ranking, risk heatmap, wafer distribution, risk timeline |
| `risk-recs` | Priority ranking, risk reduction, business impact, confidence |
| `avg-risk-score` | Risk gauge, trend, distribution, threshold analysis |
| `current-yield` | Yield trend, waterfall, wafer/lot comparison, AI effect |
| `yield-recs` | Recommendation ranking, yield contribution, success rate |
| `projected-yield` | Before/after yield, ROI waterfall, production gain, capacity |
| `est-cost-saving` | Monthly/annual savings, cost waterfall, cost by tester/product |
| `cost-recs` | Recommendation ranking, cost trend, ROI, historical comparison |
| `cost-per-device` | Cost breakdown, product/lot/tester comparison, savings simulation |
| `active-sites` | Site comparison, utilization, throughput, capacity planning |
| `site-recs` | Site optimization, load balancing, capacity forecast |
| `site-correlation` | Correlation matrix, site similarity, yield/runtime correlation |
| `total-opt-recs` | Categories, approval rate, success history, AI performance |

---

## Implementation Files

```
src/types/kpiDrillDown.ts                          — testOptimization module, TEST_OPT_BREAKDOWN_DIMENSIONS
src/lib/kpiDrillDown/kpiDrillDownUtils.ts          — TEST_OPT_AGENT_KPI_IDS (19 KPIs)
src/lib/kpiDrillDown/kpiProfiles.ts                — 19 widget profiles + custom titles
src/lib/kpiDrillDown/buildKpiWorkspace.ts          — business impact, test opt simulation, approval actions
src/components/common/kpi-drilldown/KpiRecommendationPanels.tsx  — hero simulation panel
src/components/common/kpi-drilldown/KpiDrillDownWorkspace.tsx    — isTestOptimization branch
src/components/recommendation/SectionedKPIGrid.tsx — wired via CenterKPIGrid
src/components/recommendation/tabs/TestOptAgentTab.tsx
```

---

## Four Decision Questions (Every KPI)

1. **Why did AI recommend this?** — Optimization Overview + AI Explanation
2. **What improves if applied?** — Executive Summary + Business Impact + Simulation Hero
3. **What is the business ROI?** — Simulation metrics + Business Impact cards
4. **Should the engineer approve?** — Action Center + confidence/risk badges
