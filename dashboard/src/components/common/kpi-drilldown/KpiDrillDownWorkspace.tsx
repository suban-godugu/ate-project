"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  ArrowDown,
  ArrowUp,
  Download,
  RefreshCw,
  Sparkles,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { resolveKpiIcon } from "@/components/common/kpiIcons";
import { KpiWidgetRenderer } from "@/components/common/kpi-drilldown/KpiWidgetRenderer";
import { KpiCopilotPanel } from "@/components/common/kpi-drilldown/KpiCopilotPanel";
import { KpiTraceabilityPath } from "@/components/common/kpi-drilldown/KpiTraceabilityPath";
import { KpiTopologyPanel } from "@/components/common/kpi-drilldown/KpiTopologyPanel";
import {
  KpiAiDecisionPanel,
  KpiAiExplanationPanel,
  KpiApprovalCenterPanel,
  KpiExpectedImpactPanel,
  KpiSimulationPanel,
} from "@/components/common/kpi-drilldown/KpiRecommendationPanels";
import { KpiScanDebugDecisionPanel } from "@/components/common/kpi-drilldown/KpiScanDebugDecisionPanel";
import { scanDebugTopologyHero } from "@/lib/kpiDrillDown/kpiDrillDownUtils";
import {
  ExecutiveSummaryCard,
  FilterChip,
  MetaChip,
  WorkspaceSection,
} from "@/components/common/kpi-drilldown/KpiWorkspaceSections";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { exportCSV, exportExcel } from "@/lib/exportUtils";
import { cn } from "@/lib/utils";
import type { KpiDrillDownFilters, KpiTrendTab, KpiWorkspaceData } from "@/types/kpiDrillDown";
import { WORKSPACE_LAYOUT_CLASS } from "@/types/kpiDrillDown";

const RISK_STYLE: Record<string, string> = {
  critical: "text-red-400 bg-red-500/15",
  high: "text-orange-400 bg-orange-500/15",
  medium: "text-amber-400 bg-amber-500/15",
  low: "text-blue-400 bg-blue-500/15",
  nominal: "text-emerald-400 bg-emerald-500/15",
};

const STATUS_STYLE = {
  success: "bg-emerald-500/15 text-emerald-400",
  warning: "bg-amber-500/15 text-amber-400",
  danger: "bg-red-500/15 text-red-400",
  info: "bg-blue-500/15 text-blue-400",
};

interface Props {
  workspace: KpiWorkspaceData;
  filters: KpiDrillDownFilters;
  onFiltersChange: (partial: Partial<KpiDrillDownFilters>) => void;
  onRefresh: () => void;
  onClose: () => void;
  dataSource?: "fastapi" | "mock";
}

