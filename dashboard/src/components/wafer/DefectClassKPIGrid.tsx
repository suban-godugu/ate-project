"use client";

import { EnterpriseKPIGrid } from "@/components/common/EnterpriseKPICard";
import type { WaferDefectClassKPI } from "@/types/wafer";
import { useWaferNavigation } from "@/components/wafer/WaferNavigationContext";

export function DefectClassKPIGrid({ data }: { data: WaferDefectClassKPI[] }) {
  const navigate = useWaferNavigation();

  return (
    <EnterpriseKPIGrid
      data={data.map((item) => ({
        id: item.id,
        title: item.label,
        value: `${item.avgYield}%`,
        subtitle: `${item.waferCount} wafers · ${item.avgConfidence}% confidence`,
        change: item.avgConfidence,
        trend: "up" as const,
        sparkline: item.sparkline,
        icon: "crosshair",
        positiveIsGood: true,
        status: "ACTIVE",
        statusVariant: "info" as const,
      }))}
      variant="overview"
      onCardClick={(kpi) => navigate(kpi.id as WaferDefectClassKPI["id"])}
    />
  );
}
