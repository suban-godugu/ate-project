import { buildKpiWorkspace } from "@/lib/kpiDrillDown/buildKpiWorkspace";
import type { KpiWorkspace, ScanDebugDashboardData, ScanDebugKpiId } from "@/types/kpiDrillDown";

const API_MODE = process.env.NEXT_PUBLIC_API_MODE ?? "live";

if (process.env.NODE_ENV === "production" && API_MODE === "mock") {
  throw new Error("NEXT_PUBLIC_API_MODE=mock is not allowed in production builds.");
}
const FETCH_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_FETCH_TIMEOUT_MS ?? "120000");
const EMBED_BASE_PATH = process.env.NEXT_PUBLIC_EMBED_BASE_PATH ?? "";

/** Same-origin proxy in live mode (see next.config rewrites). Avoids CORS / wrong-host failures. */
function apiBase(): string {
  if (API_MODE === "mock") return "";
  if (typeof window !== "undefined") return `${EMBED_BASE_PATH}/scan-debug-api`;
  const base = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!base) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is required for server-side API calls.");
  }
  return base.replace(/\/$/, "");
}

async function fetchWithTimeout(url: string, init?: RequestInit) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    return await fetch(url, { ...init, cache: "no-store", signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export interface AgentStatus {
  device: string;
  replay_buffer_size: number;
  epsilon: number;
  steps_done: number;
  model_weights_exist: boolean;
  auto_train_on_startup?: string;
  needs_training?: boolean;
  training_in_progress?: boolean;
  training_source?: string | null;
  dataset_cases?: number;
  auto_trained?: boolean;
  auto_train_result?: TrainAgentResult | null;
  last_train_error?: string | null;
}

export interface TrainAgentResult {
  status: string;
  episodes_trained: number;
  average_episode_reward: number;
  average_loss: number;
  final_epsilon: number;
  weights_saved: boolean;
  skipped?: boolean;
  source?: string;
}

export type DashboardFetchResult = ScanDebugDashboardData & {
  dataSource?: "live" | "mock" | "unavailable";
};

export async function fetchDashboardData(): Promise<DashboardFetchResult> {
  if (API_MODE === "mock") {
    const { getDashboardData } = await import("@/lib/recommendationData");
    return { ...normalizeDashboardData(getDashboardData()), dataSource: "mock" };
  }

  try {
    const res = await fetchWithTimeout(`${apiBase()}/api/v1/recommendation/dashboard`);
    if (!res.ok) {
      throw new Error(`Dashboard API failed (${res.status})`);
    }
    return {
      ...normalizeDashboardData((await res.json()) as ScanDebugDashboardData),
      dataSource: "live",
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network error";
    throw new Error(message);
  }
}

export function normalizeDashboardData(data: ScanDebugDashboardData): ScanDebugDashboardData {
  const rootCause = Array.isArray(data.rootCauseDistribution) ? data.rootCauseDistribution : [];
  const priority =
    Array.isArray(data.recommendationPriority) && data.recommendationPriority.length
      ? data.recommendationPriority
      : [
          { name: "Critical", value: 10, fill: "#EF4444" },
          { name: "High", value: 8, fill: "#F59E0B" },
          { name: "Medium", value: 15, fill: "#7C3AED" },
          { name: "Low", value: 9, fill: "#64748B" },
        ];
  const trend = Array.isArray(data.recommendationTrend) ? data.recommendationTrend : [];

  return {
    ...data,
    executiveSummary: data.executiveSummary ?? [],
    recommendations: data.recommendations ?? [],
    kpis: (data.kpis ?? []).map((kpi) => ({
      ...kpi,
      sparkline: Array.isArray(kpi.sparkline) && kpi.sparkline.length > 0 ? kpi.sparkline : [0, 0, 0, 0, 0],
      severity: kpi.severity ?? "medium",
      status: kpi.status ?? "at_risk",
      trendPct: typeof kpi.trendPct === "number" ? kpi.trendPct : 0,
      value: kpi.value ?? "—",
      target: kpi.target ?? "—",
    })),
    workflow: data.workflow ?? [],
    rootCauseDistribution: rootCause,
    recommendationPriority: priority,
    recommendationTrend: trend,
  };
}

export async function fetchKpiWorkspace(kpiId: ScanDebugKpiId): Promise<KpiWorkspace> {
  if (API_MODE === "mock") {
    return buildKpiWorkspace(kpiId);
  }

  const res = await fetchWithTimeout(`${apiBase()}/api/v1/kpi/${kpiId}/workspace`);
  if (!res.ok) {
    throw new Error(`KPI workspace API failed (${res.status})`);
  }
  const data = (await res.json()) as KpiWorkspace;
  return {
    ...data,
    diagnosisResults: Array.isArray(data.diagnosisResults) ? data.diagnosisResults : [],
    summaryCards: Array.isArray(data.summaryCards) ? data.summaryCards : [],
    breakdown: Array.isArray(data.breakdown) ? data.breakdown : [],
    impact: Array.isArray(data.impact) ? data.impact : [],
    vizSeries: Array.isArray(data.vizSeries) ? data.vizSeries : [],
    copilotStarters: Array.isArray(data.copilotStarters) ? data.copilotStarters : [],
  };
}

export async function fetchAgentStatus(): Promise<AgentStatus | null> {
  if (API_MODE === "mock") {
    return {
      device: "mock",
      replay_buffer_size: 0,
      epsilon: 0.05,
      steps_done: 0,
      model_weights_exist: false,
    };
  }
  try {
    const res = await fetch(`${apiBase()}/status`, { cache: "no-store" });
    if (!res.ok) throw new Error("status fetch failed");
    return (await res.json()) as AgentStatus;
  } catch {
    return null;
  }
}

export async function trainAgent(
  episodes = 500,
  opts?: { force?: boolean }
): Promise<TrainAgentResult> {
  if (API_MODE === "mock") {
    await new Promise((r) => setTimeout(r, 800));
    return {
      status: "Training complete (mock)",
      episodes_trained: episodes,
      average_episode_reward: 92.5,
      average_loss: 0.04,
      final_epsilon: 0.05,
      weights_saved: false,
      skipped: false,
      source: opts?.force === false ? "dashboard-auto" : "manual",
    };
  }
  const force = opts?.force !== false;
  const res = await fetch(
    `${apiBase()}/train?episodes=${episodes}&force=${force ? "true" : "false"}`,
    { method: "POST" }
  );
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || "Training failed");
  }
  return (await res.json()) as TrainAgentResult;
}
