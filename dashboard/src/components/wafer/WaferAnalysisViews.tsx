"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChartCard } from "@/components/scan-chain/ChartCard";
import { useFilteredWaferData } from "@/hooks/useWaferData";
import type { WaferDefectClass, WaferUploadHistoryItem } from "@/types/wafer";

const CANVAS_SIZE = 320;

function OverlayAnalyticsCanvas({
  classId,
  upload,
}: {
  classId: WaferDefectClass;
  upload: WaferUploadHistoryItem;
}) {
  const { ANALYSIS_GRID, getDieFailIntensity, isDieFail } = useFilteredWaferData();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = CANVAS_SIZE;
    canvas.width = size;
    canvas.height = size;
    ctx.clearRect(0, 0, size, size);

    ctx.fillStyle = "#050508";
    ctx.fillRect(0, 0, size, size);

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 8;
    const cell = (radius * 2) / ANALYSIS_GRID;

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.clip();

    const failCells: { x: number; y: number }[] = [];

    for (let row = 0; row < ANALYSIS_GRID; row++) {
      for (let col = 0; col < ANALYSIS_GRID; col++) {
        const intensity = getDieFailIntensity(row, col, classId, upload.seed);
        if (intensity < 0) continue;

        const x = cx - radius + col * cell;
        const y = cy - radius + row * cell;
        const failed = isDieFail(row, col, classId, upload.seed);

        ctx.fillStyle = failed ? "#EAB308" : "#0F766E";
        ctx.fillRect(x, y, cell - 0.5, cell - 0.5);

        if (failed) {
          failCells.push({ x: x + cell / 2, y: y + cell / 2 });
        }
      }
    }

    if (failCells.length > 0) {
      const clusters = [
        failCells.slice(0, Math.ceil(failCells.length / 3)),
        failCells.slice(Math.ceil(failCells.length / 3), Math.ceil((failCells.length * 2) / 3)),
        failCells.slice(Math.ceil((failCells.length * 2) / 3)),
      ].filter((c) => c.length > 2);

      ctx.strokeStyle = "rgba(34, 211, 238, 0.85)";
      ctx.lineWidth = 1.5;
      for (const cluster of clusters) {
        const minX = Math.min(...cluster.map((p) => p.x));
        const maxX = Math.max(...cluster.map((p) => p.x));
        const minY = Math.min(...cluster.map((p) => p.y));
        const maxY = Math.max(...cluster.map((p) => p.y));
        ctx.strokeRect(minX - 4, minY - 4, maxX - minX + 8, maxY - minY + 8);
      }
    }

    ctx.restore();

    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;
    ctx.stroke();
  }, [ANALYSIS_GRID, classId, getDieFailIntensity, isDieFail, upload.seed]);

  useEffect(() => {
    draw();
  }, [draw]);

  return (
    <div className="flex flex-col items-center gap-3">
      <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
        Overlay Analytics
      </p>
      <div className="rounded-2xl border border-[#2D3748] bg-black p-3">
        <canvas ref={canvasRef} className="block rounded-xl" style={{ width: CANVAS_SIZE, height: CANVAS_SIZE }} />
      </div>
      <p className="text-xs text-slate-400">
        {upload.wafer} · {upload.lot}
      </p>
    </div>
  );
}

function densityColor(t: number): string {
  const clamped = Math.max(0, Math.min(1, t));
  if (clamped < 0.25) {
    const u = clamped / 0.25;
    return `rgb(${Math.round(10 + u * 20)}, ${Math.round(20 + u * 60)}, ${Math.round(80 + u * 120)})`;
  }
  if (clamped < 0.55) {
    const u = (clamped - 0.25) / 0.3;
    return `rgb(${Math.round(30 + u * 40)}, ${Math.round(180 + u * 50)}, ${Math.round(200 + u * 30)})`;
  }
  if (clamped < 0.8) {
    const u = (clamped - 0.55) / 0.25;
    return `rgb(${Math.round(70 + u * 185)}, ${Math.round(230 - u * 30)}, ${Math.round(230 - u * 180)})`;
  }
  const u = (clamped - 0.8) / 0.2;
  return `rgb(${Math.round(255)}, ${Math.round(200 + u * 55)}, ${Math.round(50 + u * 200)})`;
}

