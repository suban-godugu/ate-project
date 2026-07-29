"use client";

import { Fragment } from "react";
import { motion } from "framer-motion";

interface FailureCorrelationMatrixProps {
  grid: number[][];
  labels: string[];
}

function cellColor(value: number): string {
  const alpha = 0.12 + (value / 100) * 0.88;
  return `rgba(124, 58, 237, ${alpha})`;
}

export function FailureCorrelationMatrix({ grid, labels }: FailureCorrelationMatrixProps) {
  const size = grid.length;

  return (
    <div className="glass-card gradient-border overflow-hidden p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-white">Failure Correlation Matrix</h3>
        <p className="text-sm text-slate-400">
          Cross-domain correlation between pattern, failure, lot, wafer, and device
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl bg-[#0A1020]/60 p-4">
        <div className="inline-grid gap-1" style={{ gridTemplateColumns: `auto repeat(${size}, 1fr)` }}>
          <div />
          {labels.map((label) => (
            <div key={`col-${label}`} className="px-1 pb-2 text-center text-[10px] text-slate-400">
              {label}
            </div>
          ))}

          {grid.map((row, ri) => (
            <Fragment key={labels[ri]}>
              <div className="flex items-center pr-2 text-[10px] text-slate-400">{labels[ri]}</div>
              {row.map((cell, ci) => (
                <motion.div
                  key={`${ri}-${ci}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: (ri * size + ci) * 0.01 }}
                  className="flex h-10 w-10 items-center justify-center rounded-md text-[10px] font-medium text-white transition-transform hover:scale-110"
                  style={{ backgroundColor: cellColor(cell) }}
                  title={`${labels[ri]} × ${labels[ci]}: ${cell}%`}
                >
                  {cell}
                </motion.div>
              ))}
            </Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}
