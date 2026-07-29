"use client";

import { TabLiveShell } from "@/components/platform/TabLiveShell";
import { TrendAreaChart, TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable, StatusBadge } from "@/components/scan-chain/DataTable";
import { AIDiagnosisProgress } from "@/components/platform/AIDiagnosisProgress";
import { KPIGrid } from "@/components/mbist/KPICard";
import { MBISTAIDiagnosisCard } from "@/components/mbist/MBISTAIDiagnosisCard";
import { MemoryConnectivityGraph, RootCauseGraph } from "@/components/mbist/MemoryGraphs";
import { useAIDiagnosis } from "@/hooks/usePrimaryAction";
import { useFilteredMbistData } from "@/hooks/useMbistData";

export function DiagnosisTab() {
  const liveData = useFilteredMbistData();
  const {aiConfidenceTrend,
    aiDiagnosisSummary,
    diagnosisKPIs,
    diagnosisReports,
    diagnosisTimeline,
    failAddressReport,
    failureCorrelation,
    repairRecommendations,
  } = liveData;
  const { run, isRunning, step, result } = useAIDiagnosis("mbist");

  return (
    <TabLiveShell module="mbist" hookResult={liveData}>
      <div className="dashboard-content">
      <KPIGrid data={diagnosisKPIs} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ChartCard title="Diagnosis Timeline" subtitle="Diagnosed vs. unknown memories">
          <TrendLineChart data={diagnosisTimeline} lines={[{ key: "value", color: "#22C55E", name: "Diagnosed" }, { key: "value2", color: "#64748B", name: "Unknown" }]} />
        </ChartCard>
        <ChartCard title="Failure Correlation" subtitle="Correlated failure propagation">
          <TrendAreaChart data={failureCorrelation} />
        </ChartCard>
        <MemoryConnectivityGraph />
        <RootCauseGraph />
        <ChartCard title="AI Confidence" subtitle="Model confidence trend" className="lg:col-span-2">
          <TrendLineChart data={aiConfidenceTrend} lines={[{ key: "value", color: "#7C3AED", name: "Confidence %" }]} />
        </ChartCard>
      </div>
      <DataTable
        title="Diagnosis Report"
        subtitle="Comprehensive MBIST diagnosis results"
        data={diagnosisReports}
        rowKey="memoryId"
        searchKeys={["memoryId", "rootCause", "repairSuggestion"]}
        searchPlaceholder="Search reports..."
        columns={[
          { key: "memoryId", label: "Memory ID", render: (row) => <span className="font-mono text-xs text-white">{row.memoryId}</span> },
          { key: "status", label: "Status", render: (row) => <StatusBadge status={row.status} variant={row.status === "Diagnosed" ? "success" : row.status === "Partial" ? "warning" : "neutral"} /> },
          { key: "rootCause", label: "Root Cause" },
          { key: "confidence", label: "Confidence", render: (row) => `${row.confidence}%` },
          { key: "repairSuggestion", label: "Repair Suggestion" },
        ]}
      />
      <div className="grid gap-6 lg:grid-cols-2">
        <DataTable
          title="Fail Address Report"
          subtitle="High-probability failing addresses"
          data={failAddressReport}
          rowKey="address"
          searchKeys={["address", "memoryId", "bank"]}
          searchPlaceholder="Search addresses..."
          pageSize={4}
          columns={[
            { key: "address", label: "Address", render: (row) => <span className="font-mono text-xs text-white">{row.address}</span> },
            { key: "memoryId", label: "Memory ID" },
            { key: "bank", label: "Bank" },
            { key: "failType", label: "Fail Type" },
            { key: "probability", label: "Probability", render: (row) => `${(row.probability * 100).toFixed(0)}%` },
          ]}
        />
        <DataTable
          title="Repair Recommendations"
          subtitle="Ranked repair actions by priority"
          data={repairRecommendations}
          rowKey="memoryId"
          searchKeys={["memoryId", "recommendation"]}
          searchPlaceholder="Search repairs..."
          pageSize={4}
          columns={[
            { key: "priority", label: "Priority" },
            { key: "memoryId", label: "Memory ID" },
            { key: "recommendation", label: "Recommendation" },
            { key: "successRate", label: "Success Rate", render: (row) => `${row.successRate}%` },
          ]}
        />
      </div>
      <MBISTAIDiagnosisCard data={aiDiagnosisSummary} onRunDiagnosis={run} />
      <AIDiagnosisProgress running={isRunning} step={step} result={result} />
      </div>
    </TabLiveShell>
  );
}
