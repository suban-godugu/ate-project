"use client";

import type { ReactNode } from "react";
import { isLiveApi } from "@/lib/api/config";
import { getLiveEmptyMessage } from "@/lib/liveTabMessages";
import {
  EnterpriseEmptyState,
  EnterpriseErrorState,
  EnterpriseLoadingState,
} from "@/components/platform/EnterpriseLiveStates";

export interface LiveModuleStatus {
  isLoading?: boolean;
  isFetching?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  error?: unknown;
  refetch?: () => void;
}

interface LiveModuleGateProps extends LiveModuleStatus {
  module: string;
  tab: string;
  children: ReactNode;
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  return "Unknown error";
}

/** In live mode: loading / error / empty gates. In mock mode: pass-through. */
export function LiveModuleGate({
  module,
  tab,
  isLoading,
  isFetching,
  isError,
  isEmpty,
  error,
  refetch,
  children,
}: LiveModuleGateProps) {
  if (!isLiveApi()) {
    return <>{children}</>;
  }

  if (isLoading) {
    return <EnterpriseLoadingState />;
  }

  if (isError) {
    return (
      <EnterpriseErrorState
        technicalDetails={error ? errorMessage(error) : undefined}
        onRetry={refetch ? () => refetch() : undefined}
      />
    );
  }

  if (isEmpty) {
    const msg = getLiveEmptyMessage(module, tab);
    return <EnterpriseEmptyState title={msg.title} description={msg.description} />;
  }

  return <>{children}</>;
}
