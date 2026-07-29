import { generateGridHeatmap } from "@/lib/heatmapUtils";
import { scanChainAlerts } from "@/lib/alertsData";
import type {
  AIDiagnosisSummary,
  AIRecommendationRow,
  ChipFailData,
  DebugPointRow,
  DiagnosisReportRow,
  FailureDistribution,
  FailureRecordRow,
  FailureAnalysisKPI,
  FailureAnalysisRow,
  FailureAISummary,
  RootCauseTreeNode,
  LotFailData,
  FailingChainRow,
  HealthSegment,
  PatternRecommendationRow,
  PatternAnalysisKPI,
  PatternAnalysisRow,
  PatternAISummary,
  PatternScatterPoint,
  PatternSummaryRow,
  RepairPriorityRow,
  RootCauseRow,
  ScanDiagnosisExecutiveSummary,
  ScanDiagnosisKPISection,
  ScanDiagnosisRecommendationRow,
  ChainFailRankingData,
  FailureCorrelationMatrix,
  TopologyGraphNode,
  TopologyGraphEdge,
  ScanKPI,
  SuspectedCellRow,
  TrendPoint,
} from "@/types/scanChain";

export const overviewKPIs: ScanKPI[] = [
  {
    id: "total-chains",
    title: "Total Scan Chains",
    value: "2,847",
    change: 2.4,
    trend: "up",
    sparkline: [2650, 2680, 2720, 2750, 2780, 2810, 2847],
    icon: "link",
    positiveIsGood: true,
  },
  {
    id: "failing-chains",
    title: "Failing Scan Chains",
    value: "142",
    change: -8.3,
    trend: "down",
    sparkline: [186, 178, 172, 165, 158, 148, 142],
    icon: "alert-triangle",
    positiveIsGood: false,
  },
  {
    id: "failing-flops",
    title: "Failing Flops",
    value: "3,284",
    change: -5.6,
    trend: "down",
    sparkline: [3800, 3650, 3520, 3450, 3380, 3320, 3284],
    icon: "cpu",
    positiveIsGood: false,
  },
  {
    id: "scan-coverage",
    title: "Scan Coverage",
    value: "96.8%",
    change: 1.2,
    trend: "up",
    sparkline: [94.2, 94.8, 95.2, 95.6, 96.0, 96.4, 96.8],
    icon: "shield-check",
    positiveIsGood: true,
  },
  {
    id: "avg-test-time",
    title: "Average Test Time",
    value: "18.4s",
    change: -3.1,
    trend: "down",
    sparkline: [21, 20.5, 20, 19.5, 19, 18.8, 18.4],
    icon: "timer",
    positiveIsGood: false,
  },
  {
    id: "pattern-count",
    title: "Pattern Count",
    value: "486",
    change: 4.8,
    trend: "up",
    sparkline: [420, 435, 448, 458, 468, 478, 486],
    icon: "layers",
    positiveIsGood: true,
  },
];

export const patternKPIs: ScanKPI[] = [
  {
    id: "total-patterns",
    title: "Total Patterns",
    value: "486",
    change: 4.8,
    trend: "up",
    sparkline: [420, 435, 448, 458, 468, 478, 486],
    icon: "layers",
    positiveIsGood: true,
  },
  {
    id: "active-patterns",
    title: "Active Patterns",
    value: "412",
    change: 2.1,
    trend: "up",
    sparkline: [380, 388, 395, 400, 405, 408, 412],
    icon: "play",
    positiveIsGood: true,
  },
  {
    id: "pattern-coverage",
    title: "Pattern Coverage",
    value: "94.2%",
    change: 1.5,
    trend: "up",
    sparkline: [90, 91, 92, 92.5, 93, 93.8, 94.2],
    icon: "target",
    positiveIsGood: true,
  },
  {
    id: "pattern-efficiency",
    title: "Pattern Efficiency",
    value: "87.6%",
    change: 3.2,
    trend: "up",
    sparkline: [80, 82, 83, 84.5, 85.5, 86.8, 87.6],
    icon: "zap",
    positiveIsGood: true,
  },
  {
    id: "pattern-runtime",
    title: "Pattern Runtime",
    value: "42.6s",
    change: -4.2,
    trend: "down",
    sparkline: [48, 47, 46, 45, 44, 43, 42.6],
    icon: "clock",
    positiveIsGood: false,
  },
  {
    id: "compressed-patterns",
    title: "Compressed Patterns",
    value: "128",
    change: 12.4,
    trend: "up",
    sparkline: [90, 98, 105, 112, 118, 124, 128],
    icon: "minimize-2",
    positiveIsGood: true,
  },
];

export const failureKPIs: ScanKPI[] = [
  {
    id: "total-failures",
    title: "Total Failures",
    value: "1,284",
    change: -6.8,
    trend: "down",
    sparkline: [1480, 1420, 1380, 1340, 1310, 1290, 1284],
    icon: "x-circle",
    positiveIsGood: false,
  },
  {
    id: "critical-failures",
    title: "Critical Failures",
    value: "86",
    change: -12.4,
    trend: "down",
    sparkline: [120, 110, 105, 98, 94, 88, 86],
    icon: "alert-octagon",
    positiveIsGood: false,
  },
  {
    id: "warning-failures",
    title: "Warning Failures",
    value: "342",
    change: -4.2,
    trend: "down",
    sparkline: [380, 370, 365, 358, 352, 346, 342],
    icon: "alert-circle",
    positiveIsGood: false,
  },
  {
    id: "recovered-failures",
    title: "Recovered Failures",
    value: "856",
    change: 8.6,
    trend: "up",
    sparkline: [720, 750, 780, 800, 820, 840, 856],
    icon: "check-circle",
    positiveIsGood: true,
  },
  {
    id: "root-causes",
    title: "Root Causes",
    value: "24",
    change: -8.0,
    trend: "down",
    sparkline: [32, 30, 28, 27, 26, 25, 24],
    icon: "git-branch",
    positiveIsGood: false,
  },
  {
    id: "repair-rate",
    title: "Repair Rate",
    value: "78.4%",
    change: 5.2,
    trend: "up",
    sparkline: [68, 70, 72, 74, 75.5, 77, 78.4],
    icon: "wrench",
    positiveIsGood: true,
  },
];

export const diagnosisKPIs: ScanKPI[] = [
  {
    id: "diagnosed-chains",
    title: "Diagnosed Chains",
    value: "2,148",
    change: 6.4,
    trend: "up",
    sparkline: [1900, 1950, 2000, 2040, 2080, 2120, 2148],
    icon: "search-check",
    positiveIsGood: true,
  },
  {
    id: "unknown-chains",
    title: "Unknown Chains",
    value: "124",
    change: -14.2,
    trend: "down",
    sparkline: [168, 158, 148, 142, 136, 128, 124],
    icon: "help-circle",
    positiveIsGood: false,
  },
  {
    id: "repair-suggestions",
    title: "Repair Suggestions",
    value: "342",
    change: 18.6,
    trend: "up",
    sparkline: [240, 260, 280, 300, 315, 330, 342],
    icon: "lightbulb",
    positiveIsGood: true,
  },
  {
    id: "diagnosis-accuracy",
    title: "Diagnosis Accuracy",
    value: "92.6%",
    change: 2.8,
    trend: "up",
    sparkline: [86, 88, 89, 90, 91, 92, 92.6],
    icon: "crosshair",
    positiveIsGood: true,
  },
  {
    id: "coverage",
    title: "Coverage",
    value: "89.4%",
    change: 3.1,
    trend: "up",
    sparkline: [82, 84, 85.5, 86.8, 87.5, 88.5, 89.4],
    icon: "scan",
    positiveIsGood: true,
  },
  {
    id: "confidence",
    title: "Confidence",
    value: "88.2%",
    change: 4.0,
    trend: "up",
    sparkline: [80, 82, 84, 85, 86.5, 87.5, 88.2],
    icon: "gauge",
    positiveIsGood: true,
  },
];

export const chainHealthData: HealthSegment[] = [
  { name: "Healthy", value: 2284, color: "#22C55E" },
  { name: "Warning", value: 421, color: "#EAB308" },
  { name: "Failing", value: 142, color: "#EF4444" },
  { name: "Unknown", value: 86, color: "#64748B" },
];

