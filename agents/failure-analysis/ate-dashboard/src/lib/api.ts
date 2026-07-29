import axios from "axios";
import { configureApiClient } from "@/lib/http";

export const api = axios.create({
  baseURL: "/api/v1",
  timeout: 600_000,
});

configureApiClient(api);

export interface UploadSummary {
  id: string;
  dataset_id?: string | null;
  original_filename: string;
  status: string;
  parser_id?: string | null;
  records_accepted?: number;
  records_quarantined?: number;
  integrity_pct?: number;
  file_size_bytes?: number;
  checksum_sha256?: string;
  created_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface UploadDetail {
  upload: UploadSummary & {
    stored_filename?: string;
    relative_path?: string | null;
    detected_mime?: string | null;
    validation_report?: Record<string, unknown>;
    processing_statistics?: Record<string, unknown>;
  };
  history: Array<{
    from_status?: string | null;
    to_status: string;
    message?: string | null;
    created_at?: string | null;
  }>;
  validation_results: Array<{
    severity: string;
    category: string;
    code: string;
    message: string;
    details?: Record<string, unknown>;
  }>;
}

export async function uploadFile(
  file: File,
  opts?: { asyncProcess?: boolean; relativePath?: string; datasetId?: string },
) {
  const form = new FormData();
  form.append("file", file);
  const params = new URLSearchParams();
  if (opts?.asyncProcess) params.set("async_process", "true");
  if (opts?.relativePath) params.set("relative_path", opts.relativePath);
  if (opts?.datasetId) params.set("dataset_id", opts.datasetId);
  const { data } = await api.post(`/uploads?${params}`, form);
  return data;
}

export async function uploadDatasetFolder(
  name: string,
  files: File[],
  relativePaths: string[],
  asyncProcess = true,
) {
  const form = new FormData();
  form.append("name", name);
  form.append("async_process", String(asyncProcess));
  files.forEach((f) => form.append("files", f));
  relativePaths.forEach((p) => form.append("relative_paths", p));
  const { data } = await api.post("/datasets/upload", form);
  return data;
}

export async function listUploads() {
  const { data } = await api.get<{ uploads: UploadSummary[] }>("/uploads?limit=100");
  return data;
}

export async function getUpload(id: string) {
  const { data } = await api.get<UploadDetail>(`/uploads/${id}`);
  return data;
}

export async function listDatasets() {
  const { data } = await api.get("/datasets");
  return data;
}

export async function getDataset(datasetId: string) {
  const { data } = await api.get(`/datasets/${datasetId}`);
  return data;
}

export async function getIngestionStats() {
  const { data } = await api.get("/ingestion/statistics");
  return data;
}

export async function scanServerDataset(name: string, root?: string) {
  const { data } = await api.post("/datasets/scan", { name, root });
  return data;
}

export async function getNormalizedRecords(uploadId: string, limit = 50) {
  const { data } = await api.get(`/uploads/${uploadId}/records?limit=${limit}`);
  return data;
}

export interface DetectedPattern {
  id: string;
  analysis_id: string;
  dataset_id?: string | null;
  pattern_id: string;
  pattern_name: string;
  pattern_category: string;
  pattern_frequency: number;
  confidence: number;
  detection_method: string;
  severity_level: string;
  failure_count: number;
  affected_device_count: number;
  affected_die_count: number;
  affected_wafer_count: number;
  affected_lot_count: number;
  created_at?: string | null;
}

export interface PatternHistory {
  id: string;
  execution_id: string;
  dataset_id?: string | null;
  upload_id?: string | null;
  status: string;
  rule_set_version: string;
  pattern_count: number;
  source_record_count: number;
  processing_ms: number;
  confidence_distribution: Record<string, number>;
  benchmark_metrics: Record<string, number | null>;
  errors: string[];
  warnings: string[];
  created_at?: string | null;
  completed_at?: string | null;
}

export async function detectPatterns(input: {
  dataset_id?: string;
  upload_id?: string;
  async_execution?: boolean;
  incremental?: boolean;
  confidence_threshold?: number;
  expected_pattern_ids?: string[];
}) {
  const { data } = await api.post("/patterns/detect", input);
  return data;
}

export async function listPatterns(params?: {
  search?: string;
  category?: string;
  severity?: string;
}) {
  const { data } = await api.get<{ patterns: DetectedPattern[] }>("/patterns", {
    params: { ...params, limit: 200 },
  });
  return data;
}

export async function getPattern(id: string) {
  const { data } = await api.get(`/patterns/${id}`);
  return data;
}

export async function getPatternStatistics() {
  const { data } = await api.get("/patterns/statistics");
  return data;
}

export async function getPatternHistory() {
  const { data } = await api.get<{ history: PatternHistory[] }>("/patterns/history?limit=100");
  return data;
}

export interface FailureRateMetric {
  id: string;
  computation_id: string;
  pattern_id: string;
  aggregation_level: string;
  aggregation_key: string;
  total_tests: number;
  pass_count: number;
  fail_count: number;
  failure_percentage: number;
  failure_density: number;
  pattern_frequency: number;
  moving_average?: number | null;
  baseline_percentage?: number | null;
  historical_delta?: number | null;
  trend_status: string;
  threshold_status: string;
  severity_level: string;
  computed_at?: string | null;
}

export interface FailureTrend {
  id: string;
  computation_id: string;
  pattern_id: string;
  aggregation_level: string;
  aggregation_key: string;
  trend_direction: string;
  current_percentage: number;
  moving_average?: number | null;
  baseline_percentage?: number | null;
  absolute_change?: number | null;
  relative_change?: number | null;
  abnormal_increase: boolean;
  created_at?: string | null;
}

export async function computeFailureRates(input: {
  dataset_id?: string;
  upload_id?: string;
  detection_execution_id?: string;
  async_execution?: boolean;
  window_size?: number;
}) {
  const { data } = await api.post("/failure-rate/compute", input);
  return data;
}

export async function listFailureRates(params?: {
  pattern_id?: string;
  aggregation_level?: string;
  computation_id?: string;
}) {
  const { data } = await api.get<{ metrics: FailureRateMetric[] }>("/failure-rate", {
    params: { ...params, limit: 500 },
  });
  return data;
}

export async function getPatternFailureRates(patternId: string) {
  const { data } = await api.get(`/failure-rate/${encodeURIComponent(patternId)}`);
  return data;
}

export async function getFailureRateTrends() {
  const { data } = await api.get<{ trends: FailureTrend[] }>("/failure-rate/trends?limit=300");
  return data;
}

export async function getFailureRateStatistics() {
  const { data } = await api.get("/failure-rate/statistics");
  return data;
}

export async function getFailureRateHistory() {
  const { data } = await api.get("/failure-rate/history?limit=100");
  return data;
}

export interface RecurrenceMetric {
  recurrence_id: string;
  analysis_id: string;
  pattern_id: string;
  pattern_name: string;
  fault_type: string;
  recurrence_count: number;
  recurrence_frequency: number;
  recurrence_percentage: number;
  confidence_score: number;
  severity: string;
  trend_direction: string;
  first_occurrence: string;
  latest_occurrence: string;
  historical_frequency: number;
  hotspot_location: Record<string, unknown>;
  engineering_recommendation: string;
  similarity_group?: string | null;
  created_at?: string | null;
}

export interface RecurrenceTrend {
  id: string;
  recurrence_id: string;
  analysis_id: string;
  pattern_id: string;
  trend_direction: string;
  current_frequency: number;
  historical_frequency: number;
  absolute_change: number;
  relative_change?: number | null;
  newly_emerging: boolean;
  time_series: Array<{
    execution_id: string;
    frequency: number;
    is_current: boolean;
  }>;
  created_at?: string | null;
}

export interface RecurrenceHotspot {
  hotspot_id: string;
  recurrence_id: string;
  analysis_id: string;
  pattern_id: string;
  lot_id: string;
  wafer_id: string;
  x?: number | null;
  y?: number | null;
  radius: number;
  occurrence_count: number;
  density: number;
  confidence_score: number;
  severity: string;
  coordinates: Array<{
    x: number;
    y: number;
    lot_id: string;
    wafer_id: string;
    source_id: string;
  }>;
  created_at?: string | null;
}

export async function analyzeRecurrence(input: {
  dataset_id?: string;
  upload_id?: string;
  detection_execution_id?: string;
  computation_id?: string;
  async_execution?: boolean;
  incremental?: boolean;
  historical_window?: number;
  similarity_threshold?: number;
}) {
  const { data } = await api.post("/recurrence/analyze", input);
  return data;
}

export async function listRecurrences(params?: {
  pattern_id?: string;
  fault_type?: string;
  severity?: string;
  trend?: string;
  analysis_id?: string;
}) {
  const { data } = await api.get<{ recurrences: RecurrenceMetric[] }>("/recurrence", {
    params: { ...params, limit: 500 },
  });
  return data;
}

export async function getRecurrence(id: string) {
  const { data } = await api.get(`/recurrence/${encodeURIComponent(id)}`);
  return data;
}

export async function getRecurrenceTrends() {
  const { data } = await api.get<{ trends: RecurrenceTrend[] }>(
    "/recurrence/trends?limit=300",
  );
  return data;
}

export async function getRecurrenceHotspots() {
  const { data } = await api.get<{ hotspots: RecurrenceHotspot[] }>(
    "/recurrence/hotspots?limit=300",
  );
  return data;
}

export async function getRecurrenceHistory() {
  const { data } = await api.get("/recurrence/history?limit=100");
  return data;
}

export async function getRecurrenceStatistics() {
  const { data } = await api.get("/recurrence/statistics");
  return data;
}

export interface CorrelationMetric {
  correlation_id: string;
  analysis_id: string;
  pattern_id: string;
  fault_type: string;
  correlated_failures: number;
  correlation_coefficient: number;
  correlation_strength: string;
  confidence_score: number;
  p_value?: number | null;
  sample_size: number;
  severity: string;
  trend_status: string;
  hotspot_location: {
    lot_id?: string;
    wafer_id?: string;
    x?: number;
    y?: number;
    point_count?: number;
    coordinates?: Array<{ x: number; y: number; lot_id: string; wafer_id: string }>;
  };
  engineering_recommendation: string;
  correlation_timestamp?: string | null;
}

export interface CorrelationTrend {
  correlation_id: string;
  analysis_id: string;
  pattern_id: string;
  fault_type: string;
  trend_status: string;
  current_coefficient: number;
  historical_coefficient: number;
  absolute_change: number;
  time_series: Array<{
    execution_id: string;
    coefficient: number;
    p_value: number;
    sample_size: number;
  }>;
  created_at?: string | null;
}

export async function analyzeCorrelation(input: {
  dataset_id?: string;
  upload_id?: string;
  recurrence_analysis_id?: string;
  coefficient_threshold?: number;
  confidence_threshold?: number;
  significance_level?: number;
  historical_window?: number;
  async_execution?: boolean;
  incremental?: boolean;
}) {
  const { data } = await api.post("/correlation/analyze", input);
  return data;
}

export async function listCorrelations(params?: {
  pattern_id?: string;
  fault_type?: string;
  strength?: string;
  severity?: string;
  trend?: string;
  analysis_id?: string;
}) {
  const { data } = await api.get<{ correlations: CorrelationMetric[] }>("/correlation", {
    params: { ...params, limit: 500 },
  });
  return data;
}

export async function getCorrelation(id: string) {
  const { data } = await api.get(`/correlation/${encodeURIComponent(id)}`);
  return data;
}

export async function getCorrelationTrends() {
  const { data } = await api.get<{ trends: CorrelationTrend[] }>(
    "/correlation/trends?limit=300",
  );
  return data;
}

export async function getCorrelationHistory() {
  const { data } = await api.get("/correlation/history?limit=100");
  return data;
}

export async function getCorrelationStatistics() {
  const { data } = await api.get("/correlation/statistics");
  return data;
}

export interface DieSummary {
  die_result_id: string;
  analysis_id: string;
  lot_id: string;
  wafer_id: string;
  die_id: string;
  x?: number | null;
  y?: number | null;
  failure_count: number;
  total_tests: number;
  failure_density: number;
  neighbor_failure_count: number;
  is_isolated: boolean;
  is_failing: boolean;
  health_score: number;
  severity: string;
  confidence_score: number;
  trend_status: string;
  dominant_fault_type: string;
  dominant_pattern_id: string;
  hotspot_id?: string | null;
  cluster_id?: string | null;
  engineering_recommendation: string;
  analyzed_at?: string | null;
}

export interface DieHotspot {
  hotspot_id: string;
  analysis_id: string;
  lot_id: string;
  wafer_id: string;
  center_x: number;
  center_y: number;
  radius: number;
  die_count: number;
  failure_count: number;
  density: number;
  severity: string;
  confidence_score: number;
  member_die_ids: string[];
  coordinates: Array<{
    die_id: string;
    x: number;
    y: number;
    failure_count: number;
  }>;
  created_at?: string | null;
}

export interface DieCluster {
  cluster_id: string;
  analysis_id: string;
  lot_id: string;
  wafer_id: string;
  algorithm: string;
  die_count: number;
  failure_count: number;
  density: number;
  centroid_x: number;
  centroid_y: number;
  severity: string;
  member_die_ids: string[];
  coordinates: Array<{
    die_id: string;
    x: number;
    y: number;
    failure_count: number;
  }>;
  created_at?: string | null;
}

export interface DieDetail {
  die: DieSummary;
  traceability: Record<string, unknown>;
  engineering_recommendations: Array<{
    recommendation_id: string;
    recommendation_code: string;
    priority: string;
    action: string;
    rationale: string;
    evidence?: Record<string, unknown>;
  }>;
  downstream_export: Record<string, unknown>;
}

export interface DieStatistics {
  execution_id?: string;
  total_dies: number;
  failing_dies: number;
  isolated_failures: number;
  hotspot_count: number;
  cluster_count: number;
  mean_failure_density: number;
  mean_health_score: number;
  mean_confidence: number;
  benchmark_metrics?: Record<string, number | boolean | null>;
  upstream_execution_ids?: Record<string, unknown>;
  statistics?: Record<string, unknown>;
}

export async function analyzeDieLevel(input: {
  dataset_id?: string;
  upload_id?: string;
  detection_execution_id?: string;
  computation_id?: string;
  recurrence_analysis_id?: string;
  correlation_analysis_id?: string;
  historical_window?: number;
  hotspot_density_threshold?: number;
  cluster_eps?: number;
  confidence_threshold?: number;
  incremental?: boolean;
  async_execution?: boolean;
  legacy?: boolean;
}) {
  const { data } = await api.post("/die-analysis/analyze", input);
  return data;
}

export async function listDieAnalyses(params?: {
  lot_id?: string;
  wafer_id?: string;
  die_id?: string;
  severity?: string;
  is_failing?: boolean;
  analysis_id?: string;
}) {
  const { data } = await api.get<{ dies: DieSummary[]; runs?: unknown[] }>("/die-analysis", {
    params: { ...params, limit: 500 },
  });
  // Assign synthetic map coordinates when STIL/log records lack die_x/die_y,
  // so Die Map still renders instead of looking "empty/broken".
  const dies = (data.dies || []).map((die, index) => {
    if (typeof die.x === "number" && typeof die.y === "number") return die;
    const ring = Math.floor(Math.sqrt(index + 1));
    const angle = (index * 2.399963) % (Math.PI * 2);
    return {
      ...die,
      x: Math.round(Math.cos(angle) * (ring + 1) * 10),
      y: Math.round(Math.sin(angle) * (ring + 1) * 10),
    };
  });
  return { ...data, dies };
}

export async function getDieDetail(dieResultId: string) {
  const { data } = await api.get<DieDetail>(
    `/die-analysis/${encodeURIComponent(dieResultId)}`,
  );
  return data;
}

export async function getDieHotspots(params?: { analysis_id?: string }) {
  const { data } = await api.get<{ hotspots: DieHotspot[] }>("/die-analysis/hotspots", {
    params: { ...params, limit: 300 },
  });
  return data;
}

export async function getDieClusters(params?: { analysis_id?: string }) {
  const { data } = await api.get<{ clusters: DieCluster[] }>("/die-analysis/clusters", {
    params: { ...params, limit: 300 },
  });
  return data;
}

export async function getDieStatistics() {
  const { data } = await api.get<DieStatistics>("/die-analysis/statistics");
  return data;
}

export interface WaferRadialDistribution {
  radial_bins: number;
  profile: number[];
  pattern?: string;
}

export interface WaferSummary {
  wafer_result_id: string;
  analysis_id: string;
  lot_id: string;
  wafer_id: string;
  total_dies: number;
  failing_dies: number;
  /** Alias for failing_dies in downstream exports */
  failed_dies?: number;
  yield_pct: number;
  /** Alias for yield_pct in dashboard views */
  yield_percentage?: number;
  failure_density: number;
  edge_failure_rate: number;
  center_failure_rate: number;
  health_score: number;
  severity: string;
  confidence_score: number;
  trend_status: string;
  hotspot_count?: number;
  engineering_recommendation: string;
  radial_distribution?: WaferRadialDistribution;
  analyzed_at?: string | null;
}

export interface WaferHotspot {
  hotspot_id: string;
  analysis_id: string;
  lot_id: string;
  wafer_id: string;
  center_x?: number | null;
  center_y?: number | null;
  radius: number;
  die_count: number;
  failure_count: number;
  density: number;
  severity: string;
  confidence_score: number;
  member_die_ids: string[];
  density_grid?: Array<{
    x: number;
    y: number;
    die_count: number;
    failure_count: number;
    density: number;
  }>;
  created_at?: string | null;
}

export interface WaferYieldMetric {
  wafer_result_id: string;
  analysis_id: string;
  lot_id: string;
  wafer_id: string;
  yield_pct: number;
  historical_yield_pct?: number | null;
  yield_delta?: number | null;
  trend_status: string;
  lot_yield_pct?: number | null;
  details?: Record<string, unknown>;
  created_at?: string | null;
}

export interface WaferDetail {
  wafer: WaferSummary;
  traceability: Record<string, unknown> & {
    radial_distribution?: WaferRadialDistribution;
  };
  engineering_recommendations: Array<{
    recommendation_id: string;
    recommendation_code: string;
    priority: string;
    action: string;
    rationale: string;
    evidence?: Record<string, unknown>;
  }>;
  downstream_export: Record<string, unknown>;
}

export interface WaferStatistics {
  execution_id?: string;
  total_wafers: number;
  failing_wafers: number;
  total_dies: number;
  failing_dies: number;
  overall_yield_pct: number;
  hotspot_count: number;
  mean_failure_density: number;
  mean_health_score: number;
  mean_confidence: number;
  benchmark_metrics?: Record<string, number | boolean | null>;
  upstream_execution_ids?: Record<string, unknown>;
  statistics?: Record<string, unknown>;
}

export function normalizeWaferSummary(row: WaferSummary): WaferSummary {
  return {
    ...row,
    failed_dies: row.failed_dies ?? row.failing_dies,
    yield_percentage: row.yield_percentage ?? row.yield_pct,
  };
}

export async function analyzeWaferLevel(input: {
  dataset_id?: string;
  upload_id?: string;
  detection_execution_id?: string;
  computation_id?: string;
  recurrence_analysis_id?: string;
  correlation_analysis_id?: string;
  die_analysis_id?: string;
  historical_window?: number;
  hotspot_density_threshold?: number;
  edge_radius_fraction?: number;
  confidence_threshold?: number;
  incremental?: boolean;
  async_execution?: boolean;
  legacy?: boolean;
}) {
  const { data } = await api.post("/wafer-analysis/analyze", input);
  return data;
}

export async function listWaferAnalyses(params?: {
  lot_id?: string;
  wafer_id?: string;
  severity?: string;
  analysis_id?: string;
}) {
  const { data } = await api.get<{ wafers: WaferSummary[]; runs?: unknown[] }>(
    "/wafer-analysis",
    { params: { ...params, limit: 500 } },
  );
  return {
    ...data,
    wafers: (data.wafers || []).map(normalizeWaferSummary),
  };
}

export async function getWaferDetail(waferResultId: string) {
  const { data } = await api.get<WaferDetail>(
    `/wafer-analysis/${encodeURIComponent(waferResultId)}`,
  );
  return {
    ...data,
    wafer: normalizeWaferSummary(data.wafer),
  };
}

export async function getWaferHotspots(params?: { analysis_id?: string }) {
  const { data } = await api.get<{ hotspots: WaferHotspot[] }>(
    "/wafer-analysis/hotspots",
    { params: { ...params, limit: 300 } },
  );
  return data;
}

export async function getWaferStatistics() {
  const { data } = await api.get<WaferStatistics>("/wafer-analysis/statistics");
  return data;
}

export async function getWaferYield(params?: { analysis_id?: string }) {
  const { data } = await api.get<{ yield_metrics: WaferYieldMetric[] }>(
    "/wafer-analysis/yield",
    { params: { ...params, limit: 300 } },
  );
  return data;
}

export interface AlternativeFaultType {
  fault_type: string;
  probability: number;
  rank: number;
}

export interface SupportingEvidence {
  source: string;
  label: string;
  weight: number;
  value?: string | number | null;
  details?: Record<string, unknown>;
}

export interface FaultPredictionSummary {
  prediction_id: string;
  pattern_id: string;
  predicted_fault_type: string;
  alternative_fault_types: AlternativeFaultType[];
  confidence_score: number;
  prediction_probability: number;
  supporting_evidence: SupportingEvidence[];
  engineering_explanation: string;
  recommended_investigation_steps: string[];
  /** Backend production serializer alias */
  investigation_steps?: Array<string | { action?: string; step_code?: string; [key: string]: unknown }>;
  model_version: string;
  prediction_timestamp?: string | null;
  /** Backend production serializer alias */
  predicted_at?: string | null;
}

function normalizeInvestigationSteps(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((step) => {
      if (typeof step === "string") return step.trim();
      if (step && typeof step === "object") {
        const row = step as { action?: string; step_code?: string; description?: string };
        return String(row.action || row.description || row.step_code || "").trim();
      }
      return "";
    })
    .filter(Boolean);
}

function normalizeEvidenceList(raw: unknown): SupportingEvidence[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item, index) => {
    const fallbackWeight = Math.max(0.05, 1 - index * 0.08);
    if (typeof item === "string") {
      return { source: "engine", label: item.trim() || "Unknown", weight: fallbackWeight };
    }
    if (item && typeof item === "object") {
      const row = item as Partial<SupportingEvidence> & Record<string, unknown>;
      const label =
        (typeof row.label === "string" && row.label) ||
        (typeof row.source === "string" && row.source) ||
        (typeof row.value === "string" && row.value) ||
        "Unknown";
      const weight = Number(row.weight);
      return {
        source: typeof row.source === "string" && row.source ? row.source : "unknown",
        label: String(label).trim() || "Unknown",
        weight: Number.isFinite(weight) && weight >= 0 ? weight : fallbackWeight,
        value: row.value as string | number | null | undefined,
        details: row.details as Record<string, unknown> | undefined,
      };
    }
    return { source: "unknown", label: "Unknown", weight: fallbackWeight };
  });
}

