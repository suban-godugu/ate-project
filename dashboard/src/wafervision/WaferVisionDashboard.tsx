"use client";

import { AnalysisProvider, useAnalysis } from "@/wafervision/context/AnalysisContext";
import { ErrorBanner } from "@/wafervision/components/ErrorBanner";
import { LoadingOverlay } from "@/wafervision/components/LoadingOverlay";
import { WaferUploadHost } from "@/wafervision/components/WaferUploadHost";
import { ControlRibbon } from "@/wafervision/components/ControlRibbon";
import { WaferFilterToolbar } from "@/wafervision/components/WaferFilterToolbar";
import { DashboardTabs } from "@/wafervision/components/DashboardTabs";
import { WaferResultsStrip } from "@/wafervision/components/WaferResultsStrip";
import { OverviewTab } from "@/wafervision/components/OverviewTab";
import { LotTabView } from "@/wafervision/components/LotTabView";
import { ReportPanel } from "@/wafervision/components/ReportPanel";
import { WaferAnalysisContent } from "@/wafervision/components/WaferAnalysisContent";
import { BatchSummary } from "@/wafervision/components/BatchSummary";
import { WaferComparison } from "@/wafervision/components/WaferComparison";
import { BatchCharts } from "@/wafervision/components/BatchCharts";
import { LotSummary } from "@/wafervision/components/LotSummary";
import { AnalysisChildNav } from "@/wafervision/components/AnalysisChildNav";
import {
  EngineeringZonesPanel,
  SpatialAnalyticsPanel,
} from "@/wafervision/components/SpatialAnalyticsPanel";
import { WaferAnalysisModal } from "@/wafervision/components/WaferAnalysisModal";

function ActiveTabContent() {
  const { activeTab } = useAnalysis();

  if (activeTab === "overview") return <OverviewTab />;
  if (activeTab === "reports") return <ReportPanel />;
  if (activeTab.startsWith("LOT_")) return <LotTabView lot={activeTab} />;
  if (activeTab === "wafer") return <WaferAnalysisContent />;
  if (activeTab === "batch") {
    return (
      <div className="space-y-4">
        <BatchSummary />
        <WaferComparison />
        <BatchCharts />
        <LotSummary />
      </div>
    );
  }
  if (activeTab === "spatial") {
    return (
      <>
        <AnalysisChildNav leaf="Spatial Analytics" />
        <SpatialAnalyticsPanel />
      </>
    );
  }
  if (activeTab === "zones") {
    return (
      <>
        <AnalysisChildNav leaf="Engineering Zone Analysis" />
        <EngineeringZonesPanel />
      </>
    );
  }
  return <OverviewTab />;
}

function WaferVisionShell() {
  return (
    <div className="wafervision-root space-y-4">
      <WaferUploadHost />
      <ErrorBanner />
      <ControlRibbon />
      <WaferFilterToolbar />
      <DashboardTabs />
      <WaferResultsStrip />
      <ActiveTabContent />
      <LoadingOverlay />
      <WaferAnalysisModal />
    </div>
  );
}

/** WaferVision-AI workflow embedded inside VERILUMEN Wafer Analysis. */
export function WaferVisionDashboard() {
  return (
    <AnalysisProvider>
      <WaferVisionShell />
    </AnalysisProvider>
  );
}
