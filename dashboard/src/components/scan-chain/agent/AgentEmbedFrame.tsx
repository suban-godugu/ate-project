"use client";

import { useEffect, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface AgentEmbedFrameProps {
  title: string;
  dashboardUrl: string;
  showEmbedded: boolean;
  isLive: boolean;
  isLoading: boolean;
  isFetching: boolean;
  onRetry: () => void;
  unavailableHint?: string;
}

function withPlatformEmbed(url: string): string {
  try {
    const base =
      typeof window !== "undefined" ? window.location.origin : "http://localhost:3000";
    const parsed = new URL(url, base);
    parsed.searchParams.set("embed", "1");
    parsed.searchParams.set("v", "agent-original-ui");
    // Keep same-origin relative path so rewrites stay on :3000
    return `${parsed.pathname}${parsed.search}`;
  } catch {
    const base = url.includes("?") ? `${url}&embed=1` : `${url}?embed=1`;
    return `${base}&v=agent-original-ui`;
  }
}

export function AgentEmbedFrame({
  title,
  dashboardUrl,
  showEmbedded,
  isLive,
  isLoading,
  isFetching,
  onRetry,
  unavailableHint,
}: AgentEmbedFrameProps) {
  const embedSrc = withPlatformEmbed(dashboardUrl);
  const [probeOk, setProbeOk] = useState(false);
  const [probing, setProbing] = useState(false);
  const workspaceClass = "overflow-hidden bg-[#090b12]";
  const iframeClass =
    "min-h-[calc(100vh-160px)] h-[calc(100vh-160px)] w-full border-0 bg-[#090b12]";

  useEffect(() => {
    if (!isLive || showEmbedded || !dashboardUrl.startsWith("/embed/")) {
      setProbeOk(false);
      setProbing(false);
      return;
    }

    let cancelled = false;
    setProbing(true);
    fetch(embedSrc, { method: "GET", cache: "no-store" })
      .then((res) => {
        if (!cancelled) setProbeOk(res.ok);
      })
      .catch(() => {
        if (!cancelled) setProbeOk(false);
      })
      .finally(() => {
        if (!cancelled) setProbing(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isLive, showEmbedded, dashboardUrl, embedSrc, isFetching]);

  const canShow = showEmbedded || probeOk;

  if (isLive && (isLoading || probing) && !canShow) {
    return (
      <div className="dashboard-content">
        <div
          className={`flex min-h-[calc(100vh-200px)] flex-col items-center justify-center ${workspaceClass}`}
        >
          <Loader2 className="h-7 w-7 animate-spin text-[#7C3AED]" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-white">Loading {title}</p>
          <p className="mt-1 text-xs text-slate-400">Preparing workspace…</p>
        </div>
      </div>
    );
  }

  if (canShow) {
    return (
      <div className="dashboard-content !gap-0">
        <div className={workspaceClass}>
          <iframe title={title} src={embedSrc} className={iframeClass} />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-content">
      <div
        className={`flex min-h-[calc(100vh-200px)] flex-col items-center justify-center border border-dashed border-[#2D3748] px-6 text-center ${workspaceClass}`}
      >
        <p className="text-base font-medium text-white">{title} workspace unavailable</p>
        <p className="mt-2 max-w-2xl text-sm text-slate-400">
          {unavailableHint ??
            `Start the ${title} service to load this Scan Chain workspace.`}
        </p>
        {isLive ? (
          <Button
            variant="outline"
            size="sm"
            className="mt-5 border-[#2D3748] text-xs"
            onClick={onRetry}
            disabled={isFetching}
          >
            <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            Retry
          </Button>
        ) : (
          <p className="mt-4 text-xs text-slate-500">Switch to live API mode to open this workspace.</p>
        )}
      </div>
    </div>
  );
}
