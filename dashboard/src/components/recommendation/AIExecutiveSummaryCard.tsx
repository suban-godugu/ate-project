"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AIExecutiveSummary } from "@/types/recommendation";

export function AIExecutiveSummaryCard({ data }: { data: AIExecutiveSummary }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className="glass-card gradient-border hover-lift relative overflow-hidden p-6">
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#7C3AED]/10 blur-2xl" />
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">AI Executive Summary</h3>
            <p className="text-sm text-slate-400">Unified insights from all analysis modules</p>
          </div>
        </div>
        <Button size="sm" className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]">
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          Run Global AI Optimization
        </Button>
      </div>
      <div className="mb-4">
        <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-slate-500">Top Problems</p>
        <ul className="space-y-1.5">
          {data.topProblems.map((p) => (
            <li key={p} className="flex items-start gap-2 text-sm text-slate-300">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[#7C3AED]" />
              {p}
            </li>
          ))}
        </ul>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Overall Risk Score", value: data.overallRiskScore },
          { label: "Expected Yield Gain", value: data.expectedYieldGain },
          { label: "Expected Cost Reduction", value: data.expectedCostReduction },
          { label: "Test Time Reduction", value: data.expectedTestTimeReduction },
        ].map((m) => (
          <div key={m.label} className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3">
            <p className="text-[10px] uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className="mt-1 text-lg font-semibold text-white">{m.value}</p>
          </div>
        ))}
      </div>
    </motion.div>
  );
}