function normalizeFaultPrediction(row: Record<string, unknown>): FaultPredictionSummary {
  const alternatives = Array.isArray(row.alternative_fault_types)
    ? (row.alternative_fault_types as AlternativeFaultType[])
    : [];
  const steps = normalizeInvestigationSteps(
    row.recommended_investigation_steps ?? row.investigation_steps,
  );
  return {
    prediction_id: String(row.prediction_id || ""),
    pattern_id: String(row.pattern_id || ""),
    predicted_fault_type: String(row.predicted_fault_type || "UNKNOWN"),
    alternative_fault_types: alternatives,
    confidence_score: Number(row.confidence_score || 0),
    prediction_probability: Number(row.prediction_probability || 0),
    supporting_evidence: normalizeEvidenceList(row.supporting_evidence),
    engineering_explanation: String(row.engineering_explanation || ""),
    recommended_investigation_steps: steps,
    investigation_steps: row.investigation_steps as FaultPredictionSummary["investigation_steps"],
    model_version: String(row.model_version || ""),
    prediction_timestamp:
      (row.prediction_timestamp as string | null | undefined) ??
      (row.predicted_at as string | null | undefined) ??
      null,
    predicted_at: (row.predicted_at as string | null | undefined) ?? null,
  };
}

export interface FaultPredictionDetail {
  prediction: FaultPredictionSummary;
  traceability?: Record<string, unknown>;
  upstream_execution_ids?: Record<string, unknown>;
  engineering_recommendations?: Array<{
    recommendation_id: string;
    recommendation_code: string;
    priority: string;
    action: string;
    rationale: string;
    evidence?: Record<string, unknown>;
  }>;
}

