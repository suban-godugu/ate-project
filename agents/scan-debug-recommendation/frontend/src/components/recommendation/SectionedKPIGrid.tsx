"use client";

import type { KpiCardModel, ScanDebugKpiId } from "@/types/kpiDrillDown";
import { SECTION_PROFILES, KPI_ORDER } from "@/lib/kpiDrillDown/kpiProfiles";
import { KpiCardView } from "@/components/recommendation/KpiCardView";

function KpiSkeleton() {
  return (
    <div className="glass-card gradient-border animate-pulse p-4">
      <div className="mb-3 h-8 w-8 rounded-xl bg-white/10" />
      <div className="mb-2 h-3 w-24 rounded bg-white/10" />
      <div className="mb-2 h-8 w-16 rounded bg-white/15" />
      <div className="h-3 w-32 rounded bg-white/10" />
    </div>
  );
}

export function SectionedKPIGrid({
  kpis,
  onKpiClick,
  loading = false,
}: {
  kpis: KpiCardModel[];
  onKpiClick: (id: ScanDebugKpiId) => void;
  loading?: boolean;
}) {
  return (
    <div className="space-y-6">
      {SECTION_PROFILES.map((section) => {
        const sectionKpis = KPI_ORDER[section.id]
          .map((id) => kpis.find((k) => k.id === id))
          .filter(Boolean) as KpiCardModel[];
        return (
          <section key={section.id} className="space-y-3">
            <div>
              <div className="text-[10px] uppercase tracking-[0.16em] text-primary">
                {section.eyebrow}
              </div>
              <h2 className="font-display text-lg font-semibold text-white">{section.title}</h2>
              <p className="mt-1 max-w-3xl text-sm text-muted">{section.description}</p>
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3 xl:grid-cols-5">
              {loading
                ? KPI_ORDER[section.id].map((id) => <KpiSkeleton key={id} />)
                : sectionKpis.map((kpi) => (
                    <KpiCardView key={kpi.id} kpi={kpi} onClick={() => onKpiClick(kpi.id)} />
                  ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
