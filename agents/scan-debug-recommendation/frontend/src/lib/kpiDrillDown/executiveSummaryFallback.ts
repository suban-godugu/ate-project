import type { ExecutiveSummaryCard, KpiCardModel } from "@/types/kpiDrillDown";

export function buildExecutiveSummaryFallback(kpis: KpiCardModel[] = []): ExecutiveSummaryCard[] {
  const find = (id: string) => kpis.find((k) => k.id === id)?.value;

  return [
    {
      id: "broken_chains",
      label: "Broken Chains",
      value: String(find("broken_chains") ?? "0"),
      detail: "Chains requiring Inspect Scan Chain",
      tone: "danger",
    },
    {
      id: "timing_debug_recs",
      label: "Timing Issues",
      value: String(find("timing_debug_recs") ?? "0"),
      detail: "Review Capture Clock Timing recommendations",
      tone: "warning",
    },
    {
      id: "power_debug_recs",
      label: "Power Issues",
      value: String(find("power_debug_recs") ?? "0"),
      detail: "Check IR-Drop During Capture recommendations",
      tone: "warning",
    },
    {
      id: "constraint_violations",
      label: "Constraint Violations",
      value: String(find("constraint_violations") ?? "0"),
      detail: "Review ATPG Constraints recommendations",
      tone: "info",
    },
    {
      id: "investigation_recs",
      label: "Physical Defects",
      value: String(find("investigation_recs") ?? "0"),
      detail: "Investigate Physical Defect recommendations",
      tone: "primary",
    },
    {
      id: "coverage_impact",
      label: "Coverage Improvement",
      value: String(find("coverage_impact") ?? "—"),
      detail: "Projected after constraint fixes",
      tone: "success",
    },
    {
      id: "debug_recommendations",
      label: "Estimated Yield Improvement",
      value: "—",
      detail: "Across active failing lots",
      tone: "success",
    },
    {
      id: "debug_time_saved",
      label: "Expected Debug Time Reduction",
      value: "—",
      detail: "Estimated debug hours saved",
      tone: "success",
    },
    {
      id: "avg_ai_confidence",
      label: "AI Confidence",
      value: String(find("avg_ai_confidence") ?? "—"),
      detail: "DQN policy confidence",
      tone: "info",
    },
  ];
}
