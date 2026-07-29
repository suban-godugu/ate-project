"use client";

import { create } from "zustand";

export type DieSelection = {
  die_id?: string;
  x: number;
  y: number;
  status?: string;
  failure_count?: number;
  confidence?: number;
};

type VisualizationState = {
  waferZoom: number;
  waferPan: { x: number; y: number };
  dieZoom: number;
  diePan: { x: number; y: number };
  selectedDie: DieSelection | null;
  selectedPatternId: string | null;
  selectedCorrelationId: string | null;
  expandedPatternRows: Set<string>;

  setWaferTransform: (zoom: number, pan: { x: number; y: number }) => void;
  setDieTransform: (zoom: number, pan: { x: number; y: number }) => void;
  setSelectedDie: (die: DieSelection | null) => void;
  setSelectedPatternId: (id: string | null) => void;
  setSelectedCorrelationId: (id: string | null) => void;
  togglePatternRow: (id: string) => void;
  reset: () => void;
};

const initial = {
  waferZoom: 1,
  waferPan: { x: 0, y: 0 },
  dieZoom: 1,
  diePan: { x: 0, y: 0 },
  selectedDie: null as DieSelection | null,
  selectedPatternId: null as string | null,
  selectedCorrelationId: null as string | null,
  expandedPatternRows: new Set<string>(),
};

export const useVisualizationStore = create<VisualizationState>((set, get) => ({
  ...initial,

  setWaferTransform: (zoom, pan) => set({ waferZoom: zoom, waferPan: pan }),
  setDieTransform: (zoom, pan) => set({ dieZoom: zoom, diePan: pan }),
  setSelectedDie: (die) => set({ selectedDie: die }),
  setSelectedPatternId: (id) => set({ selectedPatternId: id }),
  setSelectedCorrelationId: (id) => set({ selectedCorrelationId: id }),
  togglePatternRow: (id) => {
    const next = new Set(get().expandedPatternRows);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    set({ expandedPatternRows: next });
  },
  reset: () => set({ ...initial, expandedPatternRows: new Set() }),
}));
