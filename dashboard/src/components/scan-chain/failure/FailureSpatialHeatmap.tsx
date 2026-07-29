"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

function heatColor(value: number): string {
  if (value >= 0.75) return "#EF4444";
  if (value >= 0.5) return "#F97316";
  if (value >= 0.25) return "#EAB308";
  return "#22C55E";
}

interface FailureSpatialHeatmapProps {
  id: string;
  title: string;
  subtitle: string;
  rows: number;
  cols: number;
  data: { value: number; row: number; col: number }[];
  highlighted?: boolean;
}

export function FailureSpatialHeatmap({
  id,
  title,
  subtitle,
  rows,
  cols,
  data,
  highlighted,
}: FailureSpatialHeatmapProps) {
  const center = useMemo(() => ({ r: rows / 2, c: cols / 2, radius: Math.min(rows, cols) / 2 }), [rows, cols]);

  return (
    <div
      id={id}
      className={cn(
        "glass-card gradient-border overflow-hidden p-6 transition-shadow duration-300",
        highlighted && "ring-2 ring-[#7C3AED]/60 shadow-[0_0_24px_rgba(124,58,237,0.25)]"
      )}
    >
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="text-sm text-slate-400">{subtitle}</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#22C55E]" /> Low
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#EAB308]" /> Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#F97316]" /> High
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#EF4444]" /> Critical
          </span>
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl bg-[#0A1020]/60 p-4">
        <div
          className="mx-auto grid gap-[2px]"
          style={{
            gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
            maxWidth: cols * 16,
          }}
        >
          {data.map((cell, i) => {
            const dist = Math.sqrt((cell.row - center.r) ** 2 + (cell.col - center.c) ** 2);
            const inWafer = dist <= center.radius;
            return (
              <motion.div
                key={`${cell.row}-${cell.col}`}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: inWafer ? 1 : 0.15, scale: 1 }}
                transition={{ delay: i * 0.001, duration: 0.2 }}
                className="aspect-square rounded-[2px] transition-transform hover:scale-125 hover:z-10"
                style={{
                  backgroundColor: inWafer ? heatColor(cell.value) : "#1E293B",
                }}
                title={
                  inWafer
                    ? `[${cell.row}, ${cell.col}]: ${(cell.value * 100).toFixed(0)}% failure density`
                    : undefined
                }
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}