export interface FaultPredictionHistoryEntry {
  id: string;
  execution_id: string;
  dataset_id?: string | null;
  upload_id?: string | null;
  status: string;
  model_version: string;
  prediction_count: number;
  source_record_count?: number;
  processing_ms: number;
  confidence_distribution?: Record<string, number>;
  benchmark_metrics: Record<string, number | null>;
  errors: string[];
  warnings: string[];
  created_at?: string | null;
  completed_at?: string | null;
}

export interface FaultPredictionStatistics {
  execution_id?: string;
  total_predictions: number;
  mean_confidence: number;
  mean_probability: number;
  unique_fault_types: number;
  top_predicted_fault_type?: string | null;
  benchmark_metrics?: Record<string, number | boolean | null>;
  upstream_execution_ids?: Record<string, unknown>;
  statistics?: Record<string, unknown>;
}

export async function predictFaultTypes(input: {
  dataset_id?: string;
  upload_id?: string;
  detection_execution_id?: string;
  computation_id?: string;
  recurrence_analysis_id?: string;
  correlation_analysis_id?: string;
  die_analysis_id?: string;
  wafer_analysis_id?: string;
  pattern_id?: string;
  confidence_threshold?: number;
  model_version?: string;
  incremental?: boolean;
  async_execution?: boolean;
  legacy?: boolean;
}) {
  const { data } = await api.post("/fault-prediction/predict", input);
  return data;
}

