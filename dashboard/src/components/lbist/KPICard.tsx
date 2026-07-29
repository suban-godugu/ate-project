"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { LbistKPI } from "@/types/lbist";

export function KPICard({ kpi, index = 0 }: { kpi: LbistKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(kpi)} index={index} />;
}

export function KPIGrid({ data }: { data: LbistKPI[] }) {
  return <EnterpriseKPIGrid data={data} variant="overview" />;
}
