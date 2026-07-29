"use client";

import { Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { CoverageDiagnosisData } from "@/types/scanCoverage";

export function CoverageDiagnosis({ diagnosis }: { diagnosis: CoverageDiagnosisData }) {
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-xl border border-[rgba(139,92,246,0.3)] bg-gradient-to-br from-[#121826] to-[#0d111c] p-4 lg:col-span-2">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-[#8B5CF6]" />
          <span className="text-sm font-bold text-white">Coverage Diagnosis</span>
          <Badge className="ml-auto border-emerald-500/40 bg-emerald-500/15 text-xs font-semibold text-emerald-300">
            {diagnosis.confidence}% Confidence
          </Badge>
        </div>
        <p className="text-sm leading-relaxed text-[#CBD5E1]">{diagnosis.summary}</p>
      </div>
      <div className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-4">
        <p className="mb-3 text-[10px] font-bold uppercase tracking-wider text-[#64748B]">
          Coverage Factors
        </p>
        <div className="flex flex-wrap gap-2">
          {diagnosis.factors.map((factor) => (
            <Badge
              key={factor}
              className="border-[#7C3AED]/30 bg-[#7C3AED]/10 text-[11px] text-[#C4B5FD]"
            >
              {factor}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
