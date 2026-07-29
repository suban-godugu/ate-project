"use client";

import { KpiDrillDownGrid } from "@/components/common/kpi-drilldown/KpiDrillDownGrid";
import type { FailureAnalysisKPI } from "@/types/scanChain";

export function FailureKPIGrid({ data }: { data: FailureAnalysisKPI[] }) {
  return <KpiDrillDownGrid data={data} variant="overview" className="kpi-grid" />;
}
