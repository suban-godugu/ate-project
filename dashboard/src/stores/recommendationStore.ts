import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { RecommendationActionStatus } from "@/types/platform";

interface RecommendationStore {
  statuses: Record<string, RecommendationActionStatus>;
  setStatus: (id: string, status: RecommendationActionStatus) => void;
  undoStatus: (id: string) => void;
  getStatus: (id: string) => RecommendationActionStatus;
}

export const useRecommendationStore = create<RecommendationStore>()(
  persist(
    (set, get) => ({
      statuses: {},
      setStatus: (id, status) =>
        set((state) => ({
          statuses: { ...state.statuses, [id]: status },
        })),
      undoStatus: (id) =>
        set((state) => {
          const next = { ...state.statuses };
          delete next[id];
          return { statuses: next };
        }),
      getStatus: (id) => get().statuses[id] ?? "pending",
    }),
    { name: "ate-recommendation-actions" }
  )
);
