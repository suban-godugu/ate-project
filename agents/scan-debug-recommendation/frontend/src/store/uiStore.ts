"use client";

import { create } from "zustand";
import type { ScanDebugKpiId } from "@/types/kpiDrillDown";

interface UiState {
  activeKpiId: ScanDebugKpiId | null;
  setActiveKpiId: (id: ScanDebugKpiId | null) => void;
}

export const useUiStore = create<UiState>()((set) => ({
  activeKpiId: null,
  setActiveKpiId: (id) => set({ activeKpiId: id }),
}));

export const VALID_KPI_IDS = new Set<ScanDebugKpiId>([
  "broken_chains",
  "debug_recommendations",
  "avg_ai_confidence",
  "constraint_violations",
  "pending_review",
  "coverage_impact",
  "timing_violations",
  "timing_debug_recs",
  "worst_slack",
  "power_violations",
  "power_debug_recs",
  "peak_switching",
  "defect_suspects",
  "investigation_recs",
  "defect_localization",
]);

const KPI_ID_ALIASES: Record<string, ScanDebugKpiId> = {
  debug_time_saved: "timing_debug_recs",
};

export function normalizeKpiId(id: string | null | undefined): ScanDebugKpiId | null {
  if (!id) return null;
  const resolved = KPI_ID_ALIASES[id] ?? id;
  return VALID_KPI_IDS.has(resolved as ScanDebugKpiId) ? (resolved as ScanDebugKpiId) : null;
}
