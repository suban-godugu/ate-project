"use client";

import { memo, useCallback, useEffect, useRef, useState } from "react";
import type { DieSummary } from "@/lib/api";
import { useVisualizationStore } from "@/stores/visualizationStore";

type Props = {
  dies: DieSummary[];
};

export const WorkbenchWaferHeatmap = memo(function WorkbenchWaferHeatmap({ dies }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const waferZoom = useVisualizationStore((s) => s.waferZoom);
  const waferPan = useVisualizationStore((s) => s.waferPan);
  const setWaferTransform = useVisualizationStore((s) => s.setWaferTransform);
  const setSelectedDie = useVisualizationStore((s) => s.setSelectedDie);
  const selectedDie = useVisualizationStore((s) => s.selectedDie);
  const [hover, setHover] = useState<DieSummary | null>(null);
  const dragRef = useRef<{ x: number; y: number } | null>(null);

  const points = dies.filter(
    (d) => typeof d.x === "number" && typeof d.y === "number",
  ) as Array<DieSummary & { x: number; y: number }>;

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
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
    ctx.save();
    ctx.translate(width / 2 + waferPan.x, height / 2 + waferPan.y);
    ctx.scale(waferZoom, waferZoom);

    const radius = Math.min(width, height) * 0.38;
    ctx.beginPath();
    ctx.arc(0, 0, radius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(15,23,42,.85)";
    ctx.fill();
    ctx.strokeStyle = "rgba(148,163,184,.45)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    const maxAbs = Math.max(1, ...points.flatMap((p) => [Math.abs(p.x), Math.abs(p.y)]));
    for (const die of points) {
      const sx = (die.x / maxAbs) * radius * 0.9;
      const sy = (die.y / maxAbs) * radius * 0.9;
      const failing = die.is_failing;
      const density = die.failure_density || (failing ? 1 : 0);
      ctx.beginPath();
      ctx.arc(sx, sy, 4 + density * 3, 0, Math.PI * 2);
      ctx.fillStyle = failing
        ? `rgba(248,113,113,${0.35 + Math.min(0.65, density)})`
        : "rgba(52,211,153,0.55)";
      ctx.fill();
      if (selectedDie?.die_id === die.die_id) {
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    }
    ctx.restore();
  }, [dies, points, selectedDie, waferPan, waferZoom]);

  useEffect(() => {
    draw();
    const ro = new ResizeObserver(draw);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [draw]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    // React registers wheel handlers as passive, so preventDefault only works on a native listener.
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      setWaferTransform(
        Math.min(3, Math.max(0.5, waferZoom + (event.deltaY < 0 ? 0.1 : -0.1))),
        waferPan,
      );
    };
    container.addEventListener("wheel", onWheel, { passive: false });
    return () => container.removeEventListener("wheel", onWheel);
  }, [waferZoom, waferPan, setWaferTransform]);

  const hitTest = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container || !points.length) return null;
    const rect = canvas.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const cx = width / 2 + waferPan.x;
    const cy = height / 2 + waferPan.y;
    const radius = Math.min(width, height) * 0.38 * waferZoom;
    const maxAbs = Math.max(1, ...points.flatMap((p) => [Math.abs(p.x), Math.abs(p.y)]));
    const mx = clientX - rect.left;
    const my = clientY - rect.top;
    let closest: DieSummary | null = null;
    let best = Infinity;
    for (const die of points) {
      const sx = cx + (die.x / maxAbs) * radius * 0.9;
      const sy = cy + (die.y / maxAbs) * radius * 0.9;
      const d = (mx - sx) ** 2 + (my - sy) ** 2;
      if (d < best && d < 400) {
        best = d;
        closest = die;
      }
    }
    return closest;
  };

  return (
    <div className="glass-panel rounded-2xl p-4" data-testid="wafer-heatmap">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--muted)]">
          Wafer Heatmap
        </h3>
        <span className="text-xs text-[var(--muted)]">{points.length} dies</span>
      </div>
      <div
        ref={containerRef}
        className="relative h-80 overflow-hidden rounded-xl border border-white/10 bg-black/20"
        onMouseDown={(e) => {
          dragRef.current = { x: e.clientX - waferPan.x, y: e.clientY - waferPan.y };
        }}
        onMouseMove={(e) => {
          if (dragRef.current) {
            setWaferTransform(waferZoom, {
              x: e.clientX - dragRef.current.x,
              y: e.clientY - dragRef.current.y,
            });
          } else {
            setHover(hitTest(e.clientX, e.clientY));
          }
        }}
        onMouseUp={() => {
          dragRef.current = null;
        }}
        onMouseLeave={() => {
          dragRef.current = null;
          setHover(null);
        }}
        onClick={(e) => {
          const die = hitTest(e.clientX, e.clientY);
          if (die && typeof die.x === "number" && typeof die.y === "number") {
            setSelectedDie({
              die_id: die.die_id,
              x: die.x,
              y: die.y,
              status: die.is_failing ? "fail" : "pass",
              failure_count: die.failure_count,
              confidence: die.health_score,
            });
          }
        }}
      >
        <canvas ref={canvasRef} className="h-full w-full cursor-crosshair" />
        {(hover || selectedDie) && (
          <div className="pointer-events-none absolute bottom-2 left-2 rounded-lg bg-black/70 px-3 py-2 text-xs">
            <div>Die: {(hover || selectedDie)?.die_id || "—"}</div>
            <div>
              ({(hover || selectedDie)?.x}, {(hover || selectedDie)?.y}) · failures{" "}
              {(hover || selectedDie)?.failure_count ?? 0}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});
