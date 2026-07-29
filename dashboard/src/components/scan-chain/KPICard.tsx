"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { ScanKPI } from "@/types/scanChain";

export function KPICard({ kpi, index = 0 }: { kpi: ScanKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(kpi)} index={index} />;
}

export function KPIGrid({ data }: { data: ScanKPI[] }) {
  return <EnterpriseKPIGrid data={data} variant="overview" />;
}
