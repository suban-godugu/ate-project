"use client";

import type { ScanKPI } from "@/types/scanChain";
import { KpiDrillDownModal } from "@/components/common/kpi-drilldown/KpiDrillDownModal";
import { toDrillDownKPI } from "@/lib/kpiDrillDown/kpiDrillDownUtils";

interface ExecutiveKPIDrillDownModalProps {
  kpi: ScanKPI | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

/** @deprecated Use KpiDrillDownModal */
export function ExecutiveKPIDrillDownModal({ kpi, open, onOpenChange }: ExecutiveKPIDrillDownModalProps) {
  return (
    <KpiDrillDownModal
      kpi={kpi ? toDrillDownKPI(kpi) : null}
      open={open}
      onOpenChange={onOpenChange}
    />
  );
}

export { KpiDrillDownModal };
