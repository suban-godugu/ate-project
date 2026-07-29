"use client";

import { memo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { fetchAnalysisHistory } from "@/services/history";
import { reopenAnalysisExecution } from "@/services/history";
import { useHistoryStore } from "@/stores/historyStore";
import { useAnalysisStore } from "@/stores/analysisStore";
import { normalizeCharts, normalizeMetrics } from "@/services/dashboard";
import { notify } from "@/stores/toastStore";
import { useQueryClient } from "@tanstack/react-query";
import { DASHBOARD_QUERY_KEY } from "@/hooks/useDashboard";
import { WORKBENCH_QUERY_KEY } from "@/hooks/useWorkbenchData";

function formatDuration(ms?: number) {
  if (!ms) return "—";
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

export const AnalysisHistoryTable = memo(function AnalysisHistoryTable() {
  const router = useRouter();
  const qc = useQueryClient();
  const setEntries = useHistoryStore((s) => s.setEntries);
  const selectExecution = useHistoryStore((s) => s.selectExecution);
  const applyDashboard = useAnalysisStore((s) => s.applyDashboard);
  const setContext = useAnalysisStore((s) => s.setContext);
  const setStatus = useAnalysisStore((s) => s.setStatus);
  const setPolling = useAnalysisStore((s) => s.setPolling);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["analysis-history"],
    queryFn: () => fetchAnalysisHistory(50),
    refetchInterval: 30_000,
  });

  const cachedEntries = useHistoryStore((s) => s.entries);
  const entries = data?.length ? data : cachedEntries;

  useEffect(() => {
    if (data?.length) setEntries(data);
  }, [data, setEntries]);

  const reopen = async (executionId: string) => {
    try {
      const status = await reopenAnalysisExecution(executionId);
      const metrics = normalizeMetrics(status.metrics as Record<string, unknown> | undefined);
      const charts = normalizeCharts(status.charts as Record<string, unknown> | undefined);
      setContext({
        executionId: status.execution_id,
        datasetId: status.dataset_id,
        uploadId: status.upload_id,
      });
      applyDashboard({
        execution_id: status.execution_id,
        dataset_id: status.dataset_id,
        upload_id: status.upload_id,
        status: status.status,
        metrics,
        charts,
      });
      setStatus(
        status.status === "completed" ? "completed" : "evaluation",
        "Reopened analysis",
        status.progress ?? 100,
      );
      setPolling(false);
      selectExecution(executionId);
      void qc.invalidateQueries({ queryKey: [DASHBOARD_QUERY_KEY, executionId] });
      void qc.invalidateQueries({ queryKey: [WORKBENCH_QUERY_KEY, executionId] });
      notify({
        title: "Analysis Reopened",
        description: `Loaded execution ${executionId.slice(0, 8)}…`,
        variant: "info",
      });
      router.push("/overview");
    } catch (err) {
      notify({
        title: "Reopen Failed",
        description: err instanceof Error ? err.message : "Could not load execution",
        variant: "error",
      });
    }
  };

  return (
    <div className="glass-panel overflow-hidden rounded-2xl" data-testid="analysis-history">
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Analysis History
        </h3>
        <button
          type="button"
          onClick={() => refetch()}
          className="text-xs text-[var(--accent)] hover:underline"
        >
          Refresh
        </button>
      </div>
      <div className="max-h-[480px] overflow-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[var(--surface)]/95 text-xs uppercase text-[var(--muted)]">
            <tr>
              <th className="px-4 py-2 text-left">Execution ID</th>
              <th className="px-4 py-2 text-left">Started</th>
              <th className="px-4 py-2 text-left">Duration</th>
              <th className="px-4 py-2 text-left">Status</th>
              <th className="px-4 py-2 text-left">User</th>
              <th className="px-4 py-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-[var(--muted)]">
                  Loading history…
                </td>
              </tr>
            )}
            {!isLoading && !entries.length && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-[var(--muted)]">
                  No analysis runs yet. Complete an upload to populate history.
                </td>
              </tr>
            )}
            {entries.map((row) => (
              <tr key={row.execution_id} className="border-t border-white/5 hover:bg-white/5">
                <td className="px-4 py-2 font-mono text-xs">{row.execution_id.slice(0, 12)}…</td>
                <td className="px-4 py-2 text-xs">
                  {row.started_at ? new Date(row.started_at).toLocaleString() : "—"}
                </td>
                <td className="px-4 py-2">{formatDuration(row.duration_ms)}</td>
                <td className="px-4 py-2 capitalize">{row.status.replace(/_/g, " ")}</td>
                <td className="px-4 py-2">{row.user || "—"}</td>
                <td className="px-4 py-2 text-right">
                  <button
                    type="button"
                    onClick={() => reopen(row.execution_id)}
                    className="inline-flex items-center gap-1 rounded-lg border border-white/10 px-2 py-1 text-xs hover:bg-white/10"
                  >
                    <ExternalLink size={12} />
                    Reopen
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
});
