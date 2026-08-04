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
      <div className="flex h-[calc(100vh-72px-48px)] min-h-0 flex-col">
        <div className="shrink-0">
          <AgentTabs activeTab={activeTab} onTabChange={setActiveTab} />
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          <TabPanelHost
            activeTab={activeTab}
            tabs={tabContent}
            className="mt-0 h-full"
          />
        </div>
      </div>
    </ModuleTabProvider>
  );
}
