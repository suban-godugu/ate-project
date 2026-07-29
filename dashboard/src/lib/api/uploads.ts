import type { AILogSummary, DataUploadRecord, LogUploadRecord } from "@/types/upload";
import { ApiError, apiFetch, buildQuery, subscribeJobEvents } from "./client";
import { getAccessToken, getApiBaseUrl } from "./config";
export interface PresignResponse {
  job_id: string;
  upload_url: string;
  object_key: string;
}

export async function presignUpload(body: {
  file_name: string;
  size: number;
  module: string;
  metadata?: Record<string, string>;
  kind?: "data" | "log";
}): Promise<PresignResponse> {
  return apiFetch("/uploads/presign", { method: "POST", body });
}

export async function completeUpload(jobId: string, checksum?: string): Promise<void> {
  await apiFetch(`/uploads/${jobId}/complete`, {
    method: "POST",
    body: { checksum_sha256: checksum },
  });
}

export async function listDataUploads(page = 1): Promise<{ items: DataUploadRecord[]; page: number }> {
  return apiFetch(`/uploads/data${buildQuery({ page: String(page) })}`);
}

export async function listLogUploads(page = 1): Promise<{ items: LogUploadRecord[]; page: number }> {
  return apiFetch(`/uploads/log${buildQuery({ page: String(page) })}`);
}

export async function deleteUpload(jobId: string): Promise<void> {
  await apiFetch(`/uploads/${jobId}`, { method: "DELETE" });
}

export async function getAISummary(jobId: string): Promise<AILogSummary> {
  return apiFetch(`/uploads/${jobId}/ai-summary`);
}

export function subscribeUploadEvents(
  jobId: string,
  onEvent: (data: Record<string, unknown>) => void
): Promise<() => void> {
  return subscribeJobEvents(jobId, onEvent, "/uploads");
}

export async function getUploadDownloadUrl(jobId: string): Promise<string> {
  const token = getAccessToken();
  const res = await fetch(`${getApiBaseUrl()}/uploads/${jobId}/download`, {
    redirect: "manual",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 307 || res.status === 302) {
    const location = res.headers.get("Location");
    if (location) return location;
  }
  throw new ApiError("Download failed", res.status);
}

export const uploadsApi = {
  presignUpload,
  completeUpload,
  listDataUploads,
  listLogUploads,
  deleteUpload,
  getAISummary,
  getUploadDownloadUrl,
  subscribeUploadEvents,
};
