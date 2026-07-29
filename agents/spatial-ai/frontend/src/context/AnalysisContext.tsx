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
  getApiErrorMessage,
  predictWafer,
  predictWaferBatch,
} from "@/services/waferVisionService";
import type {
  DashboardTab,
  GridMode,
  PredictOptions,
  WaferAnalysisResult,
} from "@/types/wafer";
import { isLotDashboardTab } from "@/types/wafer";
import {
  DEFAULT_WAFER_FILTERS,
  type WaferFilters,
} from "@/utils/batchAggregates";

export type ApiConnectionStatus =
  | "idle"
  | "connected"
  | "offline"
  | "backend_error";

/** View shown inside the LOT Wafer Analysis modal. */
export type WaferModalView = "analysis" | "spatial" | "zones";

export const SESSION_RESULTS_QUERY_KEY = ["wafer-session-results"] as const;

interface AnalysisContextValue {
  results: WaferAnalysisResult[];
  selectedIndex: number;
  selected: WaferAnalysisResult | null;
  gridMode: GridMode;
  gridSize: number;
  files: File[];
  isAnalyzing: boolean;
  error: string | null;
  connectionStatus: ApiConnectionStatus;
  activeTab: DashboardTab;
  /** Parent Wafer Analysis tab (LOT_n / wafer) when viewing spatial or zones (non-modal). */
  analysisReturnTab: DashboardTab | null;
  /** LOT wafer analysis modal open state. */
  isWaferModalOpen: boolean;
  /** Content view inside the LOT wafer modal. */
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
  /** @deprecated use clearSession */
  reset: () => void;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

function attachSourceFiles(
  data: WaferAnalysisResult[],
  files: File[],
): WaferAnalysisResult[] {
  return data.map((item, index) => ({
    ...item,
    source_file: files[index]?.name || item.source_file || item.wafer_id,
  }));
}

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [results, setResults] = useState<WaferAnalysisResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [gridMode, setGridMode] = useState<GridMode>("automatic");
  const [gridSize, setGridSize] = useState(52);
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ApiConnectionStatus>("idle");
  const [activeTab, setActiveTabState] = useState<DashboardTab>("overview");
  const [analysisReturnTab, setAnalysisReturnTab] =
    useState<DashboardTab | null>(null);
  const [isWaferModalOpen, setIsWaferModalOpen] = useState(false);
  const [waferModalView, setWaferModalView] =
    useState<WaferModalView>("analysis");
  const lotScrollYRef = useRef(0);
  const [comparisonIndices, setComparisonIndices] = useState<number[]>([]);
  const [filters, setFiltersState] = useState<WaferFilters>(DEFAULT_WAFER_FILTERS);

  const persistResults = useCallback(
    (next: WaferAnalysisResult[]) => {
      setResults(next);
      queryClient.setQueryData(SESSION_RESULTS_QUERY_KEY, next);
    },
    [queryClient],
  );

  const mutation = useMutation({
    mutationKey: ["predict-session"],
    mutationFn: async () => {
      if (!files.length) {
        throw new Error("Select at least one wafer image.");
      }
      const options: PredictOptions = {
        gridMode,
        gridSize: gridMode === "manual" ? gridSize : undefined,
      };
      if (files.length === 1) {
        const one = await predictWafer(files[0], options);
        return attachSourceFiles([one], files);
      }
      const batch = await predictWaferBatch(files, options);
      return attachSourceFiles(batch, files);
    },
    onSuccess: (data) => {
      setResults((prev) => {
        const next = [...prev, ...data];
        queryClient.setQueryData(SESSION_RESULTS_QUERY_KEY, next);
        setSelectedIndex(prev.length);
        return next;
      });
      setError(null);
      setConnectionStatus("connected");
      setActiveTabState(data.length > 1 ? "overview" : "wafer");
      setAnalysisReturnTab(null);
      setIsWaferModalOpen(false);
      setWaferModalView("analysis");
    },
    onError: (err) => {
      const message = getApiErrorMessage(err);
      setError(message);
      if (message.toLowerCase().includes("network")) {
        setConnectionStatus("offline");
      } else {
        setConnectionStatus("backend_error");
      }
    },
  });

