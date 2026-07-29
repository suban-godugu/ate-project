"use client";

import { useState } from "react";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TabPanelHost } from "@/components/platform/TabPanelHost";
import { CostTabs } from "@/components/cost-intelligence/CostTabs";
import { AICostOptimizationTab } from "@/components/cost-intelligence/tabs/AICostOptimizationTab";
import { LbistCostTab } from "@/components/cost-intelligence/tabs/LbistCostTab";
import { MbistCostTab } from "@/components/cost-intelligence/tabs/MbistCostTab";
import { OverviewTab } from "@/components/cost-intelligence/tabs/OverviewTab";
import { ScanChainCostTab } from "@/components/cost-intelligence/tabs/ScanChainCostTab";
import { WaferCostTab } from "@/components/cost-intelligence/tabs/WaferCostTab";
import type { CostTab } from "@/types/costIntelligence";

const tabContent: Record<CostTab, React.ComponentType> = {
  overview: OverviewTab,
  "scan-chain": ScanChainCostTab,
  mbist: MbistCostTab,
  lbist: LbistCostTab,
  wafer: WaferCostTab,
  "ai-optimization": AICostOptimizationTab,
};

export default function CostIntelligencePage() {
  const [activeTab, setActiveTab] = useState<CostTab>("overview");

  return (
    <DashboardLayout
      title="Cost Intelligence"
      subtitle="Analyze and optimize semiconductor test costs across Scan Chain, MBIST, LBIST, and Wafer Analysis"
      searchPlaceholder="Search lots, wafers, products, testers..."
      primaryActionLabel="Generate Cost Optimization"
      pageId="cost-intelligence"
    >
      <ModuleTabProvider tab={activeTab}>
        <CostTabs activeTab={activeTab} onTabChange={setActiveTab} />
        <TabPanelHost activeTab={activeTab} tabs={tabContent} />
      </ModuleTabProvider>
    </DashboardLayout>
  );
}
