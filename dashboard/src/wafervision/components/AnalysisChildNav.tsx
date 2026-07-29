"use client";

import { ArrowLeft } from "lucide-react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { resolveLot } from "@/wafervision/utils/batchAggregates";
import { lotLabel } from "@/wafervision/utils/lotTaxonomy";

export function AnalysisChildNav({
  leaf,
}: {
  leaf: "Spatial Analytics" | "Engineering Zone Analysis";
}) {
  const { selected, returnToWaferAnalysis } = useAnalysis();
  const lot = selected ? resolveLot(selected) : "LOT";

  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      <button
        type="button"
        onClick={returnToWaferAnalysis}
        className="inline-flex items-center gap-1 text-sm font-medium text-[#A78BFA] hover:text-[#7C3AED]"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Wafer Analysis
      </button>
      <span className="text-xs text-slate-400">
        {lotLabel(lot)} › Wafer Analysis › {leaf}
      </span>
    </div>
  );
}
