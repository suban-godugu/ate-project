"use client";

import { motion } from "framer-motion";

interface PatternMatrixHeatmapProps {
  title: string;
  subtitle: string;
  grid: number[][];
  legendLabel?: string;
}

function cellColor(value: number): string {
  const alpha = 0.15 + (value / 100) * 0.85;
  return `rgba(124, 58, 237, ${alpha})`;
}

export function PatternMatrixHeatmap({
  title,
  subtitle,
  grid,
  legendLabel = "Similarity intensity",
}: PatternMatrixHeatmapProps) {
  const cols = grid[0]?.length ?? 0;

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <p className="text-sm text-slate-400">{subtitle}</p>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-slate-400">
          <span>{legendLabel}</span>
          <span className="h-3 w-8 rounded-sm bg-[#7C3AED]/20" />
          <span>→</span>
          <span className="h-3 w-8 rounded-sm bg-[#7C3AED]" />
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
          {grid.flatMap((row, ri) =>
            row.map((cell, ci) => (
              <motion.div
                key={`${ri}-${ci}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: (ri * cols + ci) * 0.003 }}
                className="aspect-square rounded-[2px] transition-transform hover:scale-125 hover:z-10"
                style={{ backgroundColor: cellColor(cell) }}
                title={`[${ri}, ${ci}]: ${cell}%`}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
