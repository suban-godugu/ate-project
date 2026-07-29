"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { TrendAreaChart, TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable, StatusBadge } from "@/components/scan-chain/DataTable";
import { AIDiagnosisProgress } from "@/components/platform/AIDiagnosisProgress";
import { KPIGrid } from "@/components/lbist/KPICard";
import { useAIDiagnosis } from "@/hooks/usePrimaryAction";
import { LBISTAIDiagnosisCard } from "@/components/lbist/LBISTAIDiagnosisCard";
import { CoverageCorrelationChart, LogicConnectivityGraph } from "@/components/lbist/LogicGraphs";
import { useFilteredLbistData } from "@/hooks/useLbistData";

export function DiagnosisTab() {
  const liveData = useFilteredLbistData();
  const {affectedLogicBlocks,
    aiDiagnosisSummary,
    coverageCorrelation,
    debugRecommendations,
    diagnosisKPIs,
    diagnosisReports,
    diagnosisTimeline,
    failureCorrelation,
  } = liveData;
  const { run, isRunning, step, result } = useAIDiagnosis("lbist");

  return (
    <TabLiveShell module="lbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={diagnosisKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Diagnosis Timeline" subtitle="Diagnosed vs. pending logic blocks">
          <TrendLineChart data={diagnosisTimeline} lines={[{ key: "value", color: "#22C55E", name: "Diagnosed" }, { key: "value2", color: "#64748B", name: "Pending" }]} />
        </ChartCard>
        <ChartCard title="Failure Correlation" subtitle="Correlated failure propagation">
          <TrendAreaChart data={failureCorrelation} />
        </ChartCard>
        <LogicConnectivityGraph />
        <CoverageCorrelationChart />
        <ChartCard title="Coverage Correlation Trend" subtitle="Coverage validation over time" className="lg:col-span-2">
          <TrendLineChart data={coverageCorrelation} lines={[{ key: "value", color: "#7C3AED", name: "AI Confidence %" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="Diagnosis Report"
        subtitle="Comprehensive LBIST diagnosis results"
        data={diagnosisReports}
        rowKey="logicBlock"
        searchKeys={["logicBlock", "rootCause", "repairSuggestion"]}
        searchPlaceholder="Search reports..."
        columns={[
          { key: "logicBlock", label: "Logic Block", render: (row) => <span className="font-mono text-xs text-white">{row.logicBlock}</span> },
          { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} variant={row.status === "Diagnosed" ? "success" : row.status === "Partial" ? "warning" : "neutral"} /> },
          { key: "rootCause", label: "Root Cause" },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "repairSuggestion", label: "Repair Suggestion" },
        ]}
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <DataTable
          title="Affected Logic Blocks"
          subtitle="High-probability failing logic blocks"
          data={affectedLogicBlocks}
          rowKey="logicBlock"
          searchKeys={["logicBlock", "module"]}
          searchPlaceholder="Search blocks..."
          pageSize={4}
          columns={[
            { key: "logicBlock", label: "Logic Block" },
            { key: "module", label: "Module" },
            { key: "failProbability", label: "Fail Probability", render: (row) => `${(row.failProbability * 100).toFixed(0)}%` },
            { key: "coverage", label: "Coverage", render: (row) => `${row.coverage}%` },
          ]}
        />
        <DataTable
          title="Debug Recommendations"
          subtitle="Priority debug actions for investigation"
          data={debugRecommendations}
          rowKey="id"
          searchKeys={["id", "logicBlock", "recommendation"]}
          searchPlaceholder="Search recommendations..."
          pageSize={4}
          columns={[
            { key: "id", label: "ID" },
            { key: "logicBlock", label: "Logic Block" },
            { key: "recommendation", label: "Recommendation" },
            { key: "priority", label: "Priority" },
          ]}
        />
      </div>
      <LBISTAIDiagnosisCard data={aiDiagnosisSummary} onRunDiagnosis={run} />
      <AIDiagnosisProgress running={isRunning} step={step} result={result} />
      </div>
    </TabLiveShell>
  );
}
