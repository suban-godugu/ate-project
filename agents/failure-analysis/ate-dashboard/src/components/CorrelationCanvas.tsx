"use client";

import { useEffect, useRef } from "react";
import type { CorrelationMetric } from "@/lib/api";

export function CorrelationCanvas({
  rows,
  selected,
}: {
  rows: CorrelationMetric[];
  selected?: CorrelationMetric | null;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = 300;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "rgba(4,8,20,.5)";
    ctx.fillRect(0, 0, width, height);

    const patterns = [...new Set(rows.slice(0, 12).map((row) => row.pattern_id))];
    const faults = [...new Set(rows.slice(0, 12).map((row) => row.fault_type))];
    const left = new Map(patterns.map((value, index) => [value, 32 + ((index + 1) * 236) / (patterns.length + 1)]));
    const right = new Map(faults.map((value, index) => [value, 32 + ((index + 1) * 236) / (faults.length + 1)]));
    rows.slice(0, 12).forEach((row) => {
      const y1 = left.get(row.pattern_id);
      const y2 = right.get(row.fault_type);
      if (y1 === undefined || y2 === undefined) return;
      ctx.beginPath();
      ctx.moveTo(155, y1);
      ctx.bezierCurveTo(width * 0.42, y1, width * 0.58, y2, width - 155, y2);
      ctx.strokeStyle = row.correlation_coefficient < 0 ? "rgba(248,113,113,.65)" : "rgba(56,189,248,.65)";
      ctx.lineWidth = Math.max(1, Math.abs(row.correlation_coefficient) * 6);
      ctx.stroke();
    });
    ctx.font = "11px sans-serif";
    patterns.forEach((label) => {
      const y = left.get(label)!;
      ctx.fillStyle = "#a78bfa";
      ctx.beginPath();
      ctx.arc(145, y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#cbd5e1";
      ctx.textAlign = "right";
      ctx.fillText(label.slice(0, 18), 134, y + 4);
    });
    faults.forEach((label) => {
      const y = right.get(label)!;
      ctx.fillStyle = "#38bdf8";
      ctx.beginPath();
      ctx.arc(width - 145, y, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#cbd5e1";
      ctx.textAlign = "left";
      ctx.fillText(label.slice(0, 22), width - 134, y + 4);
    });

    const coordinates = selected?.hotspot_location.coordinates || [];
    if (coordinates.length) {
      const cx = width / 2;
      const cy = 150;
      const radius = 82;
      ctx.strokeStyle = "rgba(255,255,255,.16)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.stroke();
      const max = Math.max(1, ...coordinates.flatMap((point) => [Math.abs(point.x), Math.abs(point.y)]));
      coordinates.forEach((point) => {
        ctx.fillStyle = "rgba(249,115,22,.72)";
        ctx.beginPath();
        ctx.arc(cx + (point.x / max) * radius * 0.85, cy + (point.y / max) * radius * 0.85, 3, 0, Math.PI * 2);
        ctx.fill();
      });
    }
  }, [rows, selected]);

  return (
    <canvas
      ref={ref}
      className="h-[300px] w-full rounded-xl border border-white/5"
      aria-label="Pattern relationship graph and selected wafer overlay"
    />
  );
}
