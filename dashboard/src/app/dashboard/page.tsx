"use client";

import { useState } from "react";
import { ExecutiveKPIGrid } from "@/components/cards/ExecutiveCard";
import { CostTrendChart } from "@/components/charts/CostTrendChart";
import { WaferHeatmap } from "@/components/charts/WaferHeatmap";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { LiveModuleGate } from "@/components/platform/LiveModuleGate";
import { OptimizationEngine } from "@/components/optimization/OptimizationEngine";
import { OptimizationResult } from "@/components/results/OptimizationResult";
import { PatternTable } from "@/components/tables/PatternTable";
import { useFilteredExecutiveData } from "@/hooks/usePlatformData";
import { useActionStore } from "@/stores/actionStore";
import { defaultOptimizationResults } from "@/lib/dummyData";
import type { OptimizationParams, OptimizationResults } from "@/types/dashboard";

export default function DashboardPage() {
  const liveData = useFilteredExecutiveData();
  const { data, isLoading, isFetching, isError, isEmpty, error, refetch } = liveData;
  const lastPrimaryResult = useActionStore((s) => s.lastPrimaryResult);
  const [results, setResults] = useState<OptimizationResults | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunOptimization = async (_params: OptimizationParams) => {
    setIsRunning(true);
    setResults(null);
    await new Promise((r) => setTimeout(r, 1800));
    setResults(defaultOptimizationResults);
    setIsRunning(false);
  };

  const displayResults =
    results ??
    (lastPrimaryResult?.pageId === "dashboard"
      ? {
          costReduction: 12.4,
          timeSavings: 8.2,
          projectedYield: 95.1,
          patternsReduced: 24,
          totalSavings: 284000,
        }
      : null);

  return (
    <DashboardLayout
      title="Executive Dashboard"
      pageId="dashboard"
      primaryActionLabel="AI Optimize"
    >
      <LiveModuleGate
        module="executive"
        tab="overview"
        isLoading={isLoading}
        isFetching={isFetching}
        isError={isError}
        isEmpty={isEmpty}
        error={error}
        refetch={refetch}
      >
        <div className="dashboard-content">
          <ExecutiveKPIGrid data={data.kpis} />
          <WaferHeatmap />
          <div className="grid gap-6 lg:grid-cols-2">
            <CostTrendChart data={data.costTrend} />
            <PatternTable data={data.patterns} />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <OptimizationEngine onRun={handleRunOptimization} isRunning={isRunning} />
            <OptimizationResult results={displayResults} />
          </div>
        </div>
      </LiveModuleGate>
    </DashboardLayout>
  );
}
