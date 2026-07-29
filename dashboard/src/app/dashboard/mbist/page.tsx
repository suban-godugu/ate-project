"use client";

import { useState } from "react";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TabPanelHost } from "@/components/platform/TabPanelHost";
import { MBISTTabs } from "@/components/mbist/MBISTTabs";
import { AIRecommendationTab } from "@/components/mbist/tabs/AIRecommendationTab";
import { DiagnosisTab } from "@/components/mbist/tabs/DiagnosisTab";
import { FailureAnalysisTab } from "@/components/mbist/tabs/FailureAnalysisTab";
import { MemoryHealthTab } from "@/components/mbist/tabs/MemoryHealthTab";
import { OverviewTab } from "@/components/mbist/tabs/OverviewTab";
import type { MbistTab } from "@/types/mbist";

const tabContent: Record<MbistTab, React.ComponentType> = {
  overview: OverviewTab,
  "memory-health": MemoryHealthTab,
  "failure-analysis": FailureAnalysisTab,
  diagnosis: DiagnosisTab,
  "ai-recommendation": AIRecommendationTab,
};

export default function MbistPage() {
  const [activeTab, setActiveTab] = useState<MbistTab>("overview");

  return (
    <DashboardLayout
      title="MBIST Analysis"
      subtitle="Memory Built-In Self-Test Analytics and Diagnosis"
      searchPlaceholder="Search memory instances, patterns, banks, controllers..."
      primaryActionLabel="Run AI Diagnosis"
      pageId="mbist"
    >
      <ModuleTabProvider tab={activeTab}>
        <MBISTTabs activeTab={activeTab} onTabChange={setActiveTab} />
        <TabPanelHost activeTab={activeTab} tabs={tabContent} />
      </ModuleTabProvider>
    </DashboardLayout>
  );
}
