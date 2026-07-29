import type { WaferAnalysisResult } from "@/types/wafer";
import { DEFECT_CLASSES, LOT_TAXONOMY, lotCodeFromDefect } from "@/utils/lotTaxonomy";
import { readAssignedLot, readDefectType, readWaferName } from "@/utils/format";

export interface BatchSummaryStats {
  totalWafers: number;
  averageYield: number | null;
  highestYield: number | null;
  lowestYield: number | null;
  averageConfidence: number | null;
  totalGoodDies: number;
  totalFailDies: number;
  totalDies: number;
}

export interface LotBucket {
  lot: string;
  defect: string;
  waferCount: number;
  averageYield: number | null;
}

export interface NamedCount {
  name: string;
  count: number;
}

function numOrNull(value: unknown): number | null {
  if (value == null || Number.isNaN(Number(value))) return null;
  return Number(value);
}

export function readConfidence(result: WaferAnalysisResult): number | null {
  return numOrNull(result.classification?.confidence);
}

export function readYield(result: WaferAnalysisResult): number | null {
  return numOrNull(result.yield_summary?.yield_percent);
}

/** Prefer API LOT fields; else taxonomy from defect_type for dashboard aggregates. */
export function resolveLotCode(result: WaferAnalysisResult): string {
  const fromApi = readAssignedLot(result);
  if (fromApi && fromApi !== "—") return fromApi;
  return lotCodeFromDefect(readDefectType(result)) || "—";
}

export function computeBatchSummary(results: WaferAnalysisResult[]): BatchSummaryStats {
  if (!results.length) {
    return {
      totalWafers: 0,
      averageYield: null,
      highestYield: null,
      lowestYield: null,
      averageConfidence: null,
      totalGoodDies: 0,
      totalFailDies: 0,
      totalDies: 0,
    };
  }

  const yields = results.map(readYield).filter((v): v is number => v != null);
  const confidences = results.map(readConfidence).filter((v): v is number => v != null);

  const avg = (values: number[]) =>
    values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;

  const totalGoodDies = results.reduce(
    (sum, r) => sum + (r.yield_summary?.good_dies ?? 0),
    0,
  );
  const totalFailDies = results.reduce(
    (sum, r) => sum + (r.yield_summary?.fail_dies ?? 0),
    0,
  );
  const totalDies = results.reduce(
    (sum, r) =>
      sum +
      (r.yield_summary?.total_dies ??
        (r.yield_summary?.good_dies ?? 0) + (r.yield_summary?.fail_dies ?? 0)),
    0,
  );

  return {
    totalWafers: results.length,
    averageYield: avg(yields),
    highestYield: yields.length ? Math.max(...yields) : null,
    lowestYield: yields.length ? Math.min(...yields) : null,
    averageConfidence: avg(confidences),
    totalGoodDies,
    totalFailDies,
    totalDies,
  };
}

/** Session wafers belonging to a LOT code (API field or defect taxonomy fallback). */
export function wafersInLot(
  results: WaferAnalysisResult[],
  lotCode: string,
): IndexedWafer[] {
  const target = lotCode.toUpperCase();
  return results
    .map((wafer, index) => ({ wafer, index }))
    .filter(({ wafer }) => resolveLotCode(wafer).toUpperCase() === target);
}

export function countWafersInLot(
  results: WaferAnalysisResult[],
  lotCode: string,
): number {
  return wafersInLot(results, lotCode).length;
}

export function computeLotSummary(results: WaferAnalysisResult[]): LotBucket[] {
  return LOT_TAXONOMY.map(({ lot, defect }) => {
    const members = results.filter((r) => {
      const code = resolveLotCode(r);
      const defectType = readDefectType(r);
      return (
        code.toUpperCase() === lot ||
        defectType.toLowerCase() === defect.toLowerCase()
      );
    });
    const yields = members.map(readYield).filter((v): v is number => v != null);
    return {
      lot,
      defect,
      waferCount: members.length,
      averageYield: yields.length
        ? yields.reduce((a, b) => a + b, 0) / yields.length
        : null,
    };
  });
}

export function computeDefectDistribution(
  results: WaferAnalysisResult[],
): NamedCount[] {
  return DEFECT_CLASSES.map((name) => ({
    name,
    count: results.filter(
      (r) => readDefectType(r).toLowerCase() === name.toLowerCase(),
    ).length,
  }));
}

export function computeLotDistribution(
  results: WaferAnalysisResult[],
): NamedCount[] {
  return LOT_TAXONOMY.map(({ lot }) => ({
    name: lot,
    count: results.filter((r) => resolveLotCode(r).toUpperCase() === lot).length,
  }));
}

