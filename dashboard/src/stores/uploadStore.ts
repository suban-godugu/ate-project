import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  defaultAILogSummary,
  formatNow,
  generateUploadId,
  initialDataUploadHistory,
  initialLogUploadHistory,
} from "@/lib/uploadData";
import type {
  AILogSummary,
  DataUploadRecord,
  LogUploadRecord,
  ToastType,
  UploadToastMessage,
} from "@/types/upload";

interface UploadStore {
  dataHistory: DataUploadRecord[];
  logHistory: LogUploadRecord[];
  toasts: UploadToastMessage[];
  lastAILogSummary: AILogSummary;
  addDataUpload: (record: Omit<DataUploadRecord, "id" | "uploadTime">) => string;
  addLogUpload: (record: Omit<LogUploadRecord, "id" | "uploadTime" | "processingTime">) => string;
  updateDataStatus: (id: string, status: DataUploadRecord["status"]) => void;
  updateLogStatus: (id: string, status: LogUploadRecord["status"], processingTime?: string) => void;
  removeDataUpload: (id: string) => void;
  removeLogUpload: (id: string) => void;
  showToast: (message: string, type?: ToastType) => void;
  dismissToast: (id: string) => void;
  setLastAILogSummary: (summary: AILogSummary) => void;
}

export const useUploadStore = create<UploadStore>()(
  persist(
    (set, get) => ({
      dataHistory: initialDataUploadHistory,
      logHistory: initialLogUploadHistory,
      toasts: [],
      lastAILogSummary: defaultAILogSummary,

      addDataUpload: (record) => {
        const id = generateUploadId("D");
        set((state) => ({
          dataHistory: [{ ...record, id, uploadTime: formatNow() }, ...state.dataHistory],
        }));
        return id;
      },

      addLogUpload: (record) => {
        const id = generateUploadId("L");
        set((state) => ({
          logHistory: [
            { ...record, id, uploadTime: formatNow(), processingTime: "—" },
            ...state.logHistory,
          ],
        }));
        return id;
      },

      updateDataStatus: (id, status) =>
        set((state) => ({
          dataHistory: state.dataHistory.map((r) =>
            r.id === id ? { ...r, status } : r
          ),
        })),

      updateLogStatus: (id, status, processingTime) =>
        set((state) => ({
          logHistory: state.logHistory.map((r) =>
            r.id === id
              ? { ...r, status, processingTime: processingTime ?? r.processingTime }
              : r
          ),
        })),

      removeDataUpload: (id) =>
        set((state) => ({
          dataHistory: state.dataHistory.filter((r) => r.id !== id),
        })),

      removeLogUpload: (id) =>
        set((state) => ({
          logHistory: state.logHistory.filter((r) => r.id !== id),
        })),

      showToast: (message, type = "success") => {
        const id =
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? `toast-${crypto.randomUUID()}`
            : `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        set((state) => ({
          toasts: [...state.toasts, { id, message, type }],
        }));
        setTimeout(() => {
          set((state) => ({
            toasts: state.toasts.filter((t) => t.id !== id),
          }));
        }, 4000);
      },

      dismissToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),

      setLastAILogSummary: (summary) => set({ lastAILogSummary: summary }),
    }),
    {
      name: "ate-uploads",
      partialize: (state) => ({
        dataHistory: state.dataHistory,
        logHistory: state.logHistory,
        lastAILogSummary: state.lastAILogSummary,
      }),
    }
  )
);
