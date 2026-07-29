"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { RecKPI } from "@/types/recommendation";

export function KPICard({ kpi, index = 0 }: { kpi: RecKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(kpi)} index={index} />;
}

export function KPIGrid({ data }: { data: RecKPI[] }) {
  return <EnterpriseKPIGrid data={data} variant="overview" />;
}
