"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";

export function LoadingOverlay() {
  const { isAnalyzing } = useAnalysis();
  if (!isAnalyzing) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/55 backdrop-blur-sm">
      <div className="panel mx-4 w-full max-w-md space-y-4 p-6 text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-[#7C3AED] border-t-transparent" />
        <div>
          <p className="text-base font-semibold text-[var(--text)]">Running wafer analysis</p>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Waiting for FastAPI · POST /predict or /predict/batch
          </p>
        </div>
        <div className="space-y-2">
          <div className="skeleton h-2 w-full" />
          <div className="skeleton mx-auto h-2 w-[85%]" />
          <div className="skeleton mx-auto h-2 w-[65%]" />
        </div>
      </div>
    </div>
  );
}
