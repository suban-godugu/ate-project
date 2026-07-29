"use client";

import { useMemo } from "react";

import { ChartPanel } from "@/components/ChartPanel";
import { useAnalysis } from "@/hooks/useAnalysis";
import { computeYieldHistogram } from "@/utils/batchAggregates";

export function YieldDistribution() {
  const { results } = useAnalysis();
  const data = useMemo(() => computeYieldHistogram(results), [results]);

  return (
    <ChartPanel
      title="Yield Distribution"
      data={data}
      emptyMessage="No yield histogram yet."
    />
  );
}
