"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Gauge } from "lucide-react";
import { RecommendationActionButtons } from "@/components/platform/RecommendationActionButtons";
import { VerticalBarChart } from "@/components/scan-chain/charts/BarCharts";
import { TrendAreaChart, TrendLineChart } from "@/components/scan-chain/charts/LineCharts";
import { DonutChart } from "@/components/scan-chain/charts/PieCharts";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { DataTable } from "@/components/scan-chain/DataTable";
import { AgentActionBar } from "@/components/recommendation/AgentActionBar";
import { AgentSummaryCard } from "@/components/recommendation/AgentSummaryCard";
import { AgentTabHeader } from "@/components/recommendation/AgentTabHeader";
import { AgentWorkflowDiagram } from "@/components/recommendation/AgentWorkflowDiagram";
import { PriorityBadge, StatusBadge } from "@/components/recommendation/Badges";
import { SectionedKPIGrid } from "@/components/recommendation/SectionedKPIGrid";
import { SiteUtilizationHeatmap } from "@/components/recommendation/SiteUtilizationHeatmap";
import { isLiveApi } from "@/lib/api/config";
import {
  adaptiveTestingDistribution,
  costReductionTrend,
  generateSiteUtilizationHeatmap,
  optimizationPriorityData,
  testOptAgentSummary,
  testOptKPISections,
  testOptRecRows,
  testOptRecommendationTrend,
  testOptWorkflowSteps,
  yieldImprovementTrend,
} from "@/lib/recommendationData";

type OptimizationRecommendation = {
  id: string;
  risk_level: "Low" | "Medium" | "High";
  confidence: number;
  risk_score: number;
  summary: string;
  recommended_strategy: string;
  estimated_time_reduction: string;
  estimated_cost_reduction: string;
  expected_yield_improvement: string;
  adaptive_testing: { flow_mode: string; confidence: number; recommendation: string };
  test_stop: {
    recommendation: string;
    stop_coverage_pct: number | null;
    early_stop: boolean;
    confidence: number;
  };
  risk_based_testing: {
    recommendation: string;
    high_risk_lots: string[];
    action_for_high_risk: string;
    action_for_low_risk: string;
    confidence: number;
  };
  yield_recommendations: Array<{
    action: string;
    confidence: number;
    estimated_impact: Record<string, unknown>;
  }>;
  cost_recommendations: Array<{
    action: string;
    confidence: number;
    estimated_impact: Record<string, unknown>;
  }>;
  coverage_recommendations: Array<{
    action: string;
    confidence: number;
    estimated_impact: Record<string, unknown>;
  }>;
  production_recommendations: Array<{
    action: string;
    confidence: number;
    estimated_impact: Record<string, unknown>;
  }>;
  multi_site_optimization?: {
    recommendation: string;
    site_actions: string[];
    confidence: number;
  } | null;
};

function toPct(confidence: number) {
  // Some upstream agents return [0..1]; others might return [0..100].
  return confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence);
}

function mapRiskToPriority(riskLevel: OptimizationRecommendation["risk_level"]) {
  if (riskLevel === "High") return "Critical";
  if (riskLevel === "Medium") return "High";
  return "Medium";
}

function mapConfidenceToStatus(confidence: number) {
  if (confidence >= 0.85) return "Approved";
  if (confidence >= 0.7) return "In Review";
  return "Pending";
}

function formatEstimatedImpact(impact: Record<string, unknown>): string {
  const asNum = (v: unknown) => (typeof v === "number" ? v : typeof v === "string" ? Number(v) : null);
  const yieldGap = asNum(impact["yield_gap_pct"]);
  const timeSaved = asNum(impact["time_saved_s"]);
  const coverageAfter = asNum(impact["coverage_after_optimization"]);
  const retestRate = asNum(impact["retest_rate"]);
  if (yieldGap != null) return `+${Math.abs(yieldGap).toFixed(1)} pts yield recovery`;
  if (timeSaved != null) return `-${timeSaved.toFixed(1)}s test time`;
  if (coverageAfter != null) return `Coverage -> ${coverageAfter.toFixed(2)}%`;
  if (retestRate != null) return `${(retestRate * 100).toFixed(1)}% retest rate`;
  if (impact["debug_actions"] && Array.isArray(impact["debug_actions"])) {
    return `Debug actions: ${(impact["debug_actions"] as unknown[]).slice(0, 3).join(", ")}`;
  }
  return "N/A";
}

