"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { useAnalysisMonitor } from "@/hooks/useAnalysisMonitor";

function formatDuration(ms: number) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return m > 0 ? `${m}m ${rem}s` : `${s}s`;
}

export const LiveAnalysisMonitor = memo(function LiveAnalysisMonitor() {
  const {
    stages,
    status,
    progress,
    currentStage,
    activeIdx,
    elapsedMs,
    estimatedRemainingMs,
    isActive,
  } = useAnalysisMonitor();

  if (!isActive && status !== "completed") return null;

  return (
    <div className="glass-panel rounded-2xl p-5" data-testid="live-analysis-monitor">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
            Live Analysis Monitor
          </h3>
          <p className="mt-1 text-lg font-medium">{currentStage}</p>
        </div>
        <div className="text-right text-sm">
          <div className="font-mono text-[var(--accent)]">{Math.round(progress)}%</div>
          <div className="text-xs text-[var(--muted)]">
            Elapsed {formatDuration(elapsedMs)}
            {estimatedRemainingMs > 0 && ` · ETA ${formatDuration(estimatedRemainingMs)}`}
          </div>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-[var(--accent)] to-sky-400"
          animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          transition={{ type: "spring", stiffness: 90, damping: 18 }}
        />
      </div>

      <ol className="mt-4 grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
        {stages.map((stage, idx) => {
          const done = status === "completed" || (activeIdx >= 0 && idx < activeIdx);
          const active = stage.key === status;
          return (
            <motion.li
              key={stage.key}
              animate={active ? { scale: [1, 1.02, 1] } : { scale: 1 }}
              transition={{ repeat: active ? Infinity : 0, duration: 1.6 }}
              className={`rounded-lg px-2 py-1 text-xs ${
                active
                  ? "bg-[var(--accent-soft)] text-[var(--accent)]"
                  : done
                    ? "text-[var(--success)]"
                    : "text-[var(--muted)]"
              }`}
            >
              {done ? "✓ " : active ? "● " : "○ "}
              {stage.label}
            </motion.li>
          );
        })}
      </ol>
    </div>
  );
});
