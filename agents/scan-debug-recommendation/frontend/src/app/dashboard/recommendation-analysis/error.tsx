"use client";

export default function RecommendationAnalysisError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="glass-card gradient-border mx-auto max-w-2xl p-6 text-center">
      <div className="text-[10px] uppercase tracking-[0.16em] text-warning">Page error</div>
      <h2 className="mt-2 font-display text-xl font-semibold text-white">
        Scan Debug dashboard failed to load
      </h2>
      <p className="mt-2 text-sm text-slate-400">
        Ensure the live API is running (see NEXT_PUBLIC_API_BASE_URL), then reload.
      </p>
      <p className="mt-3 rounded-lg bg-black/30 px-3 py-2 font-mono text-xs text-slate-500">
        {error.message}
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-4 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white hover:bg-primary/90"
      >
        Try again
      </button>
    </div>
  );
}
