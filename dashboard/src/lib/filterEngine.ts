import type { GlobalFilters, FilterMeta } from "@/types/platform";

const LOTS = ["lot-4421", "lot-8832", "lot-5510", "lot-9921"];
const WAFERS = ["wafer-12", "wafer-08", "wafer-03", "wafer-21"];
const FABS = ["fab-12", "fab-18"];
const TESTERS = ["ate-01", "ate-02"];
const PRODUCTS = ["chip-x7", "chip-a3"];

export function getFilterMeta(index: number): FilterMeta {
  return {
    fab: FABS[index % FABS.length]!,
    tester: TESTERS[index % TESTERS.length]!,
    product: PRODUCTS[index % PRODUCTS.length]!,
    lot: LOTS[index % LOTS.length]!,
    wafer: WAFERS[index % WAFERS.length]!,
    dateOffset: index % 30,
  };
}

export function filterSeed(filters: GlobalFilters): number {
  const key = [
    filters.datePreset,
    filters.customDateFrom,
    filters.customDateTo,
    filters.fab,
    filters.tester,
    filters.product,
    filters.lot,
    filters.wafer,
  ].join("|");
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = (hash << 5) - hash + key.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function matchesFilter(value: string, filterValue: string): boolean {
  return filterValue === "all" || value === filterValue;
}

export function matchesGlobalFilters(meta: FilterMeta, filters: GlobalFilters): boolean {
  return (
    matchesFilter(meta.fab, filters.fab) &&
    matchesFilter(meta.tester, filters.tester) &&
    matchesFilter(meta.product, filters.product) &&
    matchesFilter(meta.lot, filters.lot) &&
    matchesFilter(meta.wafer, filters.wafer)
  );
}

export function filterRowsByGlobal<T>(
  rows: T[],
  filters: GlobalFilters
): T[] {
  return rows.filter((_, index) =>
    matchesGlobalFilters(getFilterMeta(index), filters)
  );
}

function parseNumeric(value: string): number | null {
  const cleaned = value.replace(/[^0-9.-]/g, "");
  const num = parseFloat(cleaned);
  return Number.isFinite(num) ? num : null;
}

function formatWithSuffix(original: string, num: number): string {
  if (original.includes("$")) {
    if (original.includes("M")) return `$${(num / 1_000_000).toFixed(1)}M`;
    if (original.includes("K")) return `$${Math.round(num / 1000)}K`;
    if (original.includes(".")) return `$${num.toFixed(3)}`;
    return `$${Math.round(num)}`;
  }
  if (original.includes("%")) return `${num.toFixed(1)}%`;
  if (original.includes("s")) return `${num.toFixed(1)}s`;
  if (original.includes("+")) return `+${num.toFixed(1)}%`;
  if (original.includes(",")) return Math.round(num).toLocaleString();
  return String(Math.round(num));
}

export function adjustKPIValue(value: string, filters: GlobalFilters, index = 0): string {
  if (value.includes("•") || value.includes("→")) return value;

  if (value.includes("/")) {
    const parts = value.split("/").map((part) => part.trim());
    if (parts.length === 2) {
      const left = parseNumeric(parts[0]!);
      const right = parseNumeric(parts[1]!);
      if (left !== null && right !== null) {
        const seed = filterSeed(filters);
        const factor = 0.82 + ((seed + index * 13) % 28) / 100;
        return `${Math.round(left * factor)} / ${Math.round(right * factor)}`;
      }
    }
    return value;
  }

  const num = parseNumeric(value);
  if (num === null) return value;
  const seed = filterSeed(filters);
  const factor = 0.82 + ((seed + index * 13) % 28) / 100;
  return formatWithSuffix(value, num * factor);
}

export function adjustSparkline(
  sparkline: number[],
  filters: GlobalFilters
): number[] {
  const seed = filterSeed(filters);
  const factor = 0.85 + (seed % 20) / 100;
  return sparkline.map((v, i) => Math.round(v * factor * (1 + i * 0.002) * 100) / 100);
}

export function adjustTrendPoints<T extends { value: number; value2?: number }>(
  points: T[],
  filters: GlobalFilters
): T[] {
  const factor = 0.8 + (filterSeed(filters) % 25) / 100;
  return points.map((p, i) => ({
    ...p,
    value: Math.round(p.value * factor * (1 + i * 0.01) * 10) / 10,
    value2: p.value2 !== undefined
      ? Math.round(p.value2 * factor * (1 + i * 0.01) * 10) / 10
      : undefined,
  }));
}

export function adjustHeatmapValues(
  grid: number[][],
  filters: GlobalFilters
): number[][] {
  const factor = 0.75 + (filterSeed(filters) % 30) / 100;
  return grid.map((row, ri) =>
    row.map((cell, ci) => Math.min(100, Math.round(cell * factor * (1 + (ri + ci) * 0.002))))
  );
}

export function getDateRangeLabel(filters: GlobalFilters): string {
  switch (filters.datePreset) {
    case "today":
      return "Today";
    case "yesterday":
      return "Yesterday";
    case "7d":
      return "Last 7 Days";
    case "30d":
      return "Last 30 Days";
    case "this-month":
      return "This Month";
    case "custom":
      return filters.customDateFrom && filters.customDateTo
        ? `${filters.customDateFrom} – ${filters.customDateTo}`
        : "Custom Range";
    default:
      return "Last 7 Days";
  }
}
