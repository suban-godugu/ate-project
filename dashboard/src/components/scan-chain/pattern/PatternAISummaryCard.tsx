"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { PatternAISummary } from "@/types/scanChain";

interface PatternAISummaryCardProps {
  data: PatternAISummary;
  onRunOptimization?: () => void;
  isRunning?: boolean;
}

export function PatternAISummaryCard({
  data,
  onRunOptimization,
  isRunning,
}: PatternAISummaryCardProps) {
  const metrics = [
    { label: "Patterns to Remove", value: data.patternsToRemove.toString() },
    { label: "Patterns to Merge", value: data.patternsToMerge.toString() },
    { label: "Coverage Improvement", value: data.coverageImprovement },
    { label: "Compression Improvement", value: data.compressionImprovement },
    { label: "Missing Metadata", value: data.missingMetadata.toString() },
    { label: "Duplicate Patterns", value: data.duplicatePatterns.toString() },
    { label: "Expected Runtime Reduction", value: data.expectedRuntimeReduction },
    { label: "Expected Yield Improvement", value: data.expectedYieldImprovement, wide: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="glass-card gradient-border hover-lift relative overflow-hidden p-6"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#7C3AED]/10 blur-2xl" />

      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">AI Recommendation Summary</h3>
            <p className="text-sm text-slate-400">
              Pattern optimization insights from embeddings and similarity analysis
            </p>
          </div>
        </div>
        <Button
          size="sm"
          disabled={isRunning}
          onClick={onRunOptimization}
          className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]"
        >
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          {isRunning ? "Optimizing..." : "Run Pattern Optimization"}
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 ${
              metric.wide ? "sm:col-span-2 lg:col-span-2" : ""
            }`}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
              {metric.label}
            </p>
            <p className="mt-1 text-lg font-semibold text-white">{metric.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
