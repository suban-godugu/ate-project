"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Expand,
  Hand,
  RotateCcw,
  ZoomIn,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { generateWaferHeatData } from "@/lib/dummyData";
import { gridFromApi } from "@/lib/api/mergeLiveDashboard";
import { isLiveApi } from "@/lib/api/config";
import { useFilteredWaferData } from "@/hooks/useWaferData";
import type { HeatmapOverlay } from "@/types/dashboard";

const GRID_SIZE = 40;
const CELL = 10;

function heatColor(value: number, overlay: HeatmapOverlay): string {
  if (value < 0) return "transparent";
  let v = value;
  if (overlay === "yield") v = 1 - value;
  if (overlay === "fail-density") v = value * 1.2;

  if (v >= 0.75) return "#EF4444";
  if (v >= 0.5) return "#F97316";
  if (v >= 0.25) return "#EAB308";
  return "#22C55E";
}

export function WaferHeatmap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [overlay, setOverlay] = useState<HeatmapOverlay>("cost");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    row: number;
    col: number;
    value: number;
  } | null>(null);
  const waferData = useFilteredWaferData();
  const heatData = useMemo(() => {
    if (isLiveApi()) {
      const live = waferData.waferHeatmapGrid as number[][] | undefined;
      if (!live?.length) return null;
      const scaled = gridFromApi(live, GRID_SIZE, GRID_SIZE);
      return scaled.map((row, r) =>
        row.map((v, c) => {
          const dist = Math.sqrt((r - GRID_SIZE / 2) ** 2 + (c - GRID_SIZE / 2) ** 2);
          if (dist > GRID_SIZE / 2 - 1) return -1;
          return v;
        })
      );
    }
    return generateWaferHeatData(GRID_SIZE);
  }, [waferData.waferHeatmapGrid]);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !heatData) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = GRID_SIZE * CELL;
    canvas.width = size;
    canvas.height = size;

    ctx.clearRect(0, 0, size, size);
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    ctx.fillStyle = "#0A1020";
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2 - 2, 0, Math.PI * 2);
    ctx.fill();

    for (let row = 0; row < GRID_SIZE; row++) {
      const rowData = heatData[row];
      if (!rowData) continue;
      for (let col = 0; col < GRID_SIZE; col++) {
        const val = rowData[col];
        if (val === undefined) continue;
        if (val < 0) continue;
        ctx.fillStyle = heatColor(val, overlay);
        ctx.fillRect(col * CELL, row * CELL, CELL - 1, CELL - 1);
      }
    }

    ctx.strokeStyle = "#2D3748";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, size / 2 - 2, 0, Math.PI * 2);
    ctx.stroke();

    ctx.restore();
  }, [heatData, overlay, pan, zoom]);

  useEffect(() => {
    draw();
  }, [draw]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isPanning) {
      setPan((prev) => ({
        x: prev.x + e.movementX,
        y: prev.y + e.movementY,
      }));
      setTooltip(null);
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas || !heatData) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const cx = (e.clientX - rect.left) * scaleX;
    const cy = (e.clientY - rect.top) * scaleY;
    const col = Math.floor((cx - pan.x) / zoom / CELL);
    const row = Math.floor((cy - pan.y) / zoom / CELL);
    const cellValue = heatData[row]?.[col];

    if (
      row >= 0 &&
      row < GRID_SIZE &&
      col >= 0 &&
      col < GRID_SIZE &&
      cellValue !== undefined &&
      cellValue >= 0
    ) {
      setTooltip({
        x: e.clientX,
        y: e.clientY,
        row,
        col,
        value: cellValue,
      });
    } else {
      setTooltip(null);
    }
  };

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  return (
    <div
      id="wafer"
      ref={containerRef}
      className="glass-card gradient-border overflow-hidden p-6"
    >
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-white">
            Wafer Cost Heatmap (Spatial AI)
          </h3>
          <p className="text-sm text-slate-400">
            Interactive spatial cost analysis across wafer surface
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#22C55E]" /> Low
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#EAB308]" /> Medium
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#F97316]" /> High
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-3 rounded-sm bg-[#EF4444]" /> High Cost
          </span>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="flex flex-col gap-1.5">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 border-[#2D3748]"
            title="Pan"
            onMouseDown={() => setIsPanning(true)}
            onMouseUp={() => setIsPanning(false)}
            onMouseLeave={() => setIsPanning(false)}
          >
            <Hand className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 border-[#2D3748]"
            title="Zoom In"
            onClick={() => setZoom((z) => Math.min(z + 0.2, 3))}
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 border-[#2D3748]"
            title="Reset"
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 border-[#2D3748]"
            title="Fullscreen"
            onClick={toggleFullscreen}
          >
            <Expand className="h-3.5 w-3.5" />
          </Button>
        </div>

        <div className="relative flex flex-1 items-center justify-center overflow-hidden rounded-xl bg-[#0A1020]/60 p-4">
          {!heatData && isLiveApi() ? (
            <div className="flex min-h-[280px] flex-col items-center justify-center text-center">
              <p className="text-sm text-slate-300">Spatial analytics not yet available</p>
              <p className="mt-1 max-w-md text-xs text-slate-500">
                Per-die yield/cost heatmaps require die_results from STDF die map parsing.
              </p>
            </div>
          ) : (
          <canvas
            ref={canvasRef}
            className="max-h-[420px] max-w-full cursor-crosshair rounded-full"
            style={{ width: GRID_SIZE * CELL, height: GRID_SIZE * CELL }}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => setTooltip(null)}
          />
          )}
          {tooltip && heatData && (
            <div
              className="pointer-events-none fixed z-50 rounded-lg border border-[#2D3748] bg-[#111827] px-3 py-2 text-xs shadow-xl"
              style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}
            >
              <p className="font-medium text-white">
                Die [{tooltip.row}, {tooltip.col}]
              </p>
              <p className="text-slate-400">
                {overlay === "yield" ? "Yield" : overlay === "fail-density" ? "Fail Density" : "Cost"}:{" "}
                {(tooltip.value * 100).toFixed(1)}%
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <span className="text-xs text-slate-400">Overlay:</span>
        <Select
          value={overlay}
          onValueChange={(v) => setOverlay((v as HeatmapOverlay) ?? "cost")}
        >
          <SelectTrigger className="h-8 w-40 border-[#2D3748] bg-[#111827] text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fail-density">Fail Density</SelectItem>
            <SelectItem value="yield">Yield</SelectItem>
            <SelectItem value="cost">Cost</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
