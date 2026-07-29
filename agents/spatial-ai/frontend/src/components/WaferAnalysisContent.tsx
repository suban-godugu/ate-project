"use client";

import { AnalysisPanel } from "@/components/AnalysisPanel";
import { AnalysisSummary } from "@/components/AnalysisSummary";
import { DieTable } from "@/components/DieTable";
import { FutureAnalyticsPanels } from "@/components/FutureAnalyticsPanels";
import { WaferImages } from "@/components/WaferImages";
import { YieldSummary } from "@/components/YieldSummary";

/**
 * Shared Wafer Analysis body — reused by the LOT modal and the standalone wafer tab.
 * Do not duplicate panel implementations.
 */
export function WaferAnalysisContent() {
  return (
    <div className="space-y-4">
      <AnalysisSummary />
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <YieldSummary />
        <AnalysisPanel />
      </div>
      <WaferImages />
      <DieTable />
      <FutureAnalyticsPanels />
    </div>
  );
}
