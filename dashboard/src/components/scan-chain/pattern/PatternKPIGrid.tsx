"use client";

import { KpiDrillDownGrid } from "@/components/common/kpi-drilldown/KpiDrillDownGrid";
import type { PatternAnalysisKPI } from "@/types/scanChain";

export function PatternKPIGrid({ data }: { data: PatternAnalysisKPI[] }) {
  return <KpiDrillDownGrid data={data} variant="overview" className="kpi-grid" />;
}
