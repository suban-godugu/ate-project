import { generateGridHeatmap } from "@/lib/heatmapUtils";
import type {
  AIRecommendationAlertRow,
  AlertKPI,
  AlertSegment,
  CostAlertRow,
  CriticalAlertSummary,
  ExecutiveAlertSummary,
  LbistAlertRow,
  MbistAlertRow,
  RecentAlertRow,
  ScanChainAlertRow,
  TrendPoint,
  WaferAlertRow,
} from "@/types/alerts";

export const overviewKPIs: AlertKPI[] = [
  { id: "total", title: "Total Alerts", value: "248", change: 8.4, trend: "up", sparkline: [198, 210, 218, 225, 232, 240, 248], icon: "bell", positiveIsGood: false },
  { id: "critical", title: "Critical Alerts", value: "18", change: 12.5, trend: "up", sparkline: [10, 11, 12, 14, 15, 16, 18], icon: "alert-octagon", positiveIsGood: false },
  { id: "warning", title: "Warning Alerts", value: "64", change: 6.2, trend: "up", sparkline: [48, 52, 54, 56, 58, 62, 64], icon: "alert-triangle", positiveIsGood: false },
  { id: "resolved", title: "Resolved Alerts", value: "142", change: 14.8, trend: "up", sparkline: [98, 108, 115, 122, 128, 135, 142], icon: "check-circle", positiveIsGood: true },
  { id: "open", title: "Open Alerts", value: "86", change: -4.2, trend: "down", sparkline: [102, 98, 94, 92, 90, 88, 86], icon: "inbox", positiveIsGood: true },
  { id: "resolution", title: "Avg Resolution Time", value: "2.4 hrs", change: -8.6, trend: "down", sparkline: [3.8, 3.4, 3.1, 2.9, 2.7, 2.5, 2.4], icon: "timer", positiveIsGood: true },
];

export const scanChainKPIs: AlertKPI[] = [
  { id: "failing", title: "Failing Scan Chains", value: "14", change: 10.2, trend: "up", sparkline: [8, 9, 10, 11, 12, 13, 14], icon: "link", positiveIsGood: false },
  { id: "broken", title: "Broken Scan Chains", value: "6", change: 8.4, trend: "up", sparkline: [3, 3, 4, 4, 5, 5, 6], icon: "unlink", positiveIsGood: false },
  { id: "coverage", title: "Coverage Drop", value: "8", change: 6.2, trend: "up", sparkline: [4, 5, 5, 6, 7, 7, 8], icon: "trending-down", positiveIsGood: false },
  { id: "diagnosis", title: "Diagnosis Errors", value: "5", change: 4.8, trend: "up", sparkline: [2, 2, 3, 3, 4, 4, 5], icon: "search", positiveIsGood: false },
  { id: "pattern", title: "Pattern Failures", value: "22", change: 12.4, trend: "up", sparkline: [12, 14, 16, 17, 18, 20, 22], icon: "scan", positiveIsGood: false },
  { id: "critical", title: "Critical Alerts", value: "7", change: 14.2, trend: "up", sparkline: [3, 3, 4, 4, 5, 6, 7], icon: "alert-octagon", positiveIsGood: false },
];

export const mbistKPIs: AlertKPI[] = [
  { id: "memory", title: "Memory Failures", value: "18", change: 8.6, trend: "up", sparkline: [10, 12, 13, 14, 15, 16, 18], icon: "memory", positiveIsGood: false },
  { id: "repair", title: "Repair Failures", value: "9", change: 6.4, trend: "up", sparkline: [5, 5, 6, 6, 7, 8, 9], icon: "wrench", positiveIsGood: false },
  { id: "bank", title: "Bank Failures", value: "12", change: 10.2, trend: "up", sparkline: [6, 7, 8, 9, 10, 11, 12], icon: "layers", positiveIsGood: false },
  { id: "coverage", title: "Coverage Loss", value: "6", change: 4.8, trend: "up", sparkline: [3, 3, 4, 4, 5, 5, 6], icon: "target", positiveIsGood: false },
  { id: "critical", title: "Critical Memories", value: "5", change: 12.8, trend: "up", sparkline: [2, 2, 3, 3, 4, 4, 5], icon: "alert-octagon", positiveIsGood: false },
  { id: "open", title: "Open Alerts", value: "24", change: -3.2, trend: "down", sparkline: [28, 27, 26, 26, 25, 24, 24], icon: "inbox", positiveIsGood: true },
];

