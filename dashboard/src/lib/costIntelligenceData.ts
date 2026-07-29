import { generateGridHeatmap } from "@/lib/heatmapUtils";
import type {
  AICostRecommendationRow,
  AICostSummary,
  CostKPI,
  CostSegment,
  EnterpriseCostSummary,
  LbistCostRow,
  MbistCostRow,
  ProductCostRow,
  ScanChainCostRow,
  StackedCostPoint,
  TrendPoint,
  WaferCostRow,
} from "@/types/costIntelligence";

export const overviewKPIs: CostKPI[] = [
  { id: "total", title: "Total Test Cost", value: "$420K", change: -4.2, trend: "down", sparkline: [480, 465, 450, 440, 432, 425, 420], icon: "dollar", positiveIsGood: true },
  { id: "wafer", title: "Cost Per Wafer", value: "$1,842", change: -3.8, trend: "down", sparkline: [2100, 2050, 1980, 1920, 1880, 1860, 1842], icon: "microscope", positiveIsGood: true },
  { id: "die", title: "Cost Per Die", value: "$0.42", change: -2.1, trend: "down", sparkline: [0.48, 0.47, 0.46, 0.45, 0.44, 0.43, 0.42], icon: "cpu", positiveIsGood: true },
  { id: "time", title: "Average Test Time", value: "4.2 hrs", change: -5.6, trend: "down", sparkline: [5.2, 5.0, 4.8, 4.6, 4.5, 4.3, 4.2], icon: "timer", positiveIsGood: true },
  { id: "savings", title: "Estimated Savings", value: "$93K", change: 18.4, trend: "up", sparkline: [52, 58, 64, 72, 78, 86, 93], icon: "trending-up", positiveIsGood: true },
  { id: "roi", title: "ROI Improvement", value: "+22%", change: 6.2, trend: "up", sparkline: [12, 14, 16, 18, 19, 21, 22], icon: "target", positiveIsGood: true },
];

export const scanChainKPIs: CostKPI[] = [
  { id: "total", title: "Scan Chain Cost", value: "$125K", change: -6.8, trend: "down", sparkline: [148, 142, 138, 132, 130, 128, 125], icon: "scan", positiveIsGood: true },
  { id: "pattern", title: "Pattern Execution Cost", value: "$68K", change: -5.2, trend: "down", sparkline: [78, 76, 74, 72, 70, 69, 68], icon: "activity", positiveIsGood: true },
  { id: "compression", title: "Compression Cost", value: "$18K", change: -8.4, trend: "down", sparkline: [24, 22, 21, 20, 19, 18, 18], icon: "minimize", positiveIsGood: true },
  { id: "diagnosis", title: "Diagnosis Cost", value: "$22K", change: -3.1, trend: "down", sparkline: [26, 25, 24, 24, 23, 22, 22], icon: "search", positiveIsGood: true },
  { id: "retest", title: "Retest Cost", value: "$12K", change: -12.5, trend: "down", sparkline: [18, 16, 15, 14, 13, 12, 12], icon: "refresh", positiveIsGood: true },
  { id: "savings", title: "Optimization Savings", value: "$30K", change: 14.2, trend: "up", sparkline: [18, 20, 22, 24, 26, 28, 30], icon: "sparkles", positiveIsGood: true },
];

export const mbistKPIs: CostKPI[] = [
  { id: "total", title: "Total MBIST Cost", value: "$80K", change: -5.4, trend: "down", sparkline: [92, 90, 88, 86, 84, 82, 80], icon: "memory", positiveIsGood: true },
  { id: "repair", title: "Repair Cost", value: "$28K", change: -8.2, trend: "down", sparkline: [36, 34, 32, 31, 30, 29, 28], icon: "wrench", positiveIsGood: true },
  { id: "test", title: "Memory Test Cost", value: "$32K", change: -3.6, trend: "down", sparkline: [38, 37, 36, 35, 34, 33, 32], icon: "cpu", positiveIsGood: true },
  { id: "runtime", title: "Runtime Cost", value: "$14K", change: -4.8, trend: "down", sparkline: [18, 17, 16, 16, 15, 14, 14], icon: "timer", positiveIsGood: true },
  { id: "retest", title: "Retest Cost", value: "$6K", change: -10.2, trend: "down", sparkline: [9, 8, 8, 7, 7, 6, 6], icon: "refresh", positiveIsGood: true },
  { id: "savings", title: "Optimization Savings", value: "$20K", change: 12.8, trend: "up", sparkline: [12, 14, 15, 16, 17, 19, 20], icon: "sparkles", positiveIsGood: true },
];

