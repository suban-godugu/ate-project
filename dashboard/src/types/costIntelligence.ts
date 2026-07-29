export type CostTab =
  | "overview"
  | "scan-chain"
  | "mbist"
  | "lbist"
  | "wafer"
  | "ai-optimization";

export type Priority = "Critical" | "High" | "Medium" | "Low";

export type CostModule = "Scan Chain" | "MBIST" | "LBIST" | "Wafer";

export interface CostKPI {
  id: string;
  title: string;
  value: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
}

export interface CostSegment {
  name: string;
  value: number;
  color: string;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface StackedCostPoint {
  label: string;
  equipment: number;
  tester: number;
  engineering: number;
  pattern: number;
  repair: number;
  retest: number;
}

export interface ProductCostRow {
  product: string;
  lot: string;
  wafer: string;
  totalCost: string;
  costPerDie: string;
  yield: string;
  estimatedSavings: string;
}

export interface AICostSummary {
  highestCostModule: string;
  mostExpensivePattern: string;
  longestTestTime: string;
  highestRetestCost: string;
  highestRepairCost: string;
  estimatedSavings: string;
}

export interface ScanChainCostRow {
  patternId: string;
  scanChain: string;
  executionTime: string;
  cost: string;
  recommendation: string;
  expectedSavings: string;
}

export interface MbistCostRow {
  memory: string;
  bank: string;
  cost: string;
  repairCost: string;
  recommendation: string;
}

export interface LbistCostRow {
  logicBlock: string;
  runtime: string;
  cost: string;
  recommendation: string;
}

export interface WaferCostRow {
  lot: string;
  wafer: string;
  yield: string;
  cost: string;
  recommendation: string;
}

export interface AICostRecommendationRow {
  module: CostModule;
  issue: string;
  currentCost: string;
  optimizedCost: string;
  savings: string;
  priority: Priority;
  confidence: number;
  recommendation: string;
}

export interface ModuleCostSummary {
  module: CostModule;
  currentCost: string;
  optimizedCost: string;
  savings: string;
}

export interface EnterpriseCostSummary {
  modules: ModuleCostSummary[];
  totalCost: string;
  totalSavings: string;
  roi: string;
  yieldImprovement: string;
  testTimeReduction: string;
}

export const costOptimizationCategories = [
  "Pattern Optimization",
  "Memory Optimization",
  "Logic Optimization",
  "Wafer Optimization",
  "Tester Optimization",
  "Retest Reduction",
  "Yield Improvement",
  "Cost Reduction",
];
