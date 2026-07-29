"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { useFilteredAlertsData } from "@/hooks/useAlertsData";

function heatColor(value: number): string {
  if (value >= 0.85) return "#EF4444";
  if (value >= 0.65) return "#F97316";
  if (value >= 0.35) return "#EAB308";
  return "#22C55E";
}

export function WaferAlertHeatmap() {
  const { generateWaferAlertHeatmap } = useFilteredAlertsData();
  const heatData = useMemo(() => generateWaferAlertHeatmap(12, 16), [generateWaferAlertHeatmap]);

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Wafer Alert Heatmap</h3>
          <p className="text-sm text-slate-400">Yield drop and defect hotspot overlay</p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-slate-400">
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#22C55E]" /> Normal</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#EAB308]" /> Warning</span>
          <span className="flex items-center gap-1"><span className="h-3 w-3 rounded-sm bg-[#EF4444]" /> Critical</span>
        </div>
      </div>
      <div className="overflow-x-auto rounded-xl bg-[#0A1020]/60 p-4">
        <div className="mx-auto grid gap-[2px]" style={{ gridTemplateColumns: "repeat(16, minmax(0, 1fr))", maxWidth: 16 * 16 }}>
          {heatData.map((cell) => (
            <motion.div
              key={`${cell.row}-${cell.col}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="aspect-square rounded-[2px]"
              style={{ backgroundColor: heatColor(cell.value) }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
