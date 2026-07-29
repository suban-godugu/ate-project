"use client";

import { useMemo } from "react";

import { ChartPanel } from "@/components/ChartPanel";
import { useAnalysis } from "@/hooks/useAnalysis";
import { computeLotDistribution } from "@/utils/batchAggregates";

export function LotDistribution() {
  const { results } = useAnalysis();
  const data = useMemo(() => computeLotDistribution(results), [results]);

  return (
    <ChartPanel
      title="LOT Distribution"
      data={data}
      emptyMessage="No LOT counts yet."
    />
  );
}
