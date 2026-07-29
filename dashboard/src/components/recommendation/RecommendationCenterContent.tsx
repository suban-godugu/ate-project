"use client";

import { AgentTabs } from "@/components/recommendation/AgentTabs";
import { TabPanelHost } from "@/components/platform/TabPanelHost";
import { ModuleTabProvider } from "@/contexts/ModuleTabContext";
import { PatternRecommendationAgent } from "@/components/recommendation/agent/PatternRecommendationAgent";
import { ScanDebugRecommendationAgent } from "@/components/recommendation/agent/ScanDebugRecommendationAgent";
import { TestOptimizationAgent } from "@/components/recommendation/agent/TestOptimizationAgent";
import { useUIStore } from "@/stores/uiStore";
import type { RecommendationAgentTab } from "@/types/recommendation";

const tabContent: Record<RecommendationAgentTab, React.ComponentType> = {
  "pattern-agent": PatternRecommendationAgent,
  "scan-debug-agent": ScanDebugRecommendationAgent,
  "test-optimization-agent": TestOptimizationAgent,
};

export function RecommendationCenterContent() {
  const activeTab = useUIStore((s) => s.recommendationAgentTab);
  const setActiveTab = useUIStore((s) => s.setRecommendationAgentTab);

  return (
    <ModuleTabProvider tab={activeTab}>
      <AgentTabs activeTab={activeTab} onTabChange={setActiveTab} />
      <TabPanelHost activeTab={activeTab} tabs={tabContent} />
    </ModuleTabProvider>
  );
}
