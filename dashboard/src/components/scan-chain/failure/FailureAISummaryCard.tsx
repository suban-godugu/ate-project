"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { FailureAISummary } from "@/types/scanChain";

interface FailureAISummaryCardProps {
  data: FailureAISummary;
  onRunAnalysis?: () => void;
  isRunning?: boolean;
}

export function FailureAISummaryCard({
  data,
  onRunAnalysis,
  isRunning,
}: FailureAISummaryCardProps) {
  const metrics = [
    { label: "Highest Failure Lot", value: data.highestFailureLot },
    { label: "Highest Failure Wafer", value: data.highestFailureWafer },
    { label: "Critical Fault Category", value: data.criticalFaultCategory },
    { label: "Most Affected Pattern", value: data.mostAffectedPattern },
    { label: "Most Frequent Root Cause", value: data.mostFrequentRootCause },
    { label: "Estimated Yield Loss", value: data.estimatedYieldLoss },
    { label: "Estimated Cost Impact", value: data.estimatedCostImpact },
    {
      label: "Recommended Engineering Action",
      value: data.recommendedEngineeringAction,
      wide: true,
    },
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
            <h3 className="text-base font-semibold text-white">AI Failure Recommendation Summary</h3>
            <p className="text-sm text-slate-400">
              Yield impact, cost exposure, and prioritized engineering actions
            </p>
          </div>
        </div>
        <Button
          size="sm"
          disabled={isRunning}
          onClick={onRunAnalysis}
          className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]"
        >
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          {isRunning ? "Analyzing..." : "Run AI Root Cause Analysis"}
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 ${
              metric.wide ? "sm:col-span-2 lg:col-span-4" : ""
            }`}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
              {metric.label}
            </p>
            <p className="mt-1 text-sm font-semibold text-white sm:text-base">{metric.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
