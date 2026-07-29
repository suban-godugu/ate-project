"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AnalysisHistoryEntry = {
  execution_id: string;
  dataset_id?: string | null;
  upload_id?: string | null;
  dataset_name?: string;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number;
  user?: string;
  pass_count?: number;
  fail_count?: number;
};

type HistoryState = {
  entries: AnalysisHistoryEntry[];
  selectedExecutionId: string | null;
  setEntries: (entries: AnalysisHistoryEntry[]) => void;
  selectExecution: (executionId: string | null) => void;
  upsertEntry: (entry: AnalysisHistoryEntry) => void;
};

export const useHistoryStore = create<HistoryState>()(
  persist(
    (set, get) => ({
      entries: [],
      selectedExecutionId: null,
      setEntries: (entries) => set({ entries }),
      selectExecution: (executionId) => set({ selectedExecutionId: executionId }),
      upsertEntry: (entry) => {
        const existing = get().entries.filter((e) => e.execution_id !== entry.execution_id);
        set({ entries: [entry, ...existing].slice(0, 100) });
      },
    }),
    { name: "fa-analysis-history", partialize: (s) => ({ entries: s.entries }) },
  ),
);
