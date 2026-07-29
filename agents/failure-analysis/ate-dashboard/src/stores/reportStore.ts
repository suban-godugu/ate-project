"use client";

import { create } from "zustand";

export type ExportFormat = "pdf" | "csv" | "xlsx" | "json" | "html";

type ReportState = {
  reportId: string | null;
  exporting: ExportFormat | null;
  lastExportUrl: string | null;
  error: string | null;
  setReportId: (id: string | null) => void;
  setExporting: (fmt: ExportFormat | null) => void;
  setLastExportUrl: (url: string | null) => void;
  setError: (error: string | null) => void;
  reset: () => void;
};

export const useReportStore = create<ReportState>((set) => ({
  reportId: null,
  exporting: null,
  lastExportUrl: null,
  error: null,
  setReportId: (id) => set({ reportId: id }),
  setExporting: (fmt) => set({ exporting: fmt }),
  setLastExportUrl: (url) => set({ lastExportUrl: url }),
  setError: (error) => set({ error }),
  reset: () =>
    set({ reportId: null, exporting: null, lastExportUrl: null, error: null }),
}));