export const topFailingChips: ChipFailData[] = [
  { chip: "Core-CPU-0", failCount: 48 },
  { chip: "Core-CPU-1", failCount: 42 },
  { chip: "GPU-Cluster-A", failCount: 38 },
  { chip: "Memory-CTRL-2", failCount: 34 },
  { chip: "IO-Hub-North", failCount: 28 },
  { chip: "PCIe-Gen5-0", failCount: 24 },
  { chip: "NOC-Router-3", failCount: 22 },
  { chip: "Cache-L3-Bank4", failCount: 18 },
  { chip: "DSP-Accel-1", failCount: 16 },
  { chip: "Security-Enclave", failCount: 12 },
];

export const failingChainsData: FailingChainRow[] = [
  {
    chainId: "SC-004821",
    patternId: "PAT-STUCK-042",
    chip: "Core-CPU-0",
    failCycle: 1842,
    failType: "Stuck At",
    rootCause: "Clock gating defect",
    diagnosisStatus: "Complete",
  },
  {
    chainId: "SC-003156",
    patternId: "PAT-TRANS-118",
    chip: "GPU-Cluster-A",
    failCycle: 956,
    failType: "Transition",
    rootCause: "Hold time violation",
    diagnosisStatus: "In Progress",
  },
  {
    chainId: "SC-007892",
    patternId: "PAT-BRIDGE-007",
    chip: "Memory-CTRL-2",
    failCycle: 3210,
    failType: "Bridging",
    rootCause: "Metal short M4-M5",
    diagnosisStatus: "Escalated",
  },
  {
    chainId: "SC-002441",
    patternId: "PAT-TIMING-056",
    chip: "IO-Hub-North",
    failCycle: 742,
    failType: "Timing",
    rootCause: "Setup slack failure",
    diagnosisStatus: "Complete",
  },
  {
    chainId: "SC-009103",
    patternId: "PAT-STUCK-089",
    chip: "Core-CPU-1",
    failCycle: 2108,
    failType: "Stuck At",
    rootCause: "Scan cell defect",
    diagnosisStatus: "Pending",
  },
  {
    chainId: "SC-001778",
    patternId: "PAT-TRANS-203",
    chip: "PCIe-Gen5-0",
    failCycle: 428,
    failType: "Transition",
    rootCause: "Unknown",
    diagnosisStatus: "Pending",
  },
  {
    chainId: "SC-005632",
    patternId: "PAT-BRIDGE-014",
    chip: "NOC-Router-3",
    failCycle: 1564,
    failType: "Bridging",
    rootCause: "Via chain break",
    diagnosisStatus: "In Progress",
  },
  {
    chainId: "SC-008214",
    patternId: "PAT-TIMING-091",
    chip: "Cache-L3-Bank4",
    failCycle: 892,
    failType: "Timing",
    rootCause: "Clock skew",
    diagnosisStatus: "Complete",
  },
];

export const failureDistribution: FailureDistribution[] = [
  { name: "Stuck At", value: 42, color: "#7C3AED" },
  { name: "Transition", value: 28, color: "#06B6D4" },
  { name: "Bridging", value: 14, color: "#F97316" },
  { name: "Timing", value: 11, color: "#EAB308" },
  { name: "Unknown", value: 5, color: "#64748B" },
];

export const aiDiagnosisSummary: AIDiagnosisSummary = {
  detectedRootCause: "Clock domain crossing violation in Core-CPU-0 scan segment",
  criticalChains: 12,
  recommendedDebugArea: "Clock gating logic near SC-004821 segment boundary",
  estimatedRepairSuccess: 84,
  confidenceScore: 91,
};

export const patternExecutionTrend: TrendPoint[] = [
  { label: "Mon", value: 420, value2: 380 },
  { label: "Tue", value: 445, value2: 395 },
  { label: "Wed", value: 438, value2: 402 },
  { label: "Thu", value: 462, value2: 418 },
  { label: "Fri", value: 478, value2: 428 },
  { label: "Sat", value: 452, value2: 410 },
  { label: "Sun", value: 486, value2: 442 },
];

export const patternCostTrend: TrendPoint[] = [
  { label: "Mon", value: 1240 },
  { label: "Tue", value: 1180 },
  { label: "Wed", value: 1220 },
  { label: "Thu", value: 1160 },
  { label: "Fri", value: 1140 },
  { label: "Sat", value: 1100 },
  { label: "Sun", value: 1080 },
];

export const patternCoverageTrend: TrendPoint[] = [
  { label: "Mon", value: 90.2 },
  { label: "Tue", value: 91.0 },
  { label: "Wed", value: 91.8 },
  { label: "Thu", value: 92.4 },
  { label: "Fri", value: 93.2 },
  { label: "Sat", value: 93.8 },
  { label: "Sun", value: 94.2 },
];

export const patternDensityData: TrendPoint[] = [
  { label: "Segment A", value: 82 },
  { label: "Segment B", value: 68 },
  { label: "Segment C", value: 94 },
  { label: "Segment D", value: 76 },
  { label: "Segment E", value: 88 },
  { label: "Segment F", value: 72 },
];

export const patternSummaryData: PatternSummaryRow[] = [
  { patternId: "PAT-STUCK-042", chainCount: 48, coverage: 96.2, runtime: 8.4, efficiency: 92, status: "Active" },
  { patternId: "PAT-TRANS-118", chainCount: 36, coverage: 94.8, runtime: 12.6, efficiency: 88, status: "Active" },
  { patternId: "PAT-BRIDGE-007", chainCount: 24, coverage: 91.4, runtime: 18.2, efficiency: 76, status: "Active" },
  { patternId: "PAT-TIMING-056", chainCount: 42, coverage: 93.6, runtime: 14.8, efficiency: 84, status: "Active" },
  { patternId: "PAT-LEGACY-012", chainCount: 18, coverage: 78.2, runtime: 22.4, efficiency: 62, status: "Deprecated" },
  { patternId: "PAT-STUCK-089", chainCount: 32, coverage: 95.0, runtime: 9.2, efficiency: 90, status: "Active" },
];

export const patternRecommendations: PatternRecommendationRow[] = [
  { patternId: "PAT-BRIDGE-007", issue: "High runtime, low efficiency", recommendation: "Compress pattern segments 3-5", priority: "High" },
  { patternId: "PAT-LEGACY-012", issue: "Deprecated, low coverage", recommendation: "Replace with PAT-STUCK-089", priority: "High" },
  { patternId: "PAT-TRANS-118", issue: "Transition failures increasing", recommendation: "Add hold-time margin patterns", priority: "Medium" },
  { patternId: "PAT-TIMING-056", issue: "Moderate efficiency", recommendation: "Optimize scan ordering", priority: "Low" },
];

