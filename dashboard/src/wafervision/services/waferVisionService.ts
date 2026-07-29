import { getAccessToken, getApiBaseUrl } from "@/lib/api/config";
import { refreshAccessToken } from "@/lib/api/authRefresh";
import { ApiError } from "@/lib/api/client";
import type { GridMode, WaferAnalysisResult } from "@/wafervision/types";

/** Fail the spinner if FastAPI hangs (was the root cause of endless "Running wafer analysis"). */
const PREDICT_TIMEOUT_MS = 60_000;

function getWaferApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_WAFER_API_URL?.trim() || getApiBaseUrl();
}

async function multipartFetch<T>(path: string, buildForm: () => FormData): Promise<T> {
  const url = `${getWaferApiBaseUrl()}${path}`;
  let token = getAccessToken();

  const send = (authToken: string | null) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), PREDICT_TIMEOUT_MS);
    return fetch(url, {
      method: "POST",
      headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      body: buildForm(),
      signal: controller.signal,
    }).finally(() => clearTimeout(timer));
  };

  let res: Response;
  try {
    res = await send(token);
    if (res.status === 401) {
      token = await refreshAccessToken();
      res = await send(token);
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(
        "Wafer analysis timed out waiting for FastAPI /predict. Is the backend running?",
        408,
        { detail: "predict_timeout" }
      );
    }
    throw err;
  }

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    throw new ApiError(`API ${res.status}: ${res.statusText}`, res.status, detail);
  }
  return res.json() as Promise<T>;
}

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body as { detail?: unknown; message?: string } | undefined;
    if (error.status === 408) {
      return error.message;
    }
    if (error.status === 401) {
      return "Not authenticated — log in, then run Analyze Wafer again.";
    }
    if (error.status === 415) {
      return "Invalid image type. Use JPG, JPEG, PNG, or BMP.";
    }
    if (error.status >= 500) {
      return "Backend error while running wafer analysis.";
    }
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) =>
          typeof d === "object" && d && "msg" in d
            ? String((d as { msg: string }).msg)
            : String(d)
        )
        .join("; ");
    }
    if (body?.message) return body.message;
    return error.message;
  }
  if (error instanceof TypeError) {
    const base = getWaferApiBaseUrl();
    let host = base;
    try {
      host = new URL(base).host;
    } catch {
      // keep raw base string
    }
    return `Network error — unable to reach the analysis API at ${host}. Is the Spatial AI Agent running?`;
  }
  return error instanceof Error ? error.message : "Unexpected error";
}

function appendGridFields(form: FormData, gridMode: GridMode, gridSize: number) {
  form.append("grid_mode", gridMode);
  if (gridMode === "manual") form.append("grid_size", String(gridSize));
  // Panels render `visualization` JSON on canvas over the wafer photo, so the
  // original PNG is the only panel image worth transferring.
  form.append("include_images", "original");
}

export async function predictSingle(
  file: File,
  gridMode: GridMode,
  gridSize: number
): Promise<WaferAnalysisResult> {
  return multipartFetch<WaferAnalysisResult>("/predict", () => {
    const form = new FormData();
    form.append("image", file);
    appendGridFields(form, gridMode, gridSize);
    return form;
  });
}

export async function predictBatch(
  files: File[],
  gridMode: GridMode,
  gridSize: number
): Promise<WaferAnalysisResult[]> {
  return multipartFetch<WaferAnalysisResult[]>("/predict/batch", () => {
    const form = new FormData();
    for (const file of files) form.append("images", file);
    appendGridFields(form, gridMode, gridSize);
    return form;
  });
}

export async function runPrediction(
  files: File[],
  gridMode: GridMode,
  gridSize: number
): Promise<WaferAnalysisResult[]> {
  if (files.length === 1) {
    return [await predictSingle(files[0], gridMode, gridSize)];
  }
  return predictBatch(files, gridMode, gridSize);
}
