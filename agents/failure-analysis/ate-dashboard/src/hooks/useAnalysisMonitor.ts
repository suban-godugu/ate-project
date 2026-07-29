"use client";

import { useEffect, useMemo, useRef } from "react";
import { useAnalysisStore, type AnalysisStepStatus } from "@/stores/analysisStore";

const STAGES: Array<{ key: AnalysisStepStatus; label: string }> = [
  { key: "uploading_files", label: "Uploading" },
  { key: "generating_dataset", label: "Ingestion" },
  { key: "parsing_stil", label: "STIL Parsing" },
  { key: "reading_tester_logs", label: "Log Parsing" },
  { key: "pattern_detection", label: "Pattern Detection" },
  { key: "failure_rate", label: "Failure Rate" },
  { key: "classification", label: "Classification" },
  { key: "correlation", label: "Correlation" },
  { key: "die_analysis", label: "Die Analysis" },
  { key: "wafer_analysis", label: "Wafer Analysis" },
  { key: "root_cause", label: "Root Cause" },
  { key: "evaluation", label: "Evaluation" },
  { key: "reporting", label: "Reporting" },
  { key: "completed", label: "Completed" },
];

export function useAnalysisMonitor() {
  const status = useAnalysisStore((s) => s.status);
  const progress = useAnalysisStore((s) => s.progress);
  const progressLabel = useAnalysisStore((s) => s.progressLabel);
  const isPolling = useAnalysisStore((s) => s.isPolling);
  const startedAtRef = useRef<number | null>(null);

  useEffect(() => {
    if (isPolling && startedAtRef.current == null) {
      startedAtRef.current = Date.now();
    }
    if (status === "completed" || status === "failed") {
      startedAtRef.current = startedAtRef.current ?? Date.now();
    }
    if (status === "idle") {
      startedAtRef.current = null;
    }
  }, [isPolling, status]);

  const elapsedMs = useMemo(() => {
    if (!startedAtRef.current) return 0;
    return Date.now() - startedAtRef.current;
  }, [status, progress, isPolling]);

  const estimatedRemainingMs = useMemo(() => {
    if (progress <= 0 || progress >= 100) return 0;
    const elapsed = startedAtRef.current ? Date.now() - startedAtRef.current : 0;
    if (!elapsed) return 0;
    const totalEstimate = (elapsed / progress) * 100;
    return Math.max(0, Math.round(totalEstimate - elapsed));
  }, [progress, status, isPolling]);

  const activeIdx = STAGES.findIndex((s) => s.key === status);
  const currentStage = STAGES[activeIdx]?.label || progressLabel || "Idle";

  return {
    stages: STAGES,
    status,
    progress,
    progressLabel,
    currentStage,
    activeIdx,
    elapsedMs,
    estimatedRemainingMs,
    isActive: isPolling || (status !== "idle" && status !== "completed" && status !== "failed"),
  };
}
