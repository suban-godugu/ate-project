"use client";

import { HorizontalBarChart, VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { TabLiveShell } from "@/components/platform/TabLiveShell";
import {
  OverviewDrillDownSection,
  OverviewMiniKPIGrid,
} from "@/components/scan-chain/overview/OverviewDrillDownSection";
import { useScanChainOverviewSections } from "@/hooks/useScanChainOverviewSections";

export function OverviewTab() {
  const liveData = useScanChainOverviewSections();
  const {
    patternKPIs,
    patternImportTrend,
    patternClusterDistribution,
    patternLengthDistribution,
    failureKPIs,
    failureTrendData,
    rootCauseFrequency,
    diagnosisKPIs,
    topFailingScanChains,
    diagnosisDistribution,
    diagnosisTimeline,
  } = liveData;

  return (
    <TabLiveShell module="scan-chain" tab="overview" hookResult={liveData}>
      <div className="dashboard-content space-y-10">
      <OverviewDrillDownSection
        title="Pattern Analysis"
        subtitle="Live pattern ingestion, formats, clustering, and size distribution"
        targetTab="pattern-analysis"
        linkLabel="Open Pattern Analysis"
      >
        <OverviewMiniKPIGrid items={patternKPIs} />
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <ChartCard title="Pattern Import Trend" subtitle="Live pattern files ingested by period">
            <TrendLineChart data={patternImportTrend} height={260} />
          </ChartCard>
          <ChartCard title="File Format Distribution" subtitle="Live pattern inputs grouped by format">
            <DonutChart
              data={patternClusterDistribution}
              centerLabel="Files"
              centerValue={patternClusterDistribution.reduce(
                (sum: number, row: { value: number }) => sum + row.value,
                0,
              )}
            />
          </ChartCard>
          <ChartCard title="Pattern Size Distribution" subtitle="Live pattern files grouped by size">
            <DonutChart
              data={patternLengthDistribution}
              centerLabel="Files"
              centerValue={patternLengthDistribution.reduce(
                (sum: number, row: { value: number }) => sum + row.value,
                0,
              )}
            />
          </ChartCard>
        </div>
      </OverviewDrillDownSection>

      <OverviewDrillDownSection
        title="Failure Analysis"
        subtitle="Live failure records, affected lots, patterns, and root causes"
        targetTab="failure-analysis"
        linkLabel="Open Failure Analysis"
      >
        <OverviewMiniKPIGrid items={failureKPIs} />
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <ChartCard title="Failure Trend" subtitle="Failure count across the last 7 periods">
            <TrendLineChart
              data={failureTrendData}
              lines={[{ key: "value", color: "#EF4444", name: "Failures" }]}
              height={260}
            />
          </ChartCard>
          <ChartCard title="Root Cause Frequency" subtitle="Live failures grouped by diagnosed cause">
            <VerticalBarChart data={rootCauseFrequency} />
          </ChartCard>
        </div>
      </OverviewDrillDownSection>

      <OverviewDrillDownSection
        title="Scan Diagnosis"
        subtitle="Live failing-chain ranking, diagnosis status, and activity"
        targetTab="scan-diagnosis"
        linkLabel="Open Scan Diagnosis"
      >
        <OverviewMiniKPIGrid items={diagnosisKPIs} />
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <ChartCard title="Top Chain Signature" subtitle="Highest-frequency failing chain signatures">
            <HorizontalBarChart data={topFailingScanChains} />
          </ChartCard>
          <ChartCard title="Diagnosis Status" subtitle="Live diagnosis workflow distribution">
            <DonutChart
              data={diagnosisDistribution}
              centerLabel="Records"
              centerValue={diagnosisDistribution.reduce(
                (sum: number, row: { value: number }) => sum + row.value,
                0,
              )}
            />
          </ChartCard>
          <ChartCard title="Diagnosis Timeline" subtitle="Diagnosis activity across recent periods">
            <TrendLineChart data={diagnosisTimeline} height={280} />
          </ChartCard>
        </div>
      </OverviewDrillDownSection>
      </div>
    </TabLiveShell>
  );
}
