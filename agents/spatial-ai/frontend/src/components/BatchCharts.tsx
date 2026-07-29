"use client";

import { ConfidenceDistribution } from "@/components/ConfidenceDistribution";
import { DefectDistribution } from "@/components/DefectDistribution";
import { LotDistribution } from "@/components/LotDistribution";
import { YieldDistribution } from "@/components/YieldDistribution";

export function BatchCharts() {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <DefectDistribution />
      <LotDistribution />
      <YieldDistribution />
      <ConfidenceDistribution />
    </div>
  );
}
