"use client";

import { useMemo } from "react";

import { ChartPanel } from "@/components/ChartPanel";
import { useAnalysis } from "@/hooks/useAnalysis";
import { computeConfidenceHistogram } from "@/utils/batchAggregates";

export function ConfidenceDistribution() {
  const { results } = useAnalysis();
  const data = useMemo(() => computeConfidenceHistogram(results), [results]);

  return (
    <ChartPanel
      title="Confidence Distribution"
      data={data}
      emptyMessage="No confidence histogram yet."
    />
  );
}
