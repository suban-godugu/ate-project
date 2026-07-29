"use client";

import { DefectDistribution } from "@/wafervision/components/DefectDistribution";
import { LotDistribution } from "@/wafervision/components/LotDistribution";
import { YieldDistribution } from "@/wafervision/components/YieldDistribution";
import { ConfidenceDistribution } from "@/wafervision/components/ConfidenceDistribution";

export function BatchCharts() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <DefectDistribution />
      <LotDistribution />
      <YieldDistribution />
      <ConfidenceDistribution />
    </div>
  );
}
