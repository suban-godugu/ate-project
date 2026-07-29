"use client";

import { useEffect, useRef } from "react";
import type { DieCluster, DieHotspot, DieSummary } from "@/lib/api";

type OverlayMode = "wafer" | "heatmap" | "clusters";

function severityRgb(severity: string): string {
  if (severity === "critical") return "248,113,113";
  if (severity === "high") return "251,146,60";
  if (severity === "medium") return "124,58,237";
  return "56,189,248";
}

export function DieMapCanvas({
  dies,
  hotspots,
  clusters,
  selected,
  mode = "wafer",
}: {
  dies: DieSummary[];
  hotspots: DieHotspot[];
  clusters: DieCluster[];
  selected?: DieSummary | null;
  mode?: OverlayMode;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const draw = () => {
      const ratio = window.devicePixelRatio || 1;
      const width = Math.max(1, container.clientWidth);
      const height = Math.max(1, container.clientHeight || 360);
      canvas.width = Math.floor(width * ratio);
      canvas.height = Math.floor(height * ratio);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      ctx.clearRect(0, 0, width, height);

      ctx.fillStyle = "rgba(4,8,20,.55)";
      ctx.fillRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;
      const waferRadius = Math.min(width, height) * 0.42;

      ctx.beginPath();
      ctx.arc(cx, cy, waferRadius, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(15,23,42,.82)";
      ctx.fill();
      ctx.strokeStyle = "rgba(148,163,184,.4)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(cx - 20, cy + waferRadius - 1);
      ctx.lineTo(cx + 20, cy + waferRadius - 1);
      ctx.strokeStyle = "#64748b";
      ctx.stroke();

      const points = dies.filter(
        (die) => typeof die.x === "number" && typeof die.y === "number",
      ) as Array<DieSummary & { x: number; y: number }>;

      const maxAbs = Math.max(
        1,
        ...points.flatMap((die) => [Math.abs(die.x), Math.abs(die.y)]),
        ...hotspots.flatMap((row) => [Math.abs(row.center_x), Math.abs(row.center_y)]),
        ...clusters.flatMap((row) => [Math.abs(row.centroid_x), Math.abs(row.centroid_y)]),
      );

      const toScreen = (x: number, y: number) => ({
        px: cx + (x / maxAbs) * waferRadius * 0.86,
        py: cy - (y / maxAbs) * waferRadius * 0.86,
      });

      if (mode === "heatmap" || mode === "wafer") {
        points.forEach((die) => {
          const { px, py } = toScreen(die.x, die.y);
          const intensity = Math.min(1, Math.max(0.08, die.failure_density));
          const rgb = severityRgb(die.severity);
          if (mode === "heatmap") {
            const radius = 6 + intensity * 16;
            const gradient = ctx.createRadialGradient(px, py, 0, px, py, radius);
            gradient.addColorStop(0, `rgba(${rgb},${0.35 + intensity * 0.55})`);
            gradient.addColorStop(1, `rgba(${rgb},0)`);
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(px, py, radius, 0, Math.PI * 2);
            ctx.fill();
          } else {
            ctx.beginPath();
            ctx.arc(px, py, die.is_failing ? 3.8 : 2.4, 0, Math.PI * 2);
            ctx.fillStyle = die.is_failing
              ? `rgba(${rgb},${0.55 + intensity * 0.4})`
              : "rgba(148,163,184,.35)";
            ctx.fill();
          }
        });
      }

      if (mode === "clusters" || mode === "wafer") {
        clusters.slice(0, 40).forEach((cluster, index) => {
          const { px, py } = toScreen(cluster.centroid_x, cluster.centroid_y);
          const radius =
            10 + Math.min(28, Math.sqrt(Math.max(1, cluster.die_count)) * 5);
          const hue = (index * 47) % 360;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.strokeStyle = `hsla(${hue}, 80%, 70%, .75)`;
          ctx.lineWidth = 2;
          ctx.stroke();
          ctx.fillStyle = `hsla(${hue}, 70%, 55%, .12)`;
          ctx.fill();
          cluster.coordinates.slice(0, 48).forEach((point) => {
            const screen = toScreen(point.x, point.y);
            ctx.beginPath();
            ctx.arc(screen.px, screen.py, 2.2, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${hue}, 80%, 70%, .9)`;
            ctx.fill();
          });
        });
      }

      if (mode !== "clusters") {
        hotspots.slice(0, 40).forEach((hotspot) => {
          const { px, py } = toScreen(hotspot.center_x, hotspot.center_y);
          const radius =
            8 + Math.min(26, Math.sqrt(Math.max(1, hotspot.die_count)) * 4);
          const rgb = severityRgb(hotspot.severity);
          const gradient = ctx.createRadialGradient(px, py, 0, px, py, radius);
          gradient.addColorStop(0, `rgba(${rgb},.85)`);
          gradient.addColorStop(1, `rgba(${rgb},0)`);
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fill();
          ctx.strokeStyle = `rgba(${rgb},.7)`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.arc(px, py, Math.max(6, hotspot.radius / maxAbs * waferRadius * 0.35), 0, Math.PI * 2);
          ctx.stroke();
        });
      }

      if (selected && typeof selected.x === "number" && typeof selected.y === "number") {
        const { px, py } = toScreen(selected.x, selected.y);
        ctx.strokeStyle = "#f8fafc";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(px, py, 8, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = "#f8fafc";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(selected.die_id.slice(0, 16), px, py - 12);
      }

      if (!points.length && !hotspots.length && !clusters.length) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("No die coordinates for wafer map", cx, cy);
      }

      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(
        `${mode.toUpperCase()} · ${points.length} dies · ${hotspots.length} hotspots · ${clusters.length} clusters`,
        12,
        height - 12,
      );
    };

    draw();
    const observer = new ResizeObserver(() => draw());
    observer.observe(container);
    window.addEventListener("resize", draw);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", draw);
    };
  }, [dies, hotspots, clusters, selected, mode]);

  return (
    <div ref={containerRef} className="h-[360px] w-full">
      <canvas
        ref={canvasRef}
        className="h-full w-full rounded-xl border border-white/5"
        aria-label="Die-level wafer map density heatmap and cluster overlay"
      />
    </div>
  );
}
