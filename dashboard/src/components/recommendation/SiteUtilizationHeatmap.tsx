"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";

function heatColor(value: number): string {
  if (value >= 0.75) return "#EF4444";
  if (value >= 0.5) return "#F97316";
  if (value >= 0.25) return "#EAB308";
  return "#22C55E";
}

interface SiteUtilizationHeatmapProps {
  data: { value: number; row: number; col: number }[];
  rows: number;
  cols: number;
}

export function SiteUtilizationHeatmap({ data, rows, cols }: SiteUtilizationHeatmapProps) {
  const labels = useMemo(
    () => Array.from({ length: cols }, (_, i) => `Site ${i + 1}`),
    [cols]
  );

  return (
    <div className="overflow-x-auto rounded-xl bg-[#0A1020]/60 p-4">
      <div
        className="mx-auto grid gap-2"
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`, maxWidth: cols * 72 }}
      >
        {data.map((cell, i) => (
          <motion.div
            key={`${cell.row}-${cell.col}`}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.01 }}
            className="flex flex-col items-center gap-1 rounded-lg border border-[#2D3748]/40 p-2"
            style={{ backgroundColor: `${heatColor(cell.value)}22` }}
            title={`${labels[cell.col]}: ${(cell.value * 100).toFixed(0)}% utilization`}
          >
            <span className="text-[10px] font-medium text-slate-400">{labels[cell.col]}</span>
            <div
              className="h-8 w-full rounded-md"
              style={{ backgroundColor: heatColor(cell.value) }}
            />
            <span className="text-[10px] text-white">{(cell.value * 100).toFixed(0)}%</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
