"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  DEFAULT_FILTERS,
  type ConnectionStatus,
  type DashboardTab,
  type GridMode,
  type WaferAnalysisResult,
  type WaferFilters,
  type WaferModalView,
} from "@/wafervision/types";
import { getApiErrorMessage, runPrediction } from "@/wafervision/services/waferVisionService";
import { resolveLot } from "@/wafervision/utils/batchAggregates";

interface AnalysisContextValue {
  results: WaferAnalysisResult[];
  selectedIndex: number;
  selected: WaferAnalysisResult | null;
  gridMode: GridMode;
  gridSize: number;
  files: File[];
  isAnalyzing: boolean;
  error: string | null;
  connectionStatus: ConnectionStatus;
  activeTab: DashboardTab;
  analysisReturnTab: DashboardTab | null;
  isWaferModalOpen: boolean;
  waferModalView: WaferModalView;
  comparisonIndices: number[];
  filters: WaferFilters;
  setGridMode: (mode: GridMode) => void;
  setGridSize: (size: number) => void;
  setFiles: (files: File[]) => void;
  selectWafer: (index: number) => void;
  setActiveTab: (tab: DashboardTab) => void;
  openWaferAnalysisModal: (index: number) => void;
  closeWaferAnalysisModal: () => void;
  openWaferChildView: (child: "spatial" | "zones") => void;
  returnToWaferAnalysis: () => void;
  setFilters: (patch: Partial<WaferFilters>) => void;
  toggleComparison: (index: number) => void;
  clearComparison: () => void;
  clearError: () => void;
  analyze: () => void;
  clearSession: () => void;
  cycleLotWafer: (lot: string, direction: 1 | -1) => void;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const scrollYRef = useRef(0);

  const [results, setResults] = useState<WaferAnalysisResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [gridMode, setGridMode] = useState<GridMode>("automatic");
  const [gridSize, setGridSize] = useState(52);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("idle");
  const [activeTab, setActiveTabState] = useState<DashboardTab>("overview");
  const [analysisReturnTab, setAnalysisReturnTab] = useState<DashboardTab | null>(null);
  const [isWaferModalOpen, setIsWaferModalOpen] = useState(false);
  const [waferModalView, setWaferModalView] = useState<WaferModalView>("analysis");
  const [comparisonIndices, setComparisonIndices] = useState<number[]>([]);
  const [filters, setFiltersState] = useState<WaferFilters>(DEFAULT_FILTERS);

  const selected = results[selectedIndex] ?? null;

  const mutation = useMutation({
    mutationKey: ["predict-session"],
    mutationFn: () => runPrediction(files, gridMode, gridSize),
    onSuccess: (data) => {
      const attached = data.map((item, i) => ({
        ...item,
        source_file: item.source_file || files[i]?.name || item.wafer_id,
      }));
      setResults((prev) => {
        const firstNew = prev.length;
        const next = [...prev, ...attached];
        queryClient.setQueryData(["wafer-session-results"], next);
        setSelectedIndex(firstNew);
        return next;
      });
      setConnectionStatus("connected");
      setError(null);
      setIsWaferModalOpen(false);
      setWaferModalView("analysis");
      setAnalysisReturnTab(null);
      setActiveTabState(attached.length > 1 ? "overview" : "wafer");
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      setError(message);
      setConnectionStatus(
        message.toLowerCase().includes("network") ? "offline" : "backend_error"
      );
    },
  });

  const selectWafer = useCallback(
    (index: number) => {
      setSelectedIndex(index);
      setActiveTabState((tab) => {
        if (tab.startsWith("LOT_")) return tab;
        if (tab === "spatial" || tab === "zones") return tab;
        return "wafer";
      });
    },
    []
  );

  const setActiveTab = useCallback((tab: DashboardTab) => {
    setIsWaferModalOpen(false);
    setWaferModalView("analysis");
    if (tab !== "spatial" && tab !== "zones") setAnalysisReturnTab(null);
    setActiveTabState(tab);
  }, []);

