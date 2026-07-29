"use client";

import { useEffect } from "react";
import { isAxiosError } from "axios";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getExecutionStatus } from "@/services/api";
import { DASHBOARD_QUERY_KEY } from "@/hooks/useDashboard";
import { WORKBENCH_QUERY_KEY } from "@/hooks/useWorkbenchData";
import { normalizeCharts, normalizeMetrics } from "@/services/dashboard";
import { useAnalysisStore } from "@/stores/analysisStore";

const TERMINAL = new Set(["completed", "failed"]);

export function useExecutionPolling(executionId: string | null) {
  const qc = useQueryClient();
  const setStatus = useAnalysisStore((s) => s.setStatus);
  const applyDashboard = useAnalysisStore((s) => s.applyDashboard);
  const setError = useAnalysisStore((s) => s.setError);
  const setPolling = useAnalysisStore((s) => s.setPolling);

  const query = useQuery({
    queryKey: ["execution-status", executionId],
    queryFn: () => getExecutionStatus(executionId!),
    enabled: Boolean(executionId),
    retry: (failureCount, error) => {
      if (isAxiosError(error) && error.response?.status === 404) {
        return failureCount < 8;
      }
      return failureCount < 2;
    },
    retryDelay: (attempt) => Math.min(1000 * (attempt + 1), 5000),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (status && TERMINAL.has(status)) return false;
      return 2000;
    },
    refetchIntervalInBackground: true,
  });

  const data = query.data;
  const isTerminal = data?.status === "completed" || data?.status === "failed";

  useEffect(() => {
    if (!query.isError || !executionId) return;
    const detail = isAxiosError(query.error)
      ? String(query.error.response?.data?.detail || query.error.message)
      : query.error instanceof Error
        ? query.error.message
        : "Analysis status unavailable";
    if (isAxiosError(query.error) && query.error.response?.status === 404) {
      return;
    }
    setError(detail, "pipeline_failed");
    setStatus("failed", detail, useAnalysisStore.getState().progress);
    setPolling(false);
  }, [query.isError, query.error, executionId, setError, setPolling, setStatus]);

  useEffect(() => {
    if (!data || !executionId) return;

    if (data.status === "failed") {
      setError(data.error || "Analysis failed", "pipeline_failed");
      setStatus("failed", data.error || "Analysis failed", data.progress);
      setPolling(false);
      return;
    }

    if (data.status === "completed") {
      const metrics = normalizeMetrics(data.metrics as Record<string, unknown> | undefined);
      const charts = normalizeCharts(data.charts as Record<string, unknown> | undefined);
      applyDashboard({
        execution_id: data.execution_id,
        dataset_id: data.dataset_id,
        upload_id: data.upload_id,
        status: data.status,
        metrics,
        charts,
      });
      setStatus("completed", data.label || "Completed", 100);
      setPolling(false);
      void qc.invalidateQueries({ queryKey: [DASHBOARD_QUERY_KEY, executionId] });
      void qc.invalidateQueries({ queryKey: [WORKBENCH_QUERY_KEY, executionId] });
      return;
    }

    const step = (data.current_step || "pattern_detection") as Parameters<
      typeof setStatus
    >[0];
    setStatus(step, data.label || "Running analysis…", data.progress);
    setPolling(true);
  }, [data, executionId, setError, applyDashboard, setPolling, setStatus, qc]);

  return {
    ...query,
    isTerminal,
    status: data?.status,
    metrics: data?.metrics,
  };
}
