"use client";

import { useAnalysis } from "@/hooks/useAnalysis";

/**
 * Navigation cards below Wafer Analysis — open Spatial / Zones as child views.
 * Does not duplicate panel contents.
 */
export function FutureAnalyticsPanels() {
  const { openWaferChildView } = useAnalysis();

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Spatial Analytics</h2>
        <p className="mb-4 text-sm leading-relaxed text-[var(--muted)]">
          View spatial defect clusters, density maps, zone statistics and wafer
          spatial intelligence.
        </p>
        <button
          type="button"
          onClick={() => openWaferChildView("spatial")}
          className="rounded-lg bg-ink-800 px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 dark:bg-ink-200 dark:text-ink-950"
        >
          View Spatial Analytics
        </button>
      </section>
      <section className="panel p-5">
        <h2 className="panel-title mb-2">Engineering Zone Analysis</h2>
        <p className="mb-4 text-sm leading-relaxed text-[var(--muted)]">
          View engineering zones, critical regions, root-cause hotspots and
          zone-based failure statistics.
        </p>
        <button
          type="button"
          onClick={() => openWaferChildView("zones")}
          className="rounded-lg bg-ink-800 px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 dark:bg-ink-200 dark:text-ink-950"
        >
          View Engineering Zones
        </button>
      </section>
    </div>
  );
}
