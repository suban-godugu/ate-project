"use client";

import { BatchSummary } from "@/wafervision/components/BatchSummary";
import { LotSummary } from "@/wafervision/components/LotSummary";
import { BatchCharts } from "@/wafervision/components/BatchCharts";

export function OverviewTab() {
  return (
    <div className="space-y-4">
      <BatchSummary />
      <LotSummary />
      <BatchCharts />
    </div>
  );
}
