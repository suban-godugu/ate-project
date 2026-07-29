"use client";

import dynamic from "next/dynamic";
import { memo, Suspense } from "react";
import { LiveAnalysisMonitor } from "@/components/workbench/LiveAnalysisMonitor";
import { DatasetDetailsPanel } from "@/components/workbench/DatasetDetailsPanel";
import { LiveLogsPanel } from "@/components/workbench/LiveLogsPanel";
import { DashboardSnapshot } from "@/components/workbench/DashboardSnapshot";
import { ReportsExportPanel } from "@/components/workbench/ReportsExportPanel";
import { BenchmarkPanel } from "@/components/workbench/BenchmarkPanel";
import { PerformanceMetricsPanel } from "@/components/workbench/PerformanceMetricsPanel";
import { useWorkbenchData } from "@/hooks/useWorkbenchData";
import { useDashboard } from "@/hooks/useDashboard";
import { useAnalysisStore } from "@/stores/analysisStore";
import type { DieSummary } from "@/lib/api";
import type { DashboardCharts } from "@/stores/analysisStore";

const WorkbenchWaferHeatmap = dynamic(
  () =>
    import("@/components/workbench/WorkbenchWaferHeatmap").then((m) => m.WorkbenchWaferHeatmap),
  { ssr: false, loading: () => <PanelSkeleton label="Wafer Heatmap" /> },
);

const WorkbenchDieHeatmap = dynamic(
  () =>
    import("@/components/workbench/WorkbenchDieHeatmap").then((m) => m.WorkbenchDieHeatmap),
  { ssr: false, loading: () => <PanelSkeleton label="Die Heatmap" /> },
);

const FailureDistributionPanel = dynamic(
  () =>
    import("@/components/workbench/FailureDistributionPanel").then(
      (m) => m.FailureDistributionPanel,
    ),
  { ssr: false, loading: () => <PanelSkeleton label="Failure Distribution" /> },
);

const PatternAnalysisTable = dynamic(
  () =>
    import("@/components/workbench/PatternAnalysisTable").then((m) => m.PatternAnalysisTable),
  { ssr: false, loading: () => <PanelSkeleton label="Pattern Analysis" /> },
);

const CorrelationNetwork = dynamic(
  () =>
    import("@/components/workbench/CorrelationNetwork").then((m) => m.CorrelationNetwork),
  { ssr: false, loading: () => <PanelSkeleton label="Correlation Network" /> },
);

const RootCausePanel = dynamic(
  () => import("@/components/workbench/RootCausePanel").then((m) => m.RootCausePanel),
  { ssr: false, loading: () => <PanelSkeleton label="Root Cause" /> },
);

function PanelSkeleton({ label }: { label: string }) {
  return (
    <div className="glass-panel animate-pulse rounded-2xl p-6 text-sm text-[var(--muted)]">
      Loading {label}…
    </div>
  );
}

function chartToDies(charts: DashboardCharts | null): DieSummary[] {
  const points = charts?.die_heatmap || [];
  return points.map((p, i) => ({
    die_result_id: p.die_id ? `${p.die_id}@${p.x},${p.y}` : `chart-die-${i}`,
    analysis_id: "",
    lot_id: "",
    wafer_id: "",
    die_id: p.die_id || `D-${p.x}-${p.y}`,
    x: p.x,
    y: p.y,
    failure_count: Math.round(p.intensity * 10),
    total_tests: 1,
    failure_density: p.intensity,
    neighbor_failure_count: 0,
    is_isolated: false,
    is_failing: p.intensity > 0.35,
    health_score: 1 - p.intensity,
    severity: p.intensity > 0.5 ? "critical" : "normal",
    confidence_score: 1 - p.intensity,
    trend_status: "stable",
    dominant_fault_type: "",
    dominant_pattern_id: "",
    engineering_recommendation: "",
  }));
}

