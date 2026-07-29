export type GridMode = "automatic" | "manual";

export interface ClassificationResult {
  defect_type: string;
  confidence: number;
  class_index?: number | null;
  assigned_lot?: string | null;
  lot?: string | null;
}

export interface YieldSummary {
  good_dies: number;
  fail_dies: number;
  total_dies: number;
  yield_percent: number;
}

export interface GridInfo {
  mode: string;
  rows: number;
  columns: number;
  pitch?: number;
  offset_x?: number;
  offset_y?: number;
}

export interface WaferGeometry {
  center_x: number;
  center_y: number;
  radius: number;
}

export interface DieRecord {
  die_id: number;
  row: number;
  column: number;
  x: number;
  y: number;
  status: string;
  bbox?: {
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  };
}

export interface ImageSet {
  original?: string;
  overlay?: string;
  density?: string;
  gradcam?: string;
  heatmap?: string;
}

export interface ClusterPayload {
  items?: unknown[];
  [key: string]: unknown;
}

export interface ZoneAnalysisPayload {
  zones?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ClusterBoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ClusterRecord {
  cluster_id: string;
  good_dies: number;
  fail_dies: number;
  total_dies: number;
  member_die_ids: number[];
  center_x: number;
  center_y: number;
  bounding_box: ClusterBoundingBox;
  cluster_area: number;
  cluster_density: number;
  cluster_fail_percent: number;
  contribution_percent: number;
  severity_score: number;
  severity: string;
  rank: number;
}

export interface ClusterSummary {
  total_clusters_detected: number;
  displayed_clusters: number;
  critical_clusters: number;
  largest_cluster_fail_dies: number;
  highest_severity_score: number;
}

export interface ZoneBoundaryPoint {
  x: number;
  y: number;
}

export interface ZoneRecord {
  zone: string;
  good_dies: number;
  fail_dies: number;
  total_dies: number;
  yield_percent: number;
  fail_percent: number;
  defect_density: string;
  rank: number;
  status: string;
  zone_boundary: ZoneBoundaryPoint[];
}

export interface SpatialAnalysisPayload {
  cluster_summary: ClusterSummary;
  clusters: ClusterRecord[];
  zone_analysis: ZoneRecord[];
}

/** Exact analysis payload returned by POST /predict and each batch item. */
export interface WaferAnalysisResult {
  wafer_id: string;
  classification: ClassificationResult;
  yield_summary: YieldSummary;
  grid_info: GridInfo;
  wafer_geometry?: WaferGeometry;
  dies: DieRecord[];
  images?: ImageSet;
  wafer_summary?: Record<string, unknown>;
  assigned_lot?: string | null;
  lot?: string | null;
  /** Client-attached source filename for session display (not from engineering calc). */
  source_file?: string;
  /** Prompt 14 spatial analytics block (null when unavailable). */
  spatial_analysis?: SpatialAnalysisPayload | null;
  clusters?: ClusterPayload | unknown[] | null;
  zone_analysis?: ZoneAnalysisPayload | null;
  [key: string]: unknown;
}

export interface PredictOptions {
  gridMode: GridMode;
  gridSize?: number;
}

/** LOT tabs mirror static taxonomy LOT_1…LOT_9 (client navigation only). */
export type LotDashboardTab =
  | "LOT_1"
  | "LOT_2"
  | "LOT_3"
  | "LOT_4"
  | "LOT_5"
  | "LOT_6"
  | "LOT_7"
  | "LOT_8"
  | "LOT_9";

export type DashboardTab =
  | "overview"
  | "wafer"
  | "batch"
  | LotDashboardTab
  | "reports"
  | "spatial"
  | "zones";

export function isLotDashboardTab(tab: DashboardTab): tab is LotDashboardTab {
  return tab.startsWith("LOT_");
}

