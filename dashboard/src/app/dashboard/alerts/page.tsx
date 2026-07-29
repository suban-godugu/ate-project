"use client";

import { useState } from "react";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { TabPanelHost } from "@/components/platform/TabPanelHost";
import { AlertTabs } from "@/components/alerts/AlertTabs";
import { AIRecommendationAlertsTab } from "@/components/alerts/tabs/AIRecommendationAlertsTab";
import { CostAlertsTab } from "@/components/alerts/tabs/CostAlertsTab";
import { LbistAlertsTab } from "@/components/alerts/tabs/LbistAlertsTab";
import { MbistAlertsTab } from "@/components/alerts/tabs/MbistAlertsTab";
import { OverviewTab } from "@/components/alerts/tabs/OverviewTab";
import { ScanChainAlertsTab } from "@/components/alerts/tabs/ScanChainAlertsTab";
import { WaferAlertsTab } from "@/components/alerts/tabs/WaferAlertsTab";
import type { AlertTab } from "@/types/alerts";

const tabContent: Record<AlertTab, React.ComponentType> = {
  overview: OverviewTab,
  "scan-chain": ScanChainAlertsTab,
  mbist: MbistAlertsTab,
  lbist: LbistAlertsTab,
  wafer: WaferAlertsTab,
  cost: CostAlertsTab,
  "ai-recommendation": AIRecommendationAlertsTab,
};

export default function AlertsPage() {
  const [activeTab, setActiveTab] = useState<AlertTab>("overview");

  return (
    <DashboardLayout
      title="Alerts"
      subtitle="Monitor and manage real-time alerts across Scan Chain, MBIST, LBIST, Wafer Analysis, Cost Intelligence, and AI Recommendations"
      searchPlaceholder="Search alerts, lots, wafers, products, testers..."
      primaryActionLabel="Mark All as Read"
      pageId="alerts"
    >
      <ModuleTabProvider tab={activeTab}>
        <AlertTabs activeTab={activeTab} onTabChange={setActiveTab} />
        <TabPanelHost activeTab={activeTab} tabs={tabContent} />
      </ModuleTabProvider>
    </DashboardLayout>
  );
}
