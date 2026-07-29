import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIStore {
  mobileSidebarOpen: boolean;
  sidebarCollapsed: boolean;
  recommendationAgentTab: "pattern-agent" | "scan-debug-agent" | "test-optimization-agent";
  setMobileSidebarOpen: (open: boolean) => void;
  toggleMobileSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebarCollapsed: () => void;
  setRecommendationAgentTab: (
    tab: "pattern-agent" | "scan-debug-agent" | "test-optimization-agent"
  ) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      mobileSidebarOpen: false,
      sidebarCollapsed: false,
      recommendationAgentTab: "pattern-agent" as const,
      setMobileSidebarOpen: (mobileSidebarOpen) => set({ mobileSidebarOpen }),
      toggleMobileSidebar: () =>
        set((state) => ({ mobileSidebarOpen: !state.mobileSidebarOpen })),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
      toggleSidebarCollapsed: () =>
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setRecommendationAgentTab: (recommendationAgentTab) => set({ recommendationAgentTab }),
    }),
    {
      name: "ate-ui-state",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        recommendationAgentTab: state.recommendationAgentTab,
      }),
    }
  )
);
