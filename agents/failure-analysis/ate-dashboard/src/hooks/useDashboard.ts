"use client";

import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchAnalysisDashboard,
  fetchSupplementaryCharts,
  mergeDashboardCharts,
} from "@/services/dashboard";
import { api } from "@/services/api";
import { useAnalysisStore } from "@/stores/analysisStore";
import { useEmbedMode } from "@/hooks/useEmbedMode";
import {
  buildChartsFromPlatformReport,
  type PlatformFailureLatest,
} from "@/lib/platformFailureCharts";

export const DASHBOARD_QUERY_KEY = "analysis-dashboard";
export const PLATFORM_FAILURE_LATEST_KEY = "platform-failure-latest";

export function useDashboard() {
  const embed = useEmbedMode();
  const executionId = useAnalysisStore((s) => s.executionId);
  const uploadId = useAnalysisStore((s) => s.uploadId);
  const isPolling = useAnalysisStore((s) => s.isPolling);
  const applyDashboard = useAnalysisStore((s) => s.applyDashboard);
  const setLoading = useAnalysisStore((s) => s.setLoading);
  const setError = useAnalysisStore((s) => s.setError);
  const metrics = useAnalysisStore((s) => s.metrics);
  const charts = useAnalysisStore((s) => s.charts);
  const status = useAnalysisStore((s) => s.execution.status);

  const query = useQuery({
    queryKey: [DASHBOARD_QUERY_KEY, executionId],
    queryFn: async () => {
      const dashboard = await fetchAnalysisDashboard(executionId!);
      if (uploadId && dashboard.status === "completed") {
        const needsSupplement =
          !dashboard.charts?.failure_trend?.length ||
          !dashboard.charts?.failure_distribution?.length ||
          !dashboard.charts?.category_distribution?.filter((row) => row.count > 0).length ||
          !dashboard.charts?.die_heatmap?.length ||
          !dashboard.charts?.wafer_heatmap?.length ||
          !Object.keys(dashboard.charts?.correlation_graph || {}).length;

        if (needsSupplement) {
          const extra = await fetchSupplementaryCharts(uploadId);
          dashboard.charts = mergeDashboardCharts(dashboard.charts, extra);
        }
      }
      return dashboard;
    },
    enabled: Boolean(executionId) && !embed,
    staleTime: 15_000,
    refetchOnWindowFocus: true,
  });

  const platformLatest = useQuery({
    queryKey: [PLATFORM_FAILURE_LATEST_KEY],
    queryFn: async () => {
      const { data } = await api.get<PlatformFailureLatest>("/failure/latest");
      return data;
    },
    enabled: embed,
    refetchInterval: embed ? 5_000 : false,
    retry: false,
  });

  useEffect(() => {
    setLoading(isPolling || query.isFetching || (embed && platformLatest.isFetching && !metrics));
  }, [isPolling, query.isFetching, platformLatest.isFetching, embed, metrics, setLoading]);

  useEffect(() => {
    if (!query.data) return;
    if (query.data.status === "failed") {
      setError(query.data.error || "Analysis failed", "analysis_failed");
      return;
    }
    if (query.data.status === "completed" && query.data.metrics) {
      applyDashboard({
        execution_id: query.data.execution_id,
        dataset_id: query.data.dataset_id,
        upload_id: query.data.upload_id,
        status: query.data.status,
        metrics: query.data.metrics,
        charts: query.data.charts,
      });
      setError(null);
    }
  }, [query.data, applyDashboard, setError]);

  useEffect(() => {
    const data = platformLatest.data;
    if (!data || data.status !== "completed" || !data.metrics) return;
    const id = data.execution_id || data.job_id || data.upload_id || "platform-latest";
    const chartsFromReport = buildChartsFromPlatformReport(data.report, data.metrics);
    applyDashboard({
      execution_id: id,
      dataset_id: data.dataset_id || id,
      upload_id: data.upload_id || id,
      status: "completed",
      metrics: data.metrics,
      charts: chartsFromReport,
    });
    setError(null);
  }, [platformLatest.data, applyDashboard, setError]);

  useEffect(() => {
    if (query.isError && !embed) {
      setError("Backend unavailable", "backend_unavailable");
    }
  }, [query.isError, embed, setError]);

  const hasMetrics = Boolean(metrics);
  const hasDataset = Boolean(executionId);

  return {
    ...query,
    metrics,
    charts,
    executionId,
    datasetId: useAnalysisStore.getState().datasetId,
    status,
    platformLatest: platformLatest.data,
    isLoading:
      isPolling ||
      query.isLoading ||
      query.isFetching ||
      (embed && platformLatest.isFetching && !hasMetrics),
    isEmpty: !hasDataset && !hasMetrics,
    isAnalysisRunning:
      isPolling || query.data?.status === "running" || query.data?.status === "pending",
  };
}

export function useInvalidateDashboard() {
  const qc = useQueryClient();
  return (executionId?: string | null) => {
    if (executionId) {
      void qc.invalidateQueries({ queryKey: [DASHBOARD_QUERY_KEY, executionId] });
    } else {
      void qc.invalidateQueries({ queryKey: [DASHBOARD_QUERY_KEY] });
    }
    void qc.invalidateQueries({ queryKey: [PLATFORM_FAILURE_LATEST_KEY] });
  };
}
