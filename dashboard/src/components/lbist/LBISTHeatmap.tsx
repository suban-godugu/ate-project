"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useFilteredLbistData } from "@/hooks/useLbistData";

function heatColor(value: number): string {
  if (value >= 0.85) return "#EF4444";
  if (value >= 0.65) return "#F97316";
  if (value >= 0.35) return "#EAB308";
  return "#22C55E";
}

const ROWS = 14;
const COLS = 22;

export function LBISTHeatmap() {
  const { generateCoverageHeatmap } = useFilteredLbistData();
  const heatData = useMemo(() => generateCoverageHeatmap(ROWS, COLS), [generateCoverageHeatmap]);

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Logic Coverage Heatmap</h3>
          <p className="text-sm text-slate-400">Spatial logic block coverage across die grid</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#22C55E]" /> Covered</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#EAB308]" /> Partial</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#F97316]" /> Critical</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#EF4444]" /> Failed</span>
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl bg-[#0A1020]/60 p-4">
        <div className="mx-auto grid gap-[2px]" style={{ gridTemplateColumns: `repeat(${COLS}, minmax(0, 1fr))`, maxWidth: COLS * 18 }}>
          {heatData.map((cell, i) => (
            <motion.div
              key={`${cell.row}-${cell.col}`}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.001, duration: 0.2 }}
              className="aspect-square rounded-[3px] transition-transform hover:scale-125 hover:z-10"
              style={{ backgroundColor: heatColor(cell.value) }}
              title={`Block [${cell.row}, ${cell.col}]: ${(cell.value * 100).toFixed(0)}%`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
