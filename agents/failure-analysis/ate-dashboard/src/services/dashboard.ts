import { api } from "@/services/api";
import type { AnalysisMetrics, DashboardCharts } from "@/stores/analysisStore";
import { emptyCharts } from "@/stores/analysisStore";

export type DashboardApiResponse = {
  execution_id: string;
  dataset_id?: string | null;
  upload_id?: string | null;
  status: string;
  progress?: number;
  metrics?: AnalysisMetrics | null;
  charts?: DashboardCharts | null;
  error?: string | null;
};

type SpatialCell = {
  x?: number | null;
  y?: number | null;
  intensity?: number;
  die_id?: string;
  wafer_id?: string;
  is_failing?: boolean;
  is_failing_die?: boolean;
  failure_density?: number;
  density?: number;
  failure_rate?: number;
  value?: number;
};

function num(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function categoryCount(payload: unknown): number {
  if (payload && typeof payload === "object" && "count" in payload) {
    return num((payload as { count?: unknown }).count);
  }
  return num(payload);
}

function appendSpatialCell(
  cells: DashboardCharts["die_heatmap"],
  cell: SpatialCell,
  idKey: "die_id" | "wafer_id",
) {
  if (cells.length >= 500) return;
  if (cell.x == null || cell.y == null) return;
  cells.push({
    x: num(cell.x),
    y: num(cell.y),
    intensity: num(
      cell.intensity ??
        cell.failure_density ??
        cell.density ??
        cell.failure_rate ??
        cell.value ??
        (cell.is_failing || cell.is_failing_die ? 1 : 0),
    ),
    die_id: idKey === "die_id" ? String(cell.die_id || "") : undefined,
    wafer_id: idKey === "wafer_id" ? String(cell.wafer_id || cell.die_id || "") : undefined,
  });
}

function parseDieHeatmapPayload(payload: unknown): DashboardCharts["die_heatmap"] {
  const cells: DashboardCharts["die_heatmap"] = [];
  if (!payload || typeof payload !== "object") return cells;

  const root = payload as Record<string, unknown>;
  const heatmap = root.heatmap ?? root.die_heatmap ?? root;
  if (Array.isArray(heatmap)) {
    for (const cell of heatmap) appendSpatialCell(cells, cell as SpatialCell, "die_id");
    return cells;
  }
  if (!heatmap || typeof heatmap !== "object") return cells;

  const nested = heatmap as Record<string, unknown>;
  const inner = nested.die_heatmap;
  if (inner && typeof inner === "object") {
    const buckets = inner as { passing_dies?: SpatialCell[]; failing_dies?: SpatialCell[] };
    for (const cell of [...(buckets.failing_dies || []), ...(buckets.passing_dies || [])]) {
      appendSpatialCell(cells, cell, "die_id");
    }
  }
  const grid = (nested.failure_density_map as { grid?: SpatialCell[] } | undefined)?.grid;
  for (const cell of grid || []) appendSpatialCell(cells, cell, "die_id");

  for (const profile of (root.die_profiles as SpatialCell[] | undefined) || []) {
    appendSpatialCell(cells, profile, "die_id");
  }
  for (const handoff of (root.spatial_ai_handoff as SpatialCell[] | undefined) || []) {
    appendSpatialCell(cells, handoff, "die_id");
  }

  return cells;
}

function parseWaferHeatmapPayload(payload: unknown): DashboardCharts["wafer_heatmap"] {
  const cells: DashboardCharts["wafer_heatmap"] = [];
  if (!payload || typeof payload !== "object") return cells;

  const root = payload as Record<string, unknown>;
  const spatial = root.spatial_map ?? root.dashboard_feed;
  if (Array.isArray(spatial)) {
    for (const cell of spatial) appendSpatialCell(cells, cell as SpatialCell, "wafer_id");
  }

  const heatmap = root.wafer_map ?? root.wafer_heatmap ?? root.heatmap;
  if (heatmap && typeof heatmap === "object") {
    const nested = heatmap as { wafer_maps?: Array<Record<string, unknown>> };
    for (const waferMap of nested.wafer_maps || []) {
      const waferId = String(waferMap.wafer_id || "");
      for (const cell of [
        ...((waferMap.fail_dies as SpatialCell[] | undefined) || []),
        ...((waferMap.pass_dies as SpatialCell[] | undefined) || []),
      ]) {
        appendSpatialCell(cells, { ...cell, wafer_id: cell.wafer_id || waferId }, "wafer_id");
      }
      for (const cell of (waferMap.density_grid as SpatialCell[] | undefined) || []) {
        appendSpatialCell(cells, { ...cell, wafer_id: waferId }, "wafer_id");
      }
    }
  }

  return cells;
}

function buildCategoriesFromPatterns(
  patterns: Array<{
    pattern_category?: string;
    pattern_name?: string;
    pattern_id?: string;
    failure_count?: number;
  }>,
): DashboardCharts["category_distribution"] {
  const counts = new Map<string, number>();
  for (const pattern of patterns) {
    const label =
      pattern.pattern_category || pattern.pattern_name || pattern.pattern_id || "unknown";
    counts.set(label, (counts.get(label) || 0) + num(pattern.failure_count || 1));
  }
  return [...counts.entries()]
    .filter(([, count]) => count > 0)
    .map(([category, count]) => ({ category, count }));
}

function buildCategoriesFromSummary(
  summary: Record<string, unknown> | null | undefined,
): DashboardCharts["category_distribution"] {
  if (!summary) return [];
  return Object.entries(summary)
    .map(([category, payload]) => ({ category, count: categoryCount(payload) }))
    .filter((row) => row.count > 0);
}

/** Normalize legacy metric keys from older pipeline runs. */
export function normalizeMetrics(raw: Record<string, unknown> | null | undefined): AnalysisMetrics | null {
  if (!raw) return null;
  return {
    imported_test_files: Number(raw.imported_test_files ?? raw.imported_files ?? 0),
    overall_failure_rate: Number(raw.overall_failure_rate ?? 0),
    ai_detection_accuracy: Number(raw.ai_detection_accuracy ?? 0),
    failing_test_patterns: Number(raw.failing_test_patterns ?? raw.failing_patterns ?? 0),
    die_failure_rate: Number(raw.die_failure_rate ?? 0),
    wafer_failure_rate: Number(raw.wafer_failure_rate ?? 0),
    lot_failure_rate: Number(raw.lot_failure_rate ?? 0),
    fault_categories: Number(raw.fault_categories ?? 0),
    root_cause_confidence: Number(raw.root_cause_confidence ?? 0),
    recurring_failures: Number(raw.recurring_failures ?? 0),
    failure_correlations: Number(raw.failure_correlations ?? 0),
    failure_reports: Number(raw.failure_reports ?? raw.reports_generated ?? 0),
    processing_time: Number(raw.processing_time ?? 0),
    total_tests: Number(raw.total_tests ?? 0),
    total_failed: Number(raw.total_failed ?? 0),
    total_passed: Number(raw.total_passed ?? 0),
  };
}

export function normalizeCharts(raw: Record<string, unknown> | null | undefined): DashboardCharts {
  if (!raw) return emptyCharts();
  const categories = ((raw.category_distribution as DashboardCharts["category_distribution"]) || [])
    .map((row) => ({ category: row.category, count: num(row.count) }))
    .filter((row) => row.count > 0);

  return {
    failure_trend: (raw.failure_trend as DashboardCharts["failure_trend"]) || [],
    failure_distribution: (raw.failure_distribution as DashboardCharts["failure_distribution"]) || [],
    category_distribution: categories,
    pass_vs_fail: (raw.pass_vs_fail as DashboardCharts["pass_vs_fail"]) || [],
    wafer_heatmap: (raw.wafer_heatmap as DashboardCharts["wafer_heatmap"]) || [],
    die_heatmap: (raw.die_heatmap as DashboardCharts["die_heatmap"]) || [],
    correlation_graph: (raw.correlation_graph as Record<string, unknown>) || {},
  };
}

export async function fetchAnalysisDashboard(
  executionId: string,
): Promise<DashboardApiResponse> {
  const { data } = await api.get<DashboardApiResponse>(
    `/evaluation/status/${executionId}`,
  );
  return {
    ...data,
    metrics: normalizeMetrics(data.metrics as Record<string, unknown> | undefined),
    charts: normalizeCharts(data.charts as Record<string, unknown> | undefined),
  };
}

async function findLegacyRunId(
  path: string,
  uploadId: string,
): Promise<string | null> {
  try {
    const { data } = await api.get<{ runs?: Array<{ run_id: string; upload_id?: string }> }>(
      path,
      { params: { limit: 50 } },
    );
    const match = (data.runs || []).find((run) => run.upload_id === uploadId);
    return match?.run_id || data.runs?.[0]?.run_id || null;
  } catch {
    return null;
  }
}

function cellsFromUploadRecords(records: Array<{ payload?: Record<string, unknown> }>) {
  const cells: DashboardCharts["die_heatmap"] = [];
  for (const row of records) {
    const payload = row.payload || {};
    const raw = (payload.raw_fields as Record<string, unknown> | undefined) || {};
    const x = num(
      payload.x ?? raw.DIE_X ?? raw.DIE_COL ?? raw.WAFER_X ?? raw.X1,
      NaN,
    );
    const y = num(
      payload.y ?? raw.DIE_Y ?? raw.DIE_ROW ?? raw.WAFER_Y ?? raw.Y1,
      NaN,
    );
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    cells.push({
      x,
      y,
      intensity: String(payload.pass_fail || "").toUpperCase() === "FAIL" ? 1 : 0,
      die_id: String(payload.die_id || raw.DIE_LABEL || ""),
    });
  }
  return cells;
}

export async function fetchSupplementaryCharts(uploadId: string): Promise<Partial<DashboardCharts>> {
  const charts: Partial<DashboardCharts> = {};
  try {
    const [trends, patterns, correlations, uploadRecords, dieHeatmap, waferMap, classificationStats] =
      await Promise.allSettled([
        api.get("/failure-rate/trends?limit=24"),
        api.get("/patterns", { params: { limit: 200 } }),
        api.get("/correlation", { params: { upload_id: uploadId, limit: 40 } }),
        api.get(`/uploads/${uploadId}/records`, { params: { limit: 500 } }),
        findLegacyRunId("/die", uploadId).then((runId) =>
          runId ? api.get("/die/heatmap", { params: { run_id: runId } }) : Promise.reject("no run"),
        ),
        findLegacyRunId("/wafer", uploadId).then((runId) =>
          runId ? api.get("/wafer/map", { params: { run_id: runId } }) : Promise.reject("no run"),
        ),
        findLegacyRunId("/classification", uploadId).then((runId) =>
          runId
            ? api.get("/classification/statistics", { params: { run_id: runId } })
            : Promise.reject("no run"),
        ),
      ]);

    if (trends.status === "fulfilled") {
      const rows = trends.value.data?.trends || [];
      charts.failure_trend = rows.map(
        (r: { aggregation_key?: string; current_percentage?: number; pattern_id?: string }) => ({
          label: String(r.aggregation_key || r.pattern_id || "—"),
          rate: Number(r.current_percentage || 0),
        }),
      );
    }

    const patternRows =
      patterns.status === "fulfilled" ? patterns.value.data?.patterns || [] : [];
    const analyses =
      patterns.status === "fulfilled" ? patterns.value.data?.analyses || [] : [];
    const uploadAnalysisIds = new Set(
      analyses.filter((row: { upload_id?: string }) => row.upload_id === uploadId).map(
        (row: { analysis_id: string }) => row.analysis_id,
      ),
    );
    const uploadPatterns =
      uploadAnalysisIds.size > 0
        ? patternRows.filter((p: { analysis_id?: string }) =>
            uploadAnalysisIds.has(p.analysis_id || ""),
          )
        : patternRows;
    const scopedPatterns = uploadPatterns.length ? uploadPatterns : patternRows;

    if (scopedPatterns.length) {
      charts.failure_distribution = scopedPatterns.slice(0, 20).map(
        (p: { pattern_name?: string; pattern_id?: string; failure_count?: number }) => ({
          name: String(p.pattern_name || p.pattern_id),
          count: Number(p.failure_count || 0),
        }),
      );
    }

    if (correlations.status === "fulfilled") {
      charts.correlation_graph = {
        correlations: correlations.value.data?.correlations || [],
      };
    }

    if (dieHeatmap.status === "fulfilled") {
      const parsed = parseDieHeatmapPayload(dieHeatmap.value.data?.heatmap);
      if (parsed.length) charts.die_heatmap = parsed;
    }
    if (!charts.die_heatmap?.length && uploadRecords.status === "fulfilled") {
      const fromRecords = cellsFromUploadRecords(uploadRecords.value.data?.records || []);
      if (fromRecords.length) charts.die_heatmap = fromRecords;
    }

    if (waferMap.status === "fulfilled") {
      const parsed = parseWaferHeatmapPayload(waferMap.value.data?.wafer_map);
      if (parsed.length) charts.wafer_heatmap = parsed;
    }
    if (!charts.wafer_heatmap?.length && charts.die_heatmap?.length) {
      charts.wafer_heatmap = charts.die_heatmap.map((cell) => ({
        x: cell.x,
        y: cell.y,
        intensity: cell.intensity,
        wafer_id: cell.die_id || "",
      }));
    }

    const summaryCategories =
      classificationStats.status === "fulfilled"
        ? buildCategoriesFromSummary(classificationStats.value.data?.category_summary)
        : [];
    charts.category_distribution =
      summaryCategories.length > 0
        ? summaryCategories
        : buildCategoriesFromPatterns(scopedPatterns);
  } catch {
    // Supplementary fetch is best-effort only.
  }
  return charts;
}

export function mergeDashboardCharts(
  base: DashboardCharts | null | undefined,
  extra: Partial<DashboardCharts>,
): DashboardCharts {
  const current = base || emptyCharts();
  return {
    failure_trend: current.failure_trend.length
      ? current.failure_trend
      : extra.failure_trend || [],
    failure_distribution: current.failure_distribution.length
      ? current.failure_distribution
      : extra.failure_distribution || [],
    category_distribution:
      current.category_distribution.filter((row) => row.count > 0).length > 0
        ? current.category_distribution.filter((row) => row.count > 0)
        : extra.category_distribution || [],
    pass_vs_fail: current.pass_vs_fail.length ? current.pass_vs_fail : extra.pass_vs_fail || [],
    wafer_heatmap: current.wafer_heatmap.length ? current.wafer_heatmap : extra.wafer_heatmap || [],
    die_heatmap: current.die_heatmap.length ? current.die_heatmap : extra.die_heatmap || [],
    correlation_graph:
      Object.keys(current.correlation_graph || {}).length > 0
        ? current.correlation_graph
        : extra.correlation_graph || {},
  };
}
