import { seededHeatValue } from "@/lib/heatmapUtils";
import type {
  CostTrendPoint,
  ExecutiveKPI,
  OptimizationResults,
  PatternRow,
} from "@/types/dashboard";

export const executiveKPIs: ExecutiveKPI[] = [
  {
    id: "total-test-cost",
    title: "Total Test Cost",
    value: "$2.4M",
    change: -4.2,
    trend: "down",
    sparkline: [42, 38, 40, 36, 34, 33, 31],
  },
  {
    id: "cost-per-wafer",
    title: "Cost per Wafer",
    value: "$184",
    change: -2.8,
    trend: "down",
    sparkline: [210, 205, 198, 192, 188, 186, 184],
  },
  {
    id: "cost-per-die",
    title: "Cost per Die",
    value: "$0.018",
    change: -5.1,
    trend: "down",
    sparkline: [22, 21, 20, 19.5, 19, 18.5, 18],
  },
  {
    id: "test-time",
    title: "Test Time",
    value: "42.6s",
    change: -3.2,
    trend: "down",
    sparkline: [48, 47, 46, 45, 44, 43, 42.6],
  },
  {
    id: "yield",
    title: "Yield",
    value: "94.2%",
    change: 1.8,
    trend: "up",
    sparkline: [91, 91.5, 92, 92.8, 93.2, 93.8, 94.2],
  },
  {
    id: "roi-improvement",
    title: "ROI Improvement",
    value: "+18.4%",
    change: 6.2,
    trend: "up",
    sparkline: [10, 11, 12, 14, 15, 17, 18.4],
  },
];

export const patternAnalysisData: PatternRow[] = [
  {
    id: "PAT-001",
    testTime: 12.4,
    cost: 840,
    failRate: 0.8,
    detectPower: 92,
    roiScore: 88,
    recommendation: "Keep",
  },
  {
    id: "PAT-002",
    testTime: 18.2,
    cost: 1240,
    failRate: 2.4,
    detectPower: 78,
    roiScore: 62,
    recommendation: "Review",
  },
  {
    id: "PAT-003",
    testTime: 8.6,
    cost: 520,
    failRate: 0.3,
    detectPower: 95,
    roiScore: 94,
    recommendation: "Keep",
  },
  {
    id: "PAT-004",
    testTime: 24.8,
    cost: 1680,
    failRate: 5.1,
    detectPower: 65,
    roiScore: 38,
    recommendation: "Remove",
  },
  {
    id: "PAT-005",
    testTime: 14.1,
    cost: 960,
    failRate: 1.2,
    detectPower: 86,
    roiScore: 79,
    recommendation: "Keep",
  },
  {
    id: "PAT-006",
    testTime: 21.3,
    cost: 1420,
    failRate: 3.8,
    detectPower: 71,
    roiScore: 55,
    recommendation: "Review",
  },
  {
    id: "PAT-007",
    testTime: 9.8,
    cost: 680,
    failRate: 0.6,
    detectPower: 91,
    roiScore: 90,
    recommendation: "Keep",
  },
  {
    id: "PAT-008",
    testTime: 28.5,
    cost: 1920,
    failRate: 6.2,
    detectPower: 58,
    roiScore: 32,
    recommendation: "Remove",
  },
];

export const costTrendData: CostTrendPoint[] = [
  { day: "Mon", totalCost: 380, costPerWafer: 195 },
  { day: "Tue", totalCost: 365, costPerWafer: 190 },
  { day: "Wed", totalCost: 372, costPerWafer: 188 },
  { day: "Thu", totalCost: 358, costPerWafer: 186 },
  { day: "Fri", totalCost: 345, costPerWafer: 184 },
  { day: "Sat", totalCost: 338, costPerWafer: 182 },
  { day: "Sun", totalCost: 330, costPerWafer: 180 },
];

export const defaultOptimizationResults: OptimizationResults = {
  costReduction: 18.4,
  timeSavings: 12.6,
  projectedYield: 95.8,
  patternsReduced: 14,
  totalSavings: 284000,
};

export function generateWaferHeatData(size = 40): number[][] {
  const grid: number[][] = [];
  const center = size / 2;
  const radius = size / 2 - 0.5;

  for (let row = 0; row < size; row++) {
    const rowData: number[] = [];
    for (let col = 0; col < size; col++) {
      const dist = Math.sqrt((row - center) ** 2 + (col - center) ** 2);
      if (dist > radius) {
        rowData.push(-1);
      } else {
        const edgeFactor = dist / radius;
        const value = Math.min(1, Math.max(0, edgeFactor * 0.6 + seededHeatValue(row, col, size, size, 0, 1) * 0.5));
        rowData.push(value);
      }
    }
    grid.push(rowData);
  }
  return grid;
}
