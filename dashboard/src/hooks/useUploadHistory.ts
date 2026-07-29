"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { isLiveApi } from "@/lib/api/config";
import { uploadsApi } from "@/lib/api/uploads";
import { useUploadStore } from "@/stores/uploadStore";
import type { DataUploadRecord, LogUploadRecord } from "@/types/upload";

export const UPLOAD_DATA_QUERY_KEY = ["uploads", "data"] as const;
export const UPLOAD_LOG_QUERY_KEY = ["uploads", "log"] as const;

export function useDataUploadHistory() {
  const mockHistory = useUploadStore((s) => s.dataHistory);
  const query = useQuery({
    queryKey: UPLOAD_DATA_QUERY_KEY,
    queryFn: () => uploadsApi.listDataUploads(),
    enabled: isLiveApi(),
    refetchOnMount: "always",
    refetchInterval: 10_000,
  });

  return {
    history: (isLiveApi() ? query.data?.items : mockHistory) ?? [],
    isLoading: isLiveApi() ? query.isLoading : false,
  };
}

export function useLogUploadHistory() {
  const mockHistory = useUploadStore((s) => s.logHistory);
  const query = useQuery({
    queryKey: UPLOAD_LOG_QUERY_KEY,
    queryFn: () => uploadsApi.listLogUploads(),
    enabled: isLiveApi(),
    refetchOnMount: "always",
    refetchInterval: 10_000,
  });

  return {
    history: (isLiveApi() ? query.data?.items : mockHistory) ?? [],
    isLoading: isLiveApi() ? query.isLoading : false,
  };
}

export function useInvalidateUploadHistory() {
  const queryClient = useQueryClient();
  return {
    invalidateData: () => queryClient.invalidateQueries({ queryKey: UPLOAD_DATA_QUERY_KEY }),
    invalidateLog: () => queryClient.invalidateQueries({ queryKey: UPLOAD_LOG_QUERY_KEY }),
  };
}

export type { DataUploadRecord, LogUploadRecord };