export const lbistKPIs: CostKPI[] = [
  { id: "logic", title: "Logic Test Cost", value: "$65K", change: -4.6, trend: "down", sparkline: [74, 72, 70, 69, 68, 66, 65], icon: "binary", positiveIsGood: true },
  { id: "coverage", title: "Coverage Cost", value: "$24K", change: -3.2, trend: "down", sparkline: [28, 27, 26, 26, 25, 24, 24], icon: "target", positiveIsGood: true },
  { id: "runtime", title: "Runtime Cost", value: "$18K", change: -5.8, trend: "down", sparkline: [22, 21, 20, 20, 19, 18, 18], icon: "timer", positiveIsGood: true },
  { id: "retest", title: "Retest Cost", value: "$8K", change: -9.4, trend: "down", sparkline: [12, 11, 10, 10, 9, 8, 8], icon: "refresh", positiveIsGood: true },
  { id: "savings", title: "Optimization Savings", value: "$13K", change: 10.6, trend: "up", sparkline: [8, 9, 10, 10, 11, 12, 13], icon: "sparkles", positiveIsGood: true },
  { id: "repair", title: "Logic Repair Cost", value: "$15K", change: -6.4, trend: "down", sparkline: [18, 17, 17, 16, 16, 15, 15], icon: "wrench", positiveIsGood: true },
];

export const waferKPIs: CostKPI[] = [
  { id: "wafer", title: "Wafer Cost", value: "$150K", change: -4.8, trend: "down", sparkline: [168, 164, 160, 158, 155, 152, 150], icon: "microscope", positiveIsGood: true },
  { id: "retest", title: "Retest Cost", value: "$32K", change: -11.2, trend: "down", sparkline: [42, 40, 38, 36, 35, 33, 32], icon: "refresh", positiveIsGood: true },
  { id: "yield", title: "Yield Loss Cost", value: "$48K", change: -7.6, trend: "down", sparkline: [58, 56, 54, 52, 51, 49, 48], icon: "trending-down", positiveIsGood: true },
  { id: "scrap", title: "Scrap Cost", value: "$22K", change: -5.4, trend: "down", sparkline: [28, 27, 26, 25, 24, 23, 22], icon: "alert", positiveIsGood: true },
  { id: "bin", title: "Bin Cost", value: "$18K", change: -3.8, trend: "down", sparkline: [22, 21, 20, 20, 19, 18, 18], icon: "layers", positiveIsGood: true },
  { id: "savings", title: "Optimization Savings", value: "$30K", change: 15.4, trend: "up", sparkline: [18, 20, 22, 24, 26, 28, 30], icon: "sparkles", positiveIsGood: true },
];

export const costContribution: CostSegment[] = [
  { name: "Scan Chain", value: 38, color: "#7C3AED" },
  { name: "MBIST", value: 22, color: "#06B6D4" },
  { name: "LBIST", value: 18, color: "#F97316" },
  { name: "Wafer Analysis", value: 22, color: "#22C55E" },
];

export const costBreakdown: TrendPoint[] = [
  { label: "Scan Chain", value: 125 },
  { label: "MBIST", value: 80 },
  { label: "LBIST", value: 65 },
  { label: "Wafer", value: 150 },
];

export const monthlyCostTrend: TrendPoint[] = [
  { label: "Jan", value: 380 },
  { label: "Feb", value: 395 },
  { label: "Mar", value: 410 },
  { label: "Apr", value: 428 },
  { label: "May", value: 435 },
  { label: "Jun", value: 420 },
];

