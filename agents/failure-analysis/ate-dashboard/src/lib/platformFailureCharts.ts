import type { AnalysisMetrics, DashboardCharts } from "@/stores/analysisStore";
import { emptyCharts } from "@/stores/analysisStore";

export type PlatformFailureReport = {
  yield?: {
    yield_pct?: number;
    pass_count?: number;
    fail_count?: number;
    other_count?: number;
    record_count?: number;
    wafer_stats?: Record<string, { fail?: number; pass?: number; other?: number; total?: number }>;
  };
  soft_bins?: Record<string, number>;
  hard_bins?: Record<string, number>;
  failure_clusters?: Array<{ signature?: string; count?: number }>;
  tester_analysis?: Record<string, number>;
  wafer_statistics?: Record<string, { fail?: number; pass?: number; other?: number; total?: number }>;
  pattern_analysis?: Record<string, number>;
  chain_analysis?: Record<string, number>;
};

export type PlatformFailureLatest = {
  execution_id?: string;
  dataset_id?: string;
  upload_id?: string;
  job_id?: string;
  status: string;
  metadata?: Record<string, unknown>;
  metrics?: AnalysisMetrics & { other_count?: number; yield_pct?: number };
  report?: PlatformFailureReport;
  kpis?: Record<string, number>;
};

function shortLabel(value: string, max = 28): string {
  if (value.length <= max) return value;
  return `${value.slice(0, 12)}…${value.slice(-10)}`;
}

/** Build all overview charts from a platform Failure report. */
export function buildChartsFromPlatformReport(
  report: PlatformFailureReport | undefined,
  metrics: AnalysisMetrics & { other_count?: number },
): DashboardCharts {
  const softBins = report?.soft_bins || {};
  const hardBins = report?.hard_bins || {};
  const testers = report?.tester_analysis || {};
  const patterns = report?.pattern_analysis || {};
  const chains = report?.chain_analysis || {};
  const clusters = report?.failure_clusters || [];
  const waferStats = report?.wafer_statistics || report?.yield?.wafer_stats || {};

  const categoryRows = [
    ...Object.entries(softBins).map(([category, count]) => ({
      category: `soft:${category}`,
      count: Number(count),
    })),
    ...Object.entries(hardBins).map(([category, count]) => ({
      category: `hard:${category}`,
      count: Number(count),
    })),
    ...Object.entries(testers).map(([category, count]) => ({
      category: shortLabel(String(category), 22),
      count: Number(count),
    })),
    ...Object.entries(patterns).map(([category, count]) => ({
      category: `pat:${shortLabel(String(category), 16)}`,
      count: Number(count),
    })),
  ]
    .filter((row) => row.count > 0)
    .slice(0, 16);

  const trendRows = Object.entries(waferStats).map(([label, stats]) => {
    const total = Math.max(Number(stats.total || 0), 1);
    const fail = Number(stats.fail || 0);
    return {
      label: shortLabel(label, 18),
      rate: Math.round((fail / total) * 10000) / 100,
      level: fail > 0 ? "fail" : "pass",
    };
  });
  if (!trendRows.length) {
    trendRows.push({
      label: "overall",
      rate: Number(metrics.overall_failure_rate || 0),
      level: "overall",
    });
  }

  const distribution =
    Array.isArray(clusters) && clusters.length
      ? clusters.slice(0, 12).map((c) => ({
          name: shortLabel(String(c.signature || "cluster"), 24),
          count: Number(c.count || 0),
        }))
      : Object.entries(testers).length
        ? Object.entries(testers).map(([name, count]) => ({
            name: shortLabel(name, 24),
            count: Number(count),
          }))
        : Object.entries(chains).map(([name, count]) => ({
            name: shortLabel(name, 24),
            count: Number(count),
          }));

  const passed = Number(metrics.total_passed || 0);
  const failed = Number(metrics.total_failed || 0);
  const other = Number(
    metrics.other_count ??
      Math.max(Number(metrics.total_tests || 0) - passed - failed, 0),
  );
  const passFail = [
    { name: "PASS", value: passed },
    { name: "FAIL", value: failed },
    ...(other > 0 ? [{ name: "OTHER", value: other }] : []),
  ].filter((row) => row.value > 0);

  const waferEntries = Object.entries(waferStats);
  const wafer_heatmap = waferEntries.map(([wafer_id, stats], i) => {
    const total = Math.max(Number(stats.total || 0), 1);
    const fail = Number(stats.fail || 0);
    return {
      x: (i % 5) + 1,
      y: Math.floor(i / 5) + 1,
      intensity: fail / total,
      wafer_id,
    };
  });
  const die_heatmap = waferEntries.map(([die_id, stats], i) => {
    const total = Math.max(Number(stats.total || 0), 1);
    const fail = Number(stats.fail || 0);
    return {
      x: (i % 4) + 1,
      y: Math.floor(i / 4) + 1,
      intensity: Math.max(fail / total, Number(stats.pass || 0) > 0 ? 0.15 : 0.05),
      die_id,
    };
  });

  const corrSource = Object.entries(testers).length
    ? Object.entries(testers)
    : Object.entries(chains).length
      ? Object.entries(chains)
      : Object.entries(patterns);
  const correlation_graph = {
    nodes: corrSource.slice(0, 16).map(([label, weight]) => ({
      label: shortLabel(label, 18),
      weight: Number(weight),
    })),
  };

  return {
    ...emptyCharts(),
    failure_trend: trendRows,
    failure_distribution: distribution,
    category_distribution: categoryRows.length
      ? categoryRows
      : distribution.map((d) => ({ category: d.name, count: d.count })),
    pass_vs_fail: passFail.length ? passFail : [{ name: "NONE", value: 1 }],
    wafer_heatmap,
    die_heatmap,
    correlation_graph,
  };
}
