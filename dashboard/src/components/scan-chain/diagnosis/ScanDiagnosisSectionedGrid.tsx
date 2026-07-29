"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { EnterpriseKPIGrid } from "@/components/common/EnterpriseKPICard";
import { KpiDrillDownModal } from "@/components/common/kpi-drilldown/KpiDrillDownModal";
import { toDrillDownKPI } from "@/lib/kpiDrillDown/kpiDrillDownUtils";
import type { ScanDiagnosisKPISection } from "@/types/scanChain";
import type { DrillDownKPI } from "@/types/kpiDrillDown";

export function ScanDiagnosisSectionedGrid({ sections }: { sections: ScanDiagnosisKPISection[] }) {
  const [selected, setSelected] = useState<DrillDownKPI | null>(null);

  return (
    <>
      <div className="flex w-full flex-col gap-6">
        {sections.map((section, si) => (
          <motion.div
            key={section.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: si * 0.05 }}
            className="w-full"
          >
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[#7C3AED]">
              {section.title}
            </h3>
            <EnterpriseKPIGrid
              data={section.kpis}
              variant="section"
              onCardClick={(kpi) => setSelected(toDrillDownKPI(kpi))}
            />
          </motion.div>
        ))}
      </div>

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
