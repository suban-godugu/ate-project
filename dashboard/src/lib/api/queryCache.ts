import type { QueryClient } from "@tanstack/react-query";

let client: QueryClient | null = null;

export function registerQueryClient(queryClient: QueryClient) {
  client = queryClient;
}

const MODULE_KEY_MAP: Record<string, string[]> = {
  "Scan Chain Analysis": ["scan-chain", "executive"],
  "Scan Chain": ["scan-chain", "executive"],
  MBIST: ["mbist", "executive"],
  "MBIST Analysis": ["mbist", "executive"],
  LBIST: ["lbist", "executive"],
  "LBIST Analysis": ["lbist", "executive"],
  "Wafer Analysis": ["wafer-analysis", "executive"],
  "Cost Intelligence": ["cost-intelligence", "executive"],
  "Recommendation Analysis": ["recommendation-analysis", "executive"],
};

export function invalidateDashboardCaches(uploadModule?: string) {
  if (!client) return;
  client.invalidateQueries({ queryKey: ["dashboard"] });
  client.invalidateQueries({ queryKey: ["search"] });
  if (uploadModule) {
    for (const key of MODULE_KEY_MAP[uploadModule] ?? []) {
      client.invalidateQueries({ queryKey: ["dashboard", key] });
    }
  }
}
