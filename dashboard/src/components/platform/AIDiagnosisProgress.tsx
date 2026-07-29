"use client";

import { motion } from "framer-motion";
import { Brain, Loader2 } from "lucide-react";
import type { AIDiagnosisResult } from "@/types/platform";

const steps = ["Collect Data", "Analyze", "Generate AI Insight", "Complete"];

interface AIDiagnosisProgressProps {
  running: boolean;
  step: number;
  result: AIDiagnosisResult | null;
}

export function AIDiagnosisProgress({ running, step, result }: AIDiagnosisProgressProps) {
  if (!running && !result) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card mt-4 p-4"
      role="status"
      aria-live="polite"
    >
      <div className="mb-3 flex items-center gap-2">
        {running ? <Loader2 className="h-4 w-4 animate-spin text-[#7C3AED]" /> : <Brain className="h-4 w-4 text-[#7C3AED]" />}
        <p className="text-sm font-medium text-white">AI Diagnosis {running ? "In Progress" : "Complete"}</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-4">
        {steps.map((label, i) => (
          <div
            key={label}
            className={`rounded-lg border px-3 py-2 text-center text-[11px] ${
              i < step || (!running && result)
                ? "border-[#7C3AED]/40 bg-[#7C3AED]/10 text-white"
                : i === step && running
                  ? "border-[#7C3AED] bg-[#7C3AED]/20 text-white"
                  : "border-[#2D3748] text-slate-500"
            }`}
          >
            {label}
          </div>
        ))}
      </div>
      {result && !running && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3 sm:col-span-2">
            <p className="text-[10px] uppercase text-slate-500">Root Cause</p>
            <p className="mt-1 text-sm text-white">{result.rootCause}</p>
          </div>
          <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3">
            <p className="text-[10px] uppercase text-slate-500">Confidence</p>
            <p className="mt-1 text-lg font-semibold text-white">{result.confidence}%</p>
          </div>
          <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3">
            <p className="text-[10px] uppercase text-slate-500">Yield Impact</p>
            <p className="mt-1 text-lg font-semibold text-emerald-400">{result.estimatedYieldImpact}</p>
          </div>
          <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-3 sm:col-span-2">
            <p className="text-[10px] uppercase text-slate-500">Recommendation</p>
            <p className="mt-1 text-sm text-white">{result.recommendation}</p>
          </div>
        </div>
      )}
    </motion.div>
  );
}
