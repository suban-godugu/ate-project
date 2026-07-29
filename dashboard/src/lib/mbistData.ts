import { generateGridHeatmap } from "@/lib/heatmapUtils";
import type {
  AIRecommendationRow,
  BankFailData,
  DiagnosisReportRow,
  FailAddressRow,
  FailureDistribution,
  FailureRecordRow,
  HealthSegment,
  MbistAIDiagnosis,
  MbistFailureRow,
  MbistKPI,
  RepairRecommendationRow,
  RiskCard,
  TrendPoint,
} from "@/types/mbist";

export const overviewKPIs: MbistKPI[] = [
  { id: "total-instances", title: "Total Memory Instances", value: "1,248", change: 2.1, trend: "up", sparkline: [1180, 1195, 1210, 1220, 1235, 1242, 1248], icon: "memory-stick", positiveIsGood: true },
  { id: "passed", title: "Passed Memories", value: "1,142", change: 1.8, trend: "up", sparkline: [1080, 1095, 1105, 1118, 1128, 1136, 1142], icon: "check-circle", positiveIsGood: true },
  { id: "failed", title: "Failed Memories", value: "86", change: -6.4, trend: "down", sparkline: [112, 105, 98, 94, 92, 88, 86], icon: "x-circle", positiveIsGood: false },
  { id: "coverage", title: "Memory Coverage", value: "97.4%", change: 0.9, trend: "up", sparkline: [95.2, 95.8, 96.2, 96.6, 96.9, 97.1, 97.4], icon: "shield-check", positiveIsGood: true },
  { id: "runtime", title: "Average MBIST Runtime", value: "24.8s", change: -3.2, trend: "down", sparkline: [28, 27.2, 26.5, 25.8, 25.2, 24.9, 24.8], icon: "timer", positiveIsGood: false },
  { id: "repair-rate", title: "Repair Success Rate", value: "82.6%", change: 4.1, trend: "up", sparkline: [74, 76, 78, 79, 80.5, 81.8, 82.6], icon: "wrench", positiveIsGood: true },
];

export const memoryHealthKPIs: MbistKPI[] = [
  { id: "healthy", title: "Healthy Memories", value: "1,142", change: 1.8, trend: "up", sparkline: [1080, 1095, 1105, 1118, 1128, 1136, 1142], icon: "check-circle", positiveIsGood: true },
  { id: "warning", title: "Warning Memories", value: "42", change: -8.2, trend: "down", sparkline: [58, 54, 50, 48, 46, 44, 42], icon: "alert-circle", positiveIsGood: false },
  { id: "critical", title: "Critical Memories", value: "28", change: -12.5, trend: "down", sparkline: [42, 38, 36, 34, 32, 30, 28], icon: "alert-octagon", positiveIsGood: false },
  { id: "utilization", title: "Memory Utilization", value: "78.4%", change: 2.4, trend: "up", sparkline: [72, 73, 74.5, 75.8, 76.5, 77.6, 78.4], icon: "gauge", positiveIsGood: true },
  { id: "repair-rate", title: "Repair Rate", value: "82.6%", change: 4.1, trend: "up", sparkline: [74, 76, 78, 79, 80.5, 81.8, 82.6], icon: "wrench", positiveIsGood: true },
  { id: "coverage", title: "Coverage", value: "97.4%", change: 0.9, trend: "up", sparkline: [95.2, 95.8, 96.2, 96.6, 96.9, 97.1, 97.4], icon: "target", positiveIsGood: true },
];

export const failureKPIs: MbistKPI[] = [
  { id: "total-failures", title: "Total Failures", value: "286", change: -5.8, trend: "down", sparkline: [320, 310, 302, 298, 292, 288, 286], icon: "x-circle", positiveIsGood: false },
  { id: "critical-failures", title: "Critical Failures", value: "28", change: -14.2, trend: "down", sparkline: [42, 38, 36, 34, 32, 30, 28], icon: "alert-octagon", positiveIsGood: false },
  { id: "address-failures", title: "Address Failures", value: "64", change: -4.5, trend: "down", sparkline: [72, 70, 68, 67, 66, 65, 64], icon: "map-pin", positiveIsGood: false },
  { id: "coupling-faults", title: "Coupling Faults", value: "48", change: -2.1, trend: "down", sparkline: [52, 51, 50, 50, 49, 48, 48], icon: "git-branch", positiveIsGood: false },
  { id: "retention-faults", title: "Retention Faults", value: "32", change: -6.8, trend: "down", sparkline: [38, 37, 36, 35, 34, 33, 32], icon: "clock", positiveIsGood: false },
  { id: "repair-failures", title: "Repair Failures", value: "18", change: -10.0, trend: "down", sparkline: [24, 22, 21, 20, 19, 18, 18], icon: "ban", positiveIsGood: false },
];