/** Fixed histogram bins for yield % (0–100). */
export function computeYieldHistogram(
  results: WaferAnalysisResult[],
  binSize = 10,
): NamedCount[] {
  const bins: NamedCount[] = [];
  for (let start = 0; start < 100; start += binSize) {
    const end = start + binSize;
    const label = `${start}–${end}%`;
    const count = results.filter((r) => {
      const y = readYield(r);
      if (y == null) return false;
      return end === 100 ? y >= start && y <= end : y >= start && y < end;
    }).length;
    bins.push({ name: label, count });
  }
  return bins;
}

/** Fixed histogram bins for confidence % (0–100). */
export function computeConfidenceHistogram(
  results: WaferAnalysisResult[],
  binSize = 10,
): NamedCount[] {
  const bins: NamedCount[] = [];
  for (let start = 0; start < 100; start += binSize) {
    const end = start + binSize;
    const label = `${start}–${end}%`;
    const count = results.filter((r) => {
      const c = readConfidence(r);
      if (c == null) return false;
      return end === 100 ? c >= start && c <= end : c >= start && c < end;
    }).length;
    bins.push({ name: label, count });
  }
  return bins;
}

export type WaferSortKey =
  | "yield"
  | "confidence"
  | "lot"
  | "defect"
  | "fail_dies"
  | "good_dies"
  | "name";

export interface WaferFilters {
  search: string;
  defectFilter: string; // "All" or defect class
  lotFilter: string; // "All" or LOT_n
  yieldMin: number | null;
  yieldMax: number | null;
  confidenceMin: number | null;
  sortKey: WaferSortKey;
  sortAsc: boolean;
}

export const DEFAULT_WAFER_FILTERS: WaferFilters = {
  search: "",
  defectFilter: "All",
  lotFilter: "All",
  yieldMin: null,
  yieldMax: null,
  confidenceMin: null,
  sortKey: "name",
  sortAsc: true,
};

export interface IndexedWafer {
  index: number;
  wafer: WaferAnalysisResult;
}

export function filterAndSortWafers(
  results: WaferAnalysisResult[],
  filters: WaferFilters,
): IndexedWafer[] {
  const q = filters.search.trim().toLowerCase();

  let rows: IndexedWafer[] = results.map((wafer, index) => ({ wafer, index }));

  rows = rows.filter(({ wafer }) => {
    const name = readWaferName(wafer).toLowerCase();
    const defect = readDefectType(wafer);
    const lot = resolveLotCode(wafer);
    const yieldPct = readYield(wafer);
    const confidence = readConfidence(wafer);

    if (q) {
      const hay = `${name} ${defect} ${lot} ${yieldPct ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (filters.defectFilter !== "All" && defect !== filters.defectFilter) {
      return false;
    }
    if (
      filters.lotFilter !== "All" &&
      lot.toUpperCase() !== filters.lotFilter.toUpperCase()
    ) {
      return false;
    }
    if (filters.yieldMin != null && (yieldPct == null || yieldPct < filters.yieldMin)) {
      return false;
    }
    if (filters.yieldMax != null && (yieldPct == null || yieldPct > filters.yieldMax)) {
      return false;
    }
    if (
      filters.confidenceMin != null &&
      (confidence == null || confidence < filters.confidenceMin)
    ) {
      return false;
    }
    return true;
  });

  rows.sort((a, b) => {
    const left = sortValue(a.wafer, filters.sortKey);
    const right = sortValue(b.wafer, filters.sortKey);
    if (left === right) return 0;
    if (left > right) return filters.sortAsc ? 1 : -1;
    return filters.sortAsc ? -1 : 1;
  });

  return rows;
}

function sortValue(wafer: WaferAnalysisResult, key: WaferSortKey): string | number {
  switch (key) {
    case "yield":
      return readYield(wafer) ?? -1;
    case "confidence":
      return readConfidence(wafer) ?? -1;
    case "lot":
      return resolveLotCode(wafer);
    case "defect":
      return readDefectType(wafer);
    case "fail_dies":
      return wafer.yield_summary?.fail_dies ?? -1;
    case "good_dies":
      return wafer.yield_summary?.good_dies ?? -1;
    case "name":
    default:
      return readWaferName(wafer);
  }
}

export interface ExportRow {
  wafer_name: string;
  defect: string;
  lot: string;
  yield: number | null;
  confidence: number | null;
  good_dies: number | null;
  fail_dies: number | null;
  total_dies: number | null;
}

export function buildExportRows(results: WaferAnalysisResult[]): ExportRow[] {
  return results.map((r) => ({
    wafer_name: readWaferName(r),
    defect: readDefectType(r),
    lot: resolveLotCode(r),
    yield: readYield(r),
    confidence: readConfidence(r),
    good_dies: r.yield_summary?.good_dies ?? null,
    fail_dies: r.yield_summary?.fail_dies ?? null,
    total_dies: r.yield_summary?.total_dies ?? null,
  }));
}