export const patternAnalysisKPIs: PatternAnalysisKPI[] = [
  { id: "files-ingested", title: "Pattern Files Ingested", value: "2,846", subtitle: "STIL • WGL • PAT", status: "100% Imported", statusVariant: "success", description: "Total successfully imported pattern files.", change: 2.4, trend: "up", sparkline: [2620, 2680, 2720, 2760, 2790, 2820, 2846], icon: "layers", positiveIsGood: true },
  { id: "vectors-parsed", title: "Scan Vectors Parsed", value: "99.7%", subtitle: "2.8M Scan Vectors", status: "SLA Met", statusVariant: "success", description: "Successfully parsed scan vectors.", change: 0.3, trend: "up", sparkline: [98.2, 98.6, 98.9, 99.1, 99.3, 99.5, 99.7], icon: "scan", positiveIsGood: true },
  { id: "file-integrity", title: "File Integrity", value: "100%", status: "PASS", statusVariant: "success", description: "Checksum validation passed.", change: 0, trend: "up", sparkline: [100, 100, 100, 100, 100, 100, 100], icon: "shield-check", positiveIsGood: true },
  { id: "pattern-coverage-kpi", title: "Pattern Coverage", value: "98.42%", status: "+0.2% ATPG Delta", statusVariant: "info", description: "Fault coverage compared with ATPG.", change: 0.2, trend: "up", sparkline: [97.8, 97.9, 98.0, 98.1, 98.2, 98.3, 98.42], icon: "target", positiveIsGood: true },
  { id: "metadata-extracted", title: "Metadata Extracted", value: "2,846", status: "Complete", statusVariant: "success", description: "Pattern metadata extracted successfully.", change: 1.8, trend: "up", sparkline: [2700, 2740, 2770, 2790, 2810, 2830, 2846], icon: "file-stack", positiveIsGood: true },
  { id: "embeddings-generated", title: "Embeddings Generated", value: "2,846", status: "100%", statusVariant: "success", description: "AI vector embeddings generated.", change: 5.2, trend: "up", sparkline: [2400, 2500, 2600, 2680, 2740, 2800, 2846], icon: "sparkles", positiveIsGood: true },
  { id: "pattern-clusters", title: "Pattern Clusters", value: "126", status: "Threshold 0.87", statusVariant: "neutral", description: "AI similarity clusters.", change: 4.1, trend: "up", sparkline: [108, 112, 116, 118, 120, 123, 126], icon: "git-branch", positiveIsGood: true },
  { id: "redundant-patterns", title: "Redundant Patterns", value: "38", status: "94% Confidence", statusVariant: "warning", description: "Duplicate patterns detected.", change: -6.2, trend: "down", sparkline: [52, 48, 46, 44, 42, 40, 38], icon: "alert-triangle", positiveIsGood: false },
  { id: "similarity-analyses", title: "Similarity Analyses", value: "2,846", status: "182 ms", statusVariant: "info", description: "Average similarity processing latency.", change: -8.4, trend: "down", sparkline: [240, 220, 210, 200, 195, 188, 182], icon: "crosshair", positiveIsGood: false },
  { id: "pass-fail-linked", title: "Pass / Fail Linked", value: "2,741 / 2,846", status: "96.3%", statusVariant: "success", description: "Patterns linked to historical test results.", change: 1.1, trend: "up", sparkline: [93.2, 94.0, 94.6, 95.2, 95.6, 96.0, 96.3], icon: "check-circle", positiveIsGood: true },
  { id: "quality-reports", title: "Quality Reports", value: "24", status: "PDF • Excel • HTML", statusVariant: "neutral", description: "Generated quality reports.", change: 12.0, trend: "up", sparkline: [14, 16, 18, 19, 21, 22, 24], icon: "file-text", positiveIsGood: true },
];

export const patternImportTrend: TrendPoint[] = [
  { label: "W1", value: 412, value2: 380 },
  { label: "W2", value: 468, value2: 420 },
  { label: "W3", value: 524, value2: 490 },
  { label: "W4", value: 612, value2: 580 },
  { label: "W5", value: 698, value2: 660 },
  { label: "W6", value: 782, value2: 740 },
  { label: "W7", value: 846, value2: 810 },
];

export const patternAnalysisCoverageTrend: TrendPoint[] = [
  { label: "Jan", value: 96.8 },
  { label: "Feb", value: 97.2 },
  { label: "Mar", value: 97.6 },
  { label: "Apr", value: 97.9 },
  { label: "May", value: 98.1 },
  { label: "Jun", value: 98.42 },
];

export const patternClusterDistribution: HealthSegment[] = [
  { name: "Stuck-At", value: 34, color: "#7C3AED" },
  { name: "Transition", value: 28, color: "#06B6D4" },
  { name: "Bridging", value: 22, color: "#F97316" },
  { name: "Timing", value: 18, color: "#EAB308" },
  { name: "Other", value: 24, color: "#64748B" },
];

export const patternScatterData: PatternScatterPoint[] = [
  { patternId: "PAT-042", x: 0.92, y: 0.88, cluster: "A" },
  { patternId: "PAT-118", x: 0.78, y: 0.72, cluster: "B" },
  { patternId: "PAT-007", x: 0.85, y: 0.91, cluster: "A" },
  { patternId: "PAT-056", x: 0.64, y: 0.58, cluster: "C" },
  { patternId: "PAT-089", x: 0.91, y: 0.86, cluster: "A" },
  { patternId: "PAT-203", x: 0.71, y: 0.69, cluster: "B" },
  { patternId: "PAT-014", x: 0.55, y: 0.48, cluster: "D" },
  { patternId: "PAT-091", x: 0.82, y: 0.77, cluster: "B" },
  { patternId: "PAT-128", x: 0.48, y: 0.42, cluster: "D" },
  { patternId: "PAT-156", x: 0.88, y: 0.84, cluster: "A" },
  { patternId: "PAT-201", x: 0.62, y: 0.55, cluster: "C" },
  { patternId: "PAT-312", x: 0.76, y: 0.71, cluster: "B" },
];

export const patternAnalysisRows: PatternAnalysisRow[] = [
  { patternId: "PAT-4821", patternName: "Stuck-At Core Scan", fileType: "STIL", coverage: 98.4, compressionRatio: 0.72, vectors: 28400, cluster: "CL-A12", similarityScore: 0.94, redundancy: "None", qualityScore: 96, status: "Active", recommendation: "Keep" },
  { patternId: "PAT-3156", patternName: "Transition GPU Block", fileType: "WGL", coverage: 96.8, compressionRatio: 0.68, vectors: 31200, cluster: "CL-B08", similarityScore: 0.88, redundancy: "Low", qualityScore: 91, status: "Active", recommendation: "Review" },
  { patternId: "PAT-7892", patternName: "Bridge Memory Path", fileType: "PAT", coverage: 94.2, compressionRatio: 0.61, vectors: 19800, cluster: "CL-C04", similarityScore: 0.82, redundancy: "Medium", qualityScore: 87, status: "Review", recommendation: "Merge" },
  { patternId: "PAT-2441", patternName: "Timing IO Hub", fileType: "STIL", coverage: 97.1, compressionRatio: 0.75, vectors: 22600, cluster: "CL-A09", similarityScore: 0.91, redundancy: "None", qualityScore: 94, status: "Active", recommendation: "Keep" },
  { patternId: "PAT-9103", patternName: "Legacy Stuck Scan", fileType: "WGL", coverage: 78.4, compressionRatio: 0.42, vectors: 45200, cluster: "CL-D02", similarityScore: 0.58, redundancy: "High", qualityScore: 62, status: "Redundant", recommendation: "Remove" },
  { patternId: "PAT-1778", patternName: "NOC Transition", fileType: "STIL", coverage: 95.6, compressionRatio: 0.69, vectors: 26800, cluster: "CL-B11", similarityScore: 0.86, redundancy: "Low", qualityScore: 89, status: "Active", recommendation: "Keep" },
  { patternId: "PAT-5632", patternName: "Security Block Scan", fileType: "PAT", coverage: 93.8, compressionRatio: 0.64, vectors: 18400, cluster: "CL-C07", similarityScore: 0.79, redundancy: "Medium", qualityScore: 84, status: "Review", recommendation: "Merge" },
  { patternId: "PAT-8214", patternName: "Cache Bridge Test", fileType: "WGL", coverage: 91.2, compressionRatio: 0.58, vectors: 33600, cluster: "CL-C03", similarityScore: 0.74, redundancy: "High", qualityScore: 78, status: "Redundant", recommendation: "Remove" },
  { patternId: "PAT-3399", patternName: "DSP Stuck Pattern", fileType: "STIL", coverage: 97.8, compressionRatio: 0.78, vectors: 21200, cluster: "CL-A14", similarityScore: 0.93, redundancy: "None", qualityScore: 95, status: "Active", recommendation: "Keep" },
  { patternId: "PAT-6671", patternName: "PCIe Transition", fileType: "PAT", coverage: 96.2, compressionRatio: 0.71, vectors: 24800, cluster: "CL-B06", similarityScore: 0.87, redundancy: "Low", qualityScore: 90, status: "Active", recommendation: "Review" },
];

export const patternAISummary: PatternAISummary = {
  patternsToRemove: 38,
  patternsToMerge: 24,
  coverageImprovement: "+0.8%",
  compressionImprovement: "+12.4%",
  missingMetadata: 12,
  duplicatePatterns: 38,
  expectedRuntimeReduction: "-6.2s",
  expectedYieldImprovement: "+1.4%",
};

