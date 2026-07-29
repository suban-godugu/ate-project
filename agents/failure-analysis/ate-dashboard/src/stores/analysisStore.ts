"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AnalysisMetrics = {
  imported_test_files: number;
  overall_failure_rate: number;
  ai_detection_accuracy: number;
  failing_test_patterns: number;
  die_failure_rate: number;
  wafer_failure_rate: number;
  lot_failure_rate: number;
  fault_categories: number;
  root_cause_confidence: number;
  recurring_failures: number;
  failure_correlations: number;
  failure_reports: number;
  processing_time: number;
  total_tests: number;
  total_failed: number;
  total_passed: number;
};

export type DashboardCharts = {
  failure_trend: Array<{ label: string; rate: number; level?: string }>;
  failure_distribution: Array<{ name: string; count: number }>;
  category_distribution: Array<{ category: string; count: number }>;
  pass_vs_fail: Array<{ name: string; value: number }>;
  wafer_heatmap: Array<{ x: number; y: number; intensity: number; wafer_id?: string }>;
  die_heatmap: Array<{ x: number; y: number; intensity: number; die_id?: string }>;
  correlation_graph: Record<string, unknown>;
};

export type AnalysisStepStatus =
  | "idle"
  | "validating"
  | "uploading_files"
  | "parsing_stil"
  | "reading_tester_logs"
  | "generating_dataset"
  | "pattern_detection"
  | "failure_rate"
  | "classification"
  | "recurrence"
  | "correlation"
  | "die_analysis"
  | "wafer_analysis"
  | "root_cause"
  | "evaluation"
  | "reporting"
  | "completed"
  | "failed";

export type AnalysisErrorCode =
  | "upload_failed"
  | "pattern_detection_failed"
  | "backend_timeout"
  | "invalid_stil"
  | "invalid_tester_logs"
  | "network_error"
  | "pipeline_failed"
  | "no_dataset"
  | "no_metrics"
  | "analysis_failed"
  | "backend_unavailable";

export type DashboardSnapshot = {
  executionId: string | null;
  datasetId: string | null;
  uploadId: string | null;
  status: string | null;
};

type AnalysisState = {
  status: AnalysisStepStatus;
  progress: number;
  progressLabel: string;
  dataset: DashboardSnapshot;
  execution: DashboardSnapshot;
  metrics: AnalysisMetrics | null;
  charts: DashboardCharts | null;
  loading: boolean;
  error: string | null;
  errorCode: AnalysisErrorCode | null;
  toast: string | null;
  isPolling: boolean;

  setStatus: (status: AnalysisStepStatus, label?: string, progress?: number) => void;
  setContext: (ctx: {
    executionId?: string | null;
    datasetId?: string | null;
    uploadId?: string | null;
    status?: string | null;
  }) => void;
  prepareForNewUpload: () => void;
  setMetrics: (metrics: AnalysisMetrics | null) => void;
  setCharts: (charts: DashboardCharts | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null, code?: AnalysisErrorCode | null) => void;
  setToast: (toast: string | null) => void;
  setPolling: (isPolling: boolean) => void;
  applyDashboard: (payload: {
    execution_id: string;
    dataset_id?: string | null;
    upload_id?: string | null;
    status: string;
    metrics?: AnalysisMetrics | null;
    charts?: DashboardCharts | null;
  }) => void;
  reset: () => void;

  /** @deprecated use dataset.executionId via selectors */
  datasetId: string | null;
  /** @deprecated */
  executionId: string | null;
  /** @deprecated */
  uploadId: string | null;
};

const emptyCharts = (): DashboardCharts => ({
  failure_trend: [],
  failure_distribution: [],
  category_distribution: [],
  pass_vs_fail: [],
  wafer_heatmap: [],
  die_heatmap: [],
  correlation_graph: {},
});

const initialState = {
  status: "idle" as AnalysisStepStatus,
  progress: 0,
  progressLabel: "Waiting for STIL and tester logs",
  dataset: { executionId: null, datasetId: null, uploadId: null, status: null },
  execution: { executionId: null, datasetId: null, uploadId: null, status: null },
  metrics: null,
  charts: null,
  loading: false,
  error: null,
  errorCode: null,
  toast: null,
  isPolling: false,
  datasetId: null,
  executionId: null,
  uploadId: null,
};

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      ...initialState,

      setStatus: (status, label, progress) =>
        set((state) => ({
          status,
          progressLabel: label !== undefined ? label : state.progressLabel,
          progress: progress !== undefined ? progress : state.progress,
        })),

      setContext: (ctx) =>
        set((state) => {
          const snapshot: DashboardSnapshot = {
            executionId:
              "executionId" in ctx ? (ctx.executionId ?? null) : state.execution.executionId,
            datasetId:
              "datasetId" in ctx ? (ctx.datasetId ?? null) : state.execution.datasetId,
            uploadId: "uploadId" in ctx ? (ctx.uploadId ?? null) : state.execution.uploadId,
            status: "status" in ctx ? (ctx.status ?? null) : state.execution.status,
          };
          return {
            execution: snapshot,
            dataset: snapshot,
            executionId: snapshot.executionId,
            datasetId: snapshot.datasetId,
            uploadId: snapshot.uploadId,
          };
        }),

      prepareForNewUpload: () =>
        set((state) => {
          if (state.isPolling) return state;
          const active =
            state.status !== "idle" &&
            state.status !== "completed" &&
            state.status !== "failed";
          if (active) return state;
          return {
            status: "idle" as AnalysisStepStatus,
            progress: 0,
            progressLabel: "Waiting for STIL and tester logs",
            error: null,
            errorCode: null,
            toast: null,
            isPolling: false,
            loading: false,
            execution: {
              executionId: null,
              datasetId: null,
              uploadId: null,
              status: null,
            },
            dataset: {
              executionId: null,
              datasetId: null,
              uploadId: null,
              status: null,
            },
            executionId: null,
            datasetId: null,
            uploadId: null,
          };
        }),

      setMetrics: (metrics) => set({ metrics }),

      setCharts: (charts) => set({ charts }),

      setLoading: (loading) => set({ loading }),

      setError: (error, code = null) => set({ error, errorCode: code }),

      setToast: (toast) => set({ toast }),

      setPolling: (isPolling) => set({ isPolling, loading: isPolling }),

      applyDashboard: (payload) =>
        set({
          metrics: payload.metrics ?? null,
          charts: payload.charts ?? emptyCharts(),
          loading: false,
          execution: {
            executionId: payload.execution_id,
            datasetId: payload.dataset_id ?? null,
            uploadId: payload.upload_id ?? null,
            status: payload.status,
          },
          dataset: {
            executionId: payload.execution_id,
            datasetId: payload.dataset_id ?? null,
            uploadId: payload.upload_id ?? null,
            status: payload.status,
          },
          executionId: payload.execution_id,
          datasetId: payload.dataset_id ?? null,
          uploadId: payload.upload_id ?? null,
        }),

      reset: () => set({ ...initialState, charts: emptyCharts() }),
    }),
    {
      name: "fa-analysis-dashboard",
      partialize: (state) => ({
        executionId: state.executionId,
        datasetId: state.datasetId,
        uploadId: state.uploadId,
        execution: state.execution,
        dataset: state.dataset,
        metrics: state.metrics,
        charts: state.charts,
      }),
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        state.status = "idle";
        state.progress = 0;
        state.progressLabel = "Waiting for STIL and tester logs";
        state.isPolling = false;
        state.loading = false;
        state.error = null;
        state.errorCode = null;
        state.toast = null;
      },
    },
  ),
);

export { emptyCharts };