export const diagnosisKPIs: MbistKPI[] = [
  { id: "diagnosed", title: "Diagnosed Memories", value: "982", change: 5.2, trend: "up", sparkline: [880, 910, 930, 950, 965, 975, 982], icon: "search-check", positiveIsGood: true },
  { id: "unknown", title: "Unknown Memories", value: "36", change: -18.2, trend: "down", sparkline: [52, 48, 44, 42, 40, 38, 36], icon: "help-circle", positiveIsGood: false },
  { id: "repair-suggestions", title: "Repair Suggestions", value: "124", change: 12.4, trend: "up", sparkline: [88, 96, 102, 108, 114, 120, 124], icon: "lightbulb", positiveIsGood: true },
  { id: "accuracy", title: "Diagnosis Accuracy", value: "91.8%", change: 2.6, trend: "up", sparkline: [86, 87.5, 88.8, 89.5, 90.2, 91, 91.8], icon: "crosshair", positiveIsGood: true },
  { id: "coverage", title: "Coverage", value: "94.6%", change: 1.8, trend: "up", sparkline: [90, 91, 92, 92.8, 93.5, 94, 94.6], icon: "scan", positiveIsGood: true },
  { id: "confidence", title: "Confidence", value: "88.4%", change: 3.2, trend: "up", sparkline: [82, 83.5, 85, 86, 87, 88, 88.4], icon: "gauge", positiveIsGood: true },
];

export const memoryHealthData: HealthSegment[] = [
  { name: "Passed", value: 1142, color: "#22C55E" },
  { name: "Failed", value: 86, color: "#EF4444" },
  { name: "Repairable", value: 58, color: "#EAB308" },
  { name: "Unknown", value: 20, color: "#64748B" },
];

export const failureByBank: BankFailData[] = [
  { bank: "Bank-0", failCount: 18 },
  { bank: "Bank-1", failCount: 16 },
  { bank: "Bank-2", failCount: 14 },
  { bank: "Bank-3", failCount: 12 },
  { bank: "Bank-4", failCount: 10 },
  { bank: "Bank-5", failCount: 9 },
  { bank: "Bank-6", failCount: 8 },
  { bank: "Bank-7", failCount: 7 },
  { bank: "Bank-8", failCount: 6 },
  { bank: "Bank-9", failCount: 5 },
];

export const recentFailures: MbistFailureRow[] = [
  { memoryId: "MEM-004821", memoryType: "SRAM", bank: "Bank-0", address: "0x1A4F28", failureType: "Stuck-at Fault", status: "Failed", repairStatus: "In Progress", timestamp: "2026-06-29 09:12" },
  { memoryId: "MEM-003156", memoryType: "DRAM", bank: "Bank-2", address: "0x8B2C10", failureType: "Transition Fault", status: "Critical", repairStatus: "Pending", timestamp: "2026-06-29 09:08" },
  { memoryId: "MEM-007892", memoryType: "SRAM", bank: "Bank-1", address: "0x4E8914", failureType: "Coupling Fault", status: "Failed", repairStatus: "Not Repairable", timestamp: "2026-06-29 08:54" },
  { memoryId: "MEM-002441", memoryType: "eDRAM", bank: "Bank-4", address: "0xC01200", failureType: "Address Decoder Fault", status: "Warning", repairStatus: "Repaired", timestamp: "2026-06-29 08:42" },
  { memoryId: "MEM-009103", memoryType: "SRAM", bank: "Bank-3", address: "0x2F8A44", failureType: "Retention Fault", status: "Critical", repairStatus: "Pending", timestamp: "2026-06-29 08:30" },
  { memoryId: "MEM-001778", memoryType: "DRAM", bank: "Bank-5", address: "0x6D1028", failureType: "Read Disturb Fault", status: "Failed", repairStatus: "In Progress", timestamp: "2026-06-29 08:18" },
  { memoryId: "MEM-005632", memoryType: "SRAM", bank: "Bank-6", address: "0x9A3B6C", failureType: "Stuck-at Fault", status: "Warning", repairStatus: "Repaired", timestamp: "2026-06-29 08:06" },
  { memoryId: "MEM-008214", memoryType: "eDRAM", bank: "Bank-7", address: "0x1104F0", failureType: "Unknown", status: "Failed", repairStatus: "Pending", timestamp: "2026-06-29 07:58" },
];

