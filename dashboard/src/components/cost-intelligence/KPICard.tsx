"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { CostKPI } from "@/types/costIntelligence";

export function KPICard({ kpi, index = 0 }: { kpi: CostKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(kpi)} index={index} />;
}

export function KPIGrid({ data }: { data: CostKPI[] }) {
  return <EnterpriseKPIGrid data={data} variant="overview" />;
}
