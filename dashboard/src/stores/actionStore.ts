import { create } from "zustand";
import type { AIDiagnosisResult, PrimaryActionResult } from "@/types/platform";

interface ActionStore {
  runningAction: string | null;
  lastPrimaryResult: PrimaryActionResult | null;
  aiDiagnosisRunning: boolean;
  aiDiagnosisStep: number;
  aiDiagnosisResult: AIDiagnosisResult | null;
  setRunningAction: (id: string | null) => void;
  setPrimaryResult: (result: PrimaryActionResult | null) => void;
  setAIDiagnosisRunning: (running: boolean) => void;
  setAIDiagnosisStep: (step: number) => void;
  setAIDiagnosisResult: (result: AIDiagnosisResult | null) => void;
}

export const useActionStore = create<ActionStore>()((set) => ({
  runningAction: null,
  lastPrimaryResult: null,
  aiDiagnosisRunning: false,
  aiDiagnosisStep: 0,
  aiDiagnosisResult: null,
  setRunningAction: (runningAction) => set({ runningAction }),
  setPrimaryResult: (lastPrimaryResult) => set({ lastPrimaryResult }),
  setAIDiagnosisRunning: (aiDiagnosisRunning) => set({ aiDiagnosisRunning }),
  setAIDiagnosisStep: (aiDiagnosisStep) => set({ aiDiagnosisStep }),
  setAIDiagnosisResult: (aiDiagnosisResult) => set({ aiDiagnosisResult }),
}));
