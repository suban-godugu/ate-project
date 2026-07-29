import type {
  TrendPoint,
  WaferAIInsight,
  WaferBottomSummary,
  WaferDefectClass,
  WaferDefectClassBundle,
  WaferDefectClassKPI,
  WaferDefectClassMeta,
  WaferGalleryCard,
  WaferImages,
  WaferInfoPanelData,
  WaferKPI,
  WaferTopDefectRow,
  WaferUploadHistoryItem,
} from "@/types/wafer";

const WAFER_GRID = 48;
const WAFER_CELL = 6;
const WAFER_SIZE = WAFER_GRID * WAFER_CELL;

function dieValue(
  row: number,
  col: number,
  variant: WaferDefectClass,
  mode: "overlay" | "density",
  seed = 0
): number {
  const cx = WAFER_GRID / 2;
  const cy = WAFER_GRID / 2;
  const dx = col - cx;
  const dy = row - cy;
  const dist = Math.sqrt(dx * dx + dy * dy) / (WAFER_GRID / 2);
  const angle = Math.atan2(dy, dx);
  const noise = (row * 17 + col * 31 + seed * 13) % 97;

  if (dist > 1) return -1;

  switch (variant) {
    case "centre":
      return dist < 0.22 ? 0.15 + noise * 0.004 : 0.82 + noise * 0.002;
    case "donut":
      return dist > 0.35 && dist < 0.55 ? 0.12 + noise * 0.003 : 0.8 + noise * 0.002;
    case "edge-ring":
      return dist > 0.78 ? 0.1 + noise * 0.004 : 0.85 + noise * 0.002;
    case "scratch":
      return Math.abs(dx * 0.6 + dy * 0.8) < 1.8 ? 0.08 + noise * 0.003 : 0.86 + noise * 0.002;
    case "near-full":
      return 0.05 + noise * 0.008;
    case "normal":
      return noise > 88 ? 0.2 + noise * 0.003 : 0.92 + noise * 0.001;
    case "edge-loc":
      return dist > 0.72 && angle > -0.5 && angle < 1.2 ? 0.1 + noise * 0.004 : 0.84 + noise * 0.002;
    case "local":
      return dist < 0.18 && row > 28 && col > 28 ? 0.08 + noise * 0.003 : 0.86 + noise * 0.002;
    case "random":
      return noise > 82 ? 0.15 + noise * 0.004 : 0.88 + noise * 0.002;
    default:
      return 0.5;
  }
}

function dieColor(val: number, mode: "overlay" | "density"): string {
  if (mode === "density") {
    if (val < 0.3) return `rgba(239,68,68,${0.35 + (0.3 - val) * 1.5})`;
    if (val < 0.6) return `rgba(249,115,22,${0.25 + (0.6 - val) * 0.5})`;
    return `rgba(34,197,94,${0.15 + val * 0.35})`;
  }
  if (val < 0.35) return "#EF4444";
  if (val < 0.65) return "#F97316";
  return "#22C55E";
}