export const lbistKPIs: AlertKPI[] = [
  { id: "logic", title: "Logic Failures", value: "16", change: 9.4, trend: "up", sparkline: [8, 10, 11, 12, 13, 14, 16], icon: "binary", positiveIsGood: false },
  { id: "coverage", title: "Coverage Issues", value: "10", change: 7.2, trend: "up", sparkline: [5, 6, 7, 7, 8, 9, 10], icon: "target", positiveIsGood: false },
  { id: "signature", title: "Signature Mismatch", value: "7", change: 8.8, trend: "up", sparkline: [3, 3, 4, 5, 5, 6, 7], icon: "fingerprint", positiveIsGood: false },
  { id: "blocks", title: "Critical Blocks", value: "4", change: 10.6, trend: "up", sparkline: [2, 2, 2, 3, 3, 3, 4], icon: "alert-octagon", positiveIsGood: false },
  { id: "runtime", title: "Runtime Issues", value: "8", change: 5.4, trend: "up", sparkline: [4, 5, 5, 6, 6, 7, 8], icon: "timer", positiveIsGood: false },
  { id: "open", title: "Open Alerts", value: "19", change: -2.8, trend: "down", sparkline: [22, 22, 21, 21, 20, 19, 19], icon: "inbox", positiveIsGood: true },
];

export const waferKPIs: AlertKPI[] = [
  { id: "yield", title: "Yield Drop", value: "11", change: 9.8, trend: "up", sparkline: [5, 6, 7, 8, 9, 10, 11], icon: "trending-down", positiveIsGood: false },
  { id: "hotspot", title: "Hotspot Detection", value: "8", change: 7.4, trend: "up", sparkline: [4, 4, 5, 5, 6, 7, 8], icon: "flame", positiveIsGood: false },
  { id: "defect", title: "Defect Density", value: "14", change: 6.2, trend: "up", sparkline: [8, 9, 10, 11, 12, 13, 14], icon: "microscope", positiveIsGood: false },
  { id: "critical", title: "Critical Wafers", value: "6", change: 11.2, trend: "up", sparkline: [2, 2, 3, 3, 4, 5, 6], icon: "alert-octagon", positiveIsGood: false },
  { id: "retest", title: "Retest Required", value: "9", change: 8.6, trend: "up", sparkline: [4, 5, 5, 6, 7, 8, 9], icon: "refresh", positiveIsGood: false },
  { id: "scrap", title: "Scrap Risk", value: "4", change: 5.2, trend: "up", sparkline: [2, 2, 2, 3, 3, 3, 4], icon: "trash", positiveIsGood: false },
];

export const costKPIs: AlertKPI[] = [
  { id: "increase", title: "Cost Increase", value: "12", change: 8.4, trend: "up", sparkline: [6, 7, 8, 9, 10, 11, 12], icon: "trending-up", positiveIsGood: false },
  { id: "testtime", title: "High Test Time", value: "8", change: 6.8, trend: "up", sparkline: [4, 4, 5, 5, 6, 7, 8], icon: "timer", positiveIsGood: false },
  { id: "retest", title: "Retest Cost", value: "6", change: 7.2, trend: "up", sparkline: [3, 3, 4, 4, 5, 5, 6], icon: "refresh", positiveIsGood: false },
  { id: "utilization", title: "Tester Utilization", value: "94%", change: 4.2, trend: "up", sparkline: [82, 85, 87, 89, 91, 93, 94], icon: "activity", positiveIsGood: false },
  { id: "roi", title: "ROI Loss", value: "5", change: 5.6, trend: "up", sparkline: [2, 2, 3, 3, 4, 4, 5], icon: "trending-down", positiveIsGood: false },
  { id: "budget", title: "Budget Exceeded", value: "3", change: 12.4, trend: "up", sparkline: [1, 1, 1, 2, 2, 2, 3], icon: "dollar", positiveIsGood: false },
];

export const aiRecKPIs: AlertKPI[] = [
  { id: "pending", title: "Pending Recommendations", value: "42", change: 6.8, trend: "up", sparkline: [28, 32, 34, 36, 38, 40, 42], icon: "clock", positiveIsGood: false },
  { id: "critical", title: "Critical Recommendations", value: "14", change: 10.2, trend: "up", sparkline: [6, 7, 8, 10, 11, 12, 14], icon: "alert-octagon", positiveIsGood: false },
  { id: "roi", title: "High ROI Actions", value: "18", change: 8.4, trend: "up", sparkline: [10, 12, 13, 14, 15, 16, 18], icon: "target", positiveIsGood: true },
  { id: "optimization", title: "Optimization Opportunities", value: "36", change: 12.6, trend: "up", sparkline: [20, 24, 26, 28, 30, 33, 36], icon: "sparkles", positiveIsGood: true },
  { id: "approval", title: "Approval Pending", value: "22", change: 4.8, trend: "up", sparkline: [14, 16, 17, 18, 19, 21, 22], icon: "inbox", positiveIsGood: false },
  { id: "implemented", title: "Implemented", value: "68", change: 14.2, trend: "up", sparkline: [38, 44, 50, 54, 58, 64, 68], icon: "check-circle", positiveIsGood: true },
];

