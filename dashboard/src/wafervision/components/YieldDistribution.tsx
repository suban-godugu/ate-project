"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { yieldDistribution } from "@/wafervision/utils/batchAggregates";
import { ChartPanel } from "@/wafervision/components/ChartPanel";

export function YieldDistribution() {
  const { results } = useAnalysis();
  return (
    <ChartPanel
      title="Yield Distribution"
      data={yieldDistribution(results)}
      emptyMessage="No yield bins yet — analyze wafers to populate this chart."
    />
  );
}
