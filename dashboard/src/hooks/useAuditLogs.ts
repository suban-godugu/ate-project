"use client";

import { useQuery } from "@tanstack/react-query";
import { auditApi, type AuditQueryParams } from "@/lib/api/audit";
import { isLiveApi } from "@/lib/api/config";

export function useAuditLogs(params: AuditQueryParams) {
  return useQuery({
    queryKey: ["audit", params],
    queryFn: () => auditApi.getAuditLogs(params),
    enabled: isLiveApi(),
    staleTime: 30_000,
  });
}
