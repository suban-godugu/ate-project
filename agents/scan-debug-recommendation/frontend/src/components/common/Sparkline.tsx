"use client";

import { motion } from "framer-motion";

export function Sparkline({ data, className = "" }: { data?: number[]; className?: string }) {
  const series = Array.isArray(data) && data.length > 0 ? data : [0, 0, 0, 0, 0];
  const max = Math.max(...series, 1);
  const min = Math.min(...series, 0);
  const range = Math.max(max - min, 1);
  const w = 120;
  const h = 28;
  const points = series
    .map((v, i) => {
      const x = (i / Math.max(series.length - 1, 1)) * w;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={`h-7 w-full ${className}`} aria-hidden>
      <motion.polyline
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.6 }}
        fill="none"
        stroke="rgba(124,58,237,0.9)"
        strokeWidth="2"
        points={points}
      />
    </svg>
  );
}