function buildWaferImageUri(
  classId: WaferDefectClass,
  kind: keyof WaferImages,
  seed = 0
): string {
  const mode = kind === "density" ? "density" : "overlay";
  const rects: string[] = [];

  for (let row = 0; row < WAFER_GRID; row++) {
    for (let col = 0; col < WAFER_GRID; col++) {
      const val = dieValue(row, col, classId, mode, seed);
      if (val < 0) continue;
      rects.push(
        `<rect x="${col * WAFER_CELL}" y="${row * WAFER_CELL}" width="${WAFER_CELL - 1}" height="${WAFER_CELL - 1}" fill="${dieColor(val, mode)}" />`
      );
    }
  }

  const overlayLines =
    kind === "overlay"
      ? `<line x1="${WAFER_SIZE * 0.2}" y1="${WAFER_SIZE * 0.5}" x2="${WAFER_SIZE * 0.8}" y2="${WAFER_SIZE * 0.5}" stroke="rgba(124,58,237,0.35)" stroke-width="1"/><line x1="${WAFER_SIZE * 0.5}" y1="${WAFER_SIZE * 0.2}" x2="${WAFER_SIZE * 0.5}" y2="${WAFER_SIZE * 0.8}" stroke="rgba(124,58,237,0.35)" stroke-width="1"/>`
      : "";

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${WAFER_SIZE}" height="${WAFER_SIZE}" viewBox="0 0 ${WAFER_SIZE} ${WAFER_SIZE}"><defs><clipPath id="w"><circle cx="${WAFER_SIZE / 2}" cy="${WAFER_SIZE / 2}" r="${WAFER_SIZE / 2 - 2}"/></clipPath></defs><circle cx="${WAFER_SIZE / 2}" cy="${WAFER_SIZE / 2}" r="${WAFER_SIZE / 2 - 2}" fill="#0A1020"/><g clip-path="url(#w)">${rects.join("")}</g><circle cx="${WAFER_SIZE / 2}" cy="${WAFER_SIZE / 2}" r="${WAFER_SIZE / 2 - 2}" fill="none" stroke="#2D3748" stroke-width="2"/>${overlayLines}</svg>`;

  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

export function buildWaferImages(classId: WaferDefectClass, seed = 0): WaferImages {
  return {
    wafer: buildWaferImageUri(classId, "wafer", seed),
    overlay: buildWaferImageUri(classId, "overlay", seed),
    density: buildWaferImageUri(classId, "density", seed),
  };
}

export const ANALYSIS_GRID = 48;

/** Fail intensity 0–1 inside wafer, -1 outside wafer circle */
export function getDieFailIntensity(
  row: number,
  col: number,
  classId: WaferDefectClass,
  seed = 0
): number {
  const val = dieValue(row, col, classId, "overlay", seed);
  if (val < 0) return -1;
  return 1 - val;
}

export function isDieFail(row: number, col: number, classId: WaferDefectClass, seed = 0): boolean {
  const intensity = getDieFailIntensity(row, col, classId, seed);
  return intensity >= 0 && intensity > 0.35;
}

export const WAFER_DEFECT_CLASSES: WaferDefectClass[] = [
  "centre",
  "donut",
  "edge-ring",
  "scratch",
  "near-full",
  "normal",
  "edge-loc",
  "local",
  "random",
];

export const defectClassMeta: Record<WaferDefectClass, WaferDefectClassMeta> = {
  centre: {
    id: "centre",
    label: "Centre",
    tabLabel: "Centre",
    description: "AI detected wafers exhibiting centre defect patterns with localized die failures in the wafer core region.",
    color: "#EF4444",
    images: buildWaferImages("centre"),
  },
  donut: {
    id: "donut",
    label: "Donut",
    tabLabel: "Donut",
    description: "Ring-shaped defect distribution forming an annular failure band between centre and edge zones.",
    color: "#F97316",
    images: buildWaferImages("donut"),
  },
  "edge-ring": {
    id: "edge-ring",
    label: "Edge-Ring",
    tabLabel: "Edge-Ring",
    description: "Peripheral edge ring defects typically associated with handling, chucking, or edge bead effects.",
    color: "#EAB308",
    images: buildWaferImages("edge-ring"),
  },
  scratch: {
    id: "scratch",
    label: "Scratch",
    tabLabel: "Scratch",
    description: "Linear scratch signatures crossing die fields, often linked to probe card or transport damage.",
    color: "#A855F7",
    images: buildWaferImages("scratch"),
  },
  "near-full": {
    id: "near-full",
    label: "Near-Full",
    tabLabel: "Near-Full",
    description: "Near full-wafer failure patterns with catastrophic yield loss across most die positions.",
    color: "#DC2626",
    images: buildWaferImages("near-full"),
  },
  normal: {
    id: "normal",
    label: "Normal",
    tabLabel: "Normal",
    description: "Baseline wafer maps with expected random defect scatter and healthy yield distribution.",
    color: "#22C55E",
    images: buildWaferImages("normal"),
  },
  "edge-loc": {
    id: "edge-loc",
    label: "Edge-Loc",
    tabLabel: "Edge-Loc",
    description: "Localized edge defect clusters concentrated at specific wafer quadrants or flat zones.",
    color: "#06B6D4",
    images: buildWaferImages("edge-loc"),
  },
  local: {
    id: "local",
    label: "Local",
    tabLabel: "Local",
    description: "Compact local defect clusters indicating process excursion or reticle-level anomalies.",
    color: "#8B5CF6",
    images: buildWaferImages("local"),
  },
  random: {
    id: "random",
    label: "Random",
    tabLabel: "Random",
    description: "Stochastic random defect scatter without dominant spatial signature or repeatable pattern.",
    color: "#64748B",
    images: buildWaferImages("random"),
  },
};

export const inputDieStatsKPIs: WaferKPI[] = [
  { id: "wafers", title: "Number of Wafers", value: "1,248", change: 4.2, trend: "up", sparkline: [1100, 1140, 1180, 1205, 1220, 1235, 1248], icon: "layers", positiveIsGood: true, tooltip: "Total wafers analyzed in current filter scope" },
  { id: "dies", title: "Number of Dies", value: "992,640", change: 3.8, trend: "up", sparkline: [880000, 900000, 920000, 940000, 960000, 975000, 992640], icon: "grid", positiveIsGood: true, tooltip: "Total die count across all inspected wafers" },
  { id: "good-dies", title: "Good Dies", value: "931,284", change: 2.6, trend: "up", sparkline: [820000, 840000, 860000, 880000, 900000, 915000, 931284], icon: "check-circle", positiveIsGood: true, tooltip: "Passing dies after classification" },
  { id: "bad-dies", title: "Bad Dies", value: "61,356", change: -6.4, trend: "down", sparkline: [72000, 70000, 68000, 67000, 65000, 63000, 61356], icon: "x-circle", positiveIsGood: false, tooltip: "Failed dies requiring disposition" },
  { id: "clusters", title: "Defect Clusters", value: "342", change: -3.1, trend: "down", sparkline: [380, 372, 365, 358, 352, 346, 342], icon: "crosshair", positiveIsGood: false, tooltip: "Spatial defect clusters detected by AI" },
];

export const defectClassificationKPIs: WaferDefectClassKPI[] = WAFER_DEFECT_CLASSES.map((id, i) => {
  const meta = defectClassMeta[id];
  const base = [42, 38, 56, 24, 12, 312, 48, 36, 280][i] ?? 30;
  return {
    id,
    label: meta.label,
    waferCount: base,
    avgYield: Number((88 + (i % 5) * 1.4).toFixed(1)),
    avgConfidence: 78 + (i % 7) * 2,
    color: meta.color,
    sparkline: Array.from({ length: 7 }, (_, j) => base - 6 + j + (i % 3)),
  };
});

export const positiveNegativeYield: TrendPoint[] = [
  { label: "W1", value: 94.2, value2: 5.8 },
  { label: "W2", value: 93.8, value2: 6.2 },
  { label: "W3", value: 95.1, value2: 4.9 },
  { label: "W4", value: 92.4, value2: 7.6 },
  { label: "W5", value: 94.8, value2: 5.2 },
];

export const yieldTrend30: TrendPoint[] = Array.from({ length: 30 }, (_, i) => ({
  label: `W${i + 1}`,
  value: Number((91 + Math.sin(i / 4) * 2 + (i % 5) * 0.15).toFixed(1)),
}));

export const yieldDistribution: { name: string; value: number; color: string }[] = [
  { name: "90–92%", value: 142, color: "#F97316" },
  { name: "92–94%", value: 386, color: "#EAB308" },
  { name: "94–96%", value: 512, color: "#22C55E" },
  { name: "96%+", value: 208, color: "#7C3AED" },
];

export const defectClassBreakdown: TrendPoint[] = WAFER_DEFECT_CLASSES.map((id) => ({
  label: defectClassMeta[id].label,
  value: defectClassificationKPIs.find((k) => k.id === id)?.waferCount ?? 0,
}));

export const topDefectWafers: WaferTopDefectRow[] = [
  { id: "TD-001", waferId: "W-042", lotId: "LOT-8832", yield: 72.4, defectType: "Near-Full", confidence: 96, status: "Critical", images: buildWaferImages("near-full", 1) },
  { id: "TD-002", waferId: "W-118", lotId: "LOT-4421", yield: 81.2, defectType: "Centre", confidence: 91, status: "Review", images: buildWaferImages("centre", 2) },
  { id: "TD-003", waferId: "W-076", lotId: "LOT-9921", yield: 84.6, defectType: "Edge-Ring", confidence: 88, status: "Review", images: buildWaferImages("edge-ring", 3) },
  { id: "TD-004", waferId: "W-203", lotId: "LOT-5510", yield: 86.1, defectType: "Scratch", confidence: 85, status: "Open", images: buildWaferImages("scratch", 4) },
  { id: "TD-005", waferId: "W-034", lotId: "LOT-7734", yield: 87.8, defectType: "Donut", confidence: 84, status: "Open", images: buildWaferImages("donut", 5) },
  { id: "TD-006", waferId: "W-159", lotId: "LOT-6621", yield: 88.4, defectType: "Local", confidence: 82, status: "Monitoring", images: buildWaferImages("local", 6) },
  { id: "TD-007", waferId: "W-091", lotId: "LOT-3310", yield: 89.2, defectType: "Edge-Loc", confidence: 80, status: "Monitoring", images: buildWaferImages("edge-loc", 7) },
  { id: "TD-008", waferId: "W-267", lotId: "LOT-8840", yield: 90.1, defectType: "Random", confidence: 76, status: "Pass", images: buildWaferImages("random", 8) },
];

export const galleryCards: WaferGalleryCard[] = WAFER_DEFECT_CLASSES.map((id, i) => {
  const total = 796;
  const bad = [86, 72, 94, 48, 612, 28, 76, 64, 52][i] ?? 40;
  return {
    id,
    label: defectClassMeta[id].label,
    avgYield: Number((100 - (bad / total) * 100).toFixed(1)),
    confidence: 72 + (i % 8) * 3,
    totalDies: total,
    goodDies: total - bad,
    badDies: bad,
    images: defectClassMeta[id].images,
  };
});

export const bottomSummary: WaferBottomSummary = {
  totalWafers: "1,248",
  totalDies: "992,640",
  goodDies: "931,284",
  badDies: "61,356",
  averageYield: "93.8%",
  estimatedSavings: "$284K",
  aiConfidence: "91.4%",
};

export const uploadWorkflowSteps = [
  "Upload Wafer Image",
  "AI Classification",
  "Overlay Generation",
  "Fail Density Generation",
  "Defect Classification",
  "Yield Calculation",
  "Recommendation Engine",
  "Save Analysis",
];

function buildAllUploads(classId: WaferDefectClass, count = 10): WaferUploadHistoryItem[] {
  const meta = defectClassMeta[classId];
  return Array.from({ length: count }, (_, i) => ({
    id: `${classId}-UP-${i + 1}`,
    lot: `LOT-${meta.label.slice(0, 2).toUpperCase()}${4200 + i * 137}`,
    wafer: `W-${String(10 + i * 17).padStart(3, "0")}`,
    confidence: 78 + ((i + classId.length) % 12),
    uploadDate: `2026-06-${String(28 - i).padStart(2, "0")} ${String(8 + i).padStart(2, "0")}:${String((i * 7) % 60).padStart(2, "0")}`,
    images: buildWaferImages(classId, i + 1),
    seed: i + 1,
    hotspotX: 49 + (i % 5) * 2,
    hotspotY: 31 + (i % 4) * 2,
  }));
}

function buildDefectKPIs(classId: WaferDefectClass): WaferKPI[] {
  const idx = WAFER_DEFECT_CLASSES.indexOf(classId);
  const meta = defectClassMeta[classId];
  const waferCount = defectClassificationKPIs[idx]?.waferCount ?? 40;
  const avgYield = defectClassificationKPIs[idx]?.avgYield ?? 90;
  const avgConf = defectClassificationKPIs[idx]?.avgConfidence ?? 85;
  const badDies = 48 + idx * 6;
  const goodDies = 748 - idx * 4;
  return [
    { id: "total-wafers", title: "Total Wafers", value: String(waferCount), change: 2.4, trend: "up", sparkline: [waferCount - 8, waferCount - 6, waferCount - 4, waferCount - 3, waferCount - 2, waferCount - 1, waferCount], icon: "layers", positiveIsGood: true },
    { id: "good-dies", title: "Good Dies", value: String(goodDies), change: 1.8, trend: "up", sparkline: [goodDies - 20, goodDies - 15, goodDies - 12, goodDies - 8, goodDies - 5, goodDies - 2, goodDies], icon: "check-circle", positiveIsGood: true },
    { id: "bad-dies", title: "Bad Dies", value: String(badDies), change: -4.2, trend: "down", sparkline: [badDies + 12, badDies + 9, badDies + 7, badDies + 5, badDies + 3, badDies + 1, badDies], icon: "x-circle", positiveIsGood: false },
    { id: "avg-yield", title: "Average Yield", value: `${avgYield}%`, change: 1.2, trend: "up", sparkline: [avgYield - 2, avgYield - 1.5, avgYield - 1, avgYield - 0.6, avgYield - 0.3, avgYield - 0.1, avgYield], icon: "gauge", positiveIsGood: true },
    { id: "avg-confidence", title: "Average Confidence", value: `${avgConf}%`, change: 0.8, trend: "up", sparkline: [avgConf - 4, avgConf - 3, avgConf - 2, avgConf - 1.5, avgConf - 1, avgConf - 0.5, avgConf], icon: "brain", positiveIsGood: true },
    { id: "total-dies", title: "Total Dies", value: "796", change: 0, trend: "up", sparkline: [796, 796, 796, 796, 796, 796, 796], icon: "grid", positiveIsGood: true },
    { id: "severity", title: "Defect Severity", value: idx < 3 ? "High" : idx < 6 ? "Medium" : "Low", change: idx % 2 === 0 ? -2.1 : 1.4, trend: idx % 2 === 0 ? "down" : "up", sparkline: [3, 2.8, 2.6, 2.4, 2.2, 2.1, 2], icon: "alert-triangle", positiveIsGood: false },
    { id: "yield-loss", title: "Estimated Yield Loss", value: `${(100 - avgYield).toFixed(1)}%`, change: -1.6, trend: "down", sparkline: [12, 11, 10.5, 10, 9.5, 9.2, 100 - avgYield], icon: "trending-down", positiveIsGood: false },
  ].map((kpi) => ({ ...kpi, tooltip: `${meta.label} — ${kpi.title}` })) as WaferKPI[];
}

function buildAIInsight(classId: WaferDefectClass): WaferAIInsight {
  const meta = defectClassMeta[classId];
  const causes: Record<WaferDefectClass, string> = {
    centre: "Chuck contamination and centre-zone thermal non-uniformity during etch",
    donut: "Plasma ring instability creating annular process excursion",
    "edge-ring": "Edge bead removal inconsistency and wafer handling micro-scratches",
    scratch: "Probe card misalignment causing linear transport scratches",
    "near-full": "Lot-level process excursion with reticle overlay mismatch",
    normal: "Within-spec random particle scatter — no systemic root cause",
    "edge-loc": "Localized edge flat-zone clamp pressure anomaly",
    local: "Reticle defect transfer creating compact cluster signature",
    random: "Stochastic particle events without spatial correlation",
  };
  const actions: Record<WaferDefectClass, string> = {
    centre: "Inspect chuck surface, recalibrate centre thermal zone, quarantine affected lot",
    donut: "Review plasma power ramp profile and chamber seasoning cycle",
    "edge-ring": "Validate edge bead removal recipe and edge-handling SOP",
    scratch: "Align probe card, inspect transport rails, pause affected tester",
    "near-full": "Halt lot disposition, escalate to process engineering immediately",
    normal: "Continue standard monitoring — no corrective action required",
    "edge-loc": "Adjust edge clamp pressure map and re-run edge die screening",
    local: "Isolate reticle field, run focused SEM review on cluster dies",
    random: "Increase particle monitoring frequency, review UPW and fab airflow",
  };
  return {
    rootCause: causes[classId],
    affectedDies: 28 + WAFER_DEFECT_CLASSES.indexOf(classId) * 8,
    estimatedYieldLoss: `${(100 - (defectClassificationKPIs[WAFER_DEFECT_CLASSES.indexOf(classId)]?.avgYield ?? 90)).toFixed(1)}%`,
    recommendedAction: actions[classId],
    priority: classId === "near-full" ? "Critical" : classId === "centre" || classId === "scratch" ? "High" : classId === "normal" ? "Low" : "Medium",
    confidence: defectClassificationKPIs[WAFER_DEFECT_CLASSES.indexOf(classId)]?.avgConfidence ?? 85,
  };
}

function buildInfoPanel(classId: WaferDefectClass): WaferInfoPanelData {
  const meta = defectClassMeta[classId];
  const avgYield = defectClassificationKPIs[WAFER_DEFECT_CLASSES.indexOf(classId)]?.avgYield ?? 90;
  const bad = 48 + WAFER_DEFECT_CLASSES.indexOf(classId) * 5;
  const total = 796;
  return {
    defectType: meta.label,
    assignedLot: `LOT-${4400 + WAFER_DEFECT_CLASSES.indexOf(classId) * 112}`,
    confidence: defectClassificationKPIs[WAFER_DEFECT_CLASSES.indexOf(classId)]?.avgConfidence ?? 85,
    goodDies: total - bad,
    badDies: bad,
    totalDies: total,
    yield: avgYield,
    averageCost: `$${(18.4 + WAFER_DEFECT_CLASSES.indexOf(classId) * 2.1).toFixed(1)}K`,
    recommendation: buildAIInsight(classId).recommendedAction.slice(0, 80) + "...",
  };
}

function buildDefectBundle(classId: WaferDefectClass): WaferDefectClassBundle {
  return {
    meta: defectClassMeta[classId],
    kpis: buildDefectKPIs(classId),
    allUploads: buildAllUploads(classId),
    infoPanel: buildInfoPanel(classId),
  };
}

export const defectClassBundles = WAFER_DEFECT_CLASSES.reduce(
  (acc, id) => {
    acc[id] = buildDefectBundle(id);
    return acc;
  },
  {} as Record<WaferDefectClass, WaferDefectClassBundle>
);

export function getDefectBundle(classId: WaferDefectClass): WaferDefectClassBundle {
  return defectClassBundles[classId];
}

// Legacy exports kept for filter engine compatibility
export const overviewKPIs = inputDieStatsKPIs;
export const yieldRows = topDefectWafers.map((r) => ({
  id: r.id,
  lotId: r.lotId,
  waferId: r.waferId,
  yield: r.yield,
  goodDies: Math.round(796 * (r.yield / 100)),
  badDies: Math.round(796 * (1 - r.yield / 100)),
  tester: "ATE-01",
  status: r.status,
}));
export const defectRows = topDefectWafers.map((r, i) => ({
  id: `WD-${i}`,
  zone: r.defectType,
  defectType: r.defectType,
  count: Math.round(796 * (1 - r.yield / 100)),
  severity: r.status === "Critical" ? "Critical" as const : r.status === "Review" ? "High" as const : "Medium" as const,
  lotId: r.lotId,
}));
export const yieldTrend = yieldTrend30.slice(0, 5);
export const defectTrend = defectClassBreakdown;
export const waferRecommendations = topDefectWafers.slice(0, 3).map((r, i) => ({
  id: `WR-${i + 1}`,
  title: `${r.defectType} yield recovery`,
  recommendation: `Apply ${r.defectType} mitigation for ${r.lotId}`,
  priority: r.status === "Critical" ? "Critical" as const : "High" as const,
  confidence: r.confidence,
  expectedYieldGain: `+${(100 - r.yield).toFixed(1)}%`,
}));
export const waferHeatmapGrid = Array.from({ length: 12 }, (_, r) =>
  Array.from({ length: 12 }, (_, c) => Math.round(40 + ((r * 7 + c * 11) % 60)))
);