function buildPatternMatrix(size: number, seed: number): number[][] {
  return Array.from({ length: size }, (_, r) =>
    Array.from({ length: size }, (_, c) => {
      const v = Math.abs(Math.sin((r + seed) * 12.9898 + (c + seed) * 78.233) * 43758.5453) % 1;
      return Math.round(v * 100);
    })
  );
}

export const patternRedundancyHeatmap = buildPatternMatrix(14, 1);
export const patternSimilarityMatrix = buildPatternMatrix(12, 2);

export const failureTrendData: TrendPoint[] = [
  { label: "Mon", value: 186, value2: 42 },
  { label: "Tue", value: 172, value2: 38 },
  { label: "Wed", value: 168, value2: 36 },
  { label: "Thu", value: 158, value2: 32 },
  { label: "Fri", value: 148, value2: 28 },
  { label: "Sat", value: 152, value2: 30 },
  { label: "Sun", value: 142, value2: 26 },
];

export const failingRegionsData: TrendPoint[] = [
  { label: "Core", value: 48 },
  { label: "GPU", value: 38 },
  { label: "Memory", value: 34 },
  { label: "IO", value: 28 },
  { label: "NOC", value: 22 },
  { label: "Security", value: 12 },
];

export const failureDensityData: TrendPoint[] = [
  { label: "Zone 1", value: 92 },
  { label: "Zone 2", value: 68 },
  { label: "Zone 3", value: 84 },
  { label: "Zone 4", value: 56 },
  { label: "Zone 5", value: 74 },
  { label: "Zone 6", value: 48 },
];

export const failureRecords: FailureRecordRow[] = [
  { failureId: "F-10284", chainId: "SC-004821", chip: "Core-CPU-0", failType: "Stuck At", severity: "Critical", timestamp: "2026-06-29 08:42" },
  { failureId: "F-10283", chainId: "SC-003156", chip: "GPU-Cluster-A", failType: "Transition", severity: "Critical", timestamp: "2026-06-29 08:38" },
  { failureId: "F-10282", chainId: "SC-007892", chip: "Memory-CTRL-2", failType: "Bridging", severity: "Warning", timestamp: "2026-06-29 08:22" },
  { failureId: "F-10281", chainId: "SC-002441", chip: "IO-Hub-North", failType: "Timing", severity: "Warning", timestamp: "2026-06-29 07:58" },
  { failureId: "F-10280", chainId: "SC-009103", chip: "Core-CPU-1", failType: "Stuck At", severity: "Recovered", timestamp: "2026-06-29 07:44" },
  { failureId: "F-10279", chainId: "SC-001778", chip: "PCIe-Gen5-0", failType: "Transition", severity: "Warning", timestamp: "2026-06-29 07:30" },
];

export const rootCauseAnalysis: RootCauseRow[] = [
  { cause: "Clock gating defect", count: 38, percentage: 26.8, trend: -4.2 },
  { cause: "Hold time violation", count: 32, percentage: 22.5, trend: 2.1 },
  { cause: "Metal short", count: 24, percentage: 16.9, trend: -1.8 },
  { cause: "Setup slack failure", count: 18, percentage: 12.7, trend: -0.6 },
  { cause: "Scan cell defect", count: 16, percentage: 11.3, trend: 1.4 },
  { cause: "Unknown", count: 14, percentage: 9.8, trend: -2.4 },
];

export const aiRecommendations: AIRecommendationRow[] = [
  { id: "AI-001", chainId: "SC-004821", recommendation: "Inspect clock gating near segment boundary", confidence: 91, impact: "High" },
  { id: "AI-002", chainId: "SC-003156", recommendation: "Add hold-time margin to transition path", confidence: 86, impact: "High" },
  { id: "AI-003", chainId: "SC-007892", recommendation: "Run bridging isolation pattern", confidence: 78, impact: "Medium" },
  { id: "AI-004", chainId: "SC-002441", recommendation: "Adjust clock skew compensation", confidence: 82, impact: "Medium" },
];

export const diagnosisTimeline: TrendPoint[] = [
  { label: "Week 1", value: 420, value2: 86 },
  { label: "Week 2", value: 480, value2: 72 },
  { label: "Week 3", value: 540, value2: 58 },
  { label: "Week 4", value: 620, value2: 42 },
  { label: "Week 5", value: 680, value2: 32 },
  { label: "Week 6", value: 740, value2: 24 },
];

export const aiConfidenceTrend: TrendPoint[] = [
  { label: "Mon", value: 84 },
  { label: "Tue", value: 85.5 },
  { label: "Wed", value: 86.8 },
  { label: "Thu", value: 87.4 },
  { label: "Fri", value: 88.2 },
  { label: "Sat", value: 88.0 },
  { label: "Sun", value: 88.2 },
];

export const diagnosisReports: DiagnosisReportRow[] = [
  { chainId: "SC-004821", status: "Diagnosed", rootCause: "Clock gating defect", confidence: 91, repairSuggestion: "Replace scan cell SC-004821-142" },
  { chainId: "SC-003156", status: "Partial", rootCause: "Hold time violation", confidence: 78, repairSuggestion: "Adjust hold margin +12ps" },
  { chainId: "SC-007892", status: "Diagnosed", rootCause: "Metal short M4-M5", confidence: 94, repairSuggestion: "FIB repair at coordinate (1248, 892)" },
  { chainId: "SC-001778", status: "Unknown", rootCause: "Pending analysis", confidence: 42, repairSuggestion: "Run extended diagnosis pattern" },
];

export const suspectedScanCells: SuspectedCellRow[] = [
  { cellId: "SC-004821-142", chainId: "SC-004821", cellType: "SDFF", failProbability: 0.92, location: "Core-CPU-0 / Seg-4" },
  { cellId: "SC-003156-089", chainId: "SC-003156", cellType: "SDFF", failProbability: 0.86, location: "GPU-Cluster-A / Seg-2" },
  { cellId: "SC-007892-034", chainId: "SC-007892", cellType: "SDFF", failProbability: 0.94, location: "Memory-CTRL-2 / Seg-1" },
  { cellId: "SC-002441-201", chainId: "SC-002441", cellType: "SDFF", failProbability: 0.78, location: "IO-Hub-North / Seg-3" },
];

export const debugPoints: DebugPointRow[] = [
  { pointId: "DP-001", chainId: "SC-004821", region: "Clock Gating", priority: 1, description: "Primary suspect near CDC boundary" },
  { pointId: "DP-002", chainId: "SC-003156", region: "Transition Path", priority: 2, description: "Hold margin insufficient at flop 089" },
  { pointId: "DP-003", chainId: "SC-007892", region: "Metal Layer M4", priority: 1, description: "Bridging between adjacent routes" },
  { pointId: "DP-004", chainId: "SC-002441", region: "Clock Tree", priority: 3, description: "Skew compensation needed" },
];

export const repairPriorityData: RepairPriorityRow[] = [
  { chainId: "SC-004821", priority: 1, failType: "Stuck At", estimatedFixTime: "2.4h", successRate: 84 },
  { chainId: "SC-007892", priority: 2, failType: "Bridging", estimatedFixTime: "4.8h", successRate: 72 },
  { chainId: "SC-003156", priority: 3, failType: "Transition", estimatedFixTime: "3.2h", successRate: 78 },
  { chainId: "SC-002441", priority: 4, failType: "Timing", estimatedFixTime: "1.8h", successRate: 88 },
];

export function generateScanChainHeatmap(
  rows = 16,
  cols = 24
): { value: number; row: number; col: number }[] {
  return generateGridHeatmap(rows, cols, 0.4, 0.6);
}

export const connectivityGraphData = {
  nodes: [
    { id: "SC-004821", label: "SC-004821", status: "failing" },
    { id: "SC-003156", label: "SC-003156", status: "warning" },
    { id: "SC-007892", label: "SC-007892", status: "failing" },
    { id: "SC-002441", label: "SC-002441", status: "healthy" },
    { id: "SC-009103", label: "SC-009103", status: "warning" },
    { id: "SC-001778", label: "SC-001778", status: "unknown" },
  ],
  edges: [
    { from: "SC-004821", to: "SC-003156" },
    { from: "SC-003156", to: "SC-007892" },
    { from: "SC-007892", to: "SC-002441" },
    { from: "SC-002441", to: "SC-009103" },
    { from: "SC-009103", to: "SC-001778" },
  ],
};