async function fetchTestOptimizationRecommendation(): Promise<OptimizationRecommendation> {
  // Keep the browser on :3000; Next proxies this path to the internal :8043 API.
  const url = "/embed/test-opt/api-proxy/api/v1/optimize/sample/high_risk?persist=false";
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Test Opt API ${res.status}: ${text || res.statusText}`);
  }
  return (await res.json()) as OptimizationRecommendation;
}

export function TestOptAgentTab() {
  const siteHeatData = useMemo(() => generateSiteUtilizationHeatmap(4, 4), []);

  const live = isLiveApi();

  const {
    data: liveRec,
    error: liveError,
    isLoading: isLiveLoading,
    isFetching: isLiveFetching,
  } = useQuery({
    queryKey: ["integration", "test-optimization-agent", "optimize-sample", "high_risk"],
    queryFn: fetchTestOptimizationRecommendation,
    enabled: live,
    staleTime: 30_000,
    refetchInterval: live ? 120_000 : false,
    retry: 1,
  });

  const derivedKpiSections = useMemo(() => {
    if (!liveRec) return testOptKPISections;

    const riskPriority = mapRiskToPriority(liveRec.risk_level);
    const status = mapConfidenceToStatus(liveRec.confidence);

    const adaptiveCount = 1;
    const stopCount = liveRec.test_stop.early_stop ? 1 : 1;
    const riskCount = Math.max(1, liveRec.risk_based_testing.high_risk_lots.length);
    const yieldCount = Math.max(1, liveRec.yield_recommendations.length);
    const costCount = Math.max(1, liveRec.cost_recommendations.length);
    const siteCount = Math.max(1, liveRec.multi_site_optimization?.site_actions.length ?? 1);
    const totalCount = adaptiveCount + stopCount + riskCount + yieldCount + costCount + siteCount;

    const currentYield = "N/A";
    const projectedYield = liveRec.expected_yield_improvement || "N/A";

    const kpiOverrides: Record<string, Partial<(typeof testOptKPISections)[number]["kpis"][number]>> = {
      "adaptive-recs": {
        value: String(adaptiveCount),
        subtitle: `Flow mode: ${liveRec.adaptive_testing.flow_mode}`,
        status: status,
      },
      "stop-recs": {
        value: String(stopCount),
        subtitle: liveRec.test_stop.early_stop ? "Hard stop gate active" : "Continue until coverage target",
        status: status,
      },
      "high-risk-devices": {
        value: String(riskCount),
        subtitle: `High-risk lots: ${liveRec.risk_based_testing.high_risk_lots.slice(0, 3).join(", ") || "—"}`,
        status: riskPriority,
      },
      "avg-risk-score": {
        value: `${(liveRec.risk_score / 100).toFixed(2)}`,
        subtitle: `Risk score: ${liveRec.risk_score.toFixed(1)}/100`,
        status: riskPriority === "Critical" ? "Critical" : "Above threshold",
      },
      "current-yield": { value: currentYield, subtitle: "Yield current not provided by API sample" },
      "yield-recs": { value: String(yieldCount), subtitle: projectedYield },
      "est-cost-saving": { value: liveRec.estimated_cost_reduction || "N/A", subtitle: "Projected cost reduction" },
      "active-sites": { value: String(siteCount), subtitle: `${siteCount} configured test sites` },
      "total-opt-recs": { value: String(totalCount), subtitle: `Total across blocks (risk=${liveRec.risk_level})` },
    };

    return testOptKPISections.map((section) => ({
      ...section,
      kpis: section.kpis.map((kpi) => {
        const override = kpiOverrides[kpi.id];
        if (!override) return kpi;
        return {
          ...kpi,
          value: override.value ?? kpi.value,
          subtitle: override.subtitle ?? kpi.subtitle,
          status: override.status ?? kpi.status,
        };
      }),
    }));
  }, [liveRec]);

  const derivedDistribution = useMemo(() => {
    if (!liveRec) return adaptiveTestingDistribution;

    const adaptiveCount = 1;
    const stopCount = liveRec.test_stop.early_stop ? 1 : 1;
    const riskCount = Math.max(1, liveRec.risk_based_testing.high_risk_lots.length);
    const yieldCount = Math.max(1, liveRec.yield_recommendations.length);
    const costCount = Math.max(1, liveRec.cost_recommendations.length);
    const siteCount = Math.max(1, liveRec.multi_site_optimization?.site_actions.length ?? 1);

    return [
      { name: "Adaptive", value: adaptiveCount, color: "#7C3AED" },
      { name: "Stop Rules", value: stopCount, color: "#F97316" },
      { name: "Risk", value: riskCount, color: "#EF4444" },
      { name: "Yield", value: yieldCount, color: "#22C55E" },
      { name: "Cost", value: costCount, color: "#06B6D4" },
      { name: "Site", value: siteCount, color: "#EAB308" },
    ];
  }, [liveRec]);

  const derivedPriorityData = useMemo(() => {
    if (!liveRec) return optimizationPriorityData;
    const rs = liveRec.risk_score;
    return [
      { label: "Critical", value: rs >= 50 ? 18 : 6 },
      { label: "High", value: rs >= 20 ? 32 : 14 },
      { label: "Medium", value: rs >= 10 ? 38 : 20 },
      { label: "Low", value: 23 },
    ];
  }, [liveRec]);

  const derivedRecRows = useMemo(() => {
    if (!liveRec) return testOptRecRows;

    const basePriority = mapRiskToPriority(liveRec.risk_level);
    const status = mapConfidenceToStatus(liveRec.confidence);

    const engineer = "AI Engine";
    const rows: typeof testOptRecRows = [];
    const add = (r: (typeof testOptRecRows)[number]) => rows.push(r);

    const mkId = (suffix: string, idx: number) => `${liveRec.id}-${suffix}-${idx}`;

    add({
      recommendationId: mkId("adaptive", 0),
      optimizationType: "Adaptive Testing",
      currentValue: "Full flow",
      optimizedValue: liveRec.adaptive_testing.flow_mode,
      estimatedBenefit: liveRec.estimated_time_reduction || "N/A",
      priority: basePriority,
      confidence: toPct(liveRec.adaptive_testing.confidence),
      status,
      assignedEngineer: engineer,
    });

    add({
      recommendationId: mkId("stop", 0),
      optimizationType: "Test Stop",
      currentValue: "Continue until target",
      optimizedValue: liveRec.test_stop.early_stop ? "Early stop enabled" : "Coverage stop gate",
      estimatedBenefit:
        liveRec.test_stop.stop_coverage_pct != null
          ? `Stop @ ${liveRec.test_stop.stop_coverage_pct.toFixed(2)}% coverage`
          : "N/A",
      priority: basePriority,
      confidence: toPct(liveRec.test_stop.confidence),
      status,
      assignedEngineer: engineer,
    });

    add({
      recommendationId: mkId("risk", 0),
      optimizationType: "Risk-Based",
      currentValue: "Uniform sampling",
      optimizedValue: `Extended testing for ${liveRec.risk_based_testing.high_risk_lots.length || 1} lot(s)`,
      estimatedBenefit: `Risk score ${(liveRec.risk_score / 100).toFixed(2)}`,
      priority: basePriority,
      confidence: toPct(liveRec.risk_based_testing.confidence),
      status,
      assignedEngineer: engineer,
    });

    for (const [idx, item] of liveRec.yield_recommendations.entries()) {
      if (rows.length >= 8) break;
      add({
        recommendationId: mkId("yield", idx),
        optimizationType: "Yield Optimization",
        currentValue: "Baseline yield strategy",
        optimizedValue: item.action,
        estimatedBenefit: formatEstimatedImpact(item.estimated_impact),
        priority: basePriority,
        confidence: toPct(item.confidence),
        status,
        assignedEngineer: engineer,
      });
    }

    for (const [idx, item] of liveRec.cost_recommendations.entries()) {
      if (rows.length >= 8) break;
      add({
        recommendationId: mkId("cost", idx),
        optimizationType: "Cost Reduction",
        currentValue: "Baseline cost strategy",
        optimizedValue: item.action,
        estimatedBenefit: formatEstimatedImpact(item.estimated_impact),
        priority: basePriority,
        confidence: toPct(item.confidence),
        status,
        assignedEngineer: engineer,
      });
    }

    if (liveRec.multi_site_optimization?.site_actions?.length) {
      if (rows.length < 8) {
        add({
          recommendationId: mkId("site", 0),
          optimizationType: "Multi-Site",
          currentValue: "Static site mapping",
          optimizedValue: `Reassign sites: ${liveRec.multi_site_optimization.site_actions.join("; ")}`,
          estimatedBenefit: "UPH / utilization balanced",
          priority: basePriority,
          confidence: toPct(liveRec.multi_site_optimization.confidence),
          status,
          assignedEngineer: engineer,
        });
      }
    }

    // Ensure table is never empty (keep UX stable).
    return rows.length ? rows : testOptRecRows;
  }, [liveRec]);

  const derivedSummary = useMemo(() => {
    if (!liveRec) return testOptAgentSummary;

    const adaptiveCount = 1;
    const stopCount = liveRec.test_stop.early_stop ? 1 : 1;
    const riskCount = Math.max(1, liveRec.risk_based_testing.high_risk_lots.length);
    const yieldCount = Math.max(1, liveRec.yield_recommendations.length);
    const costCount = Math.max(1, liveRec.cost_recommendations.length);
    const siteCount = Math.max(1, liveRec.multi_site_optimization?.site_actions.length ?? 1);

    return {
      ...testOptAgentSummary,
      metrics: [
        { label: "Adaptive Testing", value: `${adaptiveCount} recs` },
        { label: "Yield Improvement", value: liveRec.expected_yield_improvement || "N/A" },
        { label: "Test Time Reduction", value: liveRec.estimated_time_reduction || "N/A" },
        { label: "Cost Savings", value: liveRec.estimated_cost_reduction || "N/A" },
        { label: "Risk Reduction", value: `${riskCount} risk units` },
        { label: "Multi-Site Efficiency", value: `${siteCount} sites` },
        { label: "Overall ROI", value: "N/A" },
        { label: "AI Confidence", value: `${toPct(liveRec.confidence)}%` },
      ],
    };
  }, [liveRec]);

  if (live && isLiveLoading && !liveRec) {
    return (
      <div className="dashboard-content">
        <div className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center border border-dashed border-[#2D3748] px-6 text-center bg-[#090b12]">
          <p className="text-base font-medium text-white">Loading Test Optimization recommendations…</p>
          <p className="mt-2 text-sm text-slate-400">Preparing optimization workspace.</p>
        </div>
      </div>
    );
  }

  if (live && liveError && !liveRec) {
    return (
      <div className="dashboard-content">
        <div className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center border border-dashed border-[#2D3748] px-6 text-center bg-[#090b12]">
          <p className="text-base font-medium text-white">Test Optimization API unavailable</p>
          <p className="mt-2 text-sm text-slate-400">{String((liveError as Error).message)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-content">
      <AgentTabHeader
        icon={Gauge}
        title="Test Optimization Recommendation Agent"
        description="AI-powered adaptive testing, yield optimization, cost reduction, and production test strategy recommendations."
      />

      {live && isLiveFetching && liveRec ? (
        <div className="text-[11px] text-slate-500 mb-4">Refreshing live Test Optimization data…</div>
      ) : null}
      <SectionedKPIGrid sections={derivedKpiSections} variant="section" />

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Adaptive Testing Distribution" subtitle="By optimization category">
          <DonutChart
            data={derivedDistribution}
            centerLabel="Total"
            centerValue={derivedDistribution.reduce((a, b) => a + b.value, 0)}
          />
        </ChartCard>
        <ChartCard title="Optimization Priority" subtitle="By priority level">
          <VerticalBarChart data={derivedPriorityData} color="#22C55E" />
        </ChartCard>
        <ChartCard title="Recommendation Trend" subtitle="Last 30 days">
          <TrendLineChart
            data={testOptRecommendationTrend}
            lines={[{ key: "value", color: "#7C3AED", name: "Recommendations" }]}
          />
        </ChartCard>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <ChartCard title="Yield Improvement Trend" subtitle="Current vs. projected yield">
          <TrendLineChart
            data={yieldImprovementTrend}
            lines={[
              { key: "value", color: "#64748B", name: "Current" },
              { key: "value2", color: "#22C55E", name: "Projected" },
            ]}
          />
        </ChartCard>
        <ChartCard title="Cost Reduction Trend" subtitle="Current vs. optimized cost">
          <TrendAreaChart data={costReductionTrend.map((d) => ({ label: d.label, value: d.value2 ?? d.value }))} />
        </ChartCard>
        <ChartCard title="Site Utilization" subtitle="Site 1–16 utilization heatmap">
          <SiteUtilizationHeatmap data={siteHeatData} rows={4} cols={4} />
        </ChartCard>
      </div>

      <DataTable
        title="Optimization Recommendation Table"
        subtitle="Adaptive test strategy and production optimization actions"
        data={derivedRecRows}
        rowKey="recommendationId"
        pageSize={6}
        searchKeys={["recommendationId", "optimizationType", "status", "assignedEngineer"]}
        searchPlaceholder="Search optimization recommendations..."
        columns={[
          {
            key: "recommendationId",
            label: "Recommendation ID",
            render: (row) => (
              <span className="font-mono text-xs font-medium text-white">
                {row.recommendationId}
              </span>
            ),
          },
          { key: "optimizationType", label: "Optimization Type" },
          { key: "currentValue", label: "Current Value" },
          { key: "optimizedValue", label: "Optimized Value" },
          { key: "estimatedBenefit", label: "Estimated Benefit" },
          {
            key: "priority",
            label: "Priority",
            render: (row) => <PriorityBadge priority={row.priority} />,
          },
          {
            key: "confidence",
            label: "Confidence",
            render: (row) => `${row.confidence}%`,
          },
          {
            key: "status",
            label: "Status",
            render: (row) => <StatusBadge status={row.status} />,
          },
          { key: "assignedEngineer", label: "Assigned Engineer" },
          {
            key: "action",
            label: "Action",
            sortable: false,
            render: (row) => <RecommendationActionButtons id={row.recommendationId} />,
          },
        ]}
      />

      <AgentSummaryCard data={derivedSummary} />

      <AgentWorkflowDiagram
        steps={testOptWorkflowSteps}
        title="Optimization Workflow"
        subtitle="From production data through validated test flow"
      />

      <AgentActionBar variant="test-opt" />
    </div>
  );
}