export interface FaultPredictionRun {
  run_id: string;
  upload_id?: string | null;
  total_predictions?: number;
  average_confidence?: number;
  high_confidence_count?: number;
  ml_model_trained?: boolean;
  processing_ms?: number;
  created_at?: string | null;
}

export async function listFaultPredictions(params?: {
  pattern_id?: string;
  predicted_fault_type?: string;
  model_version?: string;
  search?: string;
}) {
  const { data } = await api.get<{
    predictions: Record<string, unknown>[];
    runs?: FaultPredictionRun[];
  }>("/fault-prediction", { params: { ...params, limit: 500 } });
  return {
    predictions: (data.predictions || []).map((row) =>
      normalizeFaultPrediction(row as Record<string, unknown>),
    ),
    runs: data.runs || [],
  };
}

export async function getFaultPrediction(id: string) {
  const { data } = await api.get<{
    prediction: Record<string, unknown>;
    traceability?: Record<string, unknown>;
    upstream_execution_ids?: Record<string, unknown>;
    engineering_recommendations?: FaultPredictionDetail["engineering_recommendations"];
  }>(`/fault-prediction/${encodeURIComponent(id)}`);
  return {
    ...data,
    prediction: normalizeFaultPrediction(
      (data.prediction || {}) as Record<string, unknown>,
    ),
  } as FaultPredictionDetail;
}