export const failurePropagationData: TrendPoint[] = [
  { label: "T+0", value: 12 },
  { label: "T+1", value: 28 },
  { label: "T+2", value: 48 },
  { label: "T+3", value: 62 },
  { label: "T+4", value: 58 },
  { label: "T+5", value: 42 },
  { label: "T+6", value: 24 },
];

export const failureAnalysisKPIs: FailureAnalysisKPI[] = [
  { id: "imported-files", title: "Imported Test Files", value: "248", subtitle: "STDF + Tester Logs", status: "Validated", statusVariant: "success", description: "Total imported STDF and tester log files.", change: 4.2, trend: "up", sparkline: [210, 218, 224, 230, 236, 242, 248], icon: "file-stack", positiveIsGood: true },
  { id: "overall-failure-rate", title: "Overall Failure Rate", value: "2.84%", status: "Within Target", statusVariant: "success", description: "Aggregate failure rate across tested devices.", change: -0.3, trend: "down", sparkline: [3.4, 3.2, 3.1, 3.0, 2.95, 2.88, 2.84], icon: "activity", positiveIsGood: false },
  { id: "failing-patterns", title: "Failing Test Patterns", value: "1,246", subtitle: "286 Recurring", status: "Active", statusVariant: "warning", description: "Total failing patterns detected.", change: -2.1, trend: "down", sparkline: [1320, 1304, 1288, 1276, 1264, 1254, 1246], icon: "alert-triangle", positiveIsGood: false },
  { id: "die-failure-rate", title: "Die Failure Rate", value: "1.92%", subtitle: "48,320 Dies", status: "Open Heatmap", statusVariant: "info", description: "Failure rate at die level.", change: 0.4, trend: "up", sparkline: [1.6, 1.68, 1.74, 1.78, 1.84, 1.88, 1.92], icon: "cpu", positiveIsGood: false, focusTarget: "die-heatmap" },
  { id: "wafer-failure-rate", title: "Wafer Failure Rate", value: "2.43%", subtitle: "112 Wafers", status: "Open Heatmap", statusVariant: "info", description: "Failure rate at wafer level.", change: 0.6, trend: "up", sparkline: [1.9, 2.0, 2.08, 2.14, 2.22, 2.34, 2.43], icon: "disc", positiveIsGood: false, focusTarget: "wafer-heatmap" },
  { id: "lot-failure-rate", title: "Lot Failure Rate", value: "3.11%", subtitle: "14 / 236 Lots", status: "Monitor", statusVariant: "warning", description: "Failure rate across production lots.", change: 0.2, trend: "up", sparkline: [2.6, 2.72, 2.8, 2.88, 2.96, 3.04, 3.11], icon: "layers", positiveIsGood: false },
  { id: "fault-categories", title: "Fault Categories", value: "5", subtitle: "2 Unknown", status: "Classified", statusVariant: "neutral", description: "Detected fault classifications.", change: 0, trend: "up", sparkline: [5, 5, 5, 5, 5, 5, 5], icon: "git-branch", positiveIsGood: true },
  { id: "root-cause-confidence", title: "Root Cause Confidence", value: "94%", subtitle: "Bridge Fault", status: "High Confidence", statusVariant: "success", description: "AI predicted root cause confidence.", change: 1.2, trend: "up", sparkline: [88, 89, 90, 91, 92, 93, 94], icon: "target", positiveIsGood: true },
  { id: "recurring-failures", title: "Recurring Failures", value: "183", subtitle: "37 Lots", status: "Tracked", statusVariant: "warning", description: "Recurring failure signatures.", change: -3.4, trend: "down", sparkline: [210, 204, 198, 194, 190, 186, 183], icon: "repeat", positiveIsGood: false },
];

export const overallFailureTrend: TrendPoint[] = [
  { label: "W1", value: 312, value2: 284 },
  { label: "W2", value: 298, value2: 268 },
  { label: "W3", value: 276, value2: 248 },
  { label: "W4", value: 264, value2: 236 },
  { label: "W5", value: 252, value2: 228 },
  { label: "W6", value: 244, value2: 218 },
  { label: "W7", value: 238, value2: 212 },
];

export const failureRateTrend: TrendPoint[] = [
  { label: "Jan", value: 3.42 },
  { label: "Feb", value: 3.28 },
  { label: "Mar", value: 3.12 },
  { label: "Apr", value: 3.04 },
  { label: "May", value: 2.96 },
  { label: "Jun", value: 2.84 },
];

export const failureAnalysisDistribution: FailureDistribution[] = [
  { name: "Stuck-at", value: 32, color: "#7C3AED" },
  { name: "Bridging", value: 22, color: "#EF4444" },
  { name: "Transition Delay", value: 18, color: "#06B6D4" },
  { name: "Cell-Aware", value: 14, color: "#F97316" },
  { name: "Scan Fault", value: 10, color: "#EAB308" },
  { name: "Unknown", value: 4, color: "#64748B" },
];

export const failureByLotData: LotFailData[] = [
  { lot: "LOT-A2847", failCount: 186 },
  { lot: "LOT-B1923", failCount: 164 },
  { lot: "LOT-C4412", failCount: 142 },
  { lot: "LOT-D8831", failCount: 128 },
  { lot: "LOT-E5520", failCount: 112 },
  { lot: "LOT-F3398", failCount: 98 },
  { lot: "LOT-G7744", failCount: 86 },
  { lot: "LOT-H6612", failCount: 74 },
];

export const failureAnalysisRows: FailureAnalysisRow[] = [
  { failureId: "F-20481", patternId: "PAT-4821", lotId: "LOT-A2847", waferId: "W-042", dieId: "D-18", faultCategory: "Stuck-at", rootCause: "Clock gating defect", confidence: 94, severity: "Critical", status: "Open", recommendation: "Inspect CDC boundary", timestamp: "2026-06-29 09:12" },
  { failureId: "F-20480", patternId: "PAT-3156", lotId: "LOT-B1923", waferId: "W-038", dieId: "D-22", faultCategory: "Transition Delay", rootCause: "Hold time violation", confidence: 91, severity: "High", status: "Investigating", recommendation: "Add hold margin", timestamp: "2026-06-29 08:58" },
  { failureId: "F-20479", patternId: "PAT-7892", lotId: "LOT-C4412", waferId: "W-051", dieId: "D-09", faultCategory: "Bridging", rootCause: "Metal short M4", confidence: 88, severity: "Critical", status: "Escalated", recommendation: "Run isolation pattern", timestamp: "2026-06-29 08:44" },
  { failureId: "F-20478", patternId: "PAT-2441", lotId: "LOT-D8831", waferId: "W-029", dieId: "D-31", faultCategory: "Cell-Aware", rootCause: "Scan cell defect", confidence: 86, severity: "Medium", status: "Investigating", recommendation: "Replace scan cell", timestamp: "2026-06-29 08:30" },
  { failureId: "F-20477", patternId: "PAT-9103", lotId: "LOT-E5520", waferId: "W-063", dieId: "D-04", faultCategory: "Scan Fault", rootCause: "Pattern ordering issue", confidence: 82, severity: "Medium", status: "Open", recommendation: "Reorder scan segments", timestamp: "2026-06-29 08:18" },
  { failureId: "F-20476", patternId: "PAT-1778", lotId: "LOT-F3398", waferId: "W-017", dieId: "D-27", faultCategory: "Unknown", rootCause: "Under investigation", confidence: 62, severity: "Low", status: "Open", recommendation: "Collect additional logs", timestamp: "2026-06-29 07:56" },
  { failureId: "F-20475", patternId: "PAT-5632", lotId: "LOT-G7744", waferId: "W-044", dieId: "D-12", faultCategory: "Stuck-at", rootCause: "Setup slack failure", confidence: 90, severity: "High", status: "Resolved", recommendation: "Timing closure applied", timestamp: "2026-06-29 07:42" },
  { failureId: "F-20474", patternId: "PAT-8214", lotId: "LOT-H6612", waferId: "W-056", dieId: "D-35", faultCategory: "Bridging", rootCause: "Bridge fault", confidence: 93, severity: "Critical", status: "Investigating", recommendation: "Physical failure analysis", timestamp: "2026-06-29 07:28" },
  { failureId: "F-20473", patternId: "PAT-3399", lotId: "LOT-A2847", waferId: "W-042", dieId: "D-19", faultCategory: "Transition Delay", rootCause: "Clock skew", confidence: 87, severity: "Medium", status: "Open", recommendation: "Adjust clock tree", timestamp: "2026-06-29 07:14" },
  { failureId: "F-20472", patternId: "PAT-6671", lotId: "LOT-B1923", waferId: "W-038", dieId: "D-08", faultCategory: "Cell-Aware", rootCause: "Defective flop chain", confidence: 85, severity: "High", status: "Escalated", recommendation: "Replace affected chain", timestamp: "2026-06-29 06:58" },
];

