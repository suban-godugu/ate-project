"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { defectDistribution } from "@/wafervision/utils/batchAggregates";
import { ChartPanel } from "@/wafervision/components/ChartPanel";

export function DefectDistribution() {
  const { results } = useAnalysis();
  return (
    <ChartPanel
      title="Defect Distribution"
      data={defectDistribution(results)}
      emptyMessage="No defect counts yet — analyze wafers to populate this chart."
    />
  );
}