export const costDistribution: StackedCostPoint[] = [
  { label: "Jan", equipment: 85, tester: 62, engineering: 48, pattern: 72, repair: 38, retest: 28 },
  { label: "Feb", equipment: 88, tester: 65, engineering: 50, pattern: 75, repair: 40, retest: 30 },
  { label: "Mar", equipment: 90, tester: 68, engineering: 52, pattern: 78, repair: 42, retest: 32 },
  { label: "Apr", equipment: 92, tester: 70, engineering: 54, pattern: 80, repair: 44, retest: 34 },
  { label: "May", equipment: 94, tester: 72, engineering: 55, pattern: 82, repair: 45, retest: 35 },
  { label: "Jun", equipment: 90, tester: 68, engineering: 52, pattern: 78, repair: 42, retest: 32 },
];

export const productCostRows: ProductCostRow[] = [
  { product: "Chip-X7", lot: "LOT-4821", wafer: "W-12", totalCost: "$42,800", costPerDie: "$0.48", yield: "92.4%", estimatedSavings: "$8,200" },
  { product: "Chip-X7", lot: "LOT-4822", wafer: "W-08", totalCost: "$38,600", costPerDie: "$0.44", yield: "94.1%", estimatedSavings: "$6,400" },
  { product: "Chip-A3", lot: "LOT-3105", wafer: "W-22", totalCost: "$52,400", costPerDie: "$0.52", yield: "88.6%", estimatedSavings: "$12,800" },
  { product: "Chip-A3", lot: "LOT-3106", wafer: "W-15", totalCost: "$48,200", costPerDie: "$0.49", yield: "90.2%", estimatedSavings: "$9,600" },
  { product: "Chip-X7", lot: "LOT-4823", wafer: "W-04", totalCost: "$44,100", costPerDie: "$0.46", yield: "91.8%", estimatedSavings: "$7,400" },
];

export const aiCostSummary: AICostSummary = {
  highestCostModule: "Wafer Analysis ($150K)",
  mostExpensivePattern: "PAT-042 ($12,400)",
  longestTestTime: "SC-4821 (42 min)",
  highestRetestCost: "Wafer Retest ($32K)",
  highestRepairCost: "MBIST Repair ($28K)",
  estimatedSavings: "$93K (22% ROI)",
};

export const scanChainCostRows: ScanChainCostRow[] = [
  { patternId: "PAT-042", scanChain: "SC-4821", executionTime: "42 min", cost: "$12,400", recommendation: "Reduce pattern depth by 18%", expectedSavings: "$3,200" },
  { patternId: "PAT-118", scanChain: "SC-3156", executionTime: "38 min", cost: "$10,800", recommendation: "Enable scan compression", expectedSavings: "$2,800" },
  { patternId: "PAT-007", scanChain: "SC-7892", executionTime: "35 min", cost: "$9,600", recommendation: "Merge redundant patterns", expectedSavings: "$2,400" },
  { patternId: "PAT-056", scanChain: "SC-2441", executionTime: "28 min", cost: "$7,200", recommendation: "Optimize shift frequency", expectedSavings: "$1,800" },
  { patternId: "PAT-203", scanChain: "SC-9012", executionTime: "24 min", cost: "$6,400", recommendation: "Parallel chain execution", expectedSavings: "$1,600" },
];

export const mbistCostRows: MbistCostRow[] = [
  { memory: "SRAM-0", bank: "Bank-0", cost: "$8,400", repairCost: "$3,200", recommendation: "Allocate spare row redundancy" },
  { memory: "SRAM-1", bank: "Bank-1", cost: "$7,800", repairCost: "$2,800", recommendation: "Reduce retest iterations" },
  { memory: "DRAM-2", bank: "Bank-2", cost: "$9,200", repairCost: "$4,100", recommendation: "Optimize BIST runtime" },
  { memory: "SRAM-4", bank: "Bank-4", cost: "$6,600", repairCost: "$2,400", recommendation: "Enable soft repair flow" },
];

