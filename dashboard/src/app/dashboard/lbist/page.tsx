"use client";

import { useState } from "react";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TabPanelHost } from "@/components/platform/TabPanelHost";
import { LBISTTabs } from "@/components/lbist/LBISTTabs";
import { AIRecommendationTab } from "@/components/lbist/tabs/AIRecommendationTab";
import { CoverageAnalysisTab } from "@/components/lbist/tabs/CoverageAnalysisTab";
import { DiagnosisTab } from "@/components/lbist/tabs/DiagnosisTab";
import { FailureAnalysisTab } from "@/components/lbist/tabs/FailureAnalysisTab";
import { OverviewTab } from "@/components/lbist/tabs/OverviewTab";
import type { LbistTab } from "@/types/lbist";

const tabContent: Record<LbistTab, React.ComponentType> = {
  overview: OverviewTab,
  "coverage-analysis": CoverageAnalysisTab,
  "failure-analysis": FailureAnalysisTab,
  diagnosis: DiagnosisTab,
  "ai-recommendation": AIRecommendationTab,
};

export default function LbistPage() {
  const [activeTab, setActiveTab] = useState<LbistTab>("overview");

  return (
    <DashboardLayout
      title="LBIST Analysis"
      subtitle="Logic Built-In Self-Test Analytics, Coverage and Diagnosis"
      searchPlaceholder="Search LBIST sessions, logic blocks, signatures, controllers..."
      primaryActionLabel="Run AI Diagnosis"
      pageId="lbist"
    >
      <ModuleTabProvider tab={activeTab}>
        <LBISTTabs activeTab={activeTab} onTabChange={setActiveTab} />
        <TabPanelHost activeTab={activeTab} tabs={tabContent} />
      </ModuleTabProvider>
    </DashboardLayout>
  );
}
