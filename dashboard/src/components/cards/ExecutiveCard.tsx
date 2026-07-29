"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { UnifiedKPI } from "@/types/kpi";
import type { ExecutiveKPI } from "@/types/dashboard";

function toExecutiveUnified(kpi: ExecutiveKPI): UnifiedKPI {
  const lowerIsBetter = ["total-test-cost", "cost-per-wafer", "cost-per-die", "test-time"].includes(kpi.id);
  return {
    ...kpi,
    icon: kpi.id,
    positiveIsGood: lowerIsBetter ? false : true,
  };
}

export function ExecutiveCard({ kpi, index = 0 }: { kpi: ExecutiveKPI; index?: number }) {
  return <EnterpriseKPICard {...kpiPropsFromUnified(toExecutiveUnified(kpi))} index={index} />;
}

export function ExecutiveKPIGrid({ data }: { data: ExecutiveKPI[] }) {
  return <EnterpriseKPIGrid data={data.map(toExecutiveUnified)} variant="overview" />;
}
