"use client";

import { create } from "zustand";

export type AnalysisStatus =
  | "idle"
  | "validating"
  | "uploading"
  | "parsing_stil"
  | "reading_logs"
  | "pattern_detection"
  | "failure_analysis"
  | "classification"
  | "recurrence"
  | "correlation"
  | "die_analysis"
  | "wafer_analysis"
  | "root_cause"
  | "reporting"
  | "completed"
  | "failed";

export type AnalysisMetrics = {
  imported_files: number;
  overall_failure_rate: number;
  ai_detection_accuracy: number;
  failing_patterns: number;
  die_failure_rate: number;
  wafer_failure_rate: number;
  lot_failure_rate: number;
  fault_categories: number;
  root_cause_confidence: number;
  recurring_failures: number;
  failure_correlations: number;
  reports_generated: number;
};

export type QueueItem = {
  id: string;
  name: string;
  size: number;
  status: "queued" | "uploading" | "processing" | "completed" | "failed";
  progress: number;
  uploadId?: string;
  error?: string;
  relativePath?: string;
};

export type AnalysisResult = {
  execution_id: string;
  dataset_id: string;
  primary_upload_id?: string | null;
  stil_upload_id?: string | null;
  log_upload_ids?: string[];
  status: string;
  metrics: AnalysisMetrics;
  warnings?: string[];
  steps?: Array<{ step: string; status: string; error?: string }>;
};

type UploadState = {
  stilFile: File | null;
  logFiles: File[];
  datasetName: string;
  analysisStatus: AnalysisStatus;
  progress: number;
  progressLabel: string;
  executionId: string | null;
  datasetId: string | null;
  primaryUploadId: string | null;
  analysisResult: AnalysisResult | null;
  error: string | null;
  toast: string | null;
  queue: QueueItem[];
  selectedUploadId: string | null;

  setStilFile: (file: File | null) => void;
  setLogFiles: (files: File[]) => void;
  addLogFiles: (files: File[]) => void;
  removeLogFile: (name: string) => void;
  setDatasetName: (name: string) => void;
  setAnalysisStatus: (status: AnalysisStatus, label?: string, progress?: number) => void;
  setProgress: (progress: number, label?: string) => void;
  setAnalysisResult: (result: AnalysisResult | null) => void;
  setError: (error: string | null) => void;
  setToast: (toast: string | null) => void;
  setExecutionContext: (ctx: {
    executionId?: string | null;
    datasetId?: string | null;
    primaryUploadId?: string | null;
  }) => void;
  resetAnalysis: () => void;
  canAnalyze: () => boolean;

  setSelectedUploadId: (id: string | null) => void;
  upsertQueueItem: (item: QueueItem) => void;
  updateQueueItem: (id: string, patch: Partial<QueueItem>) => void;
  clearCompleted: () => void;
};

const emptyMetrics = (): AnalysisMetrics => ({
  imported_files: 0,
  overall_failure_rate: 0,
  ai_detection_accuracy: 0,
  failing_patterns: 0,
  die_failure_rate: 0,
  wafer_failure_rate: 0,
  lot_failure_rate: 0,
  fault_categories: 0,
  root_cause_confidence: 0,
  recurring_failures: 0,
  failure_correlations: 0,
  reports_generated: 0,
});

export const useUploadStore = create<UploadState>((set, get) => ({
  stilFile: null,
  logFiles: [],
  datasetName: "",
  analysisStatus: "idle",
  progress: 0,
  progressLabel: "Waiting for STIL and tester logs",
  executionId: null,
  datasetId: null,
  primaryUploadId: null,
  analysisResult: null,
  error: null,
  toast: null,
  queue: [],
  selectedUploadId: null,

  setStilFile: (file) => set({ stilFile: file, error: null }),
  setLogFiles: (files) => set({ logFiles: files, error: null }),
  addLogFiles: (files) =>
    set((state) => {
      const byKey = new Map(state.logFiles.map((f) => {
        const relative = (f as File & { webkitRelativePath?: string }).webkitRelativePath;
        const key = relative ? `${relative}:${f.size}` : `${f.name}:${f.size}`;
        return [key, f];
      }));
      for (const f of files) {
        const relative = (f as File & { webkitRelativePath?: string }).webkitRelativePath;
        const key = relative ? `${relative}:${f.size}` : `${f.name}:${f.size}`;
        byKey.set(key, f);
      }
      return { logFiles: Array.from(byKey.values()), error: null };
    }),
  removeLogFile: (name) =>
    set((state) => ({
      logFiles: state.logFiles.filter((f) => f.name !== name),
    })),
  setDatasetName: (name) => set({ datasetName: name }),
  setAnalysisStatus: (status, label, progress) =>
    set((state) => ({
      analysisStatus: status,
      progressLabel: label ?? state.progressLabel,
      progress: progress ?? state.progress,
    })),
  setProgress: (progress, label) =>
    set((state) => ({
      progress,
      progressLabel: label ?? state.progressLabel,
    })),
  setAnalysisResult: (result) => set({ analysisResult: result }),
  setError: (error) => set({ error }),
  setToast: (toast) => set({ toast }),
  setExecutionContext: (ctx) =>
    set({
      executionId: ctx.executionId ?? null,
      datasetId: ctx.datasetId ?? null,
      primaryUploadId: ctx.primaryUploadId ?? null,
    }),
  resetAnalysis: () =>
    set({
      analysisStatus: "idle",
      progress: 0,
      progressLabel: "Waiting for STIL and tester logs",
      executionId: null,
      datasetId: null,
      primaryUploadId: null,
      analysisResult: null,
      error: null,
    }),
  canAnalyze: () => Boolean(get().stilFile && get().logFiles.length > 0),

  setSelectedUploadId: (id) => set({ selectedUploadId: id }),
  upsertQueueItem: (item) =>
    set((state) => {
      const idx = state.queue.findIndex((q) => q.id === item.id);
      if (idx === -1) return { queue: [item, ...state.queue] };
      const next = [...state.queue];
      next[idx] = item;
      return { queue: next };
    }),
  updateQueueItem: (id, patch) =>
    set((state) => ({
      queue: state.queue.map((q) => (q.id === id ? { ...q, ...patch } : q)),
    })),
  clearCompleted: () =>
    set((state) => ({
      queue: state.queue.filter((q) => q.status !== "completed"),
    })),
}));

export { emptyMetrics };