export const lbistCostRows: LbistCostRow[] = [
  { logicBlock: "LB-GPU", runtime: "18 min", cost: "$14,200", recommendation: "Increase coverage with fewer patterns" },
  { logicBlock: "LB-NOC", runtime: "14 min", cost: "$11,800", recommendation: "Optimize MISR signature chain" },
  { logicBlock: "LB-CPU", runtime: "16 min", cost: "$12,400", recommendation: "Reduce logic retest cycles" },
  { logicBlock: "LB-DSP", runtime: "10 min", cost: "$8,600", recommendation: "Parallel LBIST execution" },
];

export const waferCostRows: WaferCostRow[] = [
  { lot: "LOT-4821", wafer: "W-12", yield: "92.4%", cost: "$42,800", recommendation: "Retest edge dies only" },
  { lot: "LOT-3105", wafer: "W-22", yield: "88.6%", cost: "$52,400", recommendation: "Hotspot retest optimization" },
  { lot: "LOT-4822", wafer: "W-08", yield: "94.1%", cost: "$38,600", recommendation: "Bin merge optimization" },
  { lot: "LOT-3106", wafer: "W-15", yield: "90.2%", cost: "$48,200", recommendation: "Reduce scrap at zone C" },
];

export const aiCostRecommendations: AICostRecommendationRow[] = [
  { module: "Scan Chain", issue: "Expensive pattern execution", currentCost: "$68K", optimizedCost: "$52K", savings: "$16K", priority: "Critical", confidence: 94, recommendation: "Pattern depth reduction + compression" },
  { module: "MBIST", issue: "High repair cost", currentCost: "$28K", optimizedCost: "$18K", savings: "$10K", priority: "High", confidence: 91, recommendation: "Redundancy allocation optimization" },
  { module: "LBIST", issue: "Long logic runtime", currentCost: "$18K", optimizedCost: "$12K", savings: "$6K", priority: "High", confidence: 88, recommendation: "Parallel LBIST + coverage tuning" },
  { module: "Wafer", issue: "Yield loss cost", currentCost: "$48K", optimizedCost: "$32K", savings: "$16K", priority: "Critical", confidence: 92, recommendation: "Targeted retest + bin optimization" },
  { module: "Scan Chain", issue: "Retest overhead", currentCost: "$12K", optimizedCost: "$6K", savings: "$6K", priority: "Medium", confidence: 86, recommendation: "Smart retest gating" },
  { module: "Wafer", issue: "Scrap cost", currentCost: "$22K", optimizedCost: "$14K", savings: "$8K", priority: "Medium", confidence: 84, recommendation: "Defect hotspot isolation" },
];

export const enterpriseCostSummary: EnterpriseCostSummary = {
  modules: [
    { module: "Scan Chain", currentCost: "$125K", optimizedCost: "$95K", savings: "$30K" },
    { module: "MBIST", currentCost: "$80K", optimizedCost: "$60K", savings: "$20K" },
    { module: "LBIST", currentCost: "$65K", optimizedCost: "$52K", savings: "$13K" },
    { module: "Wafer", currentCost: "$150K", optimizedCost: "$120K", savings: "$30K" },
  ],
  totalCost: "$420K",
  totalSavings: "$93K",
  roi: "+22%",
  yieldImprovement: "+3.8%",
  testTimeReduction: "-18%",
};

export const patternCostTrend: TrendPoint[] = [
  { label: "W1", value: 72 },
  { label: "W2", value: 70 },
  { label: "W3", value: 69 },
  { label: "W4", value: 68 },
];

export const memoryCostTrend: TrendPoint[] = [
  { label: "W1", value: 88 },
  { label: "W2", value: 86 },
  { label: "W3", value: 84 },
  { label: "W4", value: 80 },
];

export const logicCostTrend: TrendPoint[] = [
  { label: "W1", value: 72 },
  { label: "W2", value: 70 },
  { label: "W3", value: 68 },
  { label: "W4", value: 65 },
];

export const waferCostTrend: TrendPoint[] = [
  { label: "W1", value: 168 },
  { label: "W2", value: 162 },
  { label: "W3", value: 156 },
  { label: "W4", value: 150 },
];

export function generateWaferCostHeatmap(rows = 12, cols = 16): { value: number; row: number; col: number }[] {
  return generateGridHeatmap(rows, cols, 0.5, 0.5);
}
