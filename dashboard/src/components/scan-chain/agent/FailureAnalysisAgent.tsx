"use client";

import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AgentEmbedFrame } from "@/components/scan-chain/agent/AgentEmbedFrame";
import { getFailureAgentHealth } from "@/lib/api/dashboard";
import { isLiveApi } from "@/lib/api/config";
import { resolveAgentEmbedUrl } from "@/lib/agentEmbedUrls";

export function FailureAnalysisAgent() {
  const live = isLiveApi();
  const [keepEmbedded, setKeepEmbedded] = useState(false);

  const failureAgentHealth = useQuery({
    queryKey: ["integration", "failure-agent", "health"],
    queryFn: getFailureAgentHealth,
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

  const health = failureAgentHealth.data;
  const dashboardUrl = resolveAgentEmbedUrl(health?.embed_path, "failure");
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
      title="Failure Analysis Agent"
      dashboardUrl={urlRef.current || dashboardUrl}
      showEmbedded={reachableNow || keepEmbedded}
      isLive={live}
      isLoading={failureAgentHealth.isLoading && !keepEmbedded}
      isFetching={failureAgentHealth.isFetching}
      onRetry={() => failureAgentHealth.refetch()}
      unavailableHint="Failure Agent is not running. Run start-agents.ps1, then open http://localhost:3000/dashboard and click Retry."
    />
  );
}
