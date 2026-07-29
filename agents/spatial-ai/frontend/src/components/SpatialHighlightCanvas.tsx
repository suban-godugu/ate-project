"use client";

import { useEffect, useRef } from "react";

import type { ClusterRecord, ZoneRecord } from "@/types/wafer";

/**
 * Draws backend-provided cluster / zone geometry onto the overlay image.
 * Does not compute analytics — only renders returned coordinates.
 */
export function SpatialHighlightCanvas({
  cluster,
  zone,
  imageSize = 224,
}: {
  cluster: ClusterRecord | null;
  zone: ZoneRecord | null;
  imageSize?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const parent = canvas.parentElement;
    if (!parent) return;

    const width = parent.clientWidth || imageSize;
    const height = parent.clientHeight || width;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);

    const sx = width / imageSize;
    const sy = height / imageSize;

    if (cluster?.bounding_box) {
      const box = cluster.bounding_box;
      const x = box.x1 * sx;
      const y = box.y1 * sy;
      const w = (box.x2 - box.x1) * sx;
      const h = (box.y2 - box.y1) * sy;
      ctx.strokeStyle = "#d64545";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(x, y, w, h);
      ctx.setLineDash([]);

      if (cluster.center_x != null && cluster.center_y != null) {
        const cx = cluster.center_x * sx;
        const cy = cluster.center_y * sy;
        ctx.fillStyle = "#d64545";
        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx - 8, cy);
        ctx.lineTo(cx + 8, cy);
        ctx.moveTo(cx, cy - 8);
        ctx.lineTo(cx, cy + 8);
        ctx.stroke();
      }
    }

    if (zone?.zone_boundary?.length) {
      ctx.beginPath();
      zone.zone_boundary.forEach((point, index) => {
        const x = point.x * sx;
        const y = point.y * sy;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = "rgba(47, 111, 237, 0.18)";
      ctx.fill();
      ctx.strokeStyle = "#2f6fed";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [cluster, zone, imageSize]);

  return (
    <canvas
      ref={canvasRef}
      className="pointer-events-none absolute inset-0 h-full w-full"
      aria-hidden
    />
  );
}
