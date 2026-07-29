"use client";

import { motion } from "framer-motion";
import { Brain, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AIDiagnosisSummary } from "@/types/scanChain";

interface AIDiagnosisCardProps {
  data: AIDiagnosisSummary;
  onRunDiagnosis?: () => void;
}

export function AIDiagnosisCard({ data, onRunDiagnosis }: AIDiagnosisCardProps) {
  const metrics = [
    { label: "Detected Root Cause", value: data.detectedRootCause, wide: true },
    { label: "Critical Chains", value: data.criticalChains.toString() },
    { label: "Recommended Debug Area", value: data.recommendedDebugArea, wide: true },
    { label: "Estimated Repair Success", value: `${data.estimatedRepairSuccess}%` },
    { label: "Confidence Score", value: `${data.confidenceScore}%` },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="glass-card gradient-border hover-lift relative overflow-hidden p-6"
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#7C3AED]/10 blur-2xl" />

      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#7C3AED]/20 text-[#7C3AED]">
            <Brain className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">AI Diagnosis Summary</h3>
            <p className="text-sm text-slate-400">
              ML-powered root cause analysis
            </p>
          </div>
        </div>
        <Button
          size="sm"
          className="btn-glow rounded-xl bg-[#7C3AED] text-xs hover:bg-[#6D28D9]"
          onClick={onRunDiagnosis}
        >
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          Run AI Diagnosis
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className={`rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/40 p-4 ${
              metric.wide ? "sm:col-span-2" : ""
            }`}
          >
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-500">
              {metric.label}
            </p>
            <p
              className={`mt-1 font-semibold text-white ${
                metric.wide ? "text-sm leading-relaxed" : "text-lg"
              }`}
            >
              {metric.value}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-slate-400">
          <span>Confidence Score</span>
          <span>{data.confidenceScore}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-[#2D3748]">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${data.confidenceScore}%` }}
            transition={{ duration: 1, delay: 0.3 }}
            className="h-full rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A78BFA]"
          />
        </div>
      </div>
    </motion.div>
  );
}
