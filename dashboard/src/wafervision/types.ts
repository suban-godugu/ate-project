export type ConnectionStatus = "idle" | "connected" | "offline" | "backend_error";

export type GridMode = "automatic" | "manual";

export type DashboardTab =
  | "overview"
  | "LOT_1"
  | "LOT_2"
  | "LOT_3"
  | "LOT_4"
  | "LOT_5"
  | "LOT_6"
  | "LOT_7"
  | "LOT_8"
  | "LOT_9"
  | "reports"
  | "wafer"
  | "batch"
  | "spatial"
  | "zones";

export type WaferModalView = "analysis" | "spatial" | "zones";

export type SortKey =
  | "name"
  | "yield"
  | "confidence"
  | "lot"
  | "defect"
  | "failDies"
  | "goodDies";

export interface WaferFilters {
  search: string;
  defectFilter: string;
  lotFilter: string;
  yieldMin: number | null;
  yieldMax: number | null;
  confidenceMin: number | null;
  sortKey: SortKey;
  sortAsc: boolean;
}

export interface Classification {
  defect_type?: string;
  confidence?: number;
  assigned_lot?: string;
  lot?: string;
}

export interface YieldSummary {
  yield_percent?: number;
  good_dies?: number;
  fail_dies?: number;
  total_dies?: number;
}

export interface GridInfo {
  mode?: string;
  rows?: number;
  columns?: number;
  size?: number;
  /** Die pitch in agent (224) space. */
  pitch?: number;
  offset_x?: number;
  offset_y?: number;
}

export interface DieBBox {
  x0?: number;
  y0?: number;
  x1?: number;
  y1?: number;
}

export interface DieRecord {
  die_id?: string | number;
  id?: string | number;
  row?: number;
  column?: number;
  /** Die center in agent (224) space. */
  x?: number;
  y?: number;
  bbox?: DieBBox;
  status?: string;
}

export interface ClusterSummary {
  total_clusters?: number;
  total_clusters_detected?: number;
  displayed_clusters?: number;
  critical_clusters?: number;
  largest_cluster?: number;
  largest_cluster_fail_dies?: number;
  highest_severity?: string;
  highest_severity_score?: number;
}

export interface ClusterRecord {
  rank?: number;
  cluster_id?: string;
  /** Prefer fail_dies from Spatial agent; fail kept for legacy UI. */
  fail?: number;
  fail_dies?: number;
  good?: number;
  good_dies?: number;
  total?: number;
  total_dies?: number;
  fail_percent?: number;
  cluster_fail_percent?: number;
  contrib_percent?: number;
  contribution_percent?: number;
  density?: number;
  cluster_density?: number;
  severity_score?: number;
  severity?: string;
  /** Legacy UI tuple in agent 224 space. */
  bbox?: [number, number, number, number];
  centroid?: [number, number];
  /** Spatial agent fields (224 space). */
  bounding_box?: { x1?: number; y1?: number; x2?: number; y2?: number };
  center_x?: number;
  center_y?: number;
}

export interface ZoneRecord {
  zone?: string;
  good?: number;
  good_dies?: number;
  fail?: number;
  fail_dies?: number;
  total?: number;
  total_dies?: number;
  yield_percent?: number;
  fail_percent?: number;
  density?: number | string;
  defect_density?: string;
  rank?: number;
  status?: string;
  /** Legacy UI polygon in agent 224 space. */
  polygon?: [number, number][];
  /** Spatial agent zone boundary in agent 224 space. */
  zone_boundary?: Array<{ x: number; y: number } | [number, number]>;
}

export interface ZoneAnalysis {
  zones?: ZoneRecord[];
}

export interface SpatialAnalysis {
  cluster_summary?: ClusterSummary;
  clusters?: ClusterRecord[];
  /** Agent may return object `{ zones }` or a bare zone array. */
  zone_analysis?: ZoneAnalysis | ZoneRecord[];
}

export interface WaferGeometry {
  center_x?: number;
  center_y?: number;
  radius?: number;
}

export interface WaferImages {
  original?: string | null;
  overlay?: string | null;
  density?: string | null;
  /** Grad-CAM blended over original (when available). */
  gradcam?: string | null;
  /** Raw Grad-CAM color map (Heatmap mode). */
  heatmap?: string | null;
}

export interface GradcamMeta {
  available?: boolean;
  /** False when the checkpoint head is untrained; attention is uncalibrated. */
  wafer_trained?: boolean;
  layer?: string | null;
  model?: string | null;
  prediction_class?: string | null;
  confidence?: number | null;
  message?: string | null;
}

export interface VisualizationPoint {
  x: number;
  y: number;
  weight: number;
  die_id?: string | number | null;
}

export interface VisualizationColorStop {
  at: number;
  color: string;
  label?: string;
}

export interface VisualizationDensity {
  type: "gaussian_kde";
  points: VisualizationPoint[];
  sigma: number;
  radius: number;
  floor: number;
  normalization: "max";
  mask: {
    type: "circle";
    center_x: number;
    center_y: number;
    radius: number;
  };
  color_stops: VisualizationColorStop[];
}

export interface VisualizationGradcam {
  available: boolean;
  layer?: string | null;
  alpha: number;
  interpolation: string;
  heatmap?: {
    width: number;
    height: number;
    values: number[];
  } | null;
}

export interface VisualizationData {
  version: number;
  coordinate_space: {
    width: number;
    height: number;
    units: string;
  };
  rendering: {
    preferred_canvas_size: number;
    device_pixel_ratio: boolean;
    layers: string[];
  };
  original: {
    type: "die_bins";
    good_status: string;
    fail_status: string;
    colors: Record<string, string>;
  };
  failure_overlay: {
    status: string;
    fill: string;
    alpha: number;
    alpha_range: [number, number];
    border: string;
    border_width_css_px: number;
    clip_to_wafer: boolean;
  };
  density: VisualizationDensity;
  gradcam: VisualizationGradcam;
}

export interface WaferAnalysisResult {
  wafer_id?: string;
  source_file?: string;
  assigned_lot?: string;
  lot?: string;
  classification?: Classification;
  yield_summary?: YieldSummary;
  grid_info?: GridInfo;
  wafer_geometry?: WaferGeometry;
  dies?: DieRecord[];
  visualization?: VisualizationData;
  /** Deprecated compatibility payload; live API now returns visualization JSON. */
  images?: WaferImages;
  spatial_analysis?: SpatialAnalysis | null;
  gradcam_meta?: GradcamMeta;
}

export const DEFAULT_FILTERS: WaferFilters = {
  search: "",
  defectFilter: "All",
  lotFilter: "All",
  yieldMin: null,
  yieldMax: null,
  confidenceMin: null,
  sortKey: "name",
  sortAsc: true,
};
