"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { confidenceDistribution } from "@/wafervision/utils/batchAggregates";
import { ChartPanel } from "@/wafervision/components/ChartPanel";

export function ConfidenceDistribution() {
  const { results } = useAnalysis();
  return (
    <ChartPanel
      title="Confidence Distribution"
      data={confidenceDistribution(results)}
      emptyMessage="No confidence bins yet — analyze wafers to populate this chart."
    />
  );
}
