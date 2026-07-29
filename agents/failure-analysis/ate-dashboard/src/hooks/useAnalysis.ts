"use client";

import { useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  mapApiError,
  startAnalysisPipeline,
  uploadDataset,
  validateUploadInputs,
} from "@/services/upload";
import { useAnalysisStore, type AnalysisErrorCode } from "@/stores/analysisStore";
import { useUploadStore } from "@/store/upload-store";
import { useInvalidateDashboard } from "@/hooks/useDashboard";
import { useExecutionPolling } from "@/hooks/usePolling";
import { notify } from "@/stores/toastStore";
import { useHistoryStore } from "@/stores/historyStore";

function errorCodeFromValidation(code?: string): AnalysisErrorCode {
  if (code === "invalid_stil") return "invalid_stil";
  if (code === "invalid_tester_logs") return "invalid_tester_logs";
  return "upload_failed";
}

export function useAnalysis() {
  const router = useRouter();
  const qc = useQueryClient();
  const stilFile = useUploadStore((s) => s.stilFile);
  const logFiles = useUploadStore((s) => s.logFiles);
  const datasetName = useUploadStore((s) => s.datasetName);

  const status = useAnalysisStore((s) => s.status);
  const progress = useAnalysisStore((s) => s.progress);
  const progressLabel = useAnalysisStore((s) => s.progressLabel);
  const executionId = useAnalysisStore((s) => s.executionId);
  const datasetId = useAnalysisStore((s) => s.datasetId);
  const error = useAnalysisStore((s) => s.error);
  const errorCode = useAnalysisStore((s) => s.errorCode);
  const toast = useAnalysisStore((s) => s.toast);
  const metrics = useAnalysisStore((s) => s.metrics);
  const setStatus = useAnalysisStore((s) => s.setStatus);
  const setContext = useAnalysisStore((s) => s.setContext);
  const setError = useAnalysisStore((s) => s.setError);
  const setToast = useAnalysisStore((s) => s.setToast);
  const setPolling = useAnalysisStore((s) => s.setPolling);
  const isPolling = useAnalysisStore((s) => s.isPolling);
  const prepareForNewUpload = useAnalysisStore((s) => s.prepareForNewUpload);
  const reset = useAnalysisStore((s) => s.reset);

  const invalidateDashboard = useInvalidateDashboard();
  const polling = useExecutionPolling(executionId);

  useEffect(() => {
    if (polling.isTerminal && polling.status === "completed" && executionId) {
      setToast("Analysis completed — KPIs updated from backend metrics.");
      notify({
        title: "Analysis Completed",
        description: "KPIs and workbench visualizations updated from backend metrics.",
        variant: "success",
      });
      useHistoryStore.getState().upsertEntry({
        execution_id: executionId,
        dataset_id: datasetId,
        status: "completed",
        user: "ate-dashboard",
      });
      void qc.invalidateQueries({ queryKey: ["uploads"] });
      void qc.invalidateQueries({ queryKey: ["datasets"] });
      void qc.invalidateQueries({ queryKey: ["ingestion-stats"] });
      void qc.invalidateQueries({ queryKey: ["analysis-history"] });
      invalidateDashboard(executionId);
      router.push("/overview");
    }
  }, [polling.isTerminal, polling.status, executionId, datasetId, router, qc, setToast, invalidateDashboard]);

  const mutation = useMutation({
    mutationFn: async () => {
      validateUploadInputs(stilFile, logFiles);
      setError(null);
      setToast(null);
      setStatus("validating", "Validating inputs…", 2);

      setStatus("uploading_files", "Uploading Files…", 8);
      notify({ title: "Upload Started", description: `Uploading STIL and ${logFiles.length} tester log(s).`, variant: "info" });
      const uploaded = await uploadDataset({
        stilFile: stilFile!,
        logFiles,
        datasetName,
        createdBy: "ate-dashboard",
      });

      setStatus("parsing_stil", "Parsing STIL…", 14);
      setStatus("reading_tester_logs", "Reading Tester Logs…", 18);
      setStatus("generating_dataset", "Generating Dataset…", 22);

      const uploadId =
        uploaded.primary_upload_id || uploaded.log_upload_ids?.[0] || null;
      if (!uploadId) {
        throw new Error("Upload succeeded but no upload_id was returned");
      }

      setContext({
        executionId: uploaded.execution_id,
        datasetId: uploaded.dataset_id,
        uploadId,
      });

      setStatus("pattern_detection", "Pattern Detection…", 28);
      setPolling(true);

      await startAnalysisPipeline({
        executionId: uploaded.execution_id,
        uploadId,
        datasetId: uploaded.dataset_id,
        importedFiles: uploaded.file_count || logFiles.length + 1,
        datasetName,
      });
      notify({
        title: "Analysis Started",
        description: `Pipeline execution ${uploaded.execution_id.slice(0, 8)}…`,
        variant: "info",
      });
      notify({
        title: "Upload Complete",
        description: `${uploaded.file_count || logFiles.length + 1} files ingested.`,
        variant: "success",
      });
      return uploaded;
    },
    onError: (err) => {
      const mapped = mapApiError(err);
      const code =
        err instanceof Error && "code" in err
          ? errorCodeFromValidation(String((err as Error & { code?: string }).code))
          : mapped.code;
      setError(mapped.message, code);
      setStatus("failed", mapped.message, progress);
      setPolling(false);
      setContext({ executionId: null, datasetId: null, uploadId: null, status: "failed" });
      notify({
        title: "Analysis Error",
        description: mapped.message,
        variant: "error",
      });
    },
  });

  const analyze = useCallback(() => mutation.mutate(), [mutation]);

  const busy = mutation.isPending || isPolling;

  const canAnalyze = Boolean(stilFile && logFiles.length > 0);

  return {
    analyze,
    busy,
    canAnalyze,
    status,
    progress,
    progressLabel,
    executionId,
    datasetId,
    metrics,
    error,
    errorCode,
    toast,
    reset,
    prepareForNewUpload,
    setError,
    setToast,
    isPending: mutation.isPending,
    isPolling,
    polling,
  };
}
