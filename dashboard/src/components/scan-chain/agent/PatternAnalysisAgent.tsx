"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AgentEmbedFrame } from "@/components/scan-chain/agent/AgentEmbedFrame";
import { getPatternAgentHealth } from "@/lib/api/dashboard";
import { isLiveApi } from "@/lib/api/config";
import { resolveAgentEmbedUrl } from "@/lib/agentEmbedUrls";

export function PatternAnalysisAgent() {
  const live = isLiveApi();
  const [keepEmbedded, setKeepEmbedded] = useState(false);

  const patternAgentHealth = useQuery({
    queryKey: ["integration", "pattern-agent", "health"],
    queryFn: getPatternAgentHealth,
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

  const health = patternAgentHealth.data;
  const dashboardUrl = resolveAgentEmbedUrl(health?.embed_path, "pattern");
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
      title="Pattern Analysis Agent"
      dashboardUrl={urlRef.current || dashboardUrl}
      showEmbedded={reachableNow || keepEmbedded}
      isLive={live}
      isLoading={patternAgentHealth.isLoading && !keepEmbedded}
      isFetching={patternAgentHealth.isFetching}
      onRetry={() => patternAgentHealth.refetch()}
      unavailableHint="Pattern Agent is not running. Run start-agents.ps1, then open http://localhost:3000/dashboard and click Retry."
    />
  );
}
