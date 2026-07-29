import { isLiveApi } from "@/lib/api/config";
import {
  completeUpload,
  presignUpload,
  subscribeUploadEvents,
} from "@/lib/api/uploads";
import { invalidateDashboardCaches } from "@/lib/api/queryCache";
import { apiFetch } from "@/lib/api/client";

/** Human labels for enterprise Scan Chain pipeline stages (SSE `step`). */
export const PIPELINE_STAGE_LABELS: Record<string, string> = {
  uploading: "Uploading",
  validating: "Validating",
  detecting_format: "Detecting Format",
  parsing: "Parsing",
  generating_metadata: "Generating Metadata",
  normalizing: "Normalizing",
  running_pattern: "Running Pattern Analysis",
  running_failure: "Running Failure Analysis",
  running_scan_diagnosis: "Running Scan Diagnosis",
  aggregating: "Aggregating Results",
  saving: "Saving Results",
  refreshing_dashboard: "Refreshing Dashboard",
  completed: "Completed",
  failed: "Failed",
};

export function labelForPipelineStep(step: string | undefined | null): string {
  if (!step) return "Processing";
  return PIPELINE_STAGE_LABELS[step] ?? step.replace(/_/g, " ");
}

export async function retryPipelineJob(jobId: string, stage?: string): Promise<void> {
  await apiFetch(`/retry/${jobId}`, {
    method: "POST",
    body: stage ? { stage } : {},
  });
}

export async function fetchPipelineProgress(jobId: string): Promise<{
  status: string;
  step?: string;
  percent?: number;
  error?: string;
  failed_stage?: string;
}> {
  return apiFetch(`/progress/${jobId}`);
}

export async function fetchPipelineResults(jobId: string): Promise<Record<string, unknown>> {
  return apiFetch(`/results/${jobId}`);
}

export async function performFileUpload(
  file: File,
  module: string,
  metadata: Record<string, string>,
  kind: "data" | "log",
  onProgress: (percent: number, stepLabel?: string) => void
): Promise<string> {
  const presign = await presignUpload({
    file_name: file.name,
    size: file.size,
    module,
    metadata,
    kind,
  });

  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 90), labelForPipelineStep("uploading"));
      }
    };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error("Upload failed")));
    xhr.onerror = () => reject(new Error("Upload failed"));
    xhr.open("PUT", presign.upload_url);
    xhr.send(file);
  });

  await completeUpload(presign.job_id);
  onProgress(95, labelForPipelineStep("validating"));

  await new Promise<void>((resolve, reject) => {
    subscribeUploadEvents(presign.job_id, (event) => {
      const step = typeof event.step === "string" ? event.step : undefined;
      if (typeof event.percent === "number") {
        onProgress(Math.min(event.percent as number, 99), labelForPipelineStep(step));
      }
      if (event.status === "completed") resolve();
      if (event.status === "failed") {
        const stage = typeof event.failed_stage === "string" ? event.failed_stage : step;
        const detail =
          typeof event.error === "string" && event.error
            ? event.error
            : "Processing failed";
        reject(
          new Error(
            stage
              ? `Failed at ${labelForPipelineStep(stage)}: ${detail}`
              : detail
          )
        );
      }
    }).catch(reject);
  });

  onProgress(100, labelForPipelineStep("completed"));
  invalidateDashboardCaches(module);
  return presign.job_id;
}

export function shouldUseLiveUploads(): boolean {
  return isLiveApi();
}
