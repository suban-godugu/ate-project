"use client";

import { motion } from "framer-motion";
import type { FailureCorrelationMatrix } from "@/types/scanChain";

function cellColor(value: number): string {
  const alpha = 0.15 + (value / 100) * 0.85;
  return `rgba(124, 58, 237, ${alpha})`;
}

export function FailureCorrelationHeatmap({ data }: { data: FailureCorrelationMatrix }) {
  const { grid, rowLabels, colLabels } = data;
  const cols = grid[0]?.length ?? 0;

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Failure Correlation Matrix</h3>
          <p className="text-sm text-slate-400">
            Cross-dimensional failure correlation — Pattern, Chain, Failure, Lot, Wafer
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-400">
          <span>Correlation</span>
          <span className="h-3 w-8 rounded-sm bg-[#7C3AED]/20" />
          <span>→</span>
          <span className="h-3 w-8 rounded-sm bg-[#7C3AED]" />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl bg-[#0A1020]/60 p-4">
        <div className="inline-flex min-w-full flex-col gap-1">
          <div
            className="grid gap-1"
            style={{ gridTemplateColumns: `72px repeat(${cols}, minmax(48px, 1fr))` }}
          >
            <div />
            {colLabels.map((label) => (
              <div
                key={label}
                className="truncate text-center text-[10px] font-medium text-slate-400"
              >
                {label}
              </div>
            ))}
          </div>

          {grid.map((row, ri) => (
            <div
              key={rowLabels[ri]}
              className="grid gap-1"
              style={{ gridTemplateColumns: `72px repeat(${cols}, minmax(48px, 1fr))` }}
            >
              <div className="flex items-center text-[10px] font-medium text-slate-400">
                {rowLabels[ri]}
              </div>
              {row.map((cell, ci) => (
                <motion.div
                  key={`${ri}-${ci}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: (ri * cols + ci) * 0.02 }}
                  className="flex aspect-square items-center justify-center rounded-md text-[10px] font-medium text-white/80 transition-transform hover:scale-105"
                  style={{ backgroundColor: cellColor(cell) }}
                  title={`${rowLabels[ri]} × ${colLabels[ci]}: ${cell}%`}
                >
                  {cell}
                </motion.div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
