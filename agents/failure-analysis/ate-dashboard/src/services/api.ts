import axios, { isAxiosError } from "axios";
import type { AnalysisErrorCode, AnalysisMetrics, DashboardCharts } from "@/stores/analysisStore";
import { configureApiClient } from "@/lib/http";

export const api = axios.create({
  baseURL: "/api/v1",
  timeout: 600_000,
});

configureApiClient(api);

export type UploadDatasetResponse = {
  execution_id: string;
  dataset_id: string;
  name?: string;
  status: string;
  file_count: number;
  stil_count?: number;
  log_count?: number;
  primary_upload_id?: string | null;
  stil_upload_id?: string | null;
  log_upload_ids?: string[];
  uploads?: Array<Record<string, unknown>>;
};

export type ExecutionStatusResponse = {
  execution_id: string;
  status: "pending" | "running" | "completed" | "failed" | string;
  progress: number;
  current_step?: string | null;
  label?: string | null;
  dataset_id?: string | null;
  upload_id?: string | null;
  metrics?: AnalysisMetrics | Record<string, unknown> | null;
  charts?: DashboardCharts | Record<string, unknown> | null;
  error?: string | null;
  processing_ms?: number;
};

export type StartPipelineResponse = {
  execution_id: string;
  upload_id?: string;
  dataset_id?: string | null;
  status: string;
  metrics?: AnalysisMetrics;
};

export function mapApiError(err: unknown): { message: string; code: AnalysisErrorCode } {
  if (isAxiosError(err)) {
    if (err.code === "ECONNABORTED") {
      return { message: "Backend Timeout", code: "backend_timeout" };
    }
    if (!err.response) {
      return { message: "Network Error", code: "network_error" };
    }
    const detail = err.response.data?.detail;
    const text =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d) => d.msg || JSON.stringify(d)).join("; ")
          : err.message;

    if (/stil/i.test(text)) {
      return { message: "Invalid STIL", code: "invalid_stil" };
    }
    if (/log|tester/i.test(text)) {
      return { message: "Invalid Tester Logs", code: "invalid_tester_logs" };
    }
    if (/pattern detection/i.test(text)) {
      return { message: "Pattern Detection Failed", code: "pattern_detection_failed" };
    }
    if (/failure-rate input validation/i.test(text)) {
      return {
        message:
          "Failure-rate validation failed. Include at least one failing die log with detected patterns, or upload all logs as a folder and retry.",
        code: "analysis_failed",
      };
    }
    if (err.response.status >= 500) {
      return { message: text || "Upload Failed", code: "upload_failed" };
    }
    return { message: text || "Upload Failed", code: "upload_failed" };
  }
  return {
    message: err instanceof Error ? err.message : "Upload Failed",
    code: "upload_failed",
  };
}

export async function uploadDatasetBundle(input: {
  stilFile: File;
  logFiles: File[];
  datasetName?: string;
  createdBy?: string;
}): Promise<UploadDatasetResponse> {
  const form = new FormData();
  form.append("stil_file", input.stilFile);
  for (const log of input.logFiles) {
    form.append("tester_logs", log);
  }
  if (input.datasetName?.trim()) {
    form.append("dataset_name", input.datasetName.trim());
  }
  form.append("created_by", input.createdBy || "ate-dashboard");
  form.append("async_process", "false");
  const { data } = await api.post<UploadDatasetResponse>("/datasets/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function startAnalysisPipeline(input: {
  executionId: string;
  uploadId: string;
  datasetId: string;
  importedFiles: number;
  datasetName?: string;
}): Promise<StartPipelineResponse> {
  const { data } = await api.post<StartPipelineResponse>("/evaluation/run", {
    execution_id: input.executionId,
    upload_id: input.uploadId,
    dataset_id: input.datasetId,
    imported_files: input.importedFiles,
    dataset_name: input.datasetName,
    async_execution: true,
  });
  return data;
}

export async function getExecutionStatus(
  executionId: string,
): Promise<ExecutionStatusResponse> {
  const { data } = await api.get<ExecutionStatusResponse>(
    `/evaluation/status/${executionId}`,
  );
  return data;
}

export async function getDataset(datasetId: string) {
  const { data } = await api.get(`/datasets/${datasetId}`);
  return data;
}
