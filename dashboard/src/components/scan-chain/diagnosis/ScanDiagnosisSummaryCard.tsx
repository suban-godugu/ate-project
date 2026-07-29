"use client";

import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import type { ScanDiagnosisExecutiveSummary } from "@/types/scanChain";

export function ScanDiagnosisSummaryCard({ data }: { data: ScanDiagnosisExecutiveSummary }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card gradient-border hover-lift p-6"
    >
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">{data.title}</h3>
          <p className="text-sm text-slate-400">{data.subtitle}</p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {data.metrics.map((metric) => (
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
