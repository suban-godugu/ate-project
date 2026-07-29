import axios, { AxiosError } from "axios";

import type { PredictOptions, WaferAnalysisResult } from "@/types/wafer";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
});

function buildFormData(
  files: File[],
  options: PredictOptions,
  multi: boolean,
): FormData {
  const form = new FormData();
  if (multi) {
    files.forEach((file) => form.append("images", file));
  } else {
    form.append("image", files[0]);
  }
  form.append("grid_mode", options.gridMode);
  if (options.gridMode === "manual" && options.gridSize != null) {
    form.append("grid_size", String(options.gridSize));
  }
  return form;
}

export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const ax = error as AxiosError<{
      detail?: string | { msg?: string }[];
      message?: string;
      status?: string;
      code?: number;
    }>;
    if (!ax.response) {
      return "Network error. Confirm the FastAPI server is running.";
    }
    const data = ax.response.data;
    if (typeof data?.message === "string" && data.message) return data.message;
    const detail = data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
    }
    if (ax.response.status === 415) return "Invalid image or unsupported format.";
    if (ax.response.status >= 500) return "Backend error during wafer analysis.";
    return ax.message || "Request failed.";
  }
  if (error instanceof Error) return error.message;
  return "Unexpected error.";
}

/**
 * Single-wafer analysis via POST /predict.
 * Uses backend fields grid_mode + grid_size (not custom_rows/cols).
 */
export async function predictWafer(
  file: File,
  options: PredictOptions,
): Promise<WaferAnalysisResult> {
  const form = buildFormData([file], options, false);
  const { data } = await apiClient.post<WaferAnalysisResult>("/predict", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Multi-wafer analysis via POST /predict/batch.
 */
export async function predictWaferBatch(
  files: File[],
  options: PredictOptions,
): Promise<WaferAnalysisResult[]> {
  const form = buildFormData(files, options, true);
  const { data } = await apiClient.post<WaferAnalysisResult[]>(
    "/predict/batch",
    form,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}
