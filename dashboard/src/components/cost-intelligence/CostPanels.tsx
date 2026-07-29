"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ModuleBadge, PriorityBadge } from "@/components/recommendation/Badges";
import { costOptimizationCategories } from "@/types/costIntelligence";
import type { AICostSummary, EnterpriseCostSummary } from "@/types/costIntelligence";

export function AICostSummaryCard({ data }: { data?: AICostSummary | null }) {
  const metrics = [
    { label: "Highest Cost Module", value: data?.highestCostModule ?? "—" },
    { label: "Most Expensive Pattern", value: data?.mostExpensivePattern ?? "—" },
    { label: "Longest Test Time", value: data?.longestTestTime ?? "—" },
    { label: "Highest Retest Cost", value: data?.highestRetestCost ?? "—" },
    { label: "Highest Repair Cost", value: data?.highestRepairCost ?? "—" },
    { label: "Estimated Savings", value: data?.estimatedSavings ?? "—" },
  ];

  return (
    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="glass-card gradient-border hover-lift relative overflow-hidden p-6">
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#7C3AED]/10 blur-2xl" />
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">AI Cost Summary</h3>
            <p className="text-sm text-slate-400">Cross-module cost analysis and optimization insights</p>
          </div>
        </div>
        <Button size="sm" className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]">
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          Generate Cost Optimization
        </Button>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className="mt-1 text-sm font-semibold text-white">{m.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

export function CostOptimizationEnginePanel() {
  return (
    <div className="glass-card gradient-border p-6">
      <h3 className="mb-1 text-base font-semibold text-white">AI Cost Optimization Engine</h3>
      <p className="mb-4 text-sm text-slate-400">Optimization categories across Scan Chain, MBIST, LBIST, and Wafer Analysis</p>
      <div className="flex flex-wrap gap-2">
        {costOptimizationCategories.map((cat, i) => (
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

export function EnterpriseCostSummaryPanel({ data }: { data?: EnterpriseCostSummary | null }) {
  const modules = data?.modules ?? [];
  const totals = [
    { label: "Total Cost", value: data?.totalCost ?? "—" },
    { label: "Total Savings", value: data?.totalSavings ?? "—" },
    { label: "ROI", value: data?.roi ?? "—" },
    { label: "Yield Improvement", value: data?.yieldImprovement ?? "—" },
    { label: "Test Time Reduction", value: data?.testTimeReduction ?? "—" },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass-card gradient-border p-6">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-white">Enterprise Cost Summary</h3>
        <p className="text-sm text-slate-400">Current vs optimized cost across all test modules</p>
      </div>
      <div className="space-y-3">
        {modules.length === 0 ? (
          <p className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 px-4 py-6 text-center text-sm text-slate-500">
            No module cost summary available for the current filters.
          </p>
        ) : (
          modules.map((m) => (
            <div key={m.module} className="flex flex-wrap items-center gap-3 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4">
              <ModuleBadge module={m.module === "Wafer" ? "Wafer" : m.module} />
              <div className="flex flex-1 flex-wrap items-center gap-2 text-sm">
                <span className="font-medium text-white">{m.currentCost}</span>
                <span className="text-slate-500">→</span>
                <span className="font-medium text-emerald-400">{m.optimizedCost}</span>
                <span className="ml-auto rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400">
                  Savings {m.savings}
                </span>
              </div>
            </div>
          ))
        )}
        <div className="mt-4 grid gap-3 border-t border-[#2D3748]/60 pt-4 sm:grid-cols-2 lg:grid-cols-5">
          {totals.map((m) => (
            <div key={m.label} className="rounded-xl border border-[#7C3AED]/20 bg-[#7C3AED]/5 p-4">
              <p className="text-[10px] uppercase tracking-wider text-slate-500">{m.label}</p>
              <p className="mt-1 text-lg font-bold text-white">{m.value}</p>
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
}

export { PriorityBadge, ModuleBadge };
