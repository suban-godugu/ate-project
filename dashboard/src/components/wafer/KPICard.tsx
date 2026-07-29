"use client";

import {
  EnterpriseKPICard,
  EnterpriseKPIGrid,
  kpiPropsFromUnified,
} from "@/components/common/EnterpriseKPICard";
import type { WaferKPI } from "@/types/wafer";

export function KPICard({
  kpi,
  index = 0,
  onClick,
}: {
  kpi: WaferKPI;
  index?: number;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <EnterpriseKPICard
      {...kpiPropsFromUnified({ ...kpi, description: kpi.tooltip })}
      index={index}
      onClick={onClick}
    />
  );
}

export function KPIGrid({
  data,
  onCardClick,
}: {
  data: WaferKPI[];
  onCardClick?: (id: string) => void;
}) {
  return (
    <EnterpriseKPIGrid
      data={data.map((kpi) => ({ ...kpi, description: kpi.tooltip }))}
      variant="overview"
      onCardClick={onCardClick ? (kpi) => onCardClick(kpi.id) : undefined}
    />
  );
}
