"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { OptimizationResults } from "@/types/dashboard";

interface OptimizationResultProps {
  results: OptimizationResults | null;
}

const rows: {
  key: keyof OptimizationResults;
  label: string;
  format: (v: number) => string;
}[] = [
  { key: "costReduction", label: "Estimated Cost Reduction", format: (v) => `${v}%` },
  { key: "timeSavings", label: "Estimated Time Savings", format: (v) => `${v}s` },
  { key: "projectedYield", label: "Projected Yield", format: (v) => `${v}%` },
  { key: "patternsReduced", label: "Patterns Reduced", format: (v) => String(v) },
  {
    key: "totalSavings",
    label: "Total Savings",
    format: (v) => `$${(v / 1000).toFixed(0)}K`,
  },
];

export function OptimizationResult({ results }: OptimizationResultProps) {
  return (
    <AnimatePresence mode="wait">
      {results ? (
        <motion.div
          key="results"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          className="glass-card gradient-border hover-lift p-6"
        >
          <div className="mb-4 flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
            <h3 className="text-base font-semibold text-white">Optimization Results</h3>
          </div>

          <div className="space-y-3">
            {rows.map((row) => (
              <div
                key={row.key}
                className="flex items-center justify-between rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 px-4 py-3"
              >
                <span className="text-sm text-slate-400">{row.label}</span>
                <span className="text-lg font-bold text-emerald-400">
                  {row.format(results[row.key])}
                </span>
              </div>
            ))}
          </div>

          <motion.div whileHover={{ scale: 1.01 }} className="mt-6">
            <Button className="btn-glow w-full rounded-xl bg-emerald-600 hover:bg-emerald-500">
              View Optimized Pattern Set
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </motion.div>
        </motion.div>
      ) : (
        <motion.div
          key="empty"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="glass-card flex items-center justify-center border-dashed p-12 text-center"
        >
          <p className="text-sm text-slate-400">
            Run the optimization engine to view projected results
          </p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