export const alertDistribution: AlertSegment[] = [
  { name: "Scan Chain", value: 28, color: "#7C3AED" },
  { name: "MBIST", value: 18, color: "#06B6D4" },
  { name: "LBIST", value: 14, color: "#F97316" },
  { name: "Wafer", value: 20, color: "#22C55E" },
  { name: "Cost", value: 12, color: "#EAB308" },
  { name: "AI Recommendation", value: 8, color: "#EC4899" },
];

export const severityDistribution: TrendPoint[] = [
  { label: "Critical", value: 18 },
  { label: "High", value: 42 },
  { label: "Medium", value: 86 },
  { label: "Low", value: 102 },
];

export const alertTrend: TrendPoint[] = [
  { label: "Day 1", value: 12 },
  { label: "Day 5", value: 18 },
  { label: "Day 10", value: 22 },
  { label: "Day 15", value: 28 },
  { label: "Day 20", value: 24 },
  { label: "Day 25", value: 32 },
  { label: "Day 30", value: 26 },
];

export const recentAlerts: RecentAlertRow[] = [
  { id: "ALT-4821", sourceModule: "Scan Chain", lotId: "LOT-4821", waferId: "W-12", severity: "Critical", description: "Scan chain SC-4821 pattern failure detected", status: "Open", assignedEngineer: "J. Park", createdTime: "2 min ago" },
  { id: "ALT-3105", sourceModule: "MBIST", lotId: "LOT-3105", waferId: "W-22", severity: "Critical", description: "SRAM Bank-2 repair failure threshold exceeded", status: "Investigating", assignedEngineer: "M. Chen", createdTime: "8 min ago" },
  { id: "ALT-7892", sourceModule: "Wafer", lotId: "LOT-7892", waferId: "W-08", severity: "High", description: "Yield drop below 90% on edge dies", status: "Open", assignedEngineer: "S. Patel", createdTime: "15 min ago" },
  { id: "ALT-2441", sourceModule: "LBIST", lotId: "LOT-2441", waferId: "W-04", severity: "High", description: "MISR signature mismatch on LB-GPU block", status: "Investigating", assignedEngineer: "A. Kim", createdTime: "22 min ago" },
  { id: "ALT-9012", sourceModule: "Cost", lotId: "LOT-4821", waferId: "W-12", severity: "Medium", description: "Test cost exceeded budget threshold by 12%", status: "Open", assignedEngineer: "R. Singh", createdTime: "35 min ago" },
  { id: "ALT-1567", sourceModule: "AI Recommendation", lotId: "LOT-3105", waferId: "W-15", severity: "High", description: "Critical optimization pending engineer approval", status: "Pending", assignedEngineer: "L. Wong", createdTime: "48 min ago" },
  { id: "ALT-3344", sourceModule: "Scan Chain", lotId: "LOT-4822", waferId: "W-06", severity: "Medium", description: "Coverage drop on PAT-118 pattern", status: "Resolved", assignedEngineer: "J. Park", createdTime: "1 hr ago" },
  { id: "ALT-5566", sourceModule: "Wafer", lotId: "LOT-3106", waferId: "W-18", severity: "Critical", description: "Defect hotspot detected in zone C", status: "Open", assignedEngineer: "S. Patel", createdTime: "1.5 hr ago" },
];

export const criticalAlertSummary: CriticalAlertSummary = {
  mostCriticalIssue: "Scan chain SC-4821 complete pattern failure",
  affectedProduct: "Chip-X7",
  affectedTester: "ATE-01",
  affectedLot: "LOT-4821",
  estimatedYieldImpact: "-2.4%",
  estimatedCostImpact: "$18,400",
  recommendedAction: "Immediate pattern diagnosis and retest gating on SC-4821",
};

export const executiveAlertSummary: ExecutiveAlertSummary = {
  criticalAlerts: "18",
  openAlerts: "86",
  resolvedToday: "24",
  averageResolutionTime: "2.4 hrs",
  estimatedYieldLoss: "-4.2%",
  estimatedCostImpact: "$42,800",
  topPriorityModule: "Scan Chain",
};

