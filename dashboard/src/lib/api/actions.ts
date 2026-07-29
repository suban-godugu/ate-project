import type { AIDiagnosisResult, PrimaryActionResult } from "@/types/platform";
import { apiFetch, subscribeJobEvents } from "./client";

export async function triggerPrimaryAction(pageId: string): Promise<{ job_id: string }> {
  return apiFetch(`/actions/primary/${pageId}`, { method: "POST" });
}

export async function triggerAIDiagnosis(module: string): Promise<{ job_id: string }> {
  return apiFetch(`/ai-diagnosis/${module}`, { method: "POST" });
}

export function subscribeActionEvents(
  jobId: string,
  onEvent: (data: Record<string, unknown>) => void
): Promise<() => void> {
  return subscribeJobEvents(jobId, onEvent, "/actions");
}

export async function exportPDF(title: string, lines: string[]): Promise<string> {
  const res = await apiFetch<{ url: string }>("/export/pdf", {
    method: "POST",
    body: { title, lines },
  });
  return res.url;
}

export async function submitRecommendationFeedback(
  recommendationId: string,
  body: { action_taken: string; outcome_metric?: string; outcome_value?: number }
): Promise<{ ok: boolean; reward_value: number }> {
  return apiFetch(`/recommendations/${recommendationId}/feedback`, { method: "POST", body });
}

export async function getRecommendationMetrics(recommendationId: string) {
  return apiFetch<{
    confidence: number;
    confidence_change: number | null;
    reward_score: number;
    approval_rate: number;
    application_rate: number;
    feedback_count: number;
    trend: Array<{ confidence: number | null; reward: number | null; processed_at: string | null }>;
    feedback_history: Array<{ action_taken: string; reward_value: number | null; created_at: string | null }>;
  }>(`/recommendations/${recommendationId}/metrics`);
}

export const actionsApi = {
  triggerPrimaryAction,
  triggerAIDiagnosis,
  subscribeActionEvents,
  exportPDF,
  submitRecommendationFeedback,
  getRecommendationMetrics,
};

export type { PrimaryActionResult, AIDiagnosisResult };
