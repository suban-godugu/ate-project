export type Recommendation = "Keep" | "Review" | "Remove";
export type HeatmapOverlay = "fail-density" | "yield" | "cost";

export interface ExecutiveKPI {
  id: string;
  title: string;
  value: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
}

export interface PatternRow {
  id: string;
  testTime: number;
  cost: number;
  failRate: number;
  detectPower: number;
  roiScore: number;
  recommendation: Recommendation;
}

export interface CostTrendPoint {
  day: string;
  totalCost: number;
  costPerWafer: number;
}

export interface OptimizationParams {
  maxCost: number;
  yieldTarget: number;
  maxTestTime: number;
}

export interface OptimizationResults {
  costReduction: number;
  timeSavings: number;
  projectedYield: number;
  patternsReduced: number;
  totalSavings: number;
}

export interface SidebarFilters {
  dateRange: string;
  fab: string;
  tester: string;
  product: string;
}