export const scanChainAlerts: ScanChainAlertRow[] = [
  { id: "ALT-SC-001", chainId: "SC-4821", pattern: "PAT-042", severity: "Critical", recommendation: "Run scan diagnosis on chain SC-4821", status: "Open" },
  { id: "ALT-SC-002", chainId: "SC-3156", pattern: "PAT-118", severity: "High", recommendation: "Review compression settings", status: "Investigating" },
  { id: "ALT-SC-003", chainId: "SC-7892", pattern: "PAT-007", severity: "Medium", recommendation: "Optimize pattern depth", status: "Open" },
  { id: "ALT-SC-004", chainId: "SC-2441", pattern: "PAT-056", severity: "High", recommendation: "Check chain connectivity", status: "Open" },
];

export const mbistAlerts: MbistAlertRow[] = [
  { id: "ALT-MB-001", memory: "SRAM-0", bank: "Bank-0", severity: "Critical", recommendation: "Initiate FIB repair flow" },
  { id: "ALT-MB-002", memory: "DRAM-2", bank: "Bank-2", severity: "High", recommendation: "Allocate spare row redundancy" },
  { id: "ALT-MB-003", memory: "SRAM-1", bank: "Bank-1", severity: "Medium", recommendation: "Reduce retest iterations" },
  { id: "ALT-MB-004", memory: "SRAM-4", bank: "Bank-4", severity: "High", recommendation: "Enable soft repair" },
];

export const lbistAlerts: LbistAlertRow[] = [
  { id: "ALT-LB-001", logicBlock: "LB-GPU", severity: "Critical", recommendation: "Verify MISR signature chain" },
  { id: "ALT-LB-002", logicBlock: "LB-NOC", severity: "High", recommendation: "Increase coverage patterns" },
  { id: "ALT-LB-003", logicBlock: "LB-CPU", severity: "Medium", recommendation: "Review logic retest cycles" },
  { id: "ALT-LB-004", logicBlock: "LB-DSP", severity: "High", recommendation: "Check parallel LBIST config" },
];

export const waferAlerts: WaferAlertRow[] = [
  { id: "ALT-WF-001", lot: "LOT-4821", wafer: "W-12", severity: "Critical", recommendation: "Retest edge dies only" },
  { id: "ALT-WF-002", lot: "LOT-3105", wafer: "W-22", severity: "High", recommendation: "Hotspot isolation in zone C" },
  { id: "ALT-WF-003", lot: "LOT-7892", wafer: "W-08", severity: "Medium", recommendation: "Bin merge optimization" },
  { id: "ALT-WF-004", lot: "LOT-3106", wafer: "W-15", severity: "Critical", recommendation: "Scrap risk mitigation" },
];

export const costAlerts: CostAlertRow[] = [
  { id: "ALT-CS-001", module: "Scan Chain", currentCost: "$125K", threshold: "$110K", recommendation: "Pattern optimization to reduce cost" },
  { id: "ALT-CS-002", module: "MBIST", currentCost: "$80K", threshold: "$75K", recommendation: "Repair cost reduction flow" },
  { id: "ALT-CS-003", module: "Wafer", currentCost: "$150K", threshold: "$130K", recommendation: "Targeted retest strategy" },
  { id: "ALT-CS-004", module: "Cost", currentCost: "$420K", threshold: "$400K", recommendation: "Budget reallocation review" },
];

export const aiRecommendationAlerts: AIRecommendationAlertRow[] = [
  { id: "REC-ALT-001", sourceModule: "Scan Chain", priority: "Critical", confidence: 94, status: "Pending", engineer: "J. Park" },
  { id: "REC-ALT-002", sourceModule: "MBIST", priority: "High", confidence: 91, status: "Open", engineer: "M. Chen" },
  { id: "REC-ALT-003", sourceModule: "Wafer", priority: "Critical", confidence: 92, status: "Investigating", engineer: "S. Patel" },
  { id: "REC-ALT-004", sourceModule: "LBIST", priority: "High", confidence: 88, status: "Pending", engineer: "A. Kim" },
  { id: "REC-ALT-005", sourceModule: "AI Recommendation", priority: "Medium", confidence: 86, status: "Resolved", engineer: "L. Wong" },
];

export const moduleAlertTrend = (base: number): TrendPoint[] => [
  { label: "W1", value: base + 4 },
  { label: "W2", value: base + 2 },
  { label: "W3", value: base + 6 },
  { label: "W4", value: base },
];

export function generateWaferAlertHeatmap(rows = 12, cols = 16): { value: number; row: number; col: number }[] {
  return generateGridHeatmap(rows, cols, 0.5, 0.5);
}
