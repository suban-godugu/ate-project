import type { DashboardTabData } from "./dashboard";

/** Overlay live chart series from API; in live mode omit mock charts when API returns empty arrays. */
export function mergeLiveCharts<T extends Record<string, unknown>>(
  base: T,
  api: DashboardTabData | undefined,
  chartKeys: (keyof T)[],
  live: boolean
): T {
  if (!live) return base;
  if (!api?.charts) {
    const cleared = { ...base };
    for (const key of chartKeys) {
      const val = base[key];
      if (Array.isArray(val)) {
        (cleared as Record<string, unknown>)[key as string] = [];
      }
    }
    return cleared;
  }
  const merged = { ...base };
  for (const key of chartKeys) {
    const liveVal = api.charts[key as string];
    if (liveVal !== undefined) {
      (merged as Record<string, unknown>)[key as string] = liveVal;
    }
  }
  return merged;
}

export function heatmapFromCells(
  cells: { row: number; col: number; value: number }[] | undefined,
  rows: number,
  cols: number
): { value: number; row: number; col: number }[] {
  if (!cells?.length) return [];
  return cells.map((c) => ({
    row: c.row % rows,
    col: c.col % cols,
    value: c.value,
  }));
}

export function gridFromApi(
  grid: number[][] | undefined,
  rows: number,
  cols: number
): number[][] {
  if (!grid?.length) {
    return Array.from({ length: rows }, () => Array(cols).fill(0));
  }
  return Array.from({ length: rows }, (_, rowIndex) => {
    const sourceRow = grid[rowIndex];
    if (!Array.isArray(sourceRow)) {
      return Array(cols).fill(0);
    }
    return Array.from({ length: cols }, (_, colIndex) => sourceRow[colIndex] ?? 0);
  });
}
