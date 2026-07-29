import { api } from "@/services/api";

export type WorkbenchLogEntry = {
  timestamp?: string;
  module?: string;
  status?: string;
  message?: string;
  duration_ms?: number;
  exception?: string | null;
};

export async function fetchWorkbenchLogs(executionId?: string, filters?: {
  module?: string;
  status?: string;
}) {
  const q = new URLSearchParams();
  if (executionId) q.set("execution_id", executionId);
  if (filters?.module) q.set("module", filters.module);
  if (filters?.status) q.set("status", filters.status);
  const { data } = await api.get<{
    execution_id: string;
    logs: WorkbenchLogEntry[];
    total: number;
  }>(`/workbench/logs?${q}`);
  return data;
}

export async function fetchWorkbenchHealth() {
  const { data } = await api.get<Record<string, unknown>>("/workbench/health");
  return data;
}
