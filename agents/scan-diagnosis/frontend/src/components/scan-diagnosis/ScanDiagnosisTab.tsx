"use client";

import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  apiFooterLabel,
  fetchDashboard,
  fetchReviewQueue,
  patchDashboardReviewSummary,
} from "@/lib/kpiDrillDown/diagnosisApi";
import type { DiagnosisDashboard } from "@/lib/kpiDrillDown/diagnosisTypes";
import {
  dashboardFromPlatformScan,
  fetchPlatformScanLatest,
} from "@/lib/kpiDrillDown/platformScanLatest";
import { SECTION_PROFILES } from "@/lib/kpiDrillDown/kpiProfiles";
import { MlStatusBanner } from "./MlStatusBanner";
import { DiagnosisHeader } from "./DiagnosisHeader";
import { FilterBar } from "./FilterBar";
import { KpiSection } from "./KpiSection";
import { KpiWorkspaceModal } from "./KpiWorkspaceModal";
import { RankingBarChart } from "./RankingBarChart";
import { ChainSignatureCompact } from "./ChainSignaturePanel";
import { TopologyGraph } from "./TopologyGraph";
import { ShiftCaptureChart } from "./ShiftCaptureChart";
import { EngineeringTables } from "./EngineeringTables";
import { AICopilotPanel } from "./AICopilotPanel";
import { DatasetSnapshot, KpiBriefOverview } from "./KpiBriefOverview";
import { useEmbedMode, useEmbedReady } from "@/hooks/useEmbedMode";