  const analyze = useCallback(() => {
    setError(null);
    mutation.mutate();
  }, [mutation]);

  const clearSession = useCallback(() => {
    persistResults([]);
    setSelectedIndex(0);
    setFiles([]);
    setError(null);
    setComparisonIndices([]);
    setFiltersState(DEFAULT_WAFER_FILTERS);
    setActiveTabState("overview");
    setAnalysisReturnTab(null);
    setIsWaferModalOpen(false);
    setWaferModalView("analysis");
  }, [persistResults]);

  const setFilters = useCallback((patch: Partial<WaferFilters>) => {
    setFiltersState((prev) => ({ ...prev, ...patch }));
  }, []);

  const toggleComparison = useCallback((index: number) => {
    setComparisonIndices((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index],
    );
  }, []);

  const clearComparison = useCallback(() => setComparisonIndices([]), []);

  const closeWaferAnalysisModal = useCallback(() => {
    setIsWaferModalOpen(false);
    setWaferModalView("analysis");
    const y = lotScrollYRef.current;
    requestAnimationFrame(() => {
      window.scrollTo(0, y);
    });
  }, []);

  const openWaferAnalysisModal = useCallback((index: number) => {
    lotScrollYRef.current = window.scrollY;
    setSelectedIndex(index);
    setWaferModalView("analysis");
    setIsWaferModalOpen(true);
  }, []);

  const setActiveTab = useCallback(
    (tab: DashboardTab) => {
      if (tab !== "spatial" && tab !== "zones") {
        setAnalysisReturnTab(null);
      }
      setIsWaferModalOpen(false);
      setWaferModalView("analysis");
      setActiveTabState(tab);
    },
    [],
  );

  const openWaferChildView = useCallback(
    (child: "spatial" | "zones") => {
      if (isWaferModalOpen) {
        setWaferModalView(child);
        return;
      }
      setActiveTabState((current) => {
        if (current !== "spatial" && current !== "zones") {
          setAnalysisReturnTab(current);
        }
        return child;
      });
    },
    [isWaferModalOpen],
  );

  const returnToWaferAnalysis = useCallback(() => {
    if (isWaferModalOpen) {
      setWaferModalView("analysis");
      return;
    }
    const target =
      analysisReturnTab &&
      analysisReturnTab !== "spatial" &&
      analysisReturnTab !== "zones"
        ? analysisReturnTab
        : "wafer";
    setAnalysisReturnTab(null);
    setActiveTabState(target);
  }, [analysisReturnTab, isWaferModalOpen]);

  const selectWafer = useCallback((index: number) => {
    setSelectedIndex(index);
    setActiveTabState((prev) => {
      if (prev === "spatial" || prev === "zones") return prev;
      return isLotDashboardTab(prev) ? prev : "wafer";
    });
  }, []);

  const value = useMemo<AnalysisContextValue>(
    () => ({
      results,
      selectedIndex,
      selected: results[selectedIndex] ?? null,
      gridMode,
      gridSize,
      files,
      isAnalyzing: mutation.isPending,
      error,
      connectionStatus,
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
      clearError: () => setError(null),
      analyze,
      clearSession,
      reset: clearSession,
    }),
    [
      results,
      selectedIndex,
      gridMode,
      gridSize,
      files,
      mutation.isPending,
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
      analyze,
      clearSession,
    ],
  );

  return (
    <AnalysisContext.Provider value={value}>{children}</AnalysisContext.Provider>
  );
}

export function useAnalysis(): AnalysisContextValue {
  const ctx = useContext(AnalysisContext);
  if (!ctx) {
    throw new Error("useAnalysis must be used within AnalysisProvider");
  }
  return ctx;
}