function chartToWaferDies(charts: DashboardCharts | null): DieSummary[] {
  const points = charts?.wafer_heatmap || [];
  return points.map((p, i) => ({
    die_result_id: p.wafer_id ? `${p.wafer_id}@${p.x},${p.y}` : `chart-wafer-${i}`,
    analysis_id: "",
    lot_id: "",
    wafer_id: p.wafer_id || "",
    die_id: p.wafer_id || `W-${p.x}-${p.y}`,
    x: p.x,
    y: p.y,
    failure_count: Math.round(p.intensity * 10),
    total_tests: 1,
    failure_density: p.intensity,
    neighbor_failure_count: 0,
    is_isolated: false,
    is_failing: p.intensity > 0.35,
    health_score: 1 - p.intensity,
    severity: p.intensity > 0.5 ? "critical" : "normal",
    confidence_score: 1 - p.intensity,
    trend_status: "stable",
    dominant_fault_type: "",
    dominant_pattern_id: "",
    engineering_recommendation: "",
  }));
}

export const WorkbenchDashboard = memo(function WorkbenchDashboard() {
  const { metrics, charts, executionId, isAnalysisRunning } = useDashboard();
  const uploadId = useAnalysisStore((s) => s.uploadId);
  const datasetName = useAnalysisStore((s) => s.progressLabel);
  const { data: bundle, isLoading } = useWorkbenchData();

  const dies =
    bundle?.dies?.length ? bundle.dies : chartToDies(charts);
  const waferDies =
    bundle?.dies?.length ? bundle.dies : chartToWaferDies(charts);

  const reportId = bundle?.reports?.[0]?.report_id ?? null;
  const avgConfidence =
    bundle?.predictions?.length
      ? bundle.predictions.reduce((s, p) => s + (p.confidence_score || 0), 0) /
        bundle.predictions.length
      : metrics?.root_cause_confidence ?? 0;

  const showWorkbench = Boolean(executionId) || isAnalysisRunning;

  if (!showWorkbench) return null;

  return (
    <div id="workbench-root" className="space-y-6" data-testid="workbench-dashboard">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Failure Analysis Workbench
        </h2>
        <DashboardSnapshot targetId="workbench-root" />
      </div>

      <LiveAnalysisMonitor />

      <div className="grid gap-4 xl:grid-cols-2">
        <DatasetDetailsPanel
          datasetName={datasetName}
          datasetDetail={bundle?.dataset as Record<string, unknown> | null}
          uploadDetail={bundle?.upload as Record<string, unknown> | null}
          metrics={metrics}
          fileCount={metrics?.imported_test_files}
        />
        <PerformanceMetricsPanel metrics={metrics} />
      </div>

      <BenchmarkPanel metrics={metrics} executionId={executionId} />

      <div className="grid gap-4 xl:grid-cols-2">
        <Suspense fallback={<PanelSkeleton label="Wafer Heatmap" />}>
          <WorkbenchWaferHeatmap dies={waferDies} />
        </Suspense>
        <Suspense fallback={<PanelSkeleton label="Die Heatmap" />}>
          <WorkbenchDieHeatmap dies={dies} />
        </Suspense>
      </div>

      <Suspense fallback={<PanelSkeleton label="Failure Distribution" />}>
        <FailureDistributionPanel charts={charts} patterns={bundle?.patterns ?? []} />
      </Suspense>

      <Suspense fallback={<PanelSkeleton label="Pattern Analysis" />}>
        <PatternAnalysisTable patterns={bundle?.patterns ?? []} />
      </Suspense>

      <Suspense fallback={<PanelSkeleton label="Correlation Network" />}>
        <CorrelationNetwork correlations={bundle?.correlations ?? []} />
      </Suspense>

      <Suspense fallback={<PanelSkeleton label="Root Cause" />}>
        <RootCausePanel
          predictions={bundle?.predictions ?? []}
          averageConfidence={avgConfidence}
        />
      </Suspense>

      <div className="grid gap-4 xl:grid-cols-2">
        <ReportsExportPanel
          uploadId={uploadId}
          executionId={executionId}
          reportId={reportId}
        />
        <LiveLogsPanel executionId={executionId} />
      </div>

      {isLoading && (
        <p className="text-center text-xs text-[var(--muted)]">Refreshing workbench data…</p>
      )}
    </div>
  );
});
