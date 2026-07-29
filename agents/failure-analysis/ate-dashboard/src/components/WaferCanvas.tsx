"use client";

import { useEffect, useRef } from "react";

type Point = { x?: number | null; y?: number | null; severity?: string };
type CoordPoint = { x: number; y: number; severity?: string };

export function WaferCanvas({ points }: { points: Point[] }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = 280;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);
    const radius = Math.min(width, height) / 2 - 14;
    const cx = width / 2;
    const cy = height / 2;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(45, 55, 72, 0.55)";
    ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.18)";
    ctx.stroke();
    const valid: CoordPoint[] = [];
    for (const point of points) {
      if (typeof point.x === "number" && typeof point.y === "number") {
        valid.push({ x: point.x, y: point.y, severity: point.severity });
      }
    }
    const max = Math.max(1, ...valid.flatMap((p) => [Math.abs(p.x), Math.abs(p.y)]));
    valid.forEach((point) => {
      const px = cx + (point.x / max) * radius * 0.9;
      const py = cy - (point.y / max) * radius * 0.9;
      ctx.beginPath();
      ctx.arc(px, py, 4, 0, Math.PI * 2);
      ctx.fillStyle =
        point.severity === "critical"
          ? "#f87171"
          : point.severity === "high"
            ? "#fb923c"
            : "#7c3aed";
      ctx.fill();
    });
    if (!valid.length) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No coordinate-bearing occurrences", cx, cy);
    }
  }, [points]);

  return <canvas ref={ref} className="h-[280px] w-full" aria-label="Wafer pattern map" />;
}