export function ScanDiagnosisTab() {
  const embed = useEmbedMode();
  const embedReady = useEmbedReady();
  const [lot, setLot] = useState("");
  const [activeKpi, setActiveKpi] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: liveData, isLoading, isError, isFetching } = useQuery({
    queryKey: ["diagnosis-dashboard", lot],
    queryFn: () =>
      fetchDashboard({
        lot: lot || undefined,
      }),
    staleTime: 60_000,
    gcTime: 10 * 60_000,
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    placeholderData: (prev) => prev,
  });

  const liveEmpty =
    !liveData ||
    ((liveData.dataset_summary?.log_file_count ?? 0) === 0 &&
      (liveData.dataset_summary?.total_failure_records ?? 0) === 0);

  const platformQuery = useQuery({
    queryKey: ["platform-scan-latest"],
    queryFn: fetchPlatformScanLatest,
    enabled: liveEmpty,
    refetchInterval: liveEmpty ? 8_000 : false,
    retry: false,
  });

  const data: DiagnosisDashboard | undefined = useMemo(() => {
    if (!liveEmpty && liveData) return liveData;
    if (platformQuery.data) return dashboardFromPlatformScan(platformQuery.data);
    return liveData;
  }, [liveEmpty, liveData, platformQuery.data]);

  useQuery({
    queryKey: ["diagnosis-reviews-sync"],
    queryFn: async () => {
      const synced = await fetchReviewQueue({ limit: 50, seed: false });
      const summary = synced.summary || {};
      queryClient.setQueriesData<DiagnosisDashboard>(
        { queryKey: ["diagnosis-dashboard"] },
        (old) => (old ? patchDashboardReviewSummary(old, summary) : old),
      );
      return synced;
    },
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 15_000,
    enabled: !liveEmpty,
  });

  const kpisBySection = useMemo(() => data?.kpis ?? [], [data]);

  if (!embedReady) {
    return <div className="min-h-[40vh] bg-[#090b12]" aria-hidden="true" />;
  }

  return (
    <div className={embed ? "pb-8" : "pb-16"}>
      {!embed ? (
        <DiagnosisHeader
          title={data?.title ?? "Scan Diagnosis"}
          subtitle={
            data?.subtitle ??
            "Real-time diagnosis of scan chain failures using topology analysis, AI root cause detection and engineering recommendations."
          }
          onRefresh={() => {
            void queryClient.fetchQuery({
              queryKey: ["diagnosis-dashboard", lot],
              queryFn: () =>
                fetchDashboard({
                  lot: lot || undefined,
                  force: true,
                }),
            });
            void queryClient.invalidateQueries({ queryKey: ["platform-scan-latest"] });
          }}
          onExport={() => {
            if (!data) return;
            const blob = new Blob([JSON.stringify(data, null, 2)], {
              type: "application/json",
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "scan-diagnosis-dashboard.json";
            a.click();
            URL.revokeObjectURL(url);
          }}
          onReport={() => setActiveKpi("diagnosis_reports")}
        />
      ) : null}

      <div className={embed ? "px-1 py-2 md:px-2" : "mx-auto max-w-[1400px] px-4 py-6"}>
        {!embed ? (
          <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full border border-primary/40 bg-primary/15 px-3 py-1 font-medium text-violet-200">
              Scan Diagnosis
            </span>
            <span className="rounded-full border border-border px-3 py-1 text-slate-400">
              Source: {data?.data_source ?? "—"}
            </span>
            <span className="rounded-full border border-border px-3 py-1 text-slate-400">
              {isFetching ? "Refreshing…" : apiFooterLabel(data)}
            </span>
          </div>
        ) : (
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span className="rounded-md border border-[#2D3748] px-2.5 py-1">
                Source: {data?.data_source ?? "—"}
              </span>
              <span className="rounded-md border border-[#2D3748] px-2.5 py-1">
                {isFetching || platformQuery.isFetching
                  ? "Refreshing…"
                  : apiFooterLabel(data)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="rounded-lg border border-[#2D3748] px-3 py-1.5 text-xs text-slate-200 hover:border-[#7C3AED]"
                onClick={() => {
                  void queryClient.fetchQuery({
                    queryKey: ["diagnosis-dashboard", lot],
                    queryFn: () =>
                      fetchDashboard({
                        lot: lot || undefined,
                        force: true,
                      }),
                  });
                  void queryClient.invalidateQueries({ queryKey: ["platform-scan-latest"] });
                }}
              >
                Refresh
              </button>
              <button
                type="button"
                className="rounded-lg border border-[#2D3748] px-3 py-1.5 text-xs text-slate-200 hover:border-[#7C3AED]"
                onClick={() => {
                  if (!data) return;
                  const blob = new Blob([JSON.stringify(data, null, 2)], {
                    type: "application/json",
                  });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "scan-diagnosis-dashboard.json";
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Export
              </button>
            </div>
          </div>
        )}

        {data ? (
          <>
            <FilterBar
              filters={data.filters}
              summary={data.dataset_summary}
              lot={lot}
              onLot={setLot}
            />
            <MlStatusBanner status={data.ml_status} production={data.production_validation} />
          </>
        ) : null}

        {isLoading && !data ? (
          <div className="glass-card space-y-2 p-10 text-center text-slate-400">
            <div>Loading diagnosis dashboard…</div>
            <div className="text-xs text-slate-500">
              Waiting for stil/logs or latest scan results.
            </div>
          </div>
        ) : isError && !data && !platformQuery.data ? (
          <div className="glass-card space-y-2 p-10 text-center text-danger">
            <div>Failed to load dashboard.</div>
            <div className="text-xs text-slate-400">
              Check scan API connectivity, then refresh this tab.
            </div>
          </div>
        ) : data ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
            <div className="min-w-0">
              {SECTION_PROFILES.map((profile) => (
                <KpiSection
                  key={profile.id}
                  profile={profile}
                  kpis={kpisBySection.filter((k) => k.section === profile.id)}
                  onSelect={setActiveKpi}
                />
              ))}

              <motion.section
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 grid gap-4 lg:grid-cols-2"
              >
                <RankingBarChart ranking={data.ranking} />
                <ChainSignatureCompact
                  overview={
                    (data.correlations || [])
                      .map((c) => {
                        const factors =
                          (c.distinguishing_factors as { label?: string; pct_diff?: number }[]) ||
                          [];
                        const bullets = (c.signature_bullets as string[]) || [];
                        const top = factors[0];
                        return {
                          chain: String(c.chain),
                          failure_count: Number(c.failure_count ?? 0),
                          top_factor: top?.label,
                          top_pct_diff: top?.pct_diff,
                          summary: bullets[1] || bullets[0] || "",
                        };
                      })
                      .sort((a, b) => Math.abs(b.top_pct_diff ?? 0) - Math.abs(a.top_pct_diff ?? 0))
                  }
                />
                <ShiftCaptureChart
                  shiftCapture={data.shift_capture}
                  title="Shift vs Capture"
                  compact
                />
                <KpiBriefOverview kpis={kpisBySection} onSelect={setActiveKpi} />
                <TopologyGraph topology={data.topology_summary} />
                <DatasetSnapshot summary={data.dataset_summary} />
              </motion.section>

              <EngineeringTables breaks={data.breaks_table} cells={data.cells_table} />
            </div>

            <AICopilotPanel kpiId={activeKpi} dashboard={data} onSelectKpi={setActiveKpi} />
          </div>
        ) : null}

        <footer className="mt-10 text-center text-xs text-slate-500">
          {apiFooterLabel(data)}
        </footer>
      </div>

      <KpiWorkspaceModal kpiId={activeKpi} onClose={() => setActiveKpi(null)} />
    </div>
  );
}
