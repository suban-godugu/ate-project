export type WaferDefectClass =
  | "centre"
  | "donut"
  | "edge-ring"
  | "scratch"
  | "near-full"
  | "normal"
  | "edge-loc"
  | "local"
  | "random";

export type WaferTab = "overview" | WaferDefectClass;

export interface WaferImages {
  wafer: string;
  overlay: string;
  density: string;
}

export interface WaferKPI {
  id: string;
  title: string;
  value: string;
  change: number;
  trend: "up" | "down";
  sparkline: number[];
  icon: string;
  positiveIsGood?: boolean;
  tooltip?: string;
}

export interface WaferDefectClassKPI {
  id: WaferDefectClass;
  label: string;
  waferCount: number;
  avgYield: number;
  avgConfidence: number;
  color: string;
  sparkline: number[];
}

export interface WaferGalleryCard {
  id: WaferDefectClass;
  label: string;
  avgYield: number;
  confidence: number;
  totalDies: number;
  goodDies: number;
  badDies: number;
  images: WaferImages;
}

export interface WaferTopDefectRow {
  id: string;
  waferId: string;
  lotId: string;
  yield: number;
  defectType: string;
  confidence: number;
  status: string;
  images: WaferImages;
}

export interface WaferAnalysisRow {
  id: string;
  waferId: string;
  lot: string;
  tester: string;
  product: string;
  yield: number;
  goodDies: number;
  badDies: number;
  confidence: number;
  status: string;
  engineer: string;
  uploadTime: string;
  images: WaferImages;
}

export interface WaferUploadHistoryItem {
  id: string;
  lot: string;
  wafer: string;
  confidence: number;
  uploadDate: string;
  images: WaferImages;
  seed: number;
  hotspotX: number;
  hotspotY: number;
}

export interface WaferClassProbability {
  class: string;
  probability: number;
  color: string;
}

export interface WaferAIInsight {
  rootCause: string;
  affectedDies: number;
  estimatedYieldLoss: string;
  recommendedAction: string;
  priority: "Critical" | "High" | "Medium" | "Low";
  confidence: number;
}

export interface WaferInfoPanelData {
  defectType: string;
  assignedLot: string;
  confidence: number;
  goodDies: number;
  badDies: number;
  totalDies: number;
  yield: number;
  averageCost: string;
  recommendation: string;
}

export interface WaferDefectClassMeta {
  id: WaferDefectClass;
  label: string;
  tabLabel: string;
  description: string;
  color: string;
  images: WaferImages;
}

export interface WaferDefectClassBundle {
  meta: WaferDefectClassMeta;
  kpis: WaferKPI[];
  allUploads: WaferUploadHistoryItem[];
  infoPanel: WaferInfoPanelData;
}

export interface TrendPoint {
  label: string;
  value: number;
  value2?: number;
}

export interface WaferBottomSummary {
  totalWafers: string;
  totalDies: string;
  goodDies: string;
  badDies: string;
  averageYield: string;
  estimatedSavings: string;
  aiConfidence: string;
}
