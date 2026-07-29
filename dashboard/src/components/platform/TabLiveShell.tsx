"use client";

import type { ReactNode } from "react";
import { useModuleTab } from "@/contexts/ModuleTabContext";
import { LiveModuleGate, type LiveModuleStatus } from "@/components/platform/LiveModuleGate";

interface TabLiveShellProps {
  module: string;
  /** Active tab override when not using ModuleTabContext (e.g. wafer defect class). */
  tab?: string;
  hookResult: LiveModuleStatus;
  children: ReactNode;
}

export function TabLiveShell({ module, tab: tabProp, hookResult, children }: TabLiveShellProps) {
  const contextTab = useModuleTab();
  const tab = tabProp ?? contextTab;

  return (
    <LiveModuleGate
      module={module}
      tab={tab}
      isLoading={hookResult.isLoading}
      isFetching={hookResult.isFetching}
      isError={hookResult.isError}
      isEmpty={hookResult.isEmpty}
      error={hookResult.error}
      refetch={hookResult.refetch}
    >
      {children}
    </LiveModuleGate>
  );
}
