export type KPIStatusVariant = "success" | "warning" | "danger" | "neutral" | "info";

/** Shared KPI shape used by UnifiedKPICard across all modules. */
export interface UnifiedKPI {
  id: string;
  title: string;
  value: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
  subtitle?: string;
  status?: string;
  statusVariant?: KPIStatusVariant;
  description?: string;
}
