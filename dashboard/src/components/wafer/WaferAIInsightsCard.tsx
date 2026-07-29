"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { WaferAIInsight } from "@/types/wafer";

const priorityVariant: Record<string, "destructive" | "default" | "secondary" | "outline"> = {
  Critical: "destructive",
  High: "default",
  Medium: "secondary",
  Low: "outline",
};

export function WaferAIInsightsCard({ data }: { data: WaferAIInsight }) {
  const metrics = [
    { label: "Detected Root Cause", value: data.rootCause, wide: true },
    { label: "Affected Dies", value: data.affectedDies.toLocaleString() },
    { label: "Estimated Yield Loss", value: data.estimatedYieldLoss },
    { label: "Recommended Action", value: data.recommendedAction, wide: true },
    { label: "Priority", value: data.priority },
    { label: "Confidence", value: `${data.confidence}%` },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card gradient-border relative overflow-hidden p-6"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#7C3AED]/10 blur-2xl" />
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
          <Brain className="h-5 w-5" />
        </div>
        <div>
          <h3 className="text-base font-semibold text-white">AI Insights</h3>
          <p className="text-sm text-slate-400">ML-powered defect root cause analysis</p>
        </div>
        <Badge variant={priorityVariant[data.priority] ?? "secondary"} className="ml-auto">
          <Sparkles className="mr-1 h-3 w-3" />
          {data.priority}
        </Badge>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {metrics.map((m) => (
          <div
            key={m.label}
            className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 ${m.wide ? "sm:col-span-2" : ""}`}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className={`mt-1 font-semibold text-white ${m.wide ? "text-sm leading-relaxed" : "text-lg"}`}>
              {m.value}
            </p>
          </div>
        ))}
      </div>
      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>Model Confidence</span>
          <span>{data.confidence}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[#2D3748]">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${data.confidence}%` }}
            transition={{ duration: 1, delay: 0.3 }}
            className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A78BFA]"
          />
        </div>
      </div>
    </motion.div>
  );
}
