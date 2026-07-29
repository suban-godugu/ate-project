"use client";

import { useUploadStore } from "@/stores/uploadStore";

export function UploadProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function useUpload() {
  const store = useUploadStore();
  return {
    dataHistory: store.dataHistory,
    logHistory: store.logHistory,
    toasts: store.toasts,
    addDataUpload: store.addDataUpload,
    addLogUpload: store.addLogUpload,
    updateDataStatus: store.updateDataStatus,
    updateLogStatus: store.updateLogStatus,
    removeDataUpload: store.removeDataUpload,
    removeLogUpload: store.removeLogUpload,
    showToast: store.showToast,
    dismissToast: store.dismissToast,
    lastAILogSummary: store.lastAILogSummary,
    setLastAILogSummary: store.setLastAILogSummary,
  };
}
