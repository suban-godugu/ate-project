"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AgentEmbedFrame } from "@/components/scan-chain/agent/AgentEmbedFrame";
import { isLiveApi } from "@/lib/api/config";
import { apiFetch } from "@/lib/api/client";
import type { IntegrationHealth } from "@/lib/api/dashboard";
import { resolveAgentEmbedUrl } from "@/lib/agentEmbedUrls";

async function getScanDebugRecommendationAgentHealth(): Promise<IntegrationHealth> {
  return apiFetch("/integrations/scan-debug-recommendation-agent/health", { auth: false });
}

export function ScanDebugRecommendationAgent() {
  const live = isLiveApi();
  const [keepEmbedded, setKeepEmbedded] = useState(false);

  const scanDebugRecHealth = useQuery({
    queryKey: ["integration", "scan-debug-recommendation-agent", "health"],
    queryFn: getScanDebugRecommendationAgentHealth,
    enabled: live,
    staleTime: 10_000,
    refetchInterval: (query) => {
      const data = query.state.data;
      const ok = Boolean(data?.reachable && data.dashboard_present);
      return ok || keepEmbedded ? 30_000 : 4_000;
    },
    retry: 2,
    retryDelay: 1500,
  });

  const health = scanDebugRecHealth.data;
  const dashboardUrl = resolveAgentEmbedUrl(health?.embed_path, "scanDebugRec");
  const reachableNow = Boolean(live && health?.reachable && health.dashboard_present);

  const urlRef = useRef(dashboardUrl);
  useEffect(() => {
    if (reachableNow) {
      setKeepEmbedded(true);
      urlRef.current = dashboardUrl;
    }
  }, [reachableNow, dashboardUrl]);

  return (
    <AgentEmbedFrame
      title="Scan Debug Recommendation Agent"
      dashboardUrl={urlRef.current || dashboardUrl}
      showEmbedded={reachableNow || keepEmbedded}
      isLive={live}
      isLoading={scanDebugRecHealth.isLoading && !keepEmbedded}
      isFetching={scanDebugRecHealth.isFetching}
      onRetry={() => scanDebugRecHealth.refetch()}
      unavailableHint="Scan Debug Recommendation Agent is not running. Run start-agents.ps1, then open http://localhost:3000/dashboard and click Retry."
    />
  );
}
