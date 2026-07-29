import { api } from "@/services/api";
import type { AnalysisHistoryEntry } from "@/stores/historyStore";

export async function listAnalysisRuns(limit = 50) {
  const { data } = await api.get<{
    runs: Array<{
      execution_id: string;
      datasets_evaluated?: number;
      pass_count?: number;
      fail_count?: number;
      warning_count?: number;
      processing_ms?: number;
      created_at?: string | null;
    }>;
  }>(`/evaluation?limit=${limit}`);
  return data.runs || [];
}

export async function fetchAnalysisHistory(limit = 50): Promise<AnalysisHistoryEntry[]> {
  const runs = await listAnalysisRuns(limit);
  return runs.map((run) => ({
    execution_id: run.execution_id,
    status: run.fail_count && run.fail_count > 0 ? "completed_with_failures" : "completed",
    started_at: run.created_at,
    completed_at: run.created_at,
    duration_ms: run.processing_ms,
    pass_count: run.pass_count,
    fail_count: run.fail_count,
    user: "ate-dashboard",
  }));
}

export async function reopenAnalysisExecution(executionId: string) {
  const { data } = await api.get(`/evaluation/status/${executionId}`);
  return data;
}
