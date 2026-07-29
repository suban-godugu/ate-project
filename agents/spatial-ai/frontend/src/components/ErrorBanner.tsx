"use client";

import { useAnalysis } from "@/context/AnalysisContext";

export function ErrorBanner() {
  const { error, clearError } = useAnalysis();
  if (!error) return null;

  return (
    <div className="mb-4 flex items-start justify-between gap-3 rounded-xl border border-signal-fail/40 bg-signal-fail/10 px-4 py-3 text-sm text-signal-fail">
      <p>{error}</p>
      <button type="button" className="underline" onClick={clearError}>
        Dismiss
      </button>
    </div>
  );
}
