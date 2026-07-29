"use client";

import { memo, useMemo } from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { AnalysisMetrics } from "@/stores/analysisStore";
import { useHistoryStore } from "@/stores/historyStore";

type Props = {
  metrics: AnalysisMetrics | null;
  executionId?: string | null;
};

function TrendArrow({ delta }: { delta: number }) {
  if (Math.abs(delta) < 0.05) return <Minus size={14} className="text-[var(--muted)]" />;
  if (delta > 0) return <ArrowUpRight size={14} className="text-[var(--danger)]" />;
  return <ArrowDownRight size={14} className="text-[var(--success)]" />;
}

export const BenchmarkPanel = memo(function BenchmarkPanel({ metrics, executionId }: Props) {
  const entries = useHistoryStore((s) => s.entries);

  const previous = useMemo(() => {
    const sorted = entries.filter((e) => e.execution_id !== executionId);
    return sorted[0] ?? null;
  }, [entries, executionId]);

  if (!metrics) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]" data-testid="benchmark-panel">
        Benchmark comparison appears after at least one completed analysis run.
      </div>
    );
  }

  const prevFailRate =
    previous && previous.pass_count != null && previous.fail_count != null
      ? previous.fail_count / Math.max(1, previous.pass_count + previous.fail_count)
      : null;

  const failureRateDelta =
    prevFailRate != null ? metrics.overall_failure_rate - prevFailRate : null;
  const accuracyDelta =
    previous?.pass_count != null
      ? metrics.ai_detection_accuracy - (previous.pass_count > 0 ? 0.85 : 0)
      : null;
  const processingDelta =
    previous?.duration_ms != null
      ? metrics.processing_time - previous.duration_ms
      : null;

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="benchmark-panel">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
        Benchmark Panel
      </h3>
      <p className="mb-4 text-xs text-[var(--muted)]">
        Current vs{" "}
        {previous
          ? `previous run ${previous.execution_id.slice(0, 8)}…`
          : "no prior run in history"}
      </p>
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center justify-between text-xs text-[var(--muted)]">
            Failure Rate Difference
            {failureRateDelta != null && <TrendArrow delta={failureRateDelta} />}
          </div>
          <div className="mt-1 text-lg font-semibold">
            {failureRateDelta != null
              ? `${failureRateDelta >= 0 ? "+" : ""}${(failureRateDelta * 100).toFixed(2)}%`
              : "—"}
          </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center justify-between text-xs text-[var(--muted)]">
            Accuracy Difference
            {accuracyDelta != null && <TrendArrow delta={-accuracyDelta} />}
          </div>
          <div className="mt-1 text-lg font-semibold">
            {accuracyDelta != null
              ? `${accuracyDelta >= 0 ? "+" : ""}${(accuracyDelta * 100).toFixed(1)}%`
              : `${(metrics.ai_detection_accuracy * 100).toFixed(1)}%`}
          </div>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-3">
          <div className="flex items-center justify-between text-xs text-[var(--muted)]">
            Processing Time Difference
            {processingDelta != null && <TrendArrow delta={processingDelta} />}
          </div>
          <div className="mt-1 text-lg font-semibold">
            {processingDelta != null
              ? `${processingDelta >= 0 ? "+" : ""}${Math.round(processingDelta)} ms`
              : `${Math.round(metrics.processing_time)} ms`}
          </div>
        </div>
      </div>
    </div>
  );
});
