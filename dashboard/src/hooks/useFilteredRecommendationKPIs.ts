"use client";

import { useMemo } from "react";
import { adjustKPIValue, adjustSparkline } from "@/lib/filterEngine";
import { useFilterStore } from "@/stores/filterStore";
import type { CenterKPI, KPISection } from "@/types/recommendation";

function parsePercent(value: string): number | null {
  const num = parseFloat(value.replace(/[^0-9.-]/g, ""));
  return Number.isFinite(num) ? num : null;
}

function deriveKPIStatus(
  kpi: CenterKPI,
  value: string
): Pick<CenterKPI, "status" | "statusVariant"> {
  const num = parsePercent(value);

  if (kpi.id === "avg-confidence" && num !== null) {
    if (num >= 85) {
      return { status: "Above 85% Threshold", statusVariant: "success" };
    }
    if (num >= 70) {
      return { status: "Below 85% Threshold", statusVariant: "warning" };
    }
    return { status: "Low Confidence", statusVariant: "danger" };
  }

  if (kpi.id === "peak-switching" && num !== null) {
    if (num > 65) {
      return { status: "Exceeds 65% Budget", statusVariant: "danger" };
    }
    return { status: "Within 65% Budget", statusVariant: "success" };
  }

  if (kpi.id === "suspect-hit-rate" && num !== null) {
    if (num >= 70) {
      return { status: "FA Confirmed", statusVariant: "success" };
    }
    if (num >= 50) {
      return { status: "Moderate Hit Rate", statusVariant: "warning" };
    }
    return { status: "Low Hit Rate", statusVariant: "danger" };
  }

  return { status: kpi.status, statusVariant: kpi.statusVariant };
}

export function useFilteredRecommendationKPIs(kpis: CenterKPI[]): CenterKPI[] {
  const filters = useFilterStore((s) => s.filters);

  return useMemo(
    () =>
      kpis.map((kpi, i) => {
        const value = adjustKPIValue(kpi.value, filters, i);
        const sparkline = adjustSparkline(kpi.sparkline, filters);
        const statusFields = deriveKPIStatus(kpi, value);

        return {
          ...kpi,
          value,
          sparkline,
          ...statusFields,
        };
      }),
    [kpis, filters]
  );
}

export function useFilteredKPISections(sections: KPISection[]): KPISection[] {
  const filters = useFilterStore((s) => s.filters);

  return useMemo(() => {
    let globalIndex = 0;

    return sections.map((section) => ({
      ...section,
      kpis: section.kpis.map((kpi) => {
        const index = globalIndex++;
        const value = adjustKPIValue(kpi.value, filters, index);
        const sparkline = adjustSparkline(kpi.sparkline, filters);
        const statusFields = deriveKPIStatus(kpi, value);

        return {
          ...kpi,
          value,
          sparkline,
          ...statusFields,
        };
      }),
    }));
  }, [sections, filters]);
}
