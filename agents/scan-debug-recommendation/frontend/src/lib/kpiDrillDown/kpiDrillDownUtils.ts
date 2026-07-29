import type { KpiSeverity, KpiStatus, RecommendationStatus } from "@/types/kpiDrillDown";

export function severityClass(severity: KpiSeverity): string {
  switch (severity) {
    case "critical":
      return "bg-danger/15 text-danger border-danger/30";
    case "high":
      return "bg-warning/15 text-warning border-warning/30";
    case "medium":
      return "bg-primary/15 text-primary border-primary/30";
    case "low":
      return "bg-success/15 text-success border-success/30";
    default:
      return "bg-slate-500/15 text-slate-300 border-slate-500/30";
  }
}

export function statusLabel(status: KpiStatus): string {
  return status.replace(/_/g, " ");
}

export function recStatusClass(status: RecommendationStatus): string {
  switch (status) {
    case "approved":
      return "bg-success/15 text-success border-success/30";
    case "rejected":
      return "bg-danger/15 text-danger border-danger/30";
    case "in_review":
      return "bg-warning/15 text-warning border-warning/30";
    case "assigned":
      return "bg-sky-500/15 text-sky-300 border-sky-500/30";
    default:
      return "bg-primary/15 text-primary border-primary/30";
  }
}

export function formatPct(v: number, digits = 1): string {
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

export function confidenceColor(c: number): string {
  if (c >= 0.9) return "text-success";
  if (c >= 0.8) return "text-sky-300";
  if (c >= 0.7) return "text-warning";
  return "text-danger";
}
