import {
  getDataset,
  getFaultPredictionStatistics,
  getUpload,
  listCorrelations,
  listFaultPredictions,
  listReports,
  listWaferAnalyses,
} from "@/lib/api";
import type { DieSummary, DetectedPattern } from "@/lib/api";
import { api } from "@/services/api";
import { fetchAnalysisDashboard } from "@/services/dashboard";

function recordsToDies(
  records: Array<{ payload?: Record<string, unknown> }>,
): DieSummary[] {
  return records
    .map((row, index) => {
      const payload = row.payload || {};
      const raw = (payload.raw_fields as Record<string, unknown> | undefined) || {};
      const x = Number(payload.x ?? raw.DIE_X ?? raw.DIE_COL ?? raw.WAFER_X ?? raw.X1);
      const y = Number(payload.y ?? raw.DIE_Y ?? raw.DIE_ROW ?? raw.WAFER_Y ?? raw.Y1);
      if (!Number.isFinite(x) || !Number.isFinite(y)) return null;

      const isFailing = String(payload.pass_fail || "").toUpperCase() === "FAIL";
      return {
        die_result_id: String(payload.record_key || `record-die-${index}`) + `@${x},${y}`,
        analysis_id: "",
        lot_id: String(payload.lot_id || raw.LOT_ID || ""),
        wafer_id: String(payload.wafer_id || raw.WAFER_ID || ""),
        die_id: String(payload.die_id || raw.DIE_LABEL || raw.DIE_ID || `D-${index}`),
        x,
        y,
        failure_count: isFailing ? 1 : 0,
        total_tests: 1,
        failure_density: isFailing ? 1 : 0,
        neighbor_failure_count: 0,
        is_isolated: true,
        is_failing: isFailing,
        health_score: isFailing ? 0.2 : 1,
        severity: isFailing ? "critical" : "normal",
        confidence_score: isFailing ? 0.8 : 1,
        trend_status: "stable",
        dominant_fault_type: "",
        dominant_pattern_id: "",
        engineering_recommendation: "",
      } satisfies DieSummary;
    })
    .filter((row): row is DieSummary => row !== null);
}

export async function fetchWorkbenchBundle(input: {
  executionId: string;
  uploadId?: string | null;
  datasetId?: string | null;
}) {
  const dashboard = await fetchAnalysisDashboard(input.executionId);
  const uploadId = input.uploadId || dashboard.upload_id;
  const datasetId = input.datasetId || dashboard.dataset_id;

  const [patternsRes, correlations, wafers, predictions, stats, dataset, upload, reports, uploadRecords] =
    await Promise.allSettled([
      api.get<{ patterns: DetectedPattern[]; analyses?: Array<{ analysis_id: string; upload_id?: string }> }>(
        "/patterns",
        { params: { limit: 200 } },
      ),
      uploadId
        ? listCorrelations({ upload_id: uploadId })
        : Promise.resolve({ correlations: [] }),
      listWaferAnalyses({}),
      listFaultPredictions({}),
      uploadId ? getFaultPredictionStatistics() : Promise.resolve(null),
      datasetId ? getDataset(datasetId) : Promise.resolve(null),
      uploadId ? getUpload(uploadId) : Promise.resolve(null),
      listReports({ limit: 10 }),
      uploadId
        ? api.get<{ records?: Array<{ payload?: Record<string, unknown> }> }>(
            `/uploads/${uploadId}/records`,
            { params: { limit: 500 } },
          )
        : Promise.resolve({ data: { records: [] } }),
    ]);

  const unwrap = <T,>(r: PromiseSettledResult<T>, fallback: T): T =>
    r.status === "fulfilled" ? r.value : fallback;

  const allPatterns =
    patternsRes.status === "fulfilled" ? patternsRes.value.data.patterns || [] : [];
  const analyses =
    patternsRes.status === "fulfilled" ? patternsRes.value.data.analyses || [] : [];
  const uploadAnalysisIds = new Set(
    analyses.filter((row) => !uploadId || row.upload_id === uploadId).map((row) => row.analysis_id),
  );
  const uploadPatterns =
    uploadAnalysisIds.size > 0
      ? allPatterns.filter((pattern) => uploadAnalysisIds.has(pattern.analysis_id))
      : allPatterns;

  const recordPayload =
    uploadRecords.status === "fulfilled" ? uploadRecords.value.data?.records || [] : [];
  const diesFromRecords = recordsToDies(recordPayload);
  const chartDies = dashboard.charts?.die_heatmap || [];
  const diesFromCharts: DieSummary[] = chartDies.map((point, index) => ({
    die_result_id: point.die_id
      ? `${point.die_id}@${point.x},${point.y}`
      : `chart-die-${index}`,
    analysis_id: "",
    lot_id: "",
    wafer_id: "",
    die_id: point.die_id || `D-${point.x}-${point.y}`,
    x: point.x,
    y: point.y,
    failure_count: Math.round(point.intensity * 10) || (point.intensity > 0 ? 1 : 0),
    total_tests: 1,
    failure_density: point.intensity,
    neighbor_failure_count: 0,
    is_isolated: false,
    is_failing: point.intensity > 0.35,
    health_score: 1 - point.intensity,
    severity: point.intensity > 0.5 ? "critical" : "normal",
    confidence_score: 1 - point.intensity,
    trend_status: "stable",
    dominant_fault_type: "",
    dominant_pattern_id: "",
    engineering_recommendation: "",
  }));

  return {
    dashboard,
    patterns: uploadPatterns.length ? uploadPatterns : allPatterns,
    correlations: unwrap(correlations, { correlations: [] }).correlations || [],
    dies: diesFromRecords.length ? diesFromRecords : diesFromCharts,
    wafers: unwrap(wafers, { wafers: [] }).wafers || [],
    predictions: unwrap(predictions, { predictions: [], runs: [] }).predictions || [],
    faultStats: unwrap(stats, null),
    dataset: unwrap(dataset, null),
    upload: unwrap(upload, null),
    reports: unwrap(reports, { reports: [] }).reports || [],
  };
}

export type WorkbenchBundle = Awaited<ReturnType<typeof fetchWorkbenchBundle>>;
