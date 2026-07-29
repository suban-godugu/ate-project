"use client";

import { useEffect, useRef } from "react";
import type { FailureRateMetric } from "@/lib/api";

export function FailureHeatmapCanvas({ metrics }: { metrics: FailureRateMetric[] }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 640;
    const height = 280;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);

    const waferRows = metrics.filter((row) => row.aggregation_level === "wafer").slice(0, 64);
    if (!waferRows.length) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px sans-serif";
      ctx.fillText("No wafer-level failure rates for heatmap", 16, 24);
      return;
    }

    const cols = Math.ceil(Math.sqrt(waferRows.length));
    const rows = Math.ceil(waferRows.length / cols);
    const cellW = (width - 24) / cols;
    const cellH = (height - 24) / rows;
    // Scale against the observed maximum: real fleets sit well under the 20% ceiling,
    // which otherwise renders every cell as an invisible flat wash.
    const peak = Math.max(...waferRows.map((metric) => metric.failure_percentage), 0.0001);
    waferRows.forEach((metric, index) => {
      const x = 12 + (index % cols) * cellW;
      const y = 12 + Math.floor(index / cols) * cellH;
      const intensity = Math.min(1, metric.failure_percentage / peak);
      ctx.fillStyle = `rgba(124, 58, 237, ${0.15 + intensity * 0.85})`;
      ctx.fillRect(x + 2, y + 2, cellW - 4, cellH - 4);
      ctx.fillStyle = "#e8edf5";
      ctx.font = "10px sans-serif";
      ctx.fillText(
        `${metric.failure_percentage.toFixed(metric.failure_percentage < 1 ? 2 : 1)}%`,
        x + 6,
        y + 16,
      );
    });
  }, [metrics]);

  return <canvas ref={ref} className="h-[280px] w-full" aria-label="Failure rate heatmap" />;
}
