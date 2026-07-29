"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useFilteredRecommendationData } from "@/hooks/useRecommendationData";
import { recommendationCategories, type BottomAISummary } from "@/types/recommendation";

export function RecommendationEnginePanel() {
  return (
    <div className="glass-card gradient-border p-6">
      <h3 className="mb-1 text-base font-semibold text-white">AI Recommendation Engine</h3>
      <p className="mb-4 text-sm text-slate-400">Categories consolidated from Scan Chain, MBIST, LBIST, and Wafer Analysis</p>
      <div className="flex flex-wrap gap-2">
        {recommendationCategories.map((cat, i) => (
          <motion.span
            key={cat}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.03 }}
            className="rounded-lg border border-[#2D3748]/60 bg-[#0A1020]/40 px-3 py-1.5 text-xs text-slate-300 transition-colors hover:border-[#7C3AED]/40 hover:text-white"
          >
            {cat}
          </motion.span>
        ))}
      </div>
    </div>
  );
}

export function WorkflowPanel() {
  const { workflowSteps } = useFilteredRecommendationData();

  return (
    <div className="glass-card gradient-border p-6">
      <h3 className="mb-4 text-base font-semibold text-white">Recommendation Workflow</h3>
      <div className="flex flex-col gap-0 sm:flex-row sm:flex-wrap sm:items-center">
        {workflowSteps.map((step, i) => (
          <motion.div
            key={step}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.08 }}
            className="flex items-center"
          >
            <div className="rounded-xl border border-[#7C3AED]/30 bg-[#7C3AED]/10 px-3 py-2 text-xs font-medium text-white">
              {step}
            </div>
            {i < workflowSteps.length - 1 && (
              <span className="mx-1 hidden text-[#7C3AED] sm:inline">↓</span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

export function BottomAISummaryPanel({ data }: { data: BottomAISummary }) {
  const metrics = [
    { label: "Estimated Savings", value: data.estimatedSavings },
    { label: "Yield Improvement", value: data.yieldImprovement },
    { label: "Test Time Reduction", value: data.testTimeReduction },
    { label: "Memory Repair Success", value: data.memoryRepairSuccess },
    { label: "Logic Coverage Increase", value: data.logicCoverageIncrease },
    { label: "Pattern Reduction", value: data.patternReduction },
    { label: "Wafer Yield Increase", value: data.waferYieldIncrease },
    { label: "Total ROI", value: data.totalRoi },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card gradient-border p-6">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">Bottom AI Summary</h3>
          <p className="text-sm text-slate-400">Projected impact if all recommendations are implemented</p>
        </div>
        <Button size="sm" className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]">
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          Generate Final AI Report
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className="mt-1 text-lg font-semibold text-emerald-400">{m.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
