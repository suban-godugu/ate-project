"use client";

import { motion } from "framer-motion";
import { Brain } from "lucide-react";
import type { EnterpriseExecutiveSummary } from "@/types/recommendation";

export function EnterpriseExecutiveSummaryCard({ data }: { data: EnterpriseExecutiveSummary }) {
  const metrics = [
    { label: "Patterns Removed", value: data.patternsRemoved.toString() },
    { label: "Coverage Gain", value: data.coverageGain },
    { label: "Power Saving", value: data.powerSaving },
    { label: "Yield Improvement", value: data.yieldImprovement },
    { label: "Test Time Reduction", value: data.testTimeReduction },
    { label: "Cost Reduction", value: data.costReduction },
    { label: "ROI", value: data.roi },
    { label: "AI Confidence", value: data.aiConfidence },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card gradient-border hover-lift relative overflow-hidden p-6"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#7C3AED]/10 blur-2xl" />

      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
          <Brain className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">Enterprise AI Executive Summary</h3>
          <p className="text-sm text-slate-400">
            Consolidated impact across all recommendation agents
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4"
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
              {metric.label}
            </p>
            <p className="mt-1 text-lg font-semibold text-emerald-400">{metric.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
