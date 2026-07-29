"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { ArrowRight } from "lucide-react";
import { AnalysisKPICards } from "@/components/AnalysisKPICards";
import { AnalysisCharts } from "@/components/dashboard/AnalysisCharts";
import { UploadHistory } from "@/components/UploadHistory";
import { StatsPanel } from "@/components/StatsPanel";
import { useClientMounted } from "@/hooks/useClientMounted";
import { useDashboard } from "@/hooks/useDashboard";
import { useEmbedMode } from "@/hooks/useEmbedMode";
import { useAnalysisStore } from "@/stores/analysisStore";

const WorkbenchDashboard = dynamic(
  () =>
    import("@/components/workbench/WorkbenchDashboard").then((m) => m.WorkbenchDashboard),
  { ssr: false },
);

export default function OverviewPage() {
  const mounted = useClientMounted();
  const embed = useEmbedMode();
  const { metrics, charts, isLoading, isEmpty, isAnalysisRunning, executionId, datasetId } =
    useDashboard();
  const error = useAnalysisStore((s) => s.error);
  const errorCode = useAnalysisStore((s) => s.errorCode);

  return (
    <div className="space-y-6">
      {!embed ? (
        <header className="glass-panel rounded-2xl p-6">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-[var(--accent)]">
                FA-FR-001 → FA-FR-010
              </p>
              <h1 className="mt-1 text-2xl font-semibold">
                Semiconductor Failure Analysis Overview
              </h1>
              <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
                Live KPIs and charts sourced from backend analysis — refreshed automatically after
                each successful run.
              </p>
              {mounted && (executionId || datasetId) && (
                <p className="mt-2 font-mono text-xs text-[var(--muted)]">
                  {datasetId ? `dataset=${datasetId}` : ""}
                  {executionId ? ` · execution=${executionId}` : ""}
                </p>
              )}
              {error && errorCode === "analysis_failed" && (
                <p className="mt-2 text-sm text-[var(--danger)]">{error}</p>
              )}
            </div>
            {mounted && isEmpty && !isAnalysisRunning && (
              <Link
                href="/upload"
                className="inline-flex items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white"
              >
                Open Upload & Analyze
                <ArrowRight size={16} />
              </Link>
            )}
          </div>
        </header>
      ) : (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--border)] pb-3">
          <div className="text-sm text-[var(--muted)]">
            {mounted && (executionId || datasetId) ? (
              <span className="font-mono text-xs">
                {datasetId ? `dataset=${datasetId}` : ""}
                {executionId ? ` · execution=${executionId}` : ""}
              </span>
            ) : (
              <span>Failure analysis workspace</span>
            )}
            {error && errorCode === "analysis_failed" && (
              <span className="ml-3 text-[var(--danger)]">{error}</span>
            )}
          </div>
        </div>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Analysis KPIs
        </h2>
        <AnalysisKPICards />
      </section>

      {mounted && (metrics || isLoading || isAnalysisRunning) && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
            Analysis Charts
          </h2>
          <AnalysisCharts
            charts={charts}
            loading={isLoading || isAnalysisRunning}
          />
        </section>
      )}

      <WorkbenchDashboard />

      {!embed && (
        <>
          <StatsPanel />
          <UploadHistory />
        </>
      )}
    </div>
  );
}
