"use client";

import { useState } from "react";
import { KpiDrillDownModal } from "@/components/common/kpi-drilldown/KpiDrillDownModal";
import {
  EnterpriseKPIGrid,
  type EnterpriseKPIGridVariant,
} from "@/components/common/EnterpriseKPICard";
import { toDrillDownKPI } from "@/lib/kpiDrillDown/kpiDrillDownUtils";
import type { UnifiedKPI } from "@/types/kpi";
import type { DrillDownKPI } from "@/types/kpiDrillDown";

interface KpiDrillDownGridProps<T extends UnifiedKPI> {
  data: T[];
  variant?: EnterpriseKPIGridVariant;
  showSparkline?: boolean;
  className?: string;
}

export function KpiDrillDownGrid<T extends UnifiedKPI>({
  data,
  variant = "overview",
  showSparkline = true,
  className,
}: KpiDrillDownGridProps<T>) {
  const [selected, setSelected] = useState<DrillDownKPI | null>(null);

  return (
    <>
      <EnterpriseKPIGrid
        data={data}
        variant={variant}
        showSparkline={showSparkline}
        className={className}
        onCardClick={(kpi) => setSelected(toDrillDownKPI(kpi))}
      />

      <KpiDrillDownModal
        kpi={selected}
        open={Boolean(selected)}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      />
    </>
  );
}
