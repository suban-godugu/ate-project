"use client";

import { useMemo } from "react";

import { ChartPanel } from "@/components/ChartPanel";
import { useAnalysis } from "@/hooks/useAnalysis";
import { computeDefectDistribution } from "@/utils/batchAggregates";

export function DefectDistribution() {
  const { results } = useAnalysis();
  const data = useMemo(() => computeDefectDistribution(results), [results]);

  return (
    <ChartPanel
      title="Defect Distribution"
      data={data}
      emptyMessage="No defect counts yet."
    />
  );
}