export const failureCorrelationMatrix: number[][] = [
  [100, 82, 74, 68, 61],
  [82, 100, 78, 71, 64],
  [74, 78, 100, 86, 72],
  [68, 71, 86, 100, 79],
  [61, 64, 72, 79, 100],
];

export const failureCorrelationLabels = ["Pattern", "Failure", "Lot", "Wafer", "Device"];

export const failureRootCauseTree: RootCauseTreeNode[] = [
  {
    id: "rc-1",
    cause: "Bridge Fault",
    confidence: 94,
    affectedPatterns: 286,
    children: [
      { id: "rc-1a", cause: "Metal short M4", confidence: 91, affectedPatterns: 142 },
      { id: "rc-1b", cause: "Via bridging", confidence: 86, affectedPatterns: 98 },
    ],
  },
  {
    id: "rc-2",
    cause: "Clock Gating Defect",
    confidence: 88,
    affectedPatterns: 198,
    children: [
      { id: "rc-2a", cause: "CDC violation", confidence: 84, affectedPatterns: 112 },
      { id: "rc-2b", cause: "Enable glitch", confidence: 79, affectedPatterns: 86 },
    ],
  },
  {
    id: "rc-3",
    cause: "Hold Time Violation",
    confidence: 82,
    affectedPatterns: 164,
    children: [{ id: "rc-3a", cause: "Transition path slack", confidence: 78, affectedPatterns: 94 }],
  },
];

export const failureAISummary: FailureAISummary = {
  highestFailureLot: "LOT-A2847 (6.8%)",
  highestFailureWafer: "W-042 (4.2%)",
  criticalFaultCategory: "Bridging",
  mostAffectedPattern: "PAT-4821",
  mostFrequentRootCause: "Bridge Fault",
  estimatedYieldLoss: "-1.8%",
  estimatedCostImpact: "$284K / quarter",
  recommendedEngineeringAction: "Prioritize bridge fault isolation on LOT-A2847 and merge redundant stuck-at patterns",
};

export function generateWaferFailureHeatmap(rows = 20, cols = 20) {
  return generateGridHeatmap(rows, cols, 0.35, 0.65);
}

export function generateDieFailureHeatmap(rows = 16, cols = 16) {
  return generateGridHeatmap(rows, cols, 0.45, 0.55);
}

export const scanDiagnosisKPISections: ScanDiagnosisKPISection[] = [
  {
    title: "Detection & Identification",
    kpis: [
      { id: "sd-failing-chains", title: "Failing Scan Chains", value: "14", status: "Detected from Failure Logs", statusVariant: "danger", description: "Total scan chains identified with failures.", change: 8.2, trend: "up", sparkline: [8, 9, 10, 11, 12, 13, 14], icon: "unplug", positiveIsGood: false },
      { id: "sd-failing-cells", title: "Failing Scan Cells", value: "73", status: "Confidence Score Available", statusVariant: "warning", description: "Scan cells suspected to be faulty.", change: 5.4, trend: "up", sparkline: [58, 61, 64, 67, 69, 71, 73], icon: "crosshair", positiveIsGood: false },
      { id: "sd-chain-breaks", title: "Chain Breaks Detected", value: "9", status: "Topology View Available", statusVariant: "danger", description: "Detected scan chain breaks.", change: 12.5, trend: "up", sparkline: [4, 5, 6, 7, 8, 8, 9], icon: "link2off", positiveIsGood: false },
      { id: "sd-shift-capture", title: "Shift / Capture Issues", value: "21", subtitle: "Shift 13 · Capture 8", status: "Shift 13 · Capture 8", statusVariant: "warning", description: "Detected shift and capture timing issues.", change: 3.1, trend: "up", sparkline: [14, 16, 17, 18, 19, 20, 21], icon: "arrow-left-right", positiveIsGood: false },
    ],
  },
  {
    title: "Topology & Ranking",
    kpis: [
      { id: "sd-topology-chains", title: "Chains in Topology", value: "128", status: "Loaded & Visualized", statusVariant: "success", description: "Total scan chains in topology.", change: 0, trend: "up", sparkline: [128, 128, 128, 128, 128, 128, 128], icon: "network", positiveIsGood: true },
      { id: "sd-chains-ranked", title: "Chains Ranked", value: "14", status: "Failure Frequency Ranking", statusVariant: "info", description: "Highest priority failing scan chains.", change: 7.7, trend: "up", sparkline: [8, 9, 10, 11, 12, 13, 14], icon: "arrow-up-down", positiveIsGood: false },
      { id: "sd-failure-correlations", title: "Failure Correlations", value: "61", status: "Failure-to-Chain Mapping", statusVariant: "info", description: "Correlated failure signatures.", change: 4.2, trend: "up", sparkline: [48, 51, 54, 56, 58, 60, 61], icon: "git-merge", positiveIsGood: false },
      { id: "sd-top-failing-chain", title: "Top Failing Chain", value: "SC_14", subtitle: "38 Failures Across 5 Lots", status: "38 Failures Across 5 Lots", statusVariant: "danger", description: "Most frequently failing scan chain.", change: 14.3, trend: "up", sparkline: [22, 26, 28, 32, 34, 36, 38], icon: "trending-down", positiveIsGood: false },
    ],
  },
  {
    title: "Diagnosis & Reporting",
    kpis: [
      { id: "sd-diagnosis-reports", title: "Diagnosis Reports", value: "4", status: "Generated Today", statusVariant: "success", description: "AI-generated diagnosis reports.", change: 33.3, trend: "up", sparkline: [1, 2, 2, 3, 3, 4, 4], icon: "file-text", positiveIsGood: true },
      { id: "sd-debug-locations", title: "Debug Locations", value: "31", status: "Supporting Evidence Available", statusVariant: "info", description: "Recommended debug locations.", change: 6.9, trend: "up", sparkline: [22, 24, 26, 27, 28, 30, 31], icon: "map-pinned", positiveIsGood: true },
      { id: "sd-avg-confidence", title: "Average Diagnosis Confidence", value: "91%", status: "All Results Scored", statusVariant: "success", description: "Average AI diagnosis confidence.", change: 2.1, trend: "up", sparkline: [86, 87, 88, 89, 90, 90.5, 91], icon: "shield-check", positiveIsGood: true },
      { id: "sd-pending-review", title: "Diagnoses Pending Review", value: "6", subtitle: "Low Confidence 4 · Ambiguous 2", status: "Low Confidence 4 · Ambiguous 2", statusVariant: "warning", description: "Diagnosis results awaiting engineer review.", change: -14.3, trend: "down", sparkline: [10, 9, 8, 8, 7, 6, 6], icon: "clipboard-clock", positiveIsGood: true },
    ],
  },
];

export const failureLocalizationDistribution: HealthSegment[] = [
  { name: "Broken Chains", value: 9, color: "#EF4444" },
  { name: "Shift Faults", value: 13, color: "#F97316" },
  { name: "Capture Faults", value: 8, color: "#EAB308" },
  { name: "Cell Failures", value: 73, color: "#7C3AED" },
  { name: "Unknown", value: 14, color: "#64748B" },
];