export async function getFaultPredictionHistory() {
  const { data } = await api.get<{ history: FaultPredictionHistoryEntry[] }>(
    "/fault-prediction/history?limit=100",
  );
  return data;
}

export async function getFaultPredictionStatistics() {
  const { data } = await api.get<FaultPredictionStatistics>(
    "/fault-prediction/statistics",
  );
  return data;
}

export async function submitFaultPredictionFeedback(input: {
  prediction_id: string;
  actual_fault_type?: string;
  is_correct?: boolean;
  feedback_notes?: string;
  validated_by?: string;
}) {
  const { data } = await api.post("/fault-prediction/feedback", input);
  return data;
}

export interface ReportExecutiveSummary {
  title?: string;
  overview?: string;
  total_failures?: number;
  impacted_wafers?: number;
  top_fault_type?: string;
  quality_risk_score?: number;
}

export interface ReportEngineeringSummary {
  pattern_count?: number;
  recurring_count?: number;
  strong_correlations?: number;
  failing_die_count?: number;
  failing_wafer_count?: number;
  top_recommendations?: string[];
}

export interface ReportBenchmarkMetrics {
  processing_latency_ms?: number;
  throughput_records_per_minute?: number;
  confidence_mean?: number;
  top1_accuracy?: number;
  sla_met?: boolean;
  [key: string]: number | boolean | string | null | undefined;
}

