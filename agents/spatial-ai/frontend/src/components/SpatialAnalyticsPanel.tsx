"use client";

import { useMemo, useState } from "react";

import { SpatialHighlightCanvas } from "@/components/SpatialHighlightCanvas";
import { useAnalysis } from "@/hooks/useAnalysis";
import type { ClusterRecord, ZoneRecord } from "@/types/wafer";
import { cn, formatPercent, toDataUrl } from "@/utils/format";

function readSpatial(selected: ReturnType<typeof useAnalysis>["selected"]) {
  const spatial = selected?.spatial_analysis;
  if (!spatial || typeof spatial !== "object") return null;
  return spatial;
}

export function SpatialAnalyticsPanel() {
  const { selected } = useAnalysis();
  const spatial = readSpatial(selected);
  const [activeClusterId, setActiveClusterId] = useState<string | null>(null);

  const clusters = (spatial?.clusters ?? []) as ClusterRecord[];
  const summary = spatial?.cluster_summary;
  const activeCluster = useMemo(
    () => clusters.find((c) => c.cluster_id === activeClusterId) ?? null,
    [clusters, activeClusterId],
  );

  if (!spatial) {
    return (
      <section className="panel p-8 text-center">
        <h2 className="panel-title mb-3">Spatial Analytics</h2>
        <p className="text-sm text-[var(--muted)]">No Spatial Analytics Available</p>
      </section>
    );
  }

  const overlaySrc = toDataUrl(selected?.images?.overlay);

  return (
    <div className="space-y-4">
      <section className="panel p-5">
        <h2 className="panel-title mb-4">Cluster Summary</h2>
        {!summary ? (
          <p className="text-sm text-[var(--muted)]">No cluster summary.</p>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
            <Metric label="Total Clusters" value={String(summary.total_clusters_detected ?? "—")} />
            <Metric label="Displayed Clusters" value={String(summary.displayed_clusters ?? "—")} />
            <Metric label="Critical Clusters" value={String(summary.critical_clusters ?? "—")} />
            <Metric
              label="Largest Cluster"
              value={String(summary.largest_cluster_fail_dies ?? "—")}
            />
            <Metric
              label="Highest Severity"
              value={
                summary.highest_severity_score == null
                  ? "—"
                  : String(summary.highest_severity_score)
              }
            />
          </div>
        )}
      </section>

      <section className="panel p-5">
        <h2 className="panel-title mb-3">Cluster Highlight</h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Select a cluster row to highlight bounding box and centroid on the overlay
          (backend geometry only — no recalculation).
        </p>
        <div className="relative mx-auto max-w-lg overflow-hidden rounded-lg border border-[var(--line)] bg-ink-950/5">
          {overlaySrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={overlaySrc} alt="Wafer overlay" className="block w-full" />
          ) : (
            <div className="flex aspect-square items-center justify-center text-sm text-[var(--muted)]">
              Overlay image not available
            </div>
          )}
          <SpatialHighlightCanvas cluster={activeCluster} zone={null} />
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="panel-title mb-4">Top Clusters</h2>
        {clusters.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No clusters detected.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--line)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                  <th className="px-2 py-2">Rank</th>
                  <th className="px-2 py-2">Cluster ID</th>
                  <th className="px-2 py-2">Fail</th>
                  <th className="px-2 py-2">Good</th>
                  <th className="px-2 py-2">Total</th>
                  <th className="px-2 py-2">Fail %</th>
                  <th className="px-2 py-2">Contrib %</th>
                  <th className="px-2 py-2">Density</th>
                  <th className="px-2 py-2">Severity Score</th>
                  <th className="px-2 py-2">Severity</th>
                </tr>
              </thead>
              <tbody>
                {clusters.map((cluster) => {
                  const active = cluster.cluster_id === activeClusterId;
                  return (
                    <tr
                      key={cluster.cluster_id}
                      className={cn(
                        "cursor-pointer border-b border-[var(--line)] hover:bg-signal-info/5",
                        active && "bg-signal-info/10",
                      )}
                      onClick={() =>
                        setActiveClusterId(
                          active ? null : cluster.cluster_id,
                        )
                      }
                    >
                      <td className="px-2 py-2 font-mono">{cluster.rank}</td>
                      <td className="px-2 py-2 font-mono">{cluster.cluster_id}</td>
                      <td className="px-2 py-2 font-mono">{cluster.fail_dies}</td>
                      <td className="px-2 py-2 font-mono">{cluster.good_dies}</td>
                      <td className="px-2 py-2 font-mono">{cluster.total_dies}</td>
                      <td className="px-2 py-2 font-mono">
                        {formatPercent(cluster.cluster_fail_percent)}
                      </td>
                      <td className="px-2 py-2 font-mono">
                        {formatPercent(cluster.contribution_percent)}
                      </td>
                      <td className="px-2 py-2 font-mono">
                        {cluster.cluster_density?.toFixed?.(4) ?? cluster.cluster_density}
                      </td>
                      <td className="px-2 py-2 font-mono">
                        {cluster.severity_score}
                      </td>
                      <td className="px-2 py-2">
                        <SeverityBadge severity={cluster.severity} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

export function EngineeringZonesPanel() {
  const { selected } = useAnalysis();
  const spatial = readSpatial(selected);
  const [activeZone, setActiveZone] = useState<string | null>(null);

  const zones = (spatial?.zone_analysis ?? []) as ZoneRecord[];
  const active = useMemo(
    () => zones.find((z) => z.zone === activeZone) ?? null,
    [zones, activeZone],
  );

  if (!spatial) {
    return (
      <section className="panel p-8 text-center">
        <h2 className="panel-title mb-3">Engineering Zones</h2>
        <p className="text-sm text-[var(--muted)]">No Spatial Analytics Available</p>
      </section>
    );
  }

  const overlaySrc = toDataUrl(selected?.images?.overlay);

  return (
    <div className="space-y-4">
      <section className="panel p-5">
        <h2 className="panel-title mb-3">Zone Highlight</h2>
        <p className="mb-3 text-xs text-[var(--muted)]">
          Select a zone row to highlight its backend-provided boundary.
        </p>
        <div className="relative mx-auto max-w-lg overflow-hidden rounded-lg border border-[var(--line)] bg-ink-950/5">
          {overlaySrc ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={overlaySrc} alt="Wafer overlay" className="block w-full" />
          ) : (
            <div className="flex aspect-square items-center justify-center text-sm text-[var(--muted)]">
              Overlay image not available
            </div>
          )}
          <SpatialHighlightCanvas cluster={null} zone={active} />
        </div>
      </section>

      <section className="panel p-5">
        <h2 className="panel-title mb-4">Engineering Zones</h2>
        {zones.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No zone analysis.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--line)] text-left text-xs uppercase tracking-wide text-[var(--muted)]">
                  <th className="px-2 py-2">Zone</th>
                  <th className="px-2 py-2">Good</th>
                  <th className="px-2 py-2">Fail</th>
                  <th className="px-2 py-2">Total</th>
                  <th className="px-2 py-2">Yield %</th>
                  <th className="px-2 py-2">Fail %</th>
                  <th className="px-2 py-2">Density</th>
                  <th className="px-2 py-2">Rank</th>
                  <th className="px-2 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {zones.map((zone) => {
                  const selectedRow = zone.zone === activeZone;
                  return (
                    <tr
                      key={zone.zone}
                      className={cn(
                        "cursor-pointer border-b border-[var(--line)] hover:bg-signal-info/5",
                        selectedRow && "bg-signal-info/10",
                      )}
                      onClick={() =>
                        setActiveZone(selectedRow ? null : zone.zone)
                      }
                    >
                      <td className="px-2 py-2 font-medium">{zone.zone}</td>
                      <td className="px-2 py-2 font-mono">{zone.good_dies}</td>
                      <td className="px-2 py-2 font-mono">{zone.fail_dies}</td>
                      <td className="px-2 py-2 font-mono">{zone.total_dies}</td>
                      <td className="px-2 py-2 font-mono">
                        {formatPercent(zone.yield_percent)}
                      </td>
                      <td className="px-2 py-2 font-mono">
                        {formatPercent(zone.fail_percent)}
                      </td>
                      <td className="px-2 py-2">{zone.defect_density}</td>
                      <td className="px-2 py-2 font-mono">{zone.rank}</td>
                      <td className="px-2 py-2">
                        <StatusBadge status={zone.status} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-[var(--line)] px-3 py-3">
      <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className="mt-1 font-mono text-lg font-semibold">{value}</p>
    </div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const tone =
    severity === "Critical"
      ? "text-signal-fail"
      : severity === "High"
        ? "text-signal-warn"
        : "text-[var(--muted)]";
  return <span className={cn("font-semibold", tone)}>{severity}</span>;
}

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "Critical"
      ? "text-signal-fail"
      : status === "Warning"
        ? "text-signal-warn"
        : "text-signal-good";
  return <span className={cn("font-semibold", tone)}>{status}</span>;
}
