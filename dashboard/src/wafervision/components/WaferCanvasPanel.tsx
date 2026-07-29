"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type MouseEvent,
  type PointerEvent,
  type ReactNode,
  type WheelEvent,
} from "react";
import { AGENT_IMAGE_SIZE } from "@/wafervision/constants";
import { cn } from "@/wafervision/utils/format";

interface WaferCanvasPanelProps {
  label: string;
  /** Draws the full visualization into a square canvas of `size` px. */
  draw: ((ctx: CanvasRenderingContext2D, size: number) => void) | null;
  /** Base backing-store resolution; doubled automatically when zoomed in. */
  renderSize?: number;
  legend?: ReactNode;
  footnote?: string;
  emptyState?: ReactNode;
  /** Called with coordinates in agent (224) space. */
  onPick?: (x: number, y: number) => void;
  controls?: ReactNode;
}

const MAX_ZOOM = 8;

export function WaferCanvasPanel({
  label,
  draw,
  renderSize = 1024,
  legend,
  footnote,
  emptyState,
  onPick,
  controls,
}: WaferCanvasPanelProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{ x: number; y: number; panX: number; panY: number } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  // Re-render the backing store at higher resolution when magnified so die
  // borders stay crisp at 400%+ instead of upscaling pixels.
  const backingSize = zoom > 2 ? renderSize * 2 : renderSize;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !draw) return;
    canvas.width = backingSize;
    canvas.height = backingSize;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, backingSize, backingSize);
    draw(ctx, backingSize);
  }, [draw, backingSize]);

  const onWheel = useCallback((e: WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.25 : 0.25;
    setZoom((z) => Math.min(MAX_ZOOM, Math.max(1, Number((z + delta).toFixed(2)))));
  }, []);

  const onPointerDown = useCallback(
    (e: PointerEvent<HTMLDivElement>) => {
      if (zoom <= 1) return;
      (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
      dragRef.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y };
    },
    [pan.x, pan.y, zoom],
  );

  const onPointerMove = useCallback((e: PointerEvent<HTMLDivElement>) => {
    const d = dragRef.current;
    if (!d) return;
    setPan({ x: d.panX + (e.clientX - d.x), y: d.panY + (e.clientY - d.y) });
  }, []);

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  const onClick = useCallback(
    (e: MouseEvent<HTMLCanvasElement>) => {
      if (!onPick) return;
      const rect = e.currentTarget.getBoundingClientRect();
      const nx = (e.clientX - rect.left) / rect.width;
      const ny = (e.clientY - rect.top) / rect.height;
      if (nx < 0 || nx > 1 || ny < 0 || ny > 1) return;
      onPick(nx * AGENT_IMAGE_SIZE, ny * AGENT_IMAGE_SIZE);
    },
    [onPick],
  );

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="flex flex-col overflow-hidden rounded-lg border" style={{ borderColor: "var(--line)" }}>
      <div
        className="flex items-center justify-between gap-2 border-b px-2 py-1"
        style={{ borderColor: "var(--line)" }}
      >
        <p className="text-[11px] uppercase tracking-wide" style={{ color: "var(--muted)" }}>
          {label}
        </p>
        <span className="font-mono text-[10px] text-slate-500">{backingSize}px</span>
      </div>

      <div
        className={cn(
          "relative aspect-square overflow-hidden bg-[#080d17]",
          zoom > 1 ? "cursor-grab active:cursor-grabbing" : onPick ? "cursor-crosshair" : "cursor-default",
        )}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
      >
        {draw ? (
          <canvas
            ref={canvasRef}
            onClick={onClick}
            className="h-full w-full"
            style={{
              transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
              transformOrigin: "center center",
            }}
          />
        ) : (
          <div className="flex h-full items-center justify-center px-3 text-center text-xs" style={{ color: "var(--muted)" }}>
            {emptyState ?? "No analysis data"}
          </div>
        )}
      </div>

      <div
        className="flex flex-wrap items-center gap-1.5 border-t px-2 py-1.5"
        style={{ borderColor: "var(--line)" }}
      >
        <button
          type="button"
          onClick={() => setZoom((z) => Math.min(MAX_ZOOM, Number((z + 0.5).toFixed(2))))}
          className="rounded border px-1.5 py-0.5 text-[10px] text-slate-300"
          style={{ borderColor: "var(--line)" }}
        >
          +
        </button>
        <button
          type="button"
          onClick={() => setZoom((z) => Math.max(1, Number((z - 0.5).toFixed(2))))}
          className="rounded border px-1.5 py-0.5 text-[10px] text-slate-300"
          style={{ borderColor: "var(--line)" }}
        >
          −
        </button>
        <button
          type="button"
          onClick={resetView}
          className="rounded border px-1.5 py-0.5 text-[10px] text-slate-300"
          style={{ borderColor: "var(--line)" }}
        >
          Reset
        </button>
        <span className="font-mono text-[10px] text-slate-500">{Math.round(zoom * 100)}%</span>
        {controls}
      </div>

      {legend ? (
        <div className="border-t px-2 py-1.5" style={{ borderColor: "var(--line)" }}>
          {legend}
        </div>
      ) : null}

      {footnote ? (
        <p
          className="mt-auto border-t px-2 py-1 text-[10px] leading-snug text-slate-500"
          style={{ borderColor: "var(--line)" }}
        >
          {footnote}
        </p>
      ) : null}
    </div>
  );
}
