"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchWorkbenchBundle } from "@/services/analysis-data";
import { useAnalysisStore } from "@/stores/analysisStore";
import { DASHBOARD_QUERY_KEY } from "@/hooks/useDashboard";

export const WORKBENCH_QUERY_KEY = "workbench-data";

export function useWorkbenchData() {
  const executionId = useAnalysisStore((s) => s.executionId);
  const uploadId = useAnalysisStore((s) => s.uploadId);
  const datasetId = useAnalysisStore((s) => s.datasetId);
  const isPolling = useAnalysisStore((s) => s.isPolling);

  return useQuery({
    queryKey: [WORKBENCH_QUERY_KEY, executionId, uploadId],
    queryFn: () =>
      fetchWorkbenchBundle({
        executionId: executionId!,
        uploadId,
        datasetId,
      }),
    enabled: Boolean(executionId),
    staleTime: 20_000,
    refetchInterval: isPolling ? 3000 : false,
    refetchOnWindowFocus: true,
  });
}

export function workbenchQueryKeys(executionId?: string | null) {
  return {
    dashboard: [DASHBOARD_QUERY_KEY, executionId],
    workbench: [WORKBENCH_QUERY_KEY, executionId],
  };
}
