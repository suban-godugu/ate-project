"use client";

import { useAnalysis } from "@/wafervision/hooks/useAnalysis";

export function FutureAnalyticsPanels() {
  const { openWaferChildView } = useAnalysis();

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <section className="panel space-y-3 p-5">
        <h2 className="panel-title">Spatial Analytics</h2>
        <p className="text-sm text-slate-400">
          Review cluster geometry, severity ranking, and overlay highlights returned by the backend.
        </p>
        <button
          type="button"
          onClick={() => openWaferChildView("spatial")}
          className="rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9]"
        >
          View Spatial Analytics
        </button>
      </section>
      <section className="panel space-y-3 p-5">
        <h2 className="panel-title">Engineering Zone Analysis</h2>
        <p className="text-sm text-slate-400">
          Inspect zone-level yield, density, and boundary polygons from engineering zone analysis.
        </p>
        <button
          type="button"
          onClick={() => openWaferChildView("zones")}
          className="rounded-lg bg-[#7C3AED] px-4 py-2 text-sm font-medium text-white hover:bg-[#6D28D9]"
        >
          View Engineering Zones
        </button>
      </section>
    </div>
  );
}
