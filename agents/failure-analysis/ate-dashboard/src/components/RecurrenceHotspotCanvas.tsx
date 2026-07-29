"use client";

import { useEffect, useRef } from "react";
import type { RecurrenceHotspot } from "@/lib/api";

export function RecurrenceHotspotCanvas({
  hotspots,
  selectedPattern,
}: {
  hotspots: RecurrenceHotspot[];
  selectedPattern?: string | null;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ratio = window.devicePixelRatio || 1;
    const width = canvas.clientWidth || 560;
    const height = 330;
    canvas.width = width * ratio;
    canvas.height = height * ratio;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(ratio, ratio);
    ctx.clearRect(0, 0, width, height);

    const rows = hotspots
      .filter((item) => !selectedPattern || item.pattern_id === selectedPattern)
      .slice(0, 80);
    const centerX = width / 2;
    const centerY = height / 2;
    const waferRadius = Math.min(width, height) * 0.42;
    ctx.beginPath();
    ctx.arc(centerX, centerY, waferRadius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(15, 23, 42, .75)";
    ctx.fill();
    ctx.strokeStyle = "rgba(148, 163, 184, .45)";
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(centerX - 18, centerY + waferRadius - 1);
    ctx.lineTo(centerX + 18, centerY + waferRadius - 1);
    ctx.strokeStyle = "#64748b";
    ctx.stroke();

    if (!rows.length) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No recurring coordinate hotspots", centerX, centerY);
      return;
    }

    const allCoordinates = rows.flatMap((row) => row.coordinates);
    const maxAbs = Math.max(
      1,
      ...allCoordinates.flatMap((point) => [Math.abs(point.x), Math.abs(point.y)]),
    );
    rows.forEach((hotspot) => {
      const x = centerX + (Number(hotspot.x || 0) / maxAbs) * waferRadius * 0.82;
      const y = centerY - (Number(hotspot.y || 0) / maxAbs) * waferRadius * 0.82;
      const radius = 7 + Math.min(24, Math.sqrt(hotspot.occurrence_count) * 4);
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      const color =
        hotspot.severity === "critical"
          ? "248, 113, 113"
          : hotspot.severity === "high"
            ? "251, 146, 60"
            : "124, 58, 237";
      gradient.addColorStop(0, `rgba(${color}, .95)`);
      gradient.addColorStop(1, `rgba(${color}, 0)`);
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#f8fafc";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(String(hotspot.occurrence_count), x, y + 3);
    });
  }, [hotspots, selectedPattern]);

  return (
    <canvas
      ref={ref}
      className="h-[330px] w-full"
      aria-label="Recurring failure wafer hotspot overlay"
    />
  );
}
