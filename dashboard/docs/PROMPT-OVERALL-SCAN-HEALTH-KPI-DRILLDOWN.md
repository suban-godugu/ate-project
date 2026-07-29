# PROMPT: Overall Scan Health KPI Drill-Down Card

> **Module:** Scan Chain Analysis · Overview Tab · Executive KPIs  
> **KPI ID:** `overall-health`  
> **Trigger:** Click **Overall Scan Health** KPI card only  
> **Stack:** Next.js 16 (App Router) · TypeScript · Tailwind CSS v4 · shadcn/ui · Framer Motion · Lucide React · Dark Enterprise Theme

---

## Objective

Edit ONLY the **Overall Scan Health** KPI drill-down popup/card.

Do NOT modify any other KPI drill-downs, layouts, routing, shared components, global styles, or dashboard pages.

Create this as a **separate component/file** so every KPI can have its own independent drill-down implementation.

---

## File Structure

```
src/components/scan-chain/kpi-drilldowns/
    OverallScanHealthDrillCard.tsx
    OverallScanHealthDrillDownModal.tsx

src/lib/scan-chain/
    overallScanHealthDrillData.ts
```

Do not reuse the generic KPI popup (`KpiDrillDownModal` / `KpiDrillDownWorkspace`).

The component must receive all values through props.

```ts
interface OverallScanHealthProps {
  currentHealth: number;
  targetHealth: number;
  trend: number;
  gap: number;
  status: string;
  risk: string;
  businessImpact: string;
  operationalPriority: string;
  healthyChains: number;
  failingChains: number;
  unknownChains: number;
  breakdown: {
    metric: string;
    weight: number;
    score: number;
    contribution: number;
  }[];
}
```

---

## Card Layout — Three Sections Only

### Section 1 — Executive Summary

Six KPI summary cards:

| Card | Example |
|------|---------|
| Current Health | 77.9% |
| Target | 80% |
| Gap | -2.1% (red if negative, green if positive) |
| Trend | +1.8% with arrow (green up / red down) |
| Business Impact | Moderate badge (Critical=red, High=orange, Moderate=yellow, Low=green) |
| Operational Priority | Monitor badge (Immediate / Monitor / Stable / Observation) |

### Section 2 — Health Score Breakdown

Responsive table: **Metric | Weight | Score | Contribution**

Rows: Healthy Chains, Pattern Pass Rate, Coverage, Diagnosis Confidence, Test Stability.

Footer: **Final Overall Scan Health** — large purple typography.

### Section 3 — Healthy vs Failing Chains

Three equal KPI cards:

- **Healthy Chains** — green, success icon
- **Failing Chains** — red, warning icon
- **Unknown** — amber, help icon

---

## UI Requirements

- Enterprise semiconductor dashboard styling
- Dark cards, rounded-xl, soft border, subtle glow, purple accent
- Responsive layout, Framer Motion fade-in, no overflow / horizontal scroll
- Do NOT hardcode values in the presentation component — bind through props
- Support future API integration via `buildOverallScanHealthDrillProps()` mapper

---

## Wiring (Scope)

Modify ONLY `ExecutiveOverviewKPIGrid.tsx` to route `overall-health` → `OverallScanHealthDrillDownModal`.

Do NOT edit drill-downs for:

- Total Scan Chains
- Healthy Chains KPI
- Failing Chains KPI
- Scan Coverage
- Average Diagnosis Confidence
- Average Test Time
- Other KPI drill-downs

Each KPI will have its own separate drill-down component and file.

---

## Implemented Files

| File | Purpose |
|------|---------|
| `src/components/scan-chain/kpi-drilldowns/OverallScanHealthDrillCard.tsx` | Props-driven 3-section card UI |
| `src/components/scan-chain/kpi-drilldowns/OverallScanHealthDrillDownModal.tsx` | Dialog wrapper |
| `src/lib/scan-chain/overallScanHealthDrillData.ts` | Mock/API-ready props builder |
| `src/components/scan-chain/overview/ExecutiveOverviewKPIGrid.tsx` | Routes only `overall-health` to dedicated modal |

**Status:** ✅ Implemented 2026-07-10
