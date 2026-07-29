"use client";

import { useEffect, useRef } from "react";
import type { WaferHotspot, WaferRadialDistribution, WaferSummary } from "@/lib/api";

type OverlayMode = "wafer" | "heatmap" | "hotspots";

function severityRgb(severity: string): string {
  if (severity === "critical") return "248,113,113";
  if (severity === "high") return "251,146,60";
  if (severity === "medium") return "124,58,237";
  return "56,189,248";
}

type DensityCell = {
  x: number;
  y: number;
  die_count: number;
  failure_count: number;
  density: number;
};

export function WaferMapCanvas({
  wafers,
  hotspots,
  selected,
  radialDistribution,
  mode = "wafer",
}: {
  wafers: WaferSummary[];
  hotspots: WaferHotspot[];
  selected?: WaferSummary | null;
  radialDistribution?: WaferRadialDistribution | null;
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

      const activeHotspots = selected
        ? hotspots.filter(
            (row) => row.lot_id === selected.lot_id && row.wafer_id === selected.wafer_id,
          )
        : hotspots;

      const gridCells: DensityCell[] = [];
      activeHotspots.forEach((hotspot) => {
        (hotspot.density_grid || []).forEach((cell) => gridCells.push(cell));
      });

      const maxAbs = Math.max(
        1,
        ...gridCells.flatMap((cell) => [Math.abs(cell.x), Math.abs(cell.y)]),
        ...activeHotspots.flatMap((row) => [
          Math.abs(row.center_x || 0),
          Math.abs(row.center_y || 0),
        ]),
      );

      const toScreen = (x: number, y: number) => ({
        px: cx + (x / maxAbs) * waferRadius * 0.86,
        py: cy - (y / maxAbs) * waferRadius * 0.86,
      });

      const radial =
        radialDistribution ||
        selected?.radial_distribution ||
        null;

      if ((mode === "wafer" || mode === "heatmap") && radial?.profile?.length) {
        const bins = radial.profile.length;
        radial.profile.forEach((value, index) => {
          const inner = (index / bins) * waferRadius;
          const outer = ((index + 1) / bins) * waferRadius;
          const intensity = Math.min(1, Math.max(0.05, value));
          ctx.beginPath();
          ctx.arc(cx, cy, outer, 0, Math.PI * 2);
          ctx.arc(cx, cy, inner, 0, Math.PI * 2, true);
          ctx.closePath();
          ctx.fillStyle = `rgba(251,146,60,${0.08 + intensity * 0.55})`;
          ctx.fill();
        });
      }

      if (mode === "heatmap" || mode === "wafer") {
        gridCells.forEach((cell) => {
          const { px, py } = toScreen(cell.x, cell.y);
          const intensity = Math.min(1, Math.max(0.08, cell.density));
          const radius = 5 + intensity * 14;
          const gradient = ctx.createRadialGradient(px, py, 0, px, py, radius);
          gradient.addColorStop(0, `rgba(167,139,250,${0.35 + intensity * 0.55})`);
          gradient.addColorStop(1, "rgba(167,139,250,0)");
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(px, py, radius, 0, Math.PI * 2);
          ctx.fill();
        });
      }

      if (selected) {
        const edgeRate = selected.edge_failure_rate;
        const centerRate = selected.center_failure_rate;
        const edgeRadius = waferRadius * 0.86;
        const centerRadius = waferRadius * 0.42;
        ctx.beginPath();
        ctx.arc(cx, cy, edgeRadius, 0, Math.PI * 2);
        ctx.arc(cx, cy, centerRadius, 0, Math.PI * 2, true);
        ctx.closePath();
        ctx.strokeStyle = `rgba(251,146,60,${0.25 + edgeRate * 0.65})`;
        ctx.lineWidth = 3;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(cx, cy, centerRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(56,189,248,${0.25 + centerRate * 0.65})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      if (mode === "hotspots" || mode === "wafer") {
        activeHotspots.slice(0, 40).forEach((hotspot) => {
          if (typeof hotspot.center_x !== "number" || typeof hotspot.center_y !== "number") {
            return;
          }
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
          ctx.arc(
            px,
            py,
            Math.max(6, (hotspot.radius / maxAbs) * waferRadius * 0.35),
            0,
            Math.PI * 2,
          );
          ctx.stroke();
        });
      }

      if (selected) {
        ctx.strokeStyle = "#f8fafc";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(cx, cy, waferRadius * 0.9, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = "#f8fafc";
        ctx.font = "11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(
          `${selected.lot_id} · ${selected.wafer_id}`.slice(0, 28),
          cx,
          cy - waferRadius - 8,
        );
      }

      const hasSpatialData =
        activeHotspots.length > 0 || gridCells.length > 0 || Boolean(radial?.profile?.length);
      if (!hasSpatialData) {
        ctx.fillStyle = "#94a3b8";
        ctx.font = "12px sans-serif";
        ctx.textAlign = "center";
        const message = wafers.length
          ? "No die coordinates in the ingested records"
          : "No wafer spatial data for map overlay";
        ctx.fillText(message, cx, cy - 8);
        if (wafers.length) {
          ctx.font = "10px sans-serif";
          ctx.fillText(
            "hotspot / density overlays need die X-Y positions",
            cx,
            cy + 10,
          );
        }
      }

      ctx.fillStyle = "#94a3b8";
      ctx.font = "10px sans-serif";
      ctx.textAlign = "left";
      ctx.fillText(
        `${mode.toUpperCase()} · ${wafers.length} wafers · ${activeHotspots.length} hotspots · ${gridCells.length} grid cells`,
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
  }, [wafers, hotspots, selected, radialDistribution, mode]);

  return (
    <div ref={containerRef} className="h-[360px] w-full">
      <canvas
        ref={canvasRef}
        className="h-full w-full rounded-xl border border-white/5"
        aria-label="Wafer-level map heatmap and hotspot overlay"
      />
    </div>
  );
}
