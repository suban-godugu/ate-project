"use client";

import { X } from "lucide-react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";

export function ErrorBanner() {
  const { error, clearError } = useAnalysis();
  if (!error) return null;

  return (
    <div
      role="alert"
      className="mx-auto mb-0 flex max-w-[1800px] items-start gap-3 rounded-lg border border-signal-fail/40 bg-signal-fail/10 px-4 py-3 text-sm text-signal-fail md:px-6"
    >
      <p className="flex-1">{error}</p>
      <button
        type="button"
        onClick={clearError}
        className="shrink-0 rounded p-1 hover:bg-signal-fail/20"
        aria-label="Dismiss error"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
