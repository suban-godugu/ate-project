import { create } from "zustand";
import { persist } from "zustand/middleware";
import { defaultGlobalFilters, type GlobalFilters } from "@/types/platform";

interface FilterStore {
  filters: GlobalFilters;
  searchQuery: string;
  setFilters: (partial: Partial<GlobalFilters>) => void;
  resetFilters: () => void;
  setSearchQuery: (query: string) => void;
}

export const useFilterStore = create<FilterStore>()(
  persist(
    (set) => ({
      filters: defaultGlobalFilters,
      searchQuery: "",
      setFilters: (partial) =>
        set((state) => ({ filters: { ...state.filters, ...partial } })),
      resetFilters: () => set({ filters: defaultGlobalFilters }),
      setSearchQuery: (searchQuery) => set({ searchQuery }),
    }),
    { name: "ate-filters" }
  )
);