export const chainFailureRanking: ChainFailRankingData[] = [
  { chain: "SC_14", failCount: 38 },
  { chain: "SC_08", failCount: 32 },
  { chain: "SC_21", failCount: 28 },
  { chain: "SC_04", failCount: 24 },
  { chain: "SC_11", failCount: 21 },
  { chain: "SC_07", failCount: 18 },
  { chain: "SC_19", failCount: 16 },
  { chain: "SC_03", failCount: 14 },
  { chain: "SC_16", failCount: 12 },
  { chain: "SC_02", failCount: 10 },
];

export const diagnosisConfidenceTrend30Day: TrendPoint[] = [
  { label: "Day 1", value: 82 },
  { label: "Day 5", value: 83.5 },
  { label: "Day 10", value: 85 },
  { label: "Day 15", value: 86.8 },
  { label: "Day 20", value: 88.2 },
  { label: "Day 25", value: 89.6 },
  { label: "Day 30", value: 91 },
];

export const scanTopologyGraphData: {
  nodes: TopologyGraphNode[];
  edges: TopologyGraphEdge[];
} = {
  nodes: [
    { id: "SC_14", label: "SC_14", status: "broken" },
    { id: "SC_08", label: "SC_08", status: "failing-cell" },
    { id: "SC_21", label: "SC_21", status: "broken" },
    { id: "SC_04", label: "SC_04", status: "debug" },
    { id: "SC_11", label: "SC_11", status: "warning" },
    { id: "SC_07", label: "SC_07", status: "healthy" },
    { id: "SC_19", label: "SC_19", status: "failing-cell" },
    { id: "SC_03", label: "SC_03", status: "healthy" },
  ],
  edges: [
    { from: "SC_14", to: "SC_08", broken: true },
    { from: "SC_08", to: "SC_21", broken: true },
    { from: "SC_21", to: "SC_04" },
    { from: "SC_04", to: "SC_11" },
    { from: "SC_11", to: "SC_07" },
    { from: "SC_07", to: "SC_19" },
    { from: "SC_19", to: "SC_03" },
  ],
};

export const scanDiagnosisCorrelationMatrix: FailureCorrelationMatrix = {
  rowLabels: ["Pattern", "Chain", "Failure", "Lot", "Wafer"],
  colLabels: ["Pattern", "Chain", "Failure", "Lot", "Wafer"],
  grid: [
    [100, 78, 72, 64, 58],
    [78, 100, 86, 71, 65],
    [72, 86, 100, 68, 62],
    [64, 71, 68, 100, 82],
    [58, 65, 62, 82, 100],
  ],
};

export const scanDiagnosisRecommendationRows: ScanDiagnosisRecommendationRow[] = [
  { diagnosisId: "DX-001", scanChain: "SC_14", failingCell: "SC_14-142", rootCause: "Chain break at segment 4", confidence: 94, priority: "Critical", affectedLot: "LOT-A2847", affectedWafer: "W-042", engineer: "J. Chen", status: "Pending" },
  { diagnosisId: "DX-002", scanChain: "SC_08", failingCell: "SC_08-089", rootCause: "Shift timing violation", confidence: 88, priority: "High", affectedLot: "LOT-B1092", affectedWafer: "W-018", engineer: "M. Patel", status: "In Review" },
  { diagnosisId: "DX-003", scanChain: "SC_21", failingCell: "SC_21-034", rootCause: "Capture edge misalignment", confidence: 91, priority: "Critical", affectedLot: "LOT-A2847", affectedWafer: "W-043", engineer: "J. Chen", status: "Approved" },
  { diagnosisId: "DX-004", scanChain: "SC_04", failingCell: "SC_04-201", rootCause: "Scan cell defect (SDFF)", confidence: 76, priority: "Medium", affectedLot: "LOT-C3310", affectedWafer: "W-007", engineer: "S. Kim", status: "Pending" },
  { diagnosisId: "DX-005", scanChain: "SC_11", failingCell: "SC_11-067", rootCause: "Hold time violation", confidence: 82, priority: "High", affectedLot: "LOT-B1092", affectedWafer: "W-019", engineer: "M. Patel", status: "In Review" },
  { diagnosisId: "DX-006", scanChain: "SC_19", failingCell: "SC_19-118", rootCause: "Metal short M4-M5", confidence: 93, priority: "Critical", affectedLot: "LOT-D8821", affectedWafer: "W-031", engineer: "A. Rivera", status: "Validated" },
  { diagnosisId: "DX-007", scanChain: "SC_03", failingCell: "SC_03-055", rootCause: "Ambiguous failure signature", confidence: 58, priority: "Low", affectedLot: "LOT-C3310", affectedWafer: "W-008", engineer: "S. Kim", status: "Pending" },
  { diagnosisId: "DX-008", scanChain: "SC_07", failingCell: "SC_07-022", rootCause: "Clock gating defect", confidence: 87, priority: "High", affectedLot: "LOT-A2847", affectedWafer: "W-044", engineer: "J. Chen", status: "Approved" },
];

export const scanDiagnosisExecutiveSummary: ScanDiagnosisExecutiveSummary = {
  title: "AI Diagnosis Executive Summary",
  subtitle: "Scan chain diagnosis insights generated by the AI diagnosis engine",
  metrics: [
    { label: "Failing Chains", value: "14" },
    { label: "Broken Chains", value: "9" },
    { label: "Failing Cells", value: "73" },
    { label: "Debug Locations", value: "31" },
    { label: "Average Confidence", value: "91%" },
    { label: "Pending Reviews", value: "6" },
    { label: "Expected Debug Time Reduction", value: "-38%" },
    { label: "Estimated Yield Improvement", value: "+1.6%" },
  ],
};

export const scanDiagnosisWorkflowSteps = [
  "Failure Logs",
  "Pattern Correlation",
  "Topology Analysis",
  "Scan Diagnosis Engine",
  "Root Cause Detection",
  "Debug Recommendation",
  "Engineer Review",
  "Validation",
];

function flattenDiagnosisKPIs() {
  return scanDiagnosisKPISections.flatMap((section) => section.kpis);
}

function pickFailureMini(ids: string[]) {
  return ids.map((id) => {
    const kpi = failureAnalysisKPIs.find((k) => k.id === id)!;
    return { id: kpi.id, label: kpi.title, value: kpi.value };
  });
}

function pickDiagnosisMini(ids: string[]) {
  const all = flattenDiagnosisKPIs();
  return ids.map((id) => {
    const kpi = all.find((k) => k.id === id)!;
    return { id: kpi.id, label: kpi.title, value: kpi.value };
  });
}

const totalChains = chainHealthData.reduce((sum, seg) => sum + seg.value, 0);
const healthyChains = chainHealthData.find((s) => s.name === "Healthy")?.value ?? 0;
const failingChainsCount = chainHealthData.find((s) => s.name === "Failing")?.value ?? 0;
const overallHealthPct = ((healthyChains / totalChains) * 100).toFixed(1);

export const executiveOverviewKPIs: ScanKPI[] = [
  {
    id: "overall-health",
    title: "Overall Scan Health",
    subtitle: "Healthy vs total chain ratio",
    value: `${overallHealthPct}%`,
    change: 1.8,
    trend: "up",
    sparkline: [76, 77, 78, 79, 80, 81, parseFloat(overallHealthPct)],
    icon: "gauge",
    positiveIsGood: true,
  },
  {
    id: "total-chains",
    title: "Total Scan Chains",
    subtitle: "Active chains across all modules",
    value: totalChains.toLocaleString(),
    change: 2.4,
    trend: "up",
    sparkline: [2650, 2680, 2720, 2750, 2780, 2810, totalChains],
    icon: "link",
    positiveIsGood: true,
  },
  {
    id: "healthy-chains",
    title: "Healthy Chains",
    subtitle: "Passing verification & diagnosis",
    value: healthyChains.toLocaleString(),
    change: 3.1,
    trend: "up",
    sparkline: [2100, 2140, 2180, 2200, 2230, 2260, healthyChains],
    icon: "check-circle",
    positiveIsGood: true,
  },
  {
    id: "failing-chains",
    title: "Failing Chains",
    subtitle: "Require debug or repair action",
    value: failingChainsCount.toString(),
    change: -8.3,
    trend: "down",
    sparkline: [186, 178, 172, 165, 158, 148, failingChainsCount],
    icon: "alert-triangle",
    positiveIsGood: false,
  },
  { ...overviewKPIs.find((k) => k.id === "scan-coverage")!, subtitle: "Fault coverage across patterns" },
  {
    id: "avg-diagnosis-confidence",
    title: "Average Diagnosis Confidence",
    subtitle: "AI flop-level localization accuracy",
    value: "91%",
    change: 2.1,
    trend: "up",
    sparkline: [86, 87, 88, 89, 90, 90.5, 91],
    icon: "shield-check",
    positiveIsGood: true,
  },
  { ...overviewKPIs.find((k) => k.id === "avg-test-time")!, subtitle: "Mean pattern execution runtime" },
];

