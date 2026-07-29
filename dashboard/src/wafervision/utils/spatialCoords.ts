import type { ClusterRecord, ZoneRecord, SpatialAnalysis } from "@/wafervision/types";

/** Normalize Spatial agent cluster → UI highlight coords in 224 space. */
export function clusterHighlight(cluster: ClusterRecord | null | undefined): {
  bbox: [number, number, number, number] | null;
  centroid: [number, number] | null;
} {
  if (!cluster) return { bbox: null, centroid: null };

  let bbox: [number, number, number, number] | null = cluster.bbox ?? null;
  const box = cluster.bounding_box;
  if (!bbox && box && box.x1 != null && box.y1 != null && box.x2 != null && box.y2 != null) {
    bbox = [Number(box.x1), Number(box.y1), Number(box.x2), Number(box.y2)];
  }

  let centroid: [number, number] | null = cluster.centroid ?? null;
  if (!centroid && cluster.center_x != null && cluster.center_y != null) {
    centroid = [Number(cluster.center_x), Number(cluster.center_y)];
  }

  return { bbox, centroid };
}

export function clusterFail(c: ClusterRecord): number | string {
  return c.fail_dies ?? c.fail ?? "—";
}

export function clusterGood(c: ClusterRecord): number | string {
  return c.good_dies ?? c.good ?? "—";
}

export function clusterTotal(c: ClusterRecord): number | string {
  return c.total_dies ?? c.total ?? "—";
}

export function clusterFailPct(c: ClusterRecord): number | string {
  return c.cluster_fail_percent ?? c.fail_percent ?? "—";
}

export function clusterContrib(c: ClusterRecord): number | string {
  return c.contribution_percent ?? c.contrib_percent ?? "—";
}

export function clusterDensity(c: ClusterRecord): number | string {
  return c.cluster_density ?? c.density ?? "—";
}

/** Normalize zone_analysis which may be `{ zones }` or a bare array. */
export function listZones(spatial: SpatialAnalysis | null | undefined): ZoneRecord[] {
  const za = spatial?.zone_analysis;
  if (!za) return [];
  if (Array.isArray(za)) return za;
  return za.zones ?? [];
}

export function zonePolygon(zone: ZoneRecord | null | undefined): [number, number][] | null {
  if (!zone) return null;
  if (zone.polygon && zone.polygon.length > 1) return zone.polygon;

  const boundary = zone.zone_boundary;
  if (!boundary || boundary.length < 2) return null;

  return boundary.map((pt) => {
    if (Array.isArray(pt)) return [Number(pt[0]), Number(pt[1])] as [number, number];
    return [Number(pt.x), Number(pt.y)] as [number, number];
  });
}

export function zoneGood(z: ZoneRecord): number | string {
  return z.good_dies ?? z.good ?? "—";
}

export function zoneFail(z: ZoneRecord): number | string {
  return z.fail_dies ?? z.fail ?? "—";
}

export function zoneTotal(z: ZoneRecord): number | string {
  return z.total_dies ?? z.total ?? "—";
}

export function zoneDensity(z: ZoneRecord): number | string {
  return z.defect_density ?? z.density ?? "—";
}
