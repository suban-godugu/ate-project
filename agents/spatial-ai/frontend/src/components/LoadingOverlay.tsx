"use client";

import { useAnalysis } from "@/context/AnalysisContext";

export function LoadingOverlay() {
  const { isAnalyzing } = useAnalysis();
  if (!isAnalyzing) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/40 backdrop-blur-sm">
      <div className="panel w-full max-w-sm p-6 text-center">
        <div className="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-2 border-ink-300 border-t-ink-800 dark:border-ink-600 dark:border-t-ink-100" />
        <p className="font-medium">Running wafer analysis</p>
        <p className="mt-1 text-xs text-[var(--muted)]">
          Waiting for FastAPI · POST /predict or /predict/batch
        </p>
        <div className="mt-4 space-y-2">
          <div className="skeleton h-3 w-full" />
          <div className="skeleton h-3 w-4/5" />
          <div className="skeleton h-3 w-3/5" />
        </div>
      </div>
    </div>
  );
}
