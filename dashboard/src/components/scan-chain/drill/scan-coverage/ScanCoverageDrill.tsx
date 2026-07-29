"use client";

import { useCallback, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { ArrowDown, ArrowUp, Download, RefreshCw, X } from "lucide-react";
import { resolveKpiIcon } from "@/components/common/kpiIcons";
import { FilterChip, WorkspaceSection } from "@/components/common/kpi-drilldown/KpiWorkspaceSections";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { ScanCoverageDrillData } from "@/types/scanCoverage";
import { CoverageDiagnosis } from "./CoverageDiagnosis";
import { CoverageMetadata } from "./CoverageMetadata";
import { EngineeringTimeline } from "./EngineeringTimeline";
import { ExecutiveSummary } from "./ExecutiveSummary";
import { RawCoverageTable } from "./RawCoverageTable";
import { RelatedModules } from "./RelatedModules";

const CoverageDistribution = dynamic(
  () => import("./CoverageDistribution").then((m) => m.CoverageDistribution),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

const CoverageStatus = dynamic(
  () => import("./CoverageStatus").then((m) => m.CoverageStatus),
  { ssr: false, loading: () => <ChartSkeleton /> }
);

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

function ChartSkeleton() {
  return <div className="h-72 animate-pulse rounded-xl border border-[#2D3748]/60 bg-[#0A1020]/60" />;
}

interface Props {
  data: ScanCoverageDrillData;
  onRefresh?: () => void;
  onClose?: () => void;
}

export function ScanCoverageDrill({ data, onRefresh, onClose }: Props) {
  const [lastRefresh, setLastRefresh] = useState(data.header.lastUpdated);
  const Icon = resolveKpiIcon(data.header.icon);

  const handleRefresh = useCallback(() => {
    setLastRefresh(new Date().toISOString());
    onRefresh?.();
  }, [onRefresh]);

  const handleExport = useCallback(() => {
    const headers = data.table.columns.map((c) => c.label);
    const rows = data.table.rows.map((r) => data.table.columns.map((c) => String(r[c.key as keyof typeof r] ?? "")));
    import("@/lib/exportUtils").then(({ exportCSV }) => {
      exportCSV("scan-coverage-summary.csv", headers, rows);
    });
  }, [data.table]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="flex h-full flex-col overflow-hidden rounded-2xl border border-[rgba(139,92,246,0.25)] bg-[#0B0F1A]/95 shadow-2xl shadow-purple-900/25 backdrop-blur-xl"
      aria-label="Scan Coverage analytics workspace"
    >
      <header className="sticky top-0 z-30 shrink-0 border-b border-[#2D3748]/60 bg-[#0B0F1A]/95 px-5 py-4 backdrop-blur-md">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex min-w-0 flex-1 items-start gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[rgba(124,58,237,0.2)] text-[#8B5CF6]">
              <Icon className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-bold text-white">{data.header.name}</h2>
                <span className="text-2xl font-extrabold tabular-nums text-white">{data.header.currentValue}</span>
                <span
                  className={cn(
                    "rounded-full px-2.5 py-0.5 text-xs font-semibold",
                    STATUS_STYLE[data.header.statusVariant]
                  )}
                >
                  {data.header.statusBadge}
                </span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase",
                    RISK_STYLE[data.header.riskLevel]
                  )}
                >
                  {data.header.riskLevel} risk
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-[#94A3B8]">
                  {data.header.trendDirection === "up" ? (
                    <ArrowUp className="h-3 w-3 text-emerald-400" />
                  ) : data.header.trendDirection === "down" ? (
                    <ArrowDown className="h-3 w-3 text-red-400" />
                  ) : null}
                  {data.header.trendLabel}
                </span>
              </div>
              <p className="mt-1 text-[11px] text-[#64748B]">
                Updated {new Date(lastRefresh).toLocaleString()}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <FilterChip label="Fab" value={data.header.activeFilters.fab} />
                <FilterChip label="Tester" value={data.header.activeFilters.tester} />
                <FilterChip label="Product" value={data.header.activeFilters.product} />
                <FilterChip label="Lot" value={data.header.activeFilters.lot} />
                <FilterChip label="Wafer" value={data.header.activeFilters.wafer} />
              </div>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={handleExport}>
              <Download className="h-3.5 w-3.5" /> Export
            </Button>
            <Button type="button" variant="outline" size="sm" className="h-8 gap-1.5 text-xs" onClick={handleRefresh}>
              <RefreshCw className="h-3.5 w-3.5" /> Refresh
            </Button>
            {onClose && (
              <Button type="button" variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close">
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
        <div className="space-y-8">
          <WorkspaceSection row={1} title="Executive Summary">
            <ExecutiveSummary cards={data.executiveSummary} />
          </WorkspaceSection>

          <WorkspaceSection row={2} title="Coverage Distribution">
            <CoverageDistribution distributionByTab={data.distributionByTab} />
          </WorkspaceSection>

          <WorkspaceSection row={3} title="Coverage Status">
            <CoverageStatus status={data.status} />
          </WorkspaceSection>

          <WorkspaceSection row={4} title="Coverage Diagnosis">
            <CoverageDiagnosis diagnosis={data.diagnosis} />
          </WorkspaceSection>

          <WorkspaceSection row={5} title="Coverage Metadata">
            <CoverageMetadata fields={data.metadata} />
          </WorkspaceSection>

          <WorkspaceSection row={6} title="Engineering Timeline">
            <EngineeringTimeline steps={data.timeline} />
          </WorkspaceSection>

          <WorkspaceSection
            row={7}
            title="Raw Coverage Data"
            action={
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    const headers = data.table.columns.map((c) => c.label);
                    const rows = data.table.rows.map((r) =>
                      data.table.columns.map((c) => String(r[c.key as keyof typeof r] ?? ""))
                    );
                    import("@/lib/exportUtils").then(({ exportCSV }) => exportCSV("scan-coverage-data.csv", headers, rows));
                  }}
                >
                  CSV
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => {
                    const headers = data.table.columns.map((c) => c.label);
                    const rows = data.table.rows.map((r) =>
                      data.table.columns.map((c) => String(r[c.key as keyof typeof r] ?? ""))
                    );
                    import("@/lib/exportUtils").then(({ exportExcel }) =>
                      exportExcel("scan-coverage-data.xls", headers, rows)
                    );
                  }}
                >
                  Excel
                </Button>
              </div>
            }
          >
            <RawCoverageTable columns={data.table.columns} rows={data.table.rows} />
          </WorkspaceSection>

          <WorkspaceSection row={8} title="Related Modules">
            <RelatedModules modules={data.relatedModules} />
          </WorkspaceSection>
        </div>
      </div>
    </motion.div>
  );
}
