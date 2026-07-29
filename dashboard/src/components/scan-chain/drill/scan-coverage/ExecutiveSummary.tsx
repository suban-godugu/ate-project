"use client";

import type { CoverageExecutiveCard } from "@/types/scanCoverage";
import { ExecutiveSummaryCard } from "@/components/common/kpi-drilldown/KpiWorkspaceSections";

export function ExecutiveSummary({ cards }: { cards: CoverageExecutiveCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map((card) => (
        <ExecutiveSummaryCard
          key={card.id}
          card={{
            id: card.id,
            label: card.label,
            value: card.value,
            icon: card.icon,
            sparkline: card.sparkline,
            variant: card.variant,
          }}
        />
      ))}
    </div>
  );
}
