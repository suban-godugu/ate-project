"use client";

import { useMemo, useState } from "react";
import { useAnalysis } from "@/wafervision/hooks/useAnalysis";
import { useWaferBaseImage } from "@/wafervision/hooks/useWaferBaseImage";
import { SpatialHighlightCanvas } from "@/wafervision/components/SpatialHighlightCanvas";
import { cn, toDataUrl } from "@/wafervision/utils/format";
import type { WaferRenderInput } from "@/wafervision/utils/waferRender";
import type { WaferAnalysisResult } from "@/wafervision/types";
import {
  clusterContrib,
  clusterDensity,
  clusterFail,
  clusterFailPct,
  clusterGood,
  clusterHighlight,
  clusterTotal,
  listZones,
  zoneDensity,
  zoneFail,
  zoneGood,
  zonePolygon,
  zoneTotal,
} from "@/wafervision/utils/spatialCoords";

function waferInput(
  selected: WaferAnalysisResult | null,
  image: HTMLImageElement | null,
): WaferRenderInput | null {
  const dies = selected?.dies ?? [];
  if (!dies.length) return null;
  return {
    dies,
    geometry: selected?.wafer_geometry,
    gridInfo: selected?.grid_info,
    image,
  };
}

export function SpatialAnalyticsPanel() {
  const { selected } = useAnalysis();
  const [activeClusterId, setActiveClusterId] = useState<string | null>(null);

  const baseImage = useWaferBaseImage(selected?.images?.original);
  const wafer = useMemo(() => waferInput(selected, baseImage), [baseImage, selected]);
  const spatial = selected?.spatial_analysis;
  const clusters = spatial?.clusters ?? [];
  const summary = spatial?.cluster_summary;
  const active = clusters.find((c) => c.cluster_id === activeClusterId) ?? null;
  const highlight = clusterHighlight(active);
  const overlay = toDataUrl(selected?.images?.overlay);

  if (!spatial) {
    return (
      <section className="panel p-5">
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No Spatial Analytics Available
        </p>
      </section>
    );
  }

  const kpis = [
    {
      label: "Total Clusters",
      value: summary?.total_clusters_detected ?? summary?.total_clusters ?? "—",
    },
    { label: "Displayed Clusters", value: summary?.displayed_clusters ?? "—" },
    { label: "Critical Clusters", value: summary?.critical_clusters ?? "—" },
    {
      label: "Largest Cluster",
      value: summary?.largest_cluster_fail_dies ?? summary?.largest_cluster ?? "—",
    },
    {
      label: "Highest Severity",
      value: summary?.highest_severity ?? summary?.highest_severity_score ?? "—",
    },
  ];

  return (
    <div className="space-y-4">
      {summary && (
        <section className="panel p-5">
          <h2 className="panel-title mb-3">Cluster Summary</h2>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
            {kpis.map((k) => (
              <div key={k.label} className="rounded-lg border p-3" style={{ borderColor: "var(--line)" }}>
                <div className="text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
                  {k.label}
                </div>
                <div className="mt-1 font-mono text-lg font-semibold">{k.value}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="panel space-y-3 p-5">
        <h2 className="panel-title">Cluster Highlight</h2>
        <SpatialHighlightCanvas
          wafer={wafer}
          imageUrl={overlay}
          bbox={highlight.bbox}
          centroid={highlight.centroid}
        />
      </section>

      <section className="panel p-5">
        <h2 className="panel-title mb-3">Top Clusters</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-[11px] uppercase" style={{ color: "var(--muted)" }}>
                {[
                  "Rank",
                  "Cluster ID",
                  "Fail",
                  "Good",
                  "Total",
                  "Fail %",
                  "Contrib %",
                  "Density",
                  "Severity Score",
                  "Severity",
                ].map((h) => (
                  <th key={h} className="px-2 py-2 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {clusters.map((c) => {
                const id = c.cluster_id || String(c.rank);
                const activeRow = activeClusterId === id;
                return (
                  <tr
                    key={id}
                    onClick={() => setActiveClusterId(activeRow ? null : id)}
                    className={cn("cursor-pointer border-t", activeRow && "bg-[#7C3AED]/15")}
                    style={{ borderColor: "var(--line)" }}
                  >
                    <td className="px-2 py-2 font-mono">{c.rank}</td>
                    <td className="px-2 py-2 font-mono">{c.cluster_id}</td>
                    <td className="px-2 py-2 font-mono">{clusterFail(c)}</td>
                    <td className="px-2 py-2 font-mono">{clusterGood(c)}</td>
                    <td className="px-2 py-2 font-mono">{clusterTotal(c)}</td>
                    <td className="px-2 py-2 font-mono">{clusterFailPct(c)}</td>
                    <td className="px-2 py-2 font-mono">{clusterContrib(c)}</td>
                    <td className="px-2 py-2 font-mono">{clusterDensity(c)}</td>
                    <td className="px-2 py-2 font-mono">{c.severity_score}</td>
                    <td className="px-2 py-2">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs",
                          c.severity === "Critical" && "bg-signal-fail/15 text-signal-fail",
                          c.severity === "High" && "bg-[#7C3AED]/20 text-[#A78BFA]",
                          c.severity !== "Critical" && c.severity !== "High" && "opacity-70",
                        )}
                      >
                        {c.severity}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export function EngineeringZonesPanel() {
  const { selected } = useAnalysis();
  const [activeZone, setActiveZone] = useState<string | null>(null);
  const baseImage = useWaferBaseImage(selected?.images?.original);
  const wafer = useMemo(() => waferInput(selected, baseImage), [baseImage, selected]);
  const spatial = selected?.spatial_analysis;
  const zones = listZones(spatial);
  const active = zones.find((z) => z.zone === activeZone) ?? null;
  const overlay = toDataUrl(selected?.images?.overlay);

  if (!spatial) {
    return (
      <section className="panel p-5">
        <p className="text-sm" style={{ color: "var(--muted)" }}>
          No Spatial Analytics Available
        </p>
      </section>
    );
  }

  return (
    <div className="space-y-4">
      <section className="panel space-y-3 p-5">
        <h2 className="panel-title">Zone Highlight</h2>
        <SpatialHighlightCanvas wafer={wafer} imageUrl={overlay} polygon={zonePolygon(active)} />
      </section>

      <section className="panel p-5">
        <h2 className="panel-title mb-3">Engineering Zones</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-[11px] uppercase" style={{ color: "var(--muted)" }}>
                {["Zone", "Good", "Fail", "Total", "Yield %", "Fail %", "Density", "Rank", "Status"].map(
                  (h) => (
                    <th key={h} className="px-2 py-2 text-left">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {zones.map((z) => {
                const id = z.zone || String(z.rank);
                const activeRow = activeZone === id;
                return (
                  <tr
                    key={id}
                    onClick={() => setActiveZone(activeRow ? null : id)}
                    className={cn("cursor-pointer border-t", activeRow && "bg-[#7C3AED]/15")}
                    style={{ borderColor: "var(--line)" }}
                  >
                    <td className="px-2 py-2">{z.zone}</td>
                    <td className="px-2 py-2 font-mono">{zoneGood(z)}</td>
                    <td className="px-2 py-2 font-mono">{zoneFail(z)}</td>
                    <td className="px-2 py-2 font-mono">{zoneTotal(z)}</td>
                    <td className="px-2 py-2 font-mono">{z.yield_percent}</td>
                    <td className="px-2 py-2 font-mono">{z.fail_percent}</td>
                    <td className="px-2 py-2 font-mono">{zoneDensity(z)}</td>
                    <td className="px-2 py-2 font-mono">{z.rank}</td>
                    <td className="px-2 py-2">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-xs",
                          z.status === "Critical" && "bg-signal-fail/15 text-signal-fail",
                          z.status === "Warning" && "bg-[#7C3AED]/20 text-[#A78BFA]",
                          z.status !== "Critical" &&
                            z.status !== "Warning" &&
                            "bg-signal-good/15 text-signal-good",
                        )}
                      >
                        {z.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
