import type { SortKey, WaferAnalysisResult, WaferFilters } from "@/wafervision/types";
import { LOT_TAXONOMY, defectToLot } from "@/wafervision/utils/lotTaxonomy";
import { displayWaferName } from "@/wafervision/utils/format";

export function resolveLot(result: WaferAnalysisResult): string {
  return (
    result.assigned_lot ||
    result.lot ||
    result.classification?.assigned_lot ||
    result.classification?.lot ||
    defectToLot(result.classification?.defect_type) ||
    "—"
  );
}

export function resolveDefect(result: WaferAnalysisResult): string {
  return result.classification?.defect_type || "—";
}

export function resolveYield(result: WaferAnalysisResult): number | null {
  const v = result.yield_summary?.yield_percent;
  return v == null || Number.isNaN(Number(v)) ? null : Number(v);
}

export function resolveConfidence(result: WaferAnalysisResult): number | null {
  const v = result.classification?.confidence;
  return v == null || Number.isNaN(Number(v)) ? null : Number(v);
}

export function resolveGoodDies(result: WaferAnalysisResult): number {
  return Number(result.yield_summary?.good_dies ?? 0);
}

export function resolveFailDies(result: WaferAnalysisResult): number {
  return Number(result.yield_summary?.fail_dies ?? 0);
}

export function resolveTotalDies(result: WaferAnalysisResult): number {
  const total = result.yield_summary?.total_dies;
  if (total != null && !Number.isNaN(Number(total))) return Number(total);
  return resolveGoodDies(result) + resolveFailDies(result);
}

export interface IndexedWafer {
  index: number;
  result: WaferAnalysisResult;
}

function sortValue(result: WaferAnalysisResult, key: SortKey): string | number {
  switch (key) {
    case "name":
      return displayWaferName(result);
    case "yield":
      return resolveYield(result) ?? -1;
    case "confidence":
      return resolveConfidence(result) ?? -1;
    case "lot":
      return resolveLot(result);
    case "defect":
      return resolveDefect(result);
    case "failDies":
      return resolveFailDies(result);
    case "goodDies":
      return resolveGoodDies(result);
  }
}

export function filterAndSortWafers(
  results: WaferAnalysisResult[],
  filters: WaferFilters
): IndexedWafer[] {
  const q = filters.search.trim().toLowerCase();
  let list = results.map((result, index) => ({ index, result }));

  list = list.filter(({ result }) => {
    const name = displayWaferName(result);
    const defect = resolveDefect(result);
    const lot = resolveLot(result);
    const yieldVal = resolveYield(result);
    const conf = resolveConfidence(result);

    if (q) {
      const hay = `${name} ${defect} ${lot} ${yieldVal ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (filters.defectFilter !== "All" && defect !== filters.defectFilter) return false;
    if (filters.lotFilter !== "All" && lot.toUpperCase() !== filters.lotFilter.toUpperCase()) {
      return false;
    }
    if (filters.yieldMin != null) {
      if (yieldVal == null || yieldVal < filters.yieldMin) return false;
    }
    if (filters.yieldMax != null) {
      if (yieldVal == null || yieldVal > filters.yieldMax) return false;
    }
    if (filters.confidenceMin != null) {
      if (conf == null || conf < filters.confidenceMin) return false;
    }
    return true;
  });

  list.sort((a, b) => {
    const av = sortValue(a.result, filters.sortKey);
    const bv = sortValue(b.result, filters.sortKey);
    let cmp = 0;
    if (typeof av === "number" && typeof bv === "number") cmp = av - bv;
    else cmp = String(av).localeCompare(String(bv));
    return filters.sortAsc ? cmp : -cmp;
  });

  return list;
}

export function wafersInLot(results: WaferAnalysisResult[], lot: string): IndexedWafer[] {
  return results
    .map((result, index) => ({ index, result }))
    .filter(({ result }) => resolveLot(result).toUpperCase() === lot.toUpperCase());
}

export function batchSummary(results: WaferAnalysisResult[]) {
  const yields = results.map(resolveYield).filter((v): v is number => v != null);
  const confs = results.map(resolveConfidence).filter((v): v is number => v != null);
  const good = results.reduce((s, r) => s + resolveGoodDies(r), 0);
  const fail = results.reduce((s, r) => s + resolveFailDies(r), 0);
  const total = results.reduce((s, r) => s + resolveTotalDies(r), 0);
  const avg = (arr: number[]) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null);
  return {
    totalWafers: results.length,
    averageYield: avg(yields),
    highestYield: yields.length ? Math.max(...yields) : null,
    lowestYield: yields.length ? Math.min(...yields) : null,
    averageConfidence: avg(confs),
    totalGoodDies: good,
    totalFailDies: fail,
    totalDies: total,
  };
}

export function lotSummary(results: WaferAnalysisResult[]) {
  return LOT_TAXONOMY.map(({ lot, defect }) => {
    const members = results.filter((r) => {
      const resolved = resolveLot(r).toUpperCase();
      const defectMatch =
        resolveDefect(r).toLowerCase() === defect.toLowerCase();
      return resolved === lot.toUpperCase() || defectMatch;
    });
    const yields = members.map(resolveYield).filter((v): v is number => v != null);
    const avgYield = yields.length
      ? yields.reduce((a, b) => a + b, 0) / yields.length
      : null;
    return { lot, defect, count: members.length, avgYield };
  });
}

export function defectDistribution(results: WaferAnalysisResult[]) {
  return LOT_TAXONOMY.map(({ defect }) => ({
    name: defect,
    count: results.filter(
      (r) => resolveDefect(r).toLowerCase() === defect.toLowerCase()
    ).length,
  }));
}

export function lotDistribution(results: WaferAnalysisResult[]) {
  return LOT_TAXONOMY.map(({ lot }) => ({
    name: lot,
    count: results.filter((r) => resolveLot(r).toUpperCase() === lot).length,
  }));
}

function bin10(values: number[]) {
  const bins = Array.from({ length: 10 }, (_, i) => ({
    name: `${i * 10}–${i * 10 + 10}%`,
    count: 0,
  }));
  for (const v of values) {
    if (v >= 100) bins[9].count += 1;
    else if (v >= 0) bins[Math.min(9, Math.floor(v / 10))].count += 1;
  }
  return bins;
}

export function yieldDistribution(results: WaferAnalysisResult[]) {
  return bin10(results.map(resolveYield).filter((v): v is number => v != null));
}

export function confidenceDistribution(results: WaferAnalysisResult[]) {
  return bin10(
    results.map(resolveConfidence).filter((v): v is number => v != null)
  );
}

export function exportRows(results: WaferAnalysisResult[]) {
  return results.map((r) => ({
    waferName: displayWaferName(r),
    defect: resolveDefect(r),
    lot: resolveLot(r),
    yield: resolveYield(r),
    confidence: resolveConfidence(r),
    goodDies: resolveGoodDies(r),
    failDies: resolveFailDies(r),
    totalDies: resolveTotalDies(r),
  }));
}
