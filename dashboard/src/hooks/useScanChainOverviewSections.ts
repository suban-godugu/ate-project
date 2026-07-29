"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";
import { isLiveApi } from "@/lib/api/config";
import { getModuleTab, type DashboardTabData } from "@/lib/api/dashboard";
import * as mock from "@/lib/scanChainData";
import { useFilterStore } from "@/stores/filterStore";
import type { OverviewMiniKPI } from "@/components/scan-chain/overview/OverviewDrillDownSection";
import type {
  ChipFailData,
  FailureDistribution,
  TrendPoint,
} from "@/types/scanChain";

const TABS = ["pattern-analysis", "failure-analysis", "scan-diagnosis"] as const;

type LiveRow = Record<string, unknown>;

function rows(payload: DashboardTabData | undefined): LiveRow[] {
  return (payload?.rows ?? []) as LiveRow[];
}

function chart<T>(payload: DashboardTabData | undefined, key: string): T[] {
  const value = payload?.charts?.[key];
  return Array.isArray(value) ? (value as T[]) : [];
}

function text(value: unknown): string {
  return value == null ? "" : String(value);
}

function number(value: unknown): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function mini(id: string, label: string, value: string | number): OverviewMiniKPI {
  return { id, label, value: String(value) };
}

function mapLiveSections(
  pattern: DashboardTabData,
  failure: DashboardTabData,
  diagnosis: DashboardTabData,
) {
  const patternRows = rows(pattern);
  const failureRows = rows(failure);
  const diagnosisRows = rows(diagnosis);

  const parsedPatterns = patternRows.filter((row) =>
    ["parsed", "complete", "completed", "success"].includes(text(row.status).toLowerCase()),
  ).length;
  const fileTypes = new Set(patternRows.map((row) => text(row.fileType)).filter(Boolean));
  const patternClusters = chart<FailureDistribution>(pattern, "patternClusterDistribution");
  const clusterCount = patternClusters.reduce((sum, item) => sum + number(item.value), 0);

  const failurePatterns = new Set(
    failureRows.map((row) => text(row.patternId)).filter(Boolean),
  );
  const affectedLots = new Set(failureRows.map((row) => text(row.lotId)).filter(Boolean));
  const confirmedFailures = failureRows.filter(
    (row) => text(row.status).toLowerCase() === "confirmed",
  ).length;

  const totalChainFailures = diagnosisRows.reduce(
    (sum, row) => sum + number(row.failCount),
    0,
  );
  const highPriorityChains = diagnosisRows.filter(
    (row) => text(row.priority).toLowerCase() === "high",
  ).length;
  const recommendations = diagnosisRows.filter((row) => text(row.recommendation)).length;

  const patternImportTrend = chart<TrendPoint>(pattern, "patternImportTrend");
  const patternLengthDistribution = chart<FailureDistribution>(
    pattern,
    "patternLengthDistribution",
  );
  const failureTrendData = chart<TrendPoint>(failure, "failureTrendData");
  const rootCauseFrequency = chart<FailureDistribution>(failure, "rootCauseFrequency").map(
    (item) => ({ label: item.name, value: item.value }),
  );
  const diagnosisDistribution = chart<FailureDistribution>(
    diagnosis,
    "diagnosisDistribution",
  );
  const diagnosisTimeline = chart<TrendPoint>(diagnosis, "diagnosisTimeline");
  const topFailingScanChains: ChipFailData[] = (
    chart<{ chainId?: string; chain?: string; failCount?: number }>(
      diagnosis,
      "chainFailureRanking",
    ).length
      ? chart<{ chainId?: string; chain?: string; failCount?: number }>(
          diagnosis,
          "chainFailureRanking",
        )
      : diagnosisRows
  )
    .map((row) => ({
      chip: text(row.chainId ?? row.chain) || "Unknown chain",
      failCount: number(row.failCount),
    }))
    .sort((a, b) => b.failCount - a.failCount)
    .slice(0, 10);

  return {
    patternKPIs: [
      mini("live-pattern-files", "Pattern Files", patternRows.length),
      mini("live-pattern-parsed", "Parsed Successfully", parsedPatterns),
      mini("live-pattern-formats", "File Formats", fileTypes.size),
      mini("live-pattern-clusters", "Clustered Patterns", clusterCount),
    ],
    patternImportTrend,
    patternClusterDistribution: patternClusters,
    patternLengthDistribution,
    failureKPIs: [
      mini("live-failures", "Failure Records", failureRows.length),
      mini("live-failing-patterns", "Failing Patterns", failurePatterns.size),
      mini("live-affected-lots", "Affected Lots", affectedLots.size),
      mini("live-confirmed-failures", "Confirmed Failures", confirmedFailures),
    ],
    failureTrendData,
    rootCauseFrequency,
    diagnosisKPIs: [
      mini("live-failing-chains", "Failing Chains", diagnosisRows.length),
      mini("live-chain-failures", "Total Chain Failures", totalChainFailures),
      mini("live-high-priority", "High Priority Chains", highPriorityChains),
      mini("live-diagnosis-actions", "Diagnosis Actions", recommendations),
    ],
    topFailingScanChains,
    diagnosisDistribution,
    diagnosisTimeline,
  };
}

export function useScanChainOverviewSections() {
  const filters = useFilterStore((state) => state.filters);
  const live = isLiveApi();
  const queries = useQueries({
    queries: TABS.map((tab) => ({
      queryKey: ["dashboard", "scan-chain", "overview-section", tab, filters],
      queryFn: () => getModuleTab("scan-chain", tab, filters),
      enabled: live,
      staleTime: 5 * 60_000,
      placeholderData: (previous: DashboardTabData | undefined) => previous,
    })),
  });

  const liveMapped = useMemo(() => {
    if (!queries.every((query) => query.data)) return null;
    return mapLiveSections(
      queries[0].data as DashboardTabData,
      queries[1].data as DashboardTabData,
      queries[2].data as DashboardTabData,
    );
  }, [queries]);

  const mockMapped = {
    patternKPIs: mock.overviewPatternSummaryKPIs,
    patternImportTrend: mock.patternImportTrend,
    patternClusterDistribution: mock.patternClusterDistribution,
    patternLengthDistribution: mock.patternClusterDistribution,
    failureKPIs: mock.overviewFailureSummaryKPIs,
    failureTrendData: mock.failureTrendData,
    rootCauseFrequency: mock.rootCauseAnalysis.map((item) => ({
      label: item.cause,
      value: item.count,
    })),
    diagnosisKPIs: mock.overviewDiagnosisSummaryKPIs,
    topFailingScanChains: mock.topFailingScanChains,
    diagnosisDistribution: mock.failureLocalizationDistribution,
    diagnosisTimeline: mock.diagnosisTimeline,
  };

  const data = live ? liveMapped ?? mockMapped : mockMapped;
  const isLoading = live && queries.some((query) => query.isLoading || query.isPending);
  const isError = live && queries.some((query) => query.isError);
  const error = queries.find((query) => query.error)?.error ?? null;
  const isEmpty =
    live &&
    !isLoading &&
    !isError &&
    Boolean(liveMapped) &&
    data.patternKPIs.every((item) => item.value === "0") &&
    data.failureKPIs.every((item) => item.value === "0") &&
    data.diagnosisKPIs.every((item) => item.value === "0");

  return {
    ...data,
    isLoading,
    isFetching: live && queries.some((query) => query.isFetching),
    isError,
    isEmpty,
    error,
    refetch: () => {
      void Promise.all(queries.map((query) => query.refetch()));
    },
  };
}
