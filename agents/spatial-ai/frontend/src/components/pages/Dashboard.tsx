"use client";

import {
  EngineeringZonesPanel,
  SpatialAnalyticsPanel,
} from "@/components/SpatialAnalyticsPanel";
import { AnalysisChildNav } from "@/components/AnalysisChildNav";
import { BatchCharts } from "@/components/BatchCharts";
import { BatchSummary } from "@/components/BatchSummary";
import { ControlRibbon } from "@/components/ControlRibbon";
import { DashboardTabs } from "@/components/DashboardTabs";
import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingOverlay } from "@/components/LoadingOverlay";
import { LotSummary } from "@/components/LotSummary";
import { LotTabView } from "@/components/LotTabView";
import { ReportPanel } from "@/components/ReportPanel";
import { TopNav } from "@/components/TopNav";
import { WaferAnalysisContent } from "@/components/WaferAnalysisContent";
import { WaferAnalysisModal } from "@/components/WaferAnalysisModal";
import { WaferComparison } from "@/components/WaferComparison";
import { WaferFilterToolbar } from "@/components/WaferFilterToolbar";
import { WaferResultsStrip } from "@/components/WaferResultsStrip";
import { useAnalysis } from "@/hooks/useAnalysis";
import {
  isLotDashboardTab,
  type LotDashboardTab,
} from "@/types/wafer";

function OverviewTab() {
  return (
    <div className="space-y-4">
      <BatchSummary />
      <LotSummary />
      <BatchCharts />
    </div>
  );
}

/** Retained for deep links / programmatic tab — not shown in top navigation. */
function BatchAnalysisTab() {
  return (
    <div className="space-y-4">
      <BatchSummary />
      <WaferComparison />
      <BatchCharts />
      <LotSummary />
    </div>
  );
}

function ReportsTab() {
  return (
    <div className="space-y-4">
      <ReportPanel />
    </div>
  );
}

function LotAnalysisTab({ lot }: { lot: LotDashboardTab }) {
  return <LotTabView lot={lot} />;
}

function ActiveTabContent() {
  const { activeTab } = useAnalysis();

  if (isLotDashboardTab(activeTab)) {
    return <LotAnalysisTab lot={activeTab} />;
  }

  switch (activeTab) {
    case "overview":
      return <OverviewTab />;
    case "wafer":
      return <WaferAnalysisContent />;
    case "batch":
      return <BatchAnalysisTab />;
    case "reports":
      return <ReportsTab />;
    case "spatial":
      return (
        <div className="space-y-4">
          <AnalysisChildNav child="spatial" />
          <SpatialAnalyticsPanel />
        </div>
      );
    case "zones":
      return (
        <div className="space-y-4">
          <AnalysisChildNav child="zones" />
          <EngineeringZonesPanel />
        </div>
      );
    default:
      return <OverviewTab />;
  }
}

/** Dashboard composition (App Router page lives in `app/page.tsx`). */
export function DashboardPage() {
  return (
    <main className="mx-auto min-h-screen max-w-[1800px] px-4 py-6 md:px-6">
      <TopNav />
      <ErrorBanner />
      <LoadingOverlay />

      <div className="space-y-4">
        <ControlRibbon />
        <WaferFilterToolbar />
        <DashboardTabs />
        <WaferResultsStrip />
        <ActiveTabContent />
      </div>

      <WaferAnalysisModal />
    </main>
  );
}

export default DashboardPage;
