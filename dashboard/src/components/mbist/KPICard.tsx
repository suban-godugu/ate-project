"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { MbistKPI } from "@/types/mbist";

export function KPICard({ kpi, index = 0 }: { kpi: MbistKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(kpi)} index={index} />;
}

export function KPIGrid({ data }: { data: MbistKPI[] }) {
  return <EnterpriseKPIGrid data={data} variant="overview" />;
}
