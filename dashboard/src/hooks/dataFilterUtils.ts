import {
  adjustHeatmapValues,
  adjustKPIValue,
  adjustSparkline,
  filterRowsByGlobal,
} from "@/lib/filterEngine";
import type { GlobalFilters } from "@/types/platform";

type KPILike = {
  value: string;
  sparkline: number[];
};

type SparklineLike = {
  sparkline: number[];
};

export function filterKPIArray<T extends KPILike>(kpis: T[], filters: GlobalFilters): T[] {
  return kpis.map((kpi, i) => ({
    ...kpi,
    value: adjustKPIValue(kpi.value, filters, i),
    sparkline: adjustSparkline(kpi.sparkline, filters),
  }));
}

export function filterSparklineArray<T extends SparklineLike>(
  items: T[],
  filters: GlobalFilters
): T[] {
  return items.map((item, i) => ({
    ...item,
    sparkline: adjustSparkline(item.sparkline, filters),
  }));
}

export function filterRows<T extends object>(rows: T[], filters: GlobalFilters): T[] {
  return filterRowsByGlobal(rows, filters);
}

export function filterHeatmapGrid(grid: number[][], filters: GlobalFilters): number[][] {
  return adjustHeatmapValues(grid, filters);
}

export function wrapHeatmapGenerator(
  fn: (rows?: number, cols?: number) => { value: number; row: number; col: number }[],
  filters: GlobalFilters
) {
  return (rows = 12, cols = 16) => {
    const cells = fn(rows, cols);
    const grid = Array.from({ length: rows }, (_, r) =>
      Array.from({ length: cols }, (_, c) => cells.find((x) => x.row === r && x.col === c)?.value ?? 0)
    );
    const adjusted = adjustHeatmapValues(grid, filters);
    return cells.map((cell) => ({
      ...cell,
      value: adjusted[cell.row]?.[cell.col] ?? cell.value,
    }));
  };
}

export function filterKPISections<T extends { kpis: KPILike[] }>(
  sections: T[],
  filters: GlobalFilters
): T[] {
  return sections.map((section) => ({
    ...section,
    kpis: filterKPIArray(section.kpis, filters),
  }));
}
