"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { lotDistribution } from "@/wafervision/utils/batchAggregates";
import { ChartPanel } from "@/wafervision/components/ChartPanel";

export function LotDistribution() {
  const { results } = useAnalysis();
  return (
    <ChartPanel
      title="LOT Distribution"
      data={lotDistribution(results)}
      emptyMessage="No LOT counts yet — analyze wafers to populate this chart."
    />
  );
}