export const failureTypeDistribution: FailureDistribution[] = [
  { name: "Stuck-at Fault", value: 28, color: "#7C3AED" },
  { name: "Transition Fault", value: 22, color: "#06B6D4" },
  { name: "Coupling Fault", value: 16, color: "#F97316" },
  { name: "Address Decoder Fault", value: 12, color: "#EAB308" },
  { name: "Retention Fault", value: 11, color: "#22C55E" },
  { name: "Read Disturb Fault", value: 8, color: "#EC4899" },
  { name: "Unknown", value: 3, color: "#64748B" },
];

export const aiDiagnosisSummary: MbistAIDiagnosis = {
  likelyRootCause: "Address decoder timing violation in SRAM Bank-0 segment",
  repairableMemories: 58,
  nonRepairableMemories: 28,
  repairEfficiency: 82.6,
  diagnosisConfidence: 91,
};

export const utilizationTrend: TrendPoint[] = [
  { label: "Mon", value: 72, value2: 68 },
  { label: "Tue", value: 74, value2: 70 },
  { label: "Wed", value: 75, value2: 72 },
  { label: "Thu", value: 76.5, value2: 74 },
  { label: "Fri", value: 77.8, value2: 76 },
  { label: "Sat", value: 78, value2: 77 },
  { label: "Sun", value: 78.4, value2: 78 },
];

export const temperatureTrend: TrendPoint[] = [
  { label: "Mon", value: 62 }, { label: "Tue", value: 64 }, { label: "Wed", value: 63 },
  { label: "Thu", value: 65 }, { label: "Fri", value: 66 }, { label: "Sat", value: 64 }, { label: "Sun", value: 63 },
];

export const accessDistribution: TrendPoint[] = [
  { label: "Read", value: 42 }, { label: "Write", value: 28 }, { label: "Refresh", value: 18 },
  { label: "MBIST", value: 12 },
];

export const memoryDensity: TrendPoint[] = [
  { label: "Zone A", value: 88 }, { label: "Zone B", value: 72 }, { label: "Zone C", value: 94 },
  { label: "Zone D", value: 68 }, { label: "Zone E", value: 82 }, { label: "Zone F", value: 76 },
];

export const failureTrend: TrendPoint[] = [
  { label: "Mon", value: 98, value2: 28 }, { label: "Tue", value: 92, value2: 26 },
  { label: "Wed", value: 88, value2: 24 }, { label: "Thu", value: 84, value2: 22 },
  { label: "Fri", value: 80, value2: 20 }, { label: "Sat", value: 82, value2: 21 }, { label: "Sun", value: 78, value2: 18 },
];

export const failureByType: TrendPoint[] = [
  { label: "SRAM", value: 42 }, { label: "DRAM", value: 28 }, { label: "eDRAM", value: 16 },
];

export const failureByBankChart: TrendPoint[] = failureByBank.map((b) => ({ label: b.bank, value: b.failCount }));

export const failureRecords: FailureRecordRow[] = recentFailures.map((r, i) => ({
  failureId: `F-MB-${10280 + i}`,
  memoryId: r.memoryId,
  memoryType: r.memoryType,
  bank: r.bank,
  failType: r.failureType,
  severity: r.status === "Critical" ? "Critical" : r.status === "Warning" ? "Warning" : "Recovered",
  timestamp: r.timestamp,
}));

export const diagnosisTimeline: TrendPoint[] = [
  { label: "Week 1", value: 680, value2: 48 }, { label: "Week 2", value: 740, value2: 42 },
  { label: "Week 3", value: 820, value2: 38 }, { label: "Week 4", value: 880, value2: 32 },
  { label: "Week 5", value: 920, value2: 28 }, { label: "Week 6", value: 982, value2: 24 },
];

export const failureCorrelation: TrendPoint[] = [
  { label: "T+0", value: 8 }, { label: "T+1", value: 18 }, { label: "T+2", value: 32 },
  { label: "T+3", value: 42 }, { label: "T+4", value: 38 }, { label: "T+5", value: 24 }, { label: "T+6", value: 12 },
];

export const aiConfidenceTrend: TrendPoint[] = [
  { label: "Mon", value: 84 }, { label: "Tue", value: 85.5 }, { label: "Wed", value: 86.8 },
  { label: "Thu", value: 87.4 }, { label: "Fri", value: 88.4 }, { label: "Sat", value: 88.2 }, { label: "Sun", value: 88.4 },
];

