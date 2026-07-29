"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import type { FaultPredictionSummary } from "@/lib/api";

type Props = {
  predictions: FaultPredictionSummary[];
  averageConfidence?: number;
};

export const RootCausePanel = memo(function RootCausePanel({
  predictions,
  averageConfidence = 0,
}: Props) {
  const top = predictions.slice(0, 8);
  const confPct = averageConfidence <= 1 ? averageConfidence * 100 : averageConfidence;

  if (!predictions.length) {
    return (
      <div className="glass-panel rounded-2xl p-6 text-sm text-[var(--muted)]" data-testid="root-cause-panel">
        Root cause predictions appear after FA-FR-009 completes on the backend.
      </div>
    );
  }

  return (
    <div className="glass-panel space-y-4 rounded-2xl p-4" data-testid="root-cause-panel">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Root Cause Dashboard
        </h3>
        <div className="text-right">
          <div className="text-xs text-[var(--muted)]">Confidence Gauge</div>
          <div className="text-2xl font-semibold text-[var(--accent)]">{confPct.toFixed(1)}%</div>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full bg-[var(--accent)]"
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, confPct)}%` }}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div>
          <h4 className="mb-2 text-xs uppercase text-[var(--muted)]">Timeline</h4>
          <ol className="space-y-2 border-l border-white/10 pl-3">
            {top.map((p, i) => (
              <li key={p.prediction_id} className="text-sm">
                <span className="font-mono text-xs text-[var(--muted)]">T+{i + 1}</span>
                <div>{p.predicted_fault_type}</div>
                <div className="text-xs text-[var(--muted)]">
                  {p.pattern_id} · {(p.confidence_score * 100).toFixed(0)}%
                </div>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <h4 className="mb-2 text-xs uppercase text-[var(--muted)]">Evidence & Recommendations</h4>
          <ul className="max-h-48 space-y-2 overflow-auto text-sm">
            {top.map((p) => (
              <li key={`${p.prediction_id}-rec`} className="rounded-lg bg-white/5 p-2">
                <div className="font-medium">{p.predicted_fault_type}</div>
                <div className="text-xs text-[var(--muted)]">
                  {p.engineering_explanation ||
                    p.recommended_investigation_steps?.[0] ||
                    "See full prediction drill-down."}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
});
