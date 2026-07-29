"use client";

import { AnalysisSummary } from "@/wafervision/components/AnalysisSummary";
import { YieldSummary } from "@/wafervision/components/YieldSummary";
import { AnalysisPanel } from "@/wafervision/components/AnalysisPanel";
import { WaferImages } from "@/wafervision/components/WaferImages";
import { DieTable } from "@/wafervision/components/DieTable";
import { FutureAnalyticsPanels } from "@/wafervision/components/FutureAnalyticsPanels";

/** Shared analysis body for the LOT modal and the hidden wafer tab. */
export function WaferAnalysisContent() {
  return (
    <div className="space-y-4">
      <AnalysisSummary />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <YieldSummary />
        <AnalysisPanel />
      </div>
      <WaferImages />
      <DieTable />
      <FutureAnalyticsPanels />
    </div>
  );
}
