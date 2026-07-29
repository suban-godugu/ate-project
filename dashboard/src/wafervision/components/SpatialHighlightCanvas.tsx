"use client";

import { useEffect, useRef } from "react";
import { AGENT_IMAGE_SIZE, scaleFromAgent } from "@/wafervision/constants";
import {
  drawFailureOverlay,
  WAFER_COLORS,
  type WaferRenderInput,
} from "@/wafervision/utils/waferRender";

interface Props {
  /** Preferred: draw the wafer client-side at high resolution. */
  wafer?: WaferRenderInput | null;
  /** Fallback when dies are unavailable (agent 224 PNG). */
  imageUrl?: string | null;
  /** Axis-aligned box in agent 224 space: [x0, y0, x1, y1] */
  bbox?: [number, number, number, number] | null;
  /** Centroid in agent 224 space: [x, y] */
  centroid?: [number, number] | null;
  /** Polygon vertices in agent 224 space */
  polygon?: [number, number][] | null;
  /** Canvas backing-store size. */
  displaySize?: number;
}

/**
 * Cluster / engineering-zone highlights drawn on a high-resolution wafer render.
 * All input coordinates are in AGENT_IMAGE_SIZE (224) space.
 */
export function SpatialHighlightCanvas({
  wafer = null,
  imageUrl,
  bbox,
  centroid,
  polygon,
  displaySize = 1024,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = canvas.width;
    ctx.clearRect(0, 0, size, size);

    const sx = (v: number) => scaleFromAgent(v, size, AGENT_IMAGE_SIZE);

    const drawGeometry = () => {
      ctx.save();
      ctx.lineWidth = Math.max(2, size / 512);

      if (bbox) {
        const [x0, y0, x1, y1] = bbox;
        const dx = sx(x0);
        const dy = sx(y0);
        ctx.fillStyle = "rgba(251, 146, 60, 0.16)";
        ctx.strokeStyle = WAFER_COLORS.cluster;
        ctx.fillRect(dx, dy, sx(x1) - dx, sx(y1) - dy);
        ctx.strokeRect(dx, dy, sx(x1) - dx, sx(y1) - dy);
      }

      if (polygon && polygon.length > 1) {
        ctx.beginPath();
        polygon.forEach(([x, y], i) => {
          if (i === 0) ctx.moveTo(sx(x), sx(y));
          else ctx.lineTo(sx(x), sx(y));
        });
        ctx.closePath();
        ctx.fillStyle = "rgba(167, 139, 250, 0.18)";
        ctx.strokeStyle = "#A78BFA";
        ctx.fill();
        ctx.stroke();
      }

      if (centroid) {
        ctx.beginPath();
        ctx.arc(sx(centroid[0]), sx(centroid[1]), Math.max(4, size / 128), 0, Math.PI * 2);
        ctx.fillStyle = "#ef4444";
        ctx.fill();
        ctx.strokeStyle = "#fee2e2";
        ctx.lineWidth = Math.max(1.5, size / 720);
        ctx.stroke();
      }
      ctx.restore();
    };

    if (wafer) {
      drawFailureOverlay(ctx, size, { ...wafer, showClusters: false });
      drawGeometry();
      return;
    }

    if (imageUrl) {
      const img = new Image();
      img.onload = () => {
        ctx.imageSmoothingEnabled = false;
        ctx.drawImage(img, 0, 0, size, size);
        drawGeometry();
      };
      img.src = imageUrl;
      return;
    }

    ctx.fillStyle = WAFER_COLORS.background;
    ctx.fillRect(0, 0, size, size);
    drawGeometry();
  }, [wafer, imageUrl, bbox, centroid, polygon, displaySize]);

  return (
    <div className="space-y-1">
      <canvas
        ref={canvasRef}
        width={displaySize}
        height={displaySize}
        className="h-auto w-full rounded-lg border"
        style={{ borderColor: "var(--line)", maxHeight: 420 }}
      />
      <p className="text-[10px] text-slate-500">
        {wafer
          ? `Rendered at ${displaySize}px from die data`
          : `Agent ${AGENT_IMAGE_SIZE}px image upscaled`}
      </p>
    </div>
  );
}
