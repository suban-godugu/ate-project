"use client";

import dynamic from "next/dynamic";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardData, type DashboardFetchResult } from "@/lib/kpiDrillDown/api";
import { useUiStore, normalizeKpiId } from "@/store/uiStore";
import { RecommendationTable } from "@/components/recommendation/RecommendationTable";
import { SectionedKPIGrid } from "@/components/recommendation/SectionedKPIGrid";
import { ExecutiveSummary } from "@/components/recommendation/ExecutiveSummary";
import { EngineeringWorkflow } from "@/components/recommendation/EngineeringWorkflow";
import { TrainAgentPanel } from "@/components/recommendation/TrainAgentPanel";
import { ChartErrorBoundary } from "@/components/common/ChartErrorBoundary";
import { AppErrorBoundary } from "@/components/common/AppErrorBoundary";
import { buildExecutiveSummaryFallback } from "@/lib/kpiDrillDown/executiveSummaryFallback";

import { AnalyticsCharts } from "@/components/recommendation/AnalyticsCharts";

const KpiDrillDownWorkspace = dynamic(
  () =>
    import("@/components/common/kpi-drilldown/KpiDrillDownWorkspace").then(
      (m) => m.KpiDrillDownWorkspace
    ),
  { ssr: false }
);

export function ScanDebugAgentTab() {
  const { activeKpiId, setActiveKpiId } = useUiStore();
  const { data, error, isLoading, isFetching, isFetched } = useQuery<DashboardFetchResult>({
    queryKey: ["scan-debug-dashboard"],
    queryFn: fetchDashboardData,
    retry: 1,
    retryDelay: 1000,
    refetchOnWindowFocus: false,
    staleTime: 60_000,
    placeholderData: (previous) => previous,
  });

  useEffect(() => {
    try {
      localStorage.removeItem("compty-scan-debug-ui");
    } catch {
      // ignore storage errors
    }
  }, []);

  const summaryCards =
    data?.executiveSummary?.length
      ? data.executiveSummary
      : buildExecutiveSummaryFallback(data?.kpis ?? []);
  const recommendations = data?.recommendations ?? [];
  const hasLive = data?.dataSource === "live";
  const kpis = hasLive ? (data.kpis ?? []) : [];
  // Only show skeleton on the first load — never flash loading on background refetch.
  const showKpiLoading = isLoading && !hasLive;
  const safeKpiId = normalizeKpiId(activeKpiId);

  return (
    <AppErrorBoundary title="Scan Debug dashboard error">
    <div className="space-y-8">
      <div className="glass-card gradient-border p-5">
        <div className="text-[10px] uppercase tracking-[0.18em] text-primary">
          Recommendation Analysis
        </div>
        <h2 className="font-display text-2xl font-semibold text-white">Scan Debug Recommendation Agent</h2>
        <p className="mt-1 max-w-3xl text-sm text-muted">
          Failure diagnosis and debug actions across five recommendation responsibilities: scan chain debug,
          ATPG constraint review, timing debug, power-related debug, and physical defect investigation —
          ranked by diagnosis evidence, AI confidence, and yield impact.
        </p>
      </div>

      {showKpiLoading ? (
        <div className="glass-card gradient-border px-4 py-3 text-sm text-slate-400">
          Loading live scan debug data from API…
        </div>
      ) : null}

      {error && !hasLive && isFetched ? (
        <div className="glass-card gradient-border border-warning/40 px-4 py-3 text-sm text-warning">
          Live API unavailable — start the API, then refresh. ({error.message})
        </div>
      ) : null}

      {isFetching && hasLive ? (
        <div className="text-[11px] text-slate-500">Refreshing live data…</div>
      ) : null}

      <ChartErrorBoundary title="Analytics charts">
        {hasLive ? (
          <AnalyticsCharts data={data} />
        ) : showKpiLoading ? (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-52 animate-pulse rounded-glass bg-white/5" />
            ))}
          </div>
        ) : null}
      </ChartErrorBoundary>

      <SectionedKPIGrid
        kpis={kpis}
        loading={showKpiLoading}
        onKpiClick={(id) => setActiveKpiId(id)}
      />

      {hasLive ? (
        <RecommendationTable rows={recommendations} />
      ) : null}

      <TrainAgentPanel />

      <ExecutiveSummary
        cards={summaryCards}
        onCardClick={(id) => setActiveKpiId(normalizeKpiId(id))}
      />

      <EngineeringWorkflow steps={data?.workflow ?? []} />

      {safeKpiId ? (
        <AppErrorBoundary title="KPI drill-down error">
          <KpiDrillDownWorkspace kpiId={safeKpiId} onClose={() => setActiveKpiId(null)} />
        </AppErrorBoundary>
      ) : null}
    </div>
    </AppErrorBoundary>
  );
}