const overviewPatternCount = patternAnalysisKPIs.find((k) => k.id === "files-ingested")!;
const overviewToggleCoverage = patternAnalysisKPIs.find((k) => k.id === "pattern-coverage-kpi")!;
const overviewRedundancy = patternAnalysisKPIs.find((k) => k.id === "redundant-patterns")!;
const overviewPassFail = patternAnalysisKPIs.find((k) => k.id === "pass-fail-linked")!;
const overviewTotalCycles = patternAnalysisRows.reduce((sum, row) => sum + row.vectors, 0);

export const overviewPatternSummaryKPIs = [
  { id: "pattern-count", label: "Pattern Count", value: overviewPatternCount.value },
  { id: "toggle-coverage", label: "Toggle Coverage", value: overviewToggleCoverage.value },
  { id: "redundancy", label: "Redundancy", value: overviewRedundancy.value },
  { id: "total-cycles", label: "Total Cycles", value: overviewTotalCycles.toLocaleString() },
  { id: "pass-fail", label: "Pass / Fail", value: "2,741 / 105" },
  { id: "pass-rate", label: "Pass Rate", value: overviewPassFail.status },
];

export const overviewFailureSummaryKPIs = pickFailureMini([
  "overall-failure-rate",
  "failing-patterns",
]);

export const overviewDiagnosisSummaryKPIs = pickDiagnosisMini([
  "sd-failing-chains",
  "sd-failing-cells",
  "sd-chain-breaks",
  "sd-topology-chains",
]);

export const overviewPatternPinChainData: TrendPoint[] = [
  { label: "ScanIn Pins", value: 16 },
  { label: "ScanOut Pins", value: 16 },
  { label: "Scan Chains", value: 128 },
];

export const overviewPatternPassFailTrend: TrendPoint[] = [
  { label: "W1", value: 2480, value2: 142 },
  { label: "W2", value: 2542, value2: 128 },
  { label: "W3", value: 2608, value2: 116 },
  { label: "W4", value: 2664, value2: 108 },
  { label: "W5", value: 2702, value2: 102 },
  { label: "W6", value: 2724, value2: 107 },
  { label: "W7", value: 2741, value2: 105 },
];

export const topFailingScanChains: ChipFailData[] = chainFailureRanking.map((row) => ({
  chip: row.chain,
  failCount: row.failCount,
}));

export const topFailingPatterns: ChipFailData[] = [
  { chip: "PAT-4821", failCount: 186 },
  { chip: "PAT-3156", failCount: 164 },
  { chip: "PAT-7892", failCount: 142 },
  { chip: "PAT-2441", failCount: 128 },
  { chip: "PAT-9103", failCount: 112 },
  { chip: "PAT-1778", failCount: 98 },
  { chip: "PAT-5632", failCount: 86 },
  { chip: "PAT-8214", failCount: 74 },
  { chip: "PAT-3399", failCount: 62 },
  { chip: "PAT-6671", failCount: 54 },
];

export const overviewTrendCharts: import("@/types/scanChain").OverviewTrendChart[] = [
  { id: "failure", title: "Failure Trend", data: failureTrendData, lines: [{ key: "value", color: "#EF4444", name: "Failures" }] },
  { id: "pattern-growth", title: "Pattern Growth", data: patternImportTrend, lines: [{ key: "value", color: "#7C3AED", name: "Patterns" }] },
  { id: "coverage", title: "Coverage Trend", data: patternAnalysisCoverageTrend, lines: [{ key: "value", color: "#06B6D4", name: "Coverage %" }] },
  { id: "diagnosis", title: "Diagnosis Trend", data: diagnosisConfidenceTrend30Day, lines: [{ key: "value", color: "#A78BFA", name: "Confidence %" }] },
  { id: "yield", title: "Yield Trend", data: patternCoverageTrend, lines: [{ key: "value", color: "#22C55E", name: "Yield Proxy %" }] },
  { id: "chain-growth", title: "Chain Growth", data: overallFailureTrend, lines: [{ key: "value2", color: "#7C3AED", name: "Active Chains" }] },
  { id: "recurring", title: "Recurring Failure Trend", data: failureRateTrend, lines: [{ key: "value", color: "#F97316", name: "Rate %" }] },
  { id: "repair", title: "Repair Success Trend", data: diagnosisTimeline, lines: [{ key: "value2", color: "#22C55E", name: "Open Issues" }] },
];

export const overviewExecutiveInsights: import("@/types/scanChain").OverviewExecutiveInsights = {
  summary:
    "Scan chain health is stable with declining failure rate. Bridge faults on LOT-A2847 remain the top priority; pattern redundancy cleanup can reduce test time.",
  mostCriticalChain: "SC_14 (38 failures across 5 lots)",
  mostCriticalPattern: failureAISummary.mostAffectedPattern,
  highestFailureLot: failureAISummary.highestFailureLot,
  highestFailureWafer: failureAISummary.highestFailureWafer,
  mostCommonRootCause: failureAISummary.mostFrequentRootCause,
  confidence: "91%",
  estimatedSaving: "$284K / quarter",
  priorityRecommendation: failureAISummary.recommendedEngineeringAction,
};

export const overviewRecommendationPreview: import("@/types/scanChain").OverviewRecommendationPreviewRow[] =
  scanDiagnosisRecommendationRows.slice(0, 4).map((row) => ({
    id: row.diagnosisId,
    recommendation: `${row.scanChain}: ${row.rootCause}`,
    confidence: row.confidence,
    expectedSaving: row.priority === "Critical" ? "$48K" : row.priority === "High" ? "$28K" : "$12K",
    priority: row.priority,
    status: row.status,
  }));

export const overviewAlertsPreview: import("@/types/scanChain").OverviewAlertPreviewRow[] =
  scanChainAlerts.map((alert) => ({
    id: alert.id,
    title: `${alert.chainId} · ${alert.pattern}`,
    severity: alert.severity === "Critical" ? "Critical" : alert.severity === "High" ? "High" : "Warning",
    status: alert.status,
  }));

export const overviewAlertCounts = {
  critical: scanChainAlerts.filter((a) => a.severity === "Critical").length,
  high: scanChainAlerts.filter((a) => a.severity === "High").length,
  warning: scanChainAlerts.filter((a) => a.severity === "Medium").length,
};

export const overviewUploadActivity: import("@/types/scanChain").OverviewUploadActivityRow[] = [
  {
    id: "UPL-L-001",
    fileName: "lot4821_scan.stdf",
    patternsParsed: "486",
    chainsParsed: "128",
    failuresFound: "142",
    parser: "STDF Parser",
    uploadTime: "Jun 29, 2026 · 10:05",
    status: "Completed",
  },
  {
    id: "UPL-D-001",
    fileName: "scan_chain_lot4821.csv",
    patternsParsed: "412",
    chainsParsed: "128",
    failuresFound: "98",
    parser: "CSV Ingest",
    uploadTime: "Jun 29, 2026 · 09:12",
    status: "Completed",
  },
  {
    id: "UPL-L-002",
    fileName: "mbist_repair.log",
    patternsParsed: "—",
    chainsParsed: "64",
    failuresFound: "31",
    parser: "Log Parser",
    uploadTime: "Jun 29, 2026 · 09:40",
    status: "Parsing",
  },
];
