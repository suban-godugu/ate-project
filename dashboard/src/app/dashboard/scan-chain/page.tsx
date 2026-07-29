"use client";

import { useCallback, useState } from "react";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TabPanelHost } from "@/components/platform/TabPanelHost";
import { ScanChainNavigationProvider } from "@/components/scan-chain/ScanChainNavigationContext";
import { ScanChainTabs } from "@/components/scan-chain/ScanChainTabs";
import { FailureAnalysisTab } from "@/components/scan-chain/tabs/FailureAnalysisTab";
import { OverviewTab } from "@/components/scan-chain/tabs/OverviewTab";
import { PatternAnalysisTab } from "@/components/scan-chain/tabs/PatternAnalysisTab";
import { ScanDiagnosisTab } from "@/components/scan-chain/tabs/ScanDiagnosisTab";
import type { ScanChainTab } from "@/types/scanChain";

const tabContent: Record<ScanChainTab, React.ComponentType> = {
  overview: OverviewTab,
  "pattern-analysis": PatternAnalysisTab,
  "failure-analysis": FailureAnalysisTab,
  "scan-diagnosis": ScanDiagnosisTab,
};

export default function ScanChainPage() {
  const [activeTab, setActiveTab] = useState<ScanChainTab>("overview");

  const handleNavigate = useCallback((tab: ScanChainTab) => {
    setActiveTab(tab);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  return (
    <DashboardLayout
      title="Scan Chain Analysis"
      searchPlaceholder="Search scan chains, patterns, chips, flops..."
      primaryActionLabel="AI Diagnose"
      pageId="scan-chain"
    >
      <ScanChainNavigationProvider onNavigate={handleNavigate}>
        <ModuleTabProvider tab={activeTab}>
          <ScanChainTabs activeTab={activeTab} onTabChange={setActiveTab} />
          <TabPanelHost activeTab={activeTab} tabs={tabContent} />
        </ModuleTabProvider>
      </ScanChainNavigationProvider>
    </DashboardLayout>
  );
}
