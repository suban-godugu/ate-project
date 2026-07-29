/** Deterministic 0–1 value from grid coordinates (SSR-safe, no hydration mismatch). */
export function seededHeatValue(
  row: number,
  col: number,
  rows: number,
  cols: number,
  edgeWeight = 0.4,
  seedWeight = 0.6
): number {
  const centerDist = Math.sqrt((row - rows / 2) ** 2 + (col - cols / 2) ** 2);
  const edgeFactor = centerDist / (rows / 2);
  const seed = (((row * 73856093) ^ (col * 19349663)) >>> 0) % 1000 / 1000;
  return Math.min(1, Math.max(0, edgeFactor * edgeWeight + seed * seedWeight));
}

export function generateGridHeatmap(
  rows: number,
  cols: number,
  edgeWeight = 0.4,
  seedWeight = 0.6
): { value: number; row: number; col: number }[] {
  const data: { value: number; row: number; col: number }[] = [];
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) {
      data.push({
        value: seededHeatValue(row, col, rows, cols, edgeWeight, seedWeight),
        row,
        col,
      });
    }
  }
  return data;
}