export function KpiDrillDownWorkspace({ workspace, filters, onFiltersChange, onRefresh, onClose, dataSource = "mock" }: Props) {
  const router = useRouter();
  const [trendTab, setTrendTab] = useState<KpiTrendTab>("7d");
  const [breakdownDim, setBreakdownDim] = useState<string>(workspace.breakdownDimensions[0] ?? "tester");
  const [selectedBreakdown, setSelectedBreakdown] = useState<string | null>(null);
  const [tableSearch, setTableSearch] = useState("");
  const [tablePage, setTablePage] = useState(0);
  const [copilotOpen, setCopilotOpen] = useState(false);
  const [visibleCols, setVisibleCols] = useState<Set<string>>(
    () => new Set(workspace.table.columns.filter((c) => c.defaultVisible !== false).map((c) => c.key))
  );
  const [traceSelected, setTraceSelected] = useState<string | null>(null);
  const pageSize = 10;
  const isDiagnosis = workspace.module === "diagnosis";
  const isRecommendation = workspace.module === "recommendation";
  const isTestOptimization = workspace.module === "testOptimization";
  const isScanDebug = workspace.module === "scanDebug";
  const isOptAgent = isRecommendation || isTestOptimization;
  const isAgentWorkspace = isOptAgent || isScanDebug;
  const analyticsWidgets = isScanDebug ? workspace.widgets.slice(1) : workspace.widgets;

  const Icon = resolveKpiIcon(workspace.header.icon);
  const trend = workspace.trendAnalytics[trendTab];
  const breakdown = workspace.breakdowns[breakdownDim] ?? [];

  const filteredRows = useMemo(() => {
    const q = tableSearch.toLowerCase();
    if (!q) return workspace.table.rows;
    return workspace.table.rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(q)));
  }, [workspace.table.rows, tableSearch]);

  const pageRows = filteredRows.slice(tablePage * pageSize, (tablePage + 1) * pageSize);
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const activeColumns = workspace.table.columns.filter((c) => visibleCols.has(c.key));

  const exportTable = useCallback(
    (format: "csv" | "excel") => {
      const headers = activeColumns.map((c) => c.label);
      const rows = filteredRows.map((r) => activeColumns.map((c) => String(r[c.key] ?? "")));
      const name = `${workspace.kpi.id}-engineering-data`;
      if (format === "csv") exportCSV(`${name}.csv`, headers, rows);
      else exportExcel(`${name}.xls`, headers, rows);
    },
    [activeColumns, filteredRows, workspace.kpi.id]
  );

  const downloadTrend = () => {
    const headers = ["Label", "Current", "Comparison"];
    const rows = trend.series.map((s) => [s.label, String(s.value), String(s.value2 ?? "")]);
    exportCSV(`${workspace.kpi.id}-trend-${trendTab}.csv`, headers, rows);
  };

  const handleBreakdownClick = (dim: string, label: string) => {
    setSelectedBreakdown(label);
    const keyMap: Record<string, keyof KpiDrillDownFilters> = {
      fab: "fab",
      tester: "tester",
      product: "product",
      lot: "lot",
      wafer: "wafer",
      module: "module",
      pattern: "pattern",
      scanChain: "scanChain",
      vector: "vector",
      die: "die",
      scanCell: "scanChain",
      flop: "module",
      failureBin: "pattern",
      rootCause: "pattern",
    };
    const fk = keyMap[dim];
    if (fk) onFiltersChange({ [fk]: label });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={WORKSPACE_LAYOUT_CLASS[workspace.layoutPreset]}
      role="dialog"
      aria-modal="true"
      aria-label={`${workspace.header.name} analytics workspace`}
    >
      {/* Header */}
      <header className="sticky top-0 z-30 shrink-0 border-b border-[#2D3748]/60 bg-[#0B0F1A]/95 px-5 py-4 backdrop-blur-md">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 flex-1 items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[rgba(124,58,237,0.2)] text-[#8B5CF6]">
              <Icon className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-bold text-white">{workspace.header.name}</h2>
                <span className="text-2xl font-extrabold tabular-nums text-white">{workspace.header.currentValue}</span>
                <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-semibold", STATUS_STYLE[workspace.header.statusVariant])}>
                  {workspace.header.statusBadge}
                </span>
                <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase", RISK_STYLE[workspace.header.riskLevel])}>
                  {workspace.header.riskLevel} risk
                </span>
                {workspace.header.diagnosisConfidence && (
                  <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-400">
                    {workspace.header.diagnosisConfidence} confidence
                  </span>
                )}
                {workspace.header.recommendationPriority && (
                  <span className="rounded-full bg-[#8B5CF6]/20 px-2 py-0.5 text-[11px] font-semibold text-[#C4B5FD]">
                    {workspace.header.recommendationPriority}
                  </span>
                )}
                {workspace.header.recommendationVersion && (
                  <span className="text-[11px] text-[#64748B]">{workspace.header.recommendationVersion}</span>
                )}
                <span className="inline-flex items-center gap-1 text-xs text-[#94A3B8]">
                  {workspace.header.trendDirection === "up" ? <ArrowUp className="h-3 w-3 text-emerald-400" /> : workspace.header.trendDirection === "down" ? <ArrowDown className="h-3 w-3 text-red-400" /> : null}
                  {workspace.header.trendLabel}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-[#64748B]">
                Updated {new Date(workspace.header.lastUpdated).toLocaleString()}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <FilterChip label="Fab" value={workspace.header.activeFilters.fab} />
                <FilterChip label="Tester" value={workspace.header.activeFilters.tester} />
                <FilterChip label="Product" value={workspace.header.activeFilters.product} />
                <FilterChip label="Lot" value={workspace.header.activeFilters.lot} />
                <FilterChip label="Wafer" value={workspace.header.activeFilters.wafer} />
              </div>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={() => exportTable("csv")}>
              <Download className="h-3.5 w-3.5" /> Export
            </Button>
            <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={onRefresh}>
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </Button>
            <Button type="button" variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close">
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </header>

      {/* Body */}
      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
        <div className="space-y-8">
          {/* ROW 1 */}
          <WorkspaceSection row={1} title="Executive Summary">
            <div className={cn("grid grid-cols-2 gap-3 sm:grid-cols-3", workspace.executiveSummary.length >= 12 ? "lg:grid-cols-4 xl:grid-cols-6" : workspace.executiveSummary.length >= 10 ? "lg:grid-cols-5 xl:grid-cols-10" : workspace.executiveSummary.length >= 9 ? "lg:grid-cols-3 xl:grid-cols-9" : workspace.executiveSummary.length > 6 ? "lg:grid-cols-4 xl:grid-cols-8" : "lg:grid-cols-6")}>
              {workspace.executiveSummary.map((card) => (
                <ExecutiveSummaryCard key={card.id} card={card} />
              ))}
            </div>
          </WorkspaceSection>

          {/* ROW 2 */}
          {isScanDebug && workspace.aiDecision && workspace.aiExplanation && workspace.approvalActions && (
            <WorkspaceSection row={2} title="AI Debug Decision — Review & Visualize">
              <KpiScanDebugDecisionPanel
                aiDecision={workspace.aiDecision}
                aiExplanation={workspace.aiExplanation}
                approvalActions={workspace.approvalActions}
                heroWidget={workspace.widgets[0]}
                showTopology={scanDebugTopologyHero(workspace.kpi.id)}
                topologyGraph={workspace.topologyGraph}
              />
            </WorkspaceSection>
          )}

          {isOptAgent && workspace.aiDecision && (
            <WorkspaceSection row={2} title={isTestOptimization ? "Optimization Overview" : "AI Decision Overview"}>
              <KpiAiDecisionPanel
                data={workspace.aiDecision}
                variant={isTestOptimization ? "testOptimization" : "pattern"}
              />
            </WorkspaceSection>
          )}

          {isTestOptimization && workspace.simulationMetrics && (
            <WorkspaceSection row={3} title="Simulation — Current vs Optimized">
              <KpiSimulationPanel metrics={workspace.simulationMetrics} hero />
            </WorkspaceSection>
          )}

          {!isAgentWorkspace && (
          <WorkspaceSection row={2} title={isDiagnosis ? "Failure Trend" : "Historical Trend"}
            action={
              <Button type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={downloadTrend}>
                <Download className="mr-1 h-3 w-3" /> Download
              </Button>
            }
          >
            <div className="mb-3 flex flex-wrap gap-1">
              {workspace.trendTabOptions.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  suppressHydrationWarning
                  onClick={() => setTrendTab(tab.id)}
                  className={cn(
                    "rounded-lg px-3 py-1.5 text-xs font-medium transition",
                    trendTab === tab.id ? "bg-[#8B5CF6] text-white" : "bg-[#1e293b]/60 text-[#94A3B8] hover:text-white"
                  )}
                >
                  {tab.label}
                </button>
              ))}
            </div>
            <div className="h-72 rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-4">
              <ResponsiveContainer width="100%" height="100%">
                {trend.chartKind === "bar" ? (
                  <BarChart data={trend.series}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                    <Tooltip contentStyle={{ background: "#111827", border: "1px solid #2D3748", borderRadius: 8 }} />
                    <Bar dataKey="value" fill="#8B5CF6" radius={[4, 4, 0, 0]} name="Current" />
                    <Bar dataKey="value2" fill="#6366F1" radius={[4, 4, 0, 0]} opacity={0.55} name="Comparison" />
                  </BarChart>
                ) : trend.chartKind === "area" ? (
                  <AreaChart data={trend.series}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                    <Tooltip contentStyle={{ background: "#111827", border: "1px solid #2D3748", borderRadius: 8 }} />
                    <Area type="monotone" dataKey="value" stroke="#8B5CF6" fill="rgba(139,92,246,0.2)" name="Current" />
                    <Area type="monotone" dataKey="value2" stroke="#6366F1" fill="rgba(99,102,241,0.12)" name="Baseline" />
                  </AreaChart>
                ) : (
                  <LineChart data={trend.series}>
                    <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748B" fontSize={11} tickLine={false} />
                    <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                    <Tooltip contentStyle={{ background: "#111827", border: "1px solid #2D3748", borderRadius: 8 }} />
                    <Line type="monotone" dataKey="value" stroke="#8B5CF6" strokeWidth={2} dot={false} name="Current" />
                    <Line type="monotone" dataKey="value2" stroke="#6366F1" strokeWidth={1.5} dot={false} strokeDasharray="4 4" name="Baseline" />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          </WorkspaceSection>
          )}

          {/* ROW 3 */}
          <WorkspaceSection
            row={isScanDebug ? 3 : isTestOptimization ? 4 : 3}
            title={
              isScanDebug
                ? "Engineering Analytics"
                : isTestOptimization
                ? "Engineering Analytics"
                : isRecommendation
                  ? "Pattern Analytics"
                  : isDiagnosis
                    ? "Scan Diagnosis"
                    : "Engineering Analytics"
            }
          >
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              {analyticsWidgets.map((w) => (
                <KpiWidgetRenderer key={w.id} widget={w} />
              ))}
            </div>
          </WorkspaceSection>

          {isDiagnosis && (
            <WorkspaceSection row={4} title="Failure Traceability">
              <KpiTraceabilityPath
                nodes={workspace.traceability}
                selectedId={traceSelected}
                onSelect={(node) => setTraceSelected(node.id)}
              />
            </WorkspaceSection>
          )}

          {!isDiagnosis && (
          <WorkspaceSection
            row={isScanDebug ? 4 : isTestOptimization ? 5 : isRecommendation ? 4 : 4}
            title={isRecommendation ? "Pattern Breakdown" : "Breakdown Analysis"}
          >
            <div className="mb-3 flex flex-wrap gap-1">
              {workspace.breakdownDimensions.map((dim) => (
                <button
                  key={dim}
                  type="button"
                  suppressHydrationWarning
                  onClick={() => setBreakdownDim(dim)}
                  className={cn(
                    "rounded-lg px-3 py-1 text-xs capitalize",
                    breakdownDim === dim ? "bg-[#8B5CF6] text-white" : "bg-[#1e293b]/60 text-[#94A3B8]"
                  )}
                >
                  {dim.replace(/([A-Z])/g, " $1")}
                </button>
              ))}
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {breakdown.map((slice) => (
                <button
                  key={slice.label}
                  type="button"
                  suppressHydrationWarning
                  onClick={() => handleBreakdownClick(breakdownDim, slice.label)}
                  className={cn(
                    "rounded-xl border p-3 text-left transition hover:border-[rgba(139,92,246,0.45)]",
                    selectedBreakdown === slice.label ? "border-[#8B5CF6] bg-[#8B5CF6]/10" : "border-[#2D3748]/60 bg-[#121826]/60"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-white">{slice.label}</span>
                    <span className={cn("text-xs font-medium", slice.trend >= 0 ? "text-emerald-400" : "text-red-400")}>
                      {slice.trend >= 0 ? "+" : ""}
                      {slice.trend}%
                    </span>
                  </div>
                  <div className="mt-2 flex items-end justify-between">
                    <span className="text-xl font-bold tabular-nums text-white">{slice.value}</span>
                    <span className="text-xs text-[#64748B]">{slice.share}% share</span>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#1e293b]">
                    <div className="h-full rounded-full bg-[#8B5CF6]" style={{ width: `${slice.share}%` }} />
                  </div>
                </button>
              ))}
            </div>
          </WorkspaceSection>
          )}

          {isScanDebug && workspace.expectedImpactMetrics && (
            <WorkspaceSection row={5} title="Engineering Impact">
              <KpiExpectedImpactPanel metrics={workspace.expectedImpactMetrics} />
            </WorkspaceSection>
          )}

          {isScanDebug && workspace.approvalActions && (
            <WorkspaceSection row={6} title="Action Center">
              <KpiApprovalCenterPanel actions={workspace.approvalActions} />
            </WorkspaceSection>
          )}

          {isOptAgent && workspace.aiExplanation && !isScanDebug && (
            <WorkspaceSection row={isTestOptimization ? 6 : 5} title="AI Explanation">
              <KpiAiExplanationPanel data={workspace.aiExplanation} />
            </WorkspaceSection>
          )}

          {isRecommendation && workspace.expectedImpactMetrics && (
            <WorkspaceSection row={6} title="Engineering Impact">
              <KpiExpectedImpactPanel metrics={workspace.expectedImpactMetrics} />
            </WorkspaceSection>
          )}

          {isTestOptimization && workspace.expectedImpactMetrics && (
            <WorkspaceSection row={7} title="Business Impact">
              <KpiExpectedImpactPanel metrics={workspace.expectedImpactMetrics} />
            </WorkspaceSection>
          )}

          {isOptAgent && workspace.approvalActions && (
            <WorkspaceSection row={isTestOptimization ? 8 : 7} title="Action Center">
              <KpiApprovalCenterPanel actions={workspace.approvalActions} />
            </WorkspaceSection>
          )}

          {isRecommendation && workspace.simulationMetrics && (
            <WorkspaceSection row={8} title="Simulation — Before vs After">
              <KpiSimulationPanel metrics={workspace.simulationMetrics} />
            </WorkspaceSection>
          )}

          {!isAgentWorkspace && (
          <WorkspaceSection row={isDiagnosis ? 5 : 5} title="Root Cause Analysis">
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="rounded-xl border border-[rgba(139,92,246,0.3)] bg-gradient-to-br from-[#121826] to-[#0d111c] p-4 lg:col-span-2">
                <div className="mb-3 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-[#8B5CF6]" />
                  <span className="text-sm font-bold text-white">AI Diagnosis</span>
                  <span className="ml-auto rounded-full bg-emerald-500/15 px-2 py-0.5 text-xs font-semibold text-emerald-400">
                    {workspace.rootCause.confidence}% confidence
                  </span>
                </div>
                <p className="text-base font-semibold text-[#E2E8F0]">{workspace.rootCause.primaryCause}</p>
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
                  {(isDiagnosis
                    ? [
                        { label: "Failure Type", value: workspace.rootCause.failureType ?? "—" },
                        { label: "Severity", value: workspace.rootCause.severity },
                        { label: "Clock Domain", value: workspace.rootCause.clockDomain ?? "—" },
                        { label: "Shift Cycle", value: workspace.rootCause.shiftCycle ?? "—" },
                        { label: "Capture Cycle", value: workspace.rootCause.captureCycle ?? "—" },
                      ]
                    : [
                        { label: "Severity", value: workspace.rootCause.severity },
                        { label: "Risk", value: workspace.rootCause.risk },
                        { label: "Priority", value: workspace.rootCause.priority ?? "P2" },
                        { label: "Yield Impact", value: workspace.rootCause.expectedYieldImpact },
                        { label: "Cost Impact", value: workspace.rootCause.expectedCostImpact ?? "—" },
                      ]
                  ).map((item) => (
                    <MetaChip key={item.label} label={item.label} value={String(item.value)} />
                  ))}
                </div>
                {isDiagnosis && (
                  <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    {[
                      { label: "Fault Model", value: workspace.rootCause.faultModel ?? "—" },
                      { label: "Compression", value: workspace.rootCause.compressionRatio ?? "—" },
                      { label: "Physical Region", value: workspace.rootCause.suspectedPhysicalRegion ?? "—" },
                      { label: "Yield Loss", value: workspace.rootCause.expectedYieldImpact },
                    ].map((item) => (
                      <MetaChip key={item.label} label={item.label} value={String(item.value)} />
                    ))}
                  </div>
                )}
              </div>
              <div className="space-y-2">
                {[
                  { title: "Modules", items: workspace.rootCause.affectedModules },
                  { title: "Patterns", items: workspace.rootCause.affectedPatterns },
                  { title: isDiagnosis ? "Scan Cells" : "Chains", items: isDiagnosis ? (workspace.rootCause.affectedScanCells ?? []) : workspace.rootCause.affectedChains },
                  { title: "Lots", items: workspace.rootCause.affectedLots },
                  { title: "Wafers", items: workspace.rootCause.affectedWafers },
                ].map((group) => (
                  <div key={group.title} className="rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60 p-3">
                    <p className="mb-2 text-[10px] font-bold uppercase tracking-wider text-[#64748B]">{group.title}</p>
                    <div className="flex flex-wrap gap-1">
                      {group.items.map((item) => (
                        <span key={item} className="rounded-md bg-[#1e293b] px-2 py-0.5 text-xs text-[#CBD5E1]">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </WorkspaceSection>
          )}

          {isDiagnosis && (
            <WorkspaceSection row={6} title="Topology View">
              <KpiTopologyPanel
                nodes={workspace.topologyGraph.nodes}
                edges={workspace.topologyGraph.edges}
                highlightChainId={workspace.kpi.id === "sd-top-failing-chain" ? "SC_14" : undefined}
              />
            </WorkspaceSection>
          )}

          {/* Semiconductor meta strip */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
            {Object.entries(workspace.semiconductorMeta).map(([k, v]) =>
              v ? <MetaChip key={k} label={k.replace(/([A-Z])/g, " $1").trim()} value={v} /> : null
            )}
          </div>

          {/* ROW 6 */}
          {!isAgentWorkspace && (
          <WorkspaceSection row={isDiagnosis ? 7 : 6} title={isDiagnosis ? "AI Recommendation Engine" : "Recommendation Engine"}>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {workspace.recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className="rounded-xl border border-[rgba(139,92,246,0.2)] bg-[#121826]/80 p-4 transition hover:border-[rgba(139,92,246,0.45)]"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="rounded bg-[#8B5CF6]/20 px-1.5 py-0.5 text-[10px] font-bold text-[#A78BFA]">{rec.priority}</span>
                    <span className="text-xs text-emerald-400">{rec.confidence}%</span>
                  </div>
                  <p className="mt-2 text-sm font-semibold text-white">{rec.action}</p>
                  <div className="mt-3 grid grid-cols-3 gap-1 text-[10px] text-[#94A3B8]">
                    <span>Δ {rec.estimatedImprovement}</span>
                    <span>RT {rec.runtimeSaving}</span>
                    <span>{rec.costSaving}</span>
                  </div>
                  <Button type="button" size="sm" className="mt-3 h-7 w-full bg-[#8B5CF6] text-xs hover:bg-[#7C3AED]">
                    Execute
                  </Button>
                </div>
              ))}
            </div>
          </WorkspaceSection>
          )}

          <WorkspaceSection row={isAgentWorkspace ? (isScanDebug ? 7 : isTestOptimization ? 9 : 9) : 7} title="Engineering Timeline">
            <div className="flex gap-0 overflow-x-auto pb-2">
              {workspace.timeline.map((ev, i) => (
                <button
                  key={ev.id}
                  type="button"
                  suppressHydrationWarning
                  className="relative flex min-w-[110px] flex-col items-center px-2"
                >
                  <div
                    className={cn(
                      "flex h-9 w-9 items-center justify-center rounded-full border-2 text-[10px] font-bold transition hover:scale-105",
                      ev.status === "complete"
                        ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                        : ev.status === "running"
                          ? "border-[#8B5CF6] bg-[#8B5CF6]/20 text-[#A78BFA] animate-pulse"
                          : ev.status === "failed"
                            ? "border-red-500 bg-red-500/20 text-red-400"
                            : "border-[#334155] bg-[#1e293b]/40 text-[#64748B]"
                    )}
                  >
                    {i + 1}
                  </div>
                  <p className="mt-2 text-center text-[10px] font-medium text-white">{ev.label}</p>
                  <p className="text-[9px] text-[#64748B]">{ev.timestamp}</p>
                </button>
              ))}
            </div>
          </WorkspaceSection>

          {/* ROW 8 */}
          <WorkspaceSection
            row={isAgentWorkspace ? (isScanDebug ? 8 : 10) : 8}
            title={isScanDebug ? "Raw Engineering Data" : isTestOptimization ? "Raw Data" : "Raw Engineering Data"}
            action={
              <div className="flex gap-2">
                <Button type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={() => exportTable("csv")}>
                  CSV
                </Button>
                <Button type="button" variant="outline" size="sm" className="h-7 text-xs" onClick={() => exportTable("excel")}>
                  Excel
                </Button>
              </div>
            }
          >
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Input
                placeholder="Search records..."
                value={tableSearch}
                onChange={(e) => {
                  setTableSearch(e.target.value);
                  setTablePage(0);
                }}
                className="h-8 w-52 border-[#2D3748] bg-[#0A1020] text-xs"
              />
              <div className="flex flex-wrap gap-1">
                {workspace.table.columns.map((col) => (
                  <button
                    key={col.key}
                    type="button"
                    suppressHydrationWarning
                    onClick={() =>
                      setVisibleCols((prev) => {
                        const next = new Set(prev);
                        if (next.has(col.key)) next.delete(col.key);
                        else next.add(col.key);
                        return next;
                      })
                    }
                    className={cn(
                      "rounded px-2 py-1 text-[10px]",
                      visibleCols.has(col.key) ? "bg-[#8B5CF6]/25 text-[#C4B5FD]" : "bg-[#1e293b]/60 text-[#64748B]"
                    )}
                  >
                    {col.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="overflow-x-auto rounded-xl border border-[#2D3748]/60">
              <table className="w-full min-w-[720px] text-left text-xs">
                <thead className="bg-[#0A1020] text-[10px] uppercase tracking-wider text-[#64748B]">
                  <tr>
                    {activeColumns.map((col) => (
                      <th key={col.key} className={cn("px-3 py-2.5", col.frozen && "sticky left-0 bg-[#0A1020]")}>
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((row) => (
                    <tr key={row.id} className="border-t border-[#2D3748]/30 hover:bg-[#8B5CF6]/5">
                      {activeColumns.map((col) => (
                        <td key={col.key} className={cn("px-3 py-2 text-[#CBD5E1]", col.frozen && "sticky left-0 bg-[#0B0F1A]")}>
                          {String(row[col.key] ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs text-[#64748B]">
              <span>{filteredRows.length} records</span>
              <div className="flex gap-2">
                <Button type="button" variant="ghost" size="sm" disabled={tablePage === 0} onClick={() => setTablePage((p) => p - 1)}>
                  Prev
                </Button>
                <span>
                  {tablePage + 1} / {totalPages}
                </span>
                <Button type="button" variant="ghost" size="sm" disabled={tablePage >= totalPages - 1} onClick={() => setTablePage((p) => p + 1)}>
                  Next
                </Button>
              </div>
            </div>
          </WorkspaceSection>

          {/* ROW 9 */}
          <WorkspaceSection row={9} title="Related Modules">
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {workspace.relatedModules.map((mod) => (
                <button
                  key={mod.id}
                  type="button"
                  suppressHydrationWarning
                  onClick={() => router.push(mod.route)}
                  className="flex items-center justify-between rounded-xl border border-[#2D3748]/60 bg-[#121826]/60 p-3 text-left transition hover:border-[rgba(139,92,246,0.45)] hover:bg-[#8B5CF6]/5"
                >
                  <span className="text-sm font-semibold text-white">{mod.label}</span>
                  {mod.badge && (
                    <span className="rounded bg-[#8B5CF6]/20 px-1.5 py-0.5 text-[10px] text-[#A78BFA]">{mod.badge}</span>
                  )}
                </button>
              ))}
            </div>
          </WorkspaceSection>
        </div>
      </div>

      {/* Footer */}
      <footer className="sticky bottom-0 z-30 flex shrink-0 flex-wrap items-center justify-between gap-3 border-t border-[#2D3748]/60 bg-[#0B0F1A]/95 px-5 py-3 text-[11px] text-[#64748B] backdrop-blur-md">
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          <span className={dataSource === "fastapi" ? "text-cyan-400" : "text-[#64748B]"}>
            Source {dataSource === "fastapi" ? "FastAPI" : "Mock"}
          </span>
          <span>{workspace.footer.recordCount.toLocaleString()} records</span>
          <span>Parser {workspace.footer.parserVersion}</span>
          <span>AI {workspace.footer.aiModelVersion}</span>
          <span className={workspace.footer.backendStatus === "online" ? "text-emerald-400" : "text-amber-400"}>
            Backend {workspace.footer.backendStatus}
          </span>
          <span className={workspace.footer.databaseStatus === "connected" ? "text-emerald-400" : "text-amber-400"}>
            DB {workspace.footer.databaseStatus}
          </span>
          <span>{workspace.footer.latencyMs}ms API</span>
          <span>Refresh {workspace.footer.lastRefresh}</span>
        </div>
        <Button type="button" variant="outline" size="sm" className="h-7 gap-1 text-[10px]" onClick={() => setCopilotOpen(true)}>
          <Sparkles className="h-3 w-3" /> AI Copilot
        </Button>
      </footer>

      {/* ROW 10 — Copilot */}
      <KpiCopilotPanel
        open={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        kpiName={workspace.header.name}
        kpiValue={workspace.header.currentValue}
        suggestedPrompts={workspace.copilotSuggestions}
      />
    </motion.div>
  );
}