export const diagnosisReports: DiagnosisReportRow[] = [
  { memoryId: "MEM-004821", status: "Diagnosed", rootCause: "Address decoder timing", confidence: 91, repairSuggestion: "Adjust decoder hold margin +8ps" },
  { memoryId: "MEM-003156", status: "Partial", rootCause: "Transition path violation", confidence: 78, repairSuggestion: "Replace failing wordline driver" },
  { memoryId: "MEM-007892", status: "Diagnosed", rootCause: "Bit-line coupling short", confidence: 94, repairSuggestion: "FIB repair at BL pair 142" },
  { memoryId: "MEM-001778", status: "Unknown", rootCause: "Pending analysis", confidence: 42, repairSuggestion: "Run extended retention pattern" },
];

export const failAddressReport: FailAddressRow[] = [
  { address: "0x1A4F28", memoryId: "MEM-004821", bank: "Bank-0", failType: "Stuck-at", probability: 0.92 },
  { address: "0x8B2C10", memoryId: "MEM-003156", bank: "Bank-2", failType: "Transition", probability: 0.86 },
  { address: "0x4E8914", memoryId: "MEM-007892", bank: "Bank-1", failType: "Coupling", probability: 0.94 },
  { address: "0xC01200", memoryId: "MEM-002441", bank: "Bank-4", failType: "Decoder", probability: 0.78 },
];

export const repairRecommendations: RepairRecommendationRow[] = [
  { memoryId: "MEM-004821", recommendation: "Repair address decoder segment", priority: 1, successRate: 84 },
  { memoryId: "MEM-007892", recommendation: "FIB bit-line isolation", priority: 2, successRate: 72 },
  { memoryId: "MEM-003156", recommendation: "Replace wordline driver", priority: 3, successRate: 78 },
  { memoryId: "MEM-002441", recommendation: "Adjust refresh timing", priority: 4, successRate: 88 },
];

export const aiRecommendations: AIRecommendationRow[] = [
  { id: "AI-MB-001", memoryInstance: "MEM-004821", recommendation: "Repair address decoder in Bank-0", priority: "High", confidence: 91, expectedYieldGain: "+1.8%" },
  { id: "AI-MB-002", memoryInstance: "MEM-007892", recommendation: "Replace SRAM macro segment", priority: "High", confidence: 88, expectedYieldGain: "+1.2%" },
  { id: "AI-MB-003", memoryInstance: "MEM-003156", recommendation: "Increase transition margin pattern", priority: "Medium", confidence: 82, expectedYieldGain: "+0.8%" },
  { id: "AI-MB-004", memoryInstance: "MEM-009103", recommendation: "Apply retention stress screening", priority: "Medium", confidence: 76, expectedYieldGain: "+0.5%" },
];

export const riskCards: RiskCard[] = [
  { title: "Repair Suggestions", value: "124", subtitle: "Active repair actions", icon: "wrench" },
  { title: "Replacement Candidates", value: "18", subtitle: "Non-repairable macros", icon: "replace" },
  { title: "High Priority Memories", value: "12", subtitle: "Critical yield impact", icon: "alert-octagon" },
  { title: "Risk Score", value: "6.2/10", subtitle: "Aggregate memory risk", icon: "gauge" },
  { title: "Expected Yield Improvement", value: "+4.2%", subtitle: "If all repairs applied", icon: "trending-up" },
  { title: "Estimated Cost Savings", value: "$186K", subtitle: "Monthly projected savings", icon: "dollar" },
];


export function generateMemoryHeatmap(rows = 14, cols = 20): { value: number; row: number; col: number }[] {
  return generateGridHeatmap(rows, cols, 0.35, 0.65);
}

export const connectivityNodes = {
  nodes: [
    { id: "MEM-004821", label: "MEM-004821", status: "failed" },
    { id: "MEM-003156", label: "MEM-003156", status: "warning" },
    { id: "MEM-007892", label: "MEM-007892", status: "failed" },
    { id: "MEM-002441", label: "MEM-002441", status: "healthy" },
    { id: "MEM-009103", label: "MEM-009103", status: "warning" },
  ],
  edges: [
    { from: "MEM-004821", to: "MEM-003156" },
    { from: "MEM-003156", to: "MEM-007892" },
    { from: "MEM-007892", to: "MEM-002441" },
    { from: "MEM-002441", to: "MEM-009103" },
  ],
};