function FailDensityCanvas({
  classId,
  upload,
}: {
  classId: WaferDefectClass;
  upload: WaferUploadHistoryItem;
}) {
  const { ANALYSIS_GRID, getDieFailIntensity } = useFilteredWaferData();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [cursor, setCursor] = useState({ x: upload.hotspotX, y: upload.hotspotY });

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = CANVAS_SIZE;
    canvas.width = size;
    canvas.height = size;

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 8;
    const cell = (radius * 2) / ANALYSIS_GRID;

    const density = new Float32Array(ANALYSIS_GRID * ANALYSIS_GRID);
    for (let row = 0; row < ANALYSIS_GRID; row++) {
      for (let col = 0; col < ANALYSIS_GRID; col++) {
        const intensity = getDieFailIntensity(row, col, classId, upload.seed);
        density[row * ANALYSIS_GRID + col] = intensity < 0 ? 0 : intensity;
      }
    }

    const blurred = new Float32Array(ANALYSIS_GRID * ANALYSIS_GRID);
    const kernel = 2;
    for (let row = 0; row < ANALYSIS_GRID; row++) {
      for (let col = 0; col < ANALYSIS_GRID; col++) {
        let sum = 0;
        let count = 0;
        for (let dr = -kernel; dr <= kernel; dr++) {
          for (let dc = -kernel; dc <= kernel; dc++) {
            const nr = row + dr;
            const nc = col + dc;
            if (nr >= 0 && nr < ANALYSIS_GRID && nc >= 0 && nc < ANALYSIS_GRID) {
              sum += density[nr * ANALYSIS_GRID + nc]!;
              count++;
            }
          }
        }
        blurred[row * ANALYSIS_GRID + col] = sum / count;
      }
    }

    let max = 0.001;
    for (const v of blurred) max = Math.max(max, v);

    ctx.fillStyle = "#050508";
    ctx.fillRect(0, 0, size, size);

    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.clip();

    for (let row = 0; row < ANALYSIS_GRID; row++) {
      for (let col = 0; col < ANALYSIS_GRID; col++) {
        const val = blurred[row * ANALYSIS_GRID + col]! / max;
        if (val <= 0.02) continue;
        const x = cx - radius + col * cell;
        const y = cy - radius + row * cell;
        ctx.fillStyle = densityColor(val);
        ctx.fillRect(x, y, cell + 0.5, cell + 0.5);
      }
    }

    ctx.restore();

    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.strokeStyle = "#FFFFFF";
    ctx.lineWidth = 2;
    ctx.stroke();

    const hx = cx - radius + cursor.x * cell + cell / 2;
    const hy = cy - radius + cursor.y * cell + cell / 2;

    ctx.strokeStyle = "#7C3AED";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(hx, cy - radius);
    ctx.lineTo(hx, cy + radius);
    ctx.moveTo(cx - radius, hy);
    ctx.lineTo(cx + radius, hy);
    ctx.stroke();
  }, [ANALYSIS_GRID, classId, getDieFailIntensity, upload.seed, cursor.x, cursor.y]);

  useEffect(() => {
    draw();
  }, [draw]);

  useEffect(() => {
    setCursor({ x: upload.hotspotX, y: upload.hotspotY });
  }, [upload.hotspotX, upload.hotspotY, upload.id]);

  const handleMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * CANVAS_SIZE;
    const py = ((e.clientY - rect.top) / rect.height) * CANVAS_SIZE;
    const cx = CANVAS_SIZE / 2;
    const cy = CANVAS_SIZE / 2;
    const radius = CANVAS_SIZE / 2 - 8;
    const cell = (radius * 2) / ANALYSIS_GRID;
    const col = Math.floor((px - (cx - radius)) / cell);
    const row = Math.floor((py - (cy - radius)) / cell);
    if (col >= 0 && col < ANALYSIS_GRID && row >= 0 && row < ANALYSIS_GRID) {
      setCursor({ x: col, y: row });
    }
  };

  return (
    <div className="relative flex flex-col items-center gap-3">
      <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-500">
        Fail Density Map
      </p>
      <div className="relative rounded-2xl border border-[#2D3748] bg-black p-3">
        <canvas
          ref={canvasRef}
          className="block cursor-crosshair rounded-xl"
          style={{ width: CANVAS_SIZE, height: CANVAS_SIZE }}
          onMouseMove={handleMove}
        />
        <div
          className="pointer-events-none absolute rounded-lg border border-[#7C3AED]/40 bg-[#111827]/95 px-2.5 py-1 text-xs font-medium text-white shadow-lg"
          style={{
            left: `calc(50% + ${((cursor.x - ANALYSIS_GRID / 2) / ANALYSIS_GRID) * (CANVAS_SIZE - 16)}px)`,
            top: `calc(50% + ${((cursor.y - ANALYSIS_GRID / 2) / ANALYSIS_GRID) * (CANVAS_SIZE - 16) - 36}px)`,
            transform: "translateX(-50%)",
          }}
        >
          X: {cursor.x} · Y: {cursor.y}
        </div>
      </div>
      <p className="text-xs text-slate-400">
        {upload.wafer} · density hotspot
      </p>
    </div>
  );
}

export function WaferAnalysisViews({
  classId,
  upload,
}: {
  classId: WaferDefectClass;
  upload: WaferUploadHistoryItem;
}) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <ChartCard title="" subtitle="" className="[&_h3]:hidden">
        <OverlayAnalyticsCanvas classId={classId} upload={upload} />
      </ChartCard>
      <ChartCard title="" subtitle="" className="[&_h3]:hidden">
        <FailDensityCanvas classId={classId} upload={upload} />
      </ChartCard>
    </div>
  );
}
