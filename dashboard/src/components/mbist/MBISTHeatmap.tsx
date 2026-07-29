"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useFilteredMbistData } from "@/hooks/useMbistData";

function heatColor(value: number): string {
  if (value >= 0.85) return "#EF4444";
  if (value >= 0.65) return "#F97316";
  if (value >= 0.35) return "#EAB308";
  return "#22C55E";
}

const ROWS = 14;
const COLS = 20;

export function MBISTHeatmap() {
  const { generateMemoryHeatmap } = useFilteredMbistData();
  const heatData = useMemo(() => generateMemoryHeatmap(ROWS, COLS), [generateMemoryHeatmap]);

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Memory Heatmap</h3>
          <p className="text-sm text-slate-400">Spatial memory health across instance grid</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#22C55E]" /> Healthy</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#EAB308]" /> Warning</span>
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
              title={`Memory [${cell.row}, ${cell.col}]: ${(cell.value * 100).toFixed(0)}%`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
