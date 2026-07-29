"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { AlertKPI } from "@/types/alerts";

export function KPICard({ kpi, index = 0 }: { kpi: AlertKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(kpi)} index={index} />;
}

export function KPIGrid({ data }: { data: AlertKPI[] }) {
  return <EnterpriseKPIGrid data={data} variant="overview" />;
}
