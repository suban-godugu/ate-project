"use client";

import { MetaChip } from "@/components/common/kpi-drilldown/KpiWorkspaceSections";
import type { CoverageMetadataField } from "@/types/scanCoverage";

export function CoverageMetadata({ fields }: { fields: CoverageMetadataField[] }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-8">
      {fields.map((field) => (
        <MetaChip key={field.label} label={field.label} value={field.value} />
      ))}
    </div>
  );
}
