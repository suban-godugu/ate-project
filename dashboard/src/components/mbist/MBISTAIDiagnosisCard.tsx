"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { MbistAIDiagnosis } from "@/types/mbist";

export function MBISTAIDiagnosisCard({
  data,
  buttonLabel = "Run AI MBIST Diagnosis",
  onRunDiagnosis,
}: {
  data: MbistAIDiagnosis;
  buttonLabel?: string;
  onRunDiagnosis?: () => void;
}) {
  const metrics = [
    { label: "Likely Root Cause", value: data.likelyRootCause, wide: true },
    { label: "Repairable Memories", value: data.repairableMemories.toString() },
    { label: "Non-repairable Memories", value: data.nonRepairableMemories.toString() },
    { label: "Repair Efficiency", value: `${data.repairEfficiency}%` },
    { label: "Diagnosis Confidence", value: `${data.diagnosisConfidence}%` },
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
            <h3 className="text-base font-semibold text-white">AI Diagnosis Summary</h3>
            <p className="text-sm text-slate-400">ML-powered MBIST root cause analysis</p>
          </div>
        </div>
        <Button size="sm" className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]" onClick={onRunDiagnosis}>
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          {buttonLabel}
        </Button>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {metrics.map((m) => (
          <div key={m.label} className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 ${m.wide ? "sm:col-span-2" : ""}`}>
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">{m.label}</p>
            <p className={`mt-1 font-semibold text-white ${m.wide ? "text-sm leading-relaxed" : "text-lg"}`}>{m.value}</p>
          </div>
        ))}
      </div>
      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>Diagnosis Confidence</span>
          <span>{data.diagnosisConfidence}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[#2D3748]">
          <motion.div initial={{ width: 0 }} animate={{ width: `${data.diagnosisConfidence}%` }} transition={{ duration: 1, delay: 0.3 }} className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A78BFA]" />
        </div>
      </div>
    </motion.div>
  );
}