export interface ReportPredictionSummary {
  top_fault_type?: string;
  confidence?: number;
  probability?: number;
  alternatives?: Array<{ fault_type: string; probability: number }>;
}

export interface ReportRecommendation {
  id?: string;
  priority?: string;
  area?: string;
  action: string;
  rationale?: string;
  owner?: string;
}

export interface ReportChartSeries {
  key: string;
  title: string;
  points: Array<{ label: string; value: number }>;
}

export interface ReportArtifact {
  report_id: string;
  report_name?: string;
  template_id?: string | null;
  status?: string;
  generated_at?: string | null;
  created_at?: string | null;
  dataset_id?: string | null;
  upload_id?: string | null;
  legacy?: boolean;
  total_dies?: number;
  failing_dies?: number;
  overall_yield_pct?: number;
  processing_ms?: number;
  /** Legacy FA report payload keys (pre FA-FR-010 summary shape). */
  executive_report?: Record<string, unknown>;
  engineering_report?: Record<string, unknown>;
  root_cause_report?: Record<string, unknown>;
  dashboard_dataset?: Record<string, unknown>;
  executive_summary?: ReportExecutiveSummary;
  engineering_summary?: ReportEngineeringSummary;
  benchmark_metrics?: ReportBenchmarkMetrics;
  prediction_summary?: ReportPredictionSummary;
  recommendations?: ReportRecommendation[];
  chart_payload?: Record<string, unknown>;
  /** Flattened chart series for the in-app interactive chart panel. */
  chart_series?: ReportChartSeries[];
  sections?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

/** Map legacy executive_report / engineering_report into FA-FR-010 UI fields. */
export function normalizeReportArtifact(raw: ReportArtifact): ReportArtifact {
  const execLegacy = (raw.executive_report || {}) as Record<string, unknown>;
  const engLegacy = (raw.engineering_report || {}) as Record<string, unknown>;

  const totalFailures =
    raw.executive_summary?.total_failures ??
    num(execLegacy.total_failing_dies) ??
    num(raw.failing_dies) ??
    0;

  const topFault =
    raw.executive_summary?.top_fault_type ||
    raw.prediction_summary?.top_fault_type ||
    str(execLegacy.top_fault_category) ||
    str(execLegacy.top_predicted_root_cause) ||
    undefined;

  const executive_summary: ReportExecutiveSummary = {
    title: raw.executive_summary?.title,
    overview:
      raw.executive_summary?.overview ||
      str(execLegacy.headline) ||
      (raw.report_name ? String(raw.report_name) : undefined),
    total_failures: totalFailures,
    impacted_wafers:
      raw.executive_summary?.impacted_wafers ??
      num(engLegacy.wafer_profiles_analyzed) ??
      0,
    top_fault_type: topFault,
    quality_risk_score:
      raw.executive_summary?.quality_risk_score ??
      (num(execLegacy.overall_die_failure_rate) != null
        ? Number(execLegacy.overall_die_failure_rate) * 100
        : num(execLegacy.high_risk_pattern_count) ?? 0),
  };

  const engineering_summary: ReportEngineeringSummary = {
    pattern_count:
      raw.engineering_summary?.pattern_count ??
      num(engLegacy.total_failing_patterns) ??
      num(engLegacy.classified_fault_count) ??
      0,
    recurring_count:
      raw.engineering_summary?.recurring_count ??
      num(engLegacy.recurring_pattern_count) ??
      num(execLegacy.recurring_pattern_count) ??
      0,
    strong_correlations:
      raw.engineering_summary?.strong_correlations ??
      num(engLegacy.correlation_report_size) ??
      0,
    failing_die_count:
      raw.engineering_summary?.failing_die_count ??
      num(engLegacy.die_profiles_analyzed) ??
      totalFailures,
    failing_wafer_count:
      raw.engineering_summary?.failing_wafer_count ??
      num(engLegacy.wafer_profiles_analyzed) ??
      0,
    top_recommendations: raw.engineering_summary?.top_recommendations,
  };

  const conf =
    raw.prediction_summary?.confidence ??
    raw.prediction_summary?.probability ??
    num(execLegacy.top_prediction_confidence);

  const prediction_summary: ReportPredictionSummary = {
    top_fault_type:
      raw.prediction_summary?.top_fault_type ||
      topFault ||
      str(execLegacy.top_predicted_root_cause),
    confidence: conf,
    probability: raw.prediction_summary?.probability ?? conf,
    alternatives: raw.prediction_summary?.alternatives,
  };

  return {
    ...raw,
    executive_summary,
    engineering_summary,
    prediction_summary,
    recommendations: raw.recommendations?.length
      ? raw.recommendations
      : legacyRecommendations(raw),
    chart_series: raw.chart_series?.length ? raw.chart_series : legacyChartSeries(raw),
    benchmark_metrics: {
      processing_latency_ms:
        raw.benchmark_metrics?.processing_latency_ms ?? num(raw.processing_ms) ?? undefined,
      ...(raw.benchmark_metrics || {}),
    },
  };
}

/**
 * Legacy reports keep actionable items in dashboard_dataset.tables.corrective_actions
 * and in the per-prediction investigation steps of root_cause_report.
 */
function legacyRecommendations(raw: ReportArtifact): ReportRecommendation[] {
  const out: ReportRecommendation[] = [];

  const tables = record(record(raw.dashboard_dataset)?.tables);
  const corrective = Array.isArray(tables?.corrective_actions)
    ? (tables!.corrective_actions as unknown[])
    : [];
  corrective.forEach((entry, index) => {
    const row = record(entry);
    const action = str(row?.action);
    if (!action) return;
    out.push({
      id: `corrective-${index}`,
      action,
      priority: str(row?.priority)?.toLowerCase(),
      area: str(row?.source),
      rationale: str(row?.rationale),
    });
  });

  const predictions = Array.isArray(record(raw.root_cause_report)?.predictions)
    ? (record(raw.root_cause_report)!.predictions as unknown[])
    : [];
  predictions.slice(0, 3).forEach((entry, predictionIndex) => {
    const prediction = record(entry);
    const faultType = str(prediction?.predicted_fault_type);
    const steps = Array.isArray(prediction?.investigation_steps)
      ? (prediction!.investigation_steps as unknown[])
      : [];
    steps.slice(0, 4).forEach((stepEntry, stepIndex) => {
      const step = record(stepEntry);
      const action = str(step?.action) || str(step?.step) || str(stepEntry);
      if (!action) return;
      out.push({
        id: `investigation-${predictionIndex}-${stepIndex}`,
        action,
        priority: str(step?.priority)?.toLowerCase() || "normal",
        area: faultType || "root cause",
        rationale: str(step?.rationale) || str(step?.detail),
      });
    });
  });

  const highlights = record(record(raw.engineering_report)?.technical_highlights);
  const observations = Array.isArray(highlights?.engineering_observations)
    ? (highlights!.engineering_observations as unknown[])
    : [];
  observations.slice(0, 3).forEach((entry, index) => {
    const action = str(entry) || str(record(entry)?.observation);
    if (!action) return;
    out.push({ id: `observation-${index}`, action, area: "engineering" });
  });

  return out;
}

/** Flatten legacy Plotly chart payloads into simple label/value series. */
function legacyChartSeries(raw: ReportArtifact): ReportChartSeries[] {
  const charts = record(record(raw.dashboard_dataset)?.charts);
  if (!charts) return [];
  const series: ReportChartSeries[] = [];
  for (const [key, value] of Object.entries(charts)) {
    const chart = record(value);
    const traces = Array.isArray(record(chart?.plotly)?.data)
      ? (record(chart!.plotly)!.data as unknown[])
      : [];
    const trace = record(traces[0]);
    const labels = Array.isArray(trace?.x) ? (trace!.x as unknown[]) : [];
    const values = Array.isArray(trace?.y) ? (trace!.y as unknown[]) : [];
    const points = labels
      .map((label, index) => ({
        label: String(label),
        value: num(values[index]) ?? 0,
      }))
      .filter((point) => point.label);
    if (!points.length) continue;
    series.push({
      key,
      title: str(chart?.title) || key.replaceAll("_", " "),
      points,
    });
  }
  return series;
}

function record(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function num(value: unknown): number | undefined {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "" && Number.isFinite(Number(value))) {
    return Number(value);
  }
  return undefined;
}

function str(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

export interface ReportTemplate {
  template_id: string;
  name: string;
  description?: string;
  category?: string;
  formats?: string[];
  default?: boolean;
}

export interface ReportHistoryEntry {
  id: string;
  report_id?: string;
  report_name?: string;
  template_id?: string | null;
  status: string;
  created_at?: string | null;
  completed_at?: string | null;
  created_by?: string | null;
  duration_ms?: number | null;
}

export interface GenerateReportInput {
  upload_id?: string;
  dataset_id?: string;
  template_id?: string;
  title?: string;
  include_sections?: string[];
  filters?: Record<string, unknown>;
  async_execution?: boolean;
  legacy?: boolean;
}

export interface ExportReportInput {
  report_id: string;
  format: "pdf" | "html" | "csv" | "xlsx" | "json";
  include_raw?: boolean;
}

export async function generateReport(input: GenerateReportInput) {
  const { data } = await api.post<ReportArtifact>("/reports/generate", input);
  return normalizeReportArtifact(data);
}

export async function listReports(params?: {
  status?: string;
  template_id?: string;
  search?: string;
  limit?: number;
}) {
  const { data } = await api.get<{ reports: ReportArtifact[] }>("/reports", {
    params: { limit: 100, ...params },
  });
  return {
    ...data,
    reports: (data.reports || []).map(normalizeReportArtifact),
  };
}

export async function getReport(id: string) {
  const { data } = await api.get<ReportArtifact>(`/reports/${encodeURIComponent(id)}`);
  return normalizeReportArtifact(data);
}

export async function getReportHistory(params?: { limit?: number }) {
  const { data } = await api.get<{ history: ReportHistoryEntry[] }>("/reports/history", {
    params: { limit: 100, ...params },
  });
  return data;
}

export async function getReportTemplates() {
  const { data } = await api.get<{ templates: ReportTemplate[] }>("/reports/templates");
  return data;
}

export async function exportReport(input: ExportReportInput) {
  const { data } = await api.post<{
    report_id: string;
    format: string;
    download_url?: string;
    content?: string;
    filename?: string;
  }>("/reports/export", input);
  return data;
}
