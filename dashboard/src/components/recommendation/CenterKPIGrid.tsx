"use client";

import { useState } from "react";
import { KpiDrillDownModal } from "@/components/common/kpi-drilldown/KpiDrillDownModal";
import {
  EnterpriseKPIGrid,
  legacyGridClassToVariant,
  type EnterpriseKPIGridVariant,
} from "@/components/common/EnterpriseKPICard";
import { toDrillDownKPI } from "@/lib/kpiDrillDown/kpiDrillDownUtils";
import type { CenterKPI } from "@/types/recommendation";
import type { DrillDownKPI } from "@/types/kpiDrillDown";

export function CenterKPIGrid({
  data,
  gridClassName,
  variant,
}: {
  data: CenterKPI[];
  gridClassName?: string;
  variant?: EnterpriseKPIGridVariant;
}) {
  const resolvedVariant = variant ?? legacyGridClassToVariant(gridClassName);
  const [selected, setSelected] = useState<DrillDownKPI | null>(null);

  return (
    <>
      <EnterpriseKPIGrid
        data={data}
        variant={resolvedVariant}
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