  const openWaferAnalysisModal = useCallback((index: number) => {
    scrollYRef.current = window.scrollY;
    setSelectedIndex(index);
    setWaferModalView("analysis");
    setIsWaferModalOpen(true);
  }, []);

  const closeWaferAnalysisModal = useCallback(() => {
    setIsWaferModalOpen(false);
    setWaferModalView("analysis");
    requestAnimationFrame(() => {
      window.scrollTo({ top: scrollYRef.current });
    });
  }, []);

  const openWaferChildView = useCallback(
    (child: "spatial" | "zones") => {
      if (isWaferModalOpen) {
        setWaferModalView(child);
        return;
      }
      setAnalysisReturnTab(activeTab);
      setActiveTabState(child);
    },
    [activeTab, isWaferModalOpen]
  );

  const returnToWaferAnalysis = useCallback(() => {
    if (isWaferModalOpen) {
      setWaferModalView("analysis");
      return;
    }
    setActiveTabState(analysisReturnTab ?? "wafer");
    setAnalysisReturnTab(null);
  }, [analysisReturnTab, isWaferModalOpen]);

  const setFilters = useCallback((patch: Partial<WaferFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...patch }));
  }, []);

  const toggleComparison = useCallback((index: number) => {
    setComparisonIndices((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  }, []);

  const clearComparison = useCallback(() => setComparisonIndices([]), []);
  const clearError = useCallback(() => setError(null), []);

  const clearSession = useCallback(() => {
    setResults([]);
    queryClient.setQueryData(["wafer-session-results"], []);
    setSelectedIndex(0);
    setFiles([]);
    setError(null);
    setComparisonIndices([]);
    setFiltersState(DEFAULT_FILTERS);
    setActiveTabState("overview");
    setAnalysisReturnTab(null);
    setIsWaferModalOpen(false);
    setWaferModalView("analysis");
  }, [queryClient]);

  const cycleLotWafer = useCallback(
    (lot: string, direction: 1 | -1) => {
      const members = results
        .map((r, i) => ({ r, i }))
        .filter(({ r }) => resolveLot(r).toUpperCase() === lot.toUpperCase());
      if (!members.length) return;
      const pos = members.findIndex((m) => m.i === selectedIndex);
      const next =
        members[(pos < 0 ? 0 : pos + direction + members.length) % members.length];
      setSelectedIndex(next.i);
      setWaferModalView("analysis");
    },
    [results, selectedIndex]
  );

  const value = useMemo<AnalysisContextValue>(
    () => ({
      results,
      selectedIndex,
      selected,
      gridMode,
      gridSize,
      files,
      isAnalyzing: mutation.isPending,
      error,
      connectionStatus: mutation.isPending ? "idle" : connectionStatus,
      activeTab,
      analysisReturnTab,
      isWaferModalOpen,
      waferModalView,
      comparisonIndices,
      filters,
      setGridMode,
      setGridSize,
      setFiles,
      selectWafer,
      setActiveTab,
      openWaferAnalysisModal,
      closeWaferAnalysisModal,
      openWaferChildView,
      returnToWaferAnalysis,
      setFilters,
      toggleComparison,
      clearComparison,
      clearError,
      analyze: () => mutation.mutate(),
      clearSession,
      cycleLotWafer,
    }),
    [
      results,
      selectedIndex,
      selected,
      gridMode,
      gridSize,
      files,
      mutation,
      error,
      connectionStatus,
      activeTab,
      analysisReturnTab,
      isWaferModalOpen,
      waferModalView,
      comparisonIndices,
      filters,
      selectWafer,
      setActiveTab,
      openWaferAnalysisModal,
      closeWaferAnalysisModal,
      openWaferChildView,
      returnToWaferAnalysis,
      setFilters,
      toggleComparison,
      clearComparison,
      clearError,
      clearSession,
      cycleLotWafer,
    ]
  );

  return (
    <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
  );
}

export function useAnalysis() {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error("useAnalysis must be used within AnalysisProvider");
  return ctx;
}
