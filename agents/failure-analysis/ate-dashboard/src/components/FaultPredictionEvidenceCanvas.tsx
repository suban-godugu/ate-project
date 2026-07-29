"use client";

import { useEffect, useRef } from "react";
import type { SupportingEvidence } from "@/lib/api";

/** Backend may return plain strings or incomplete objects for supporting_evidence. */
export function normalizeSupportingEvidence(raw: unknown): SupportingEvidence[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item, index) => {
    const fallbackWeight = Math.max(0.05, 1 - index * 0.08);
    if (typeof item === "string") {
      return {
        source: "engine",
        label: item.trim() || "Unknown",
        weight: fallbackWeight,
      };
    }
    if (item && typeof item === "object") {
      const row = item as Partial<SupportingEvidence> & Record<string, unknown>;
      const labelCandidate =
        (typeof row.label === "string" && row.label) ||
        (typeof row.source === "string" && row.source) ||
        (typeof row.value === "string" && row.value) ||
        "Unknown";
      const weight = Number(row.weight);
      return {
        source: typeof row.source === "string" && row.source ? row.source : "unknown",
        label: labelCandidate.trim() || "Unknown",
        weight: Number.isFinite(weight) && weight >= 0 ? weight : fallbackWeight,
        value: row.value,
        details: row.details,
      };
    }
    return { source: "unknown", label: "Unknown", weight: fallbackWeight };
  });
}

export function FaultPredictionEvidenceCanvas({
  evidence,
  selectedLabel,
}: {
  evidence: SupportingEvidence[];
  selectedLabel?: string | null;
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
      const height = Math.max(1, container.clientHeight || 220);
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

      const rows = normalizeSupportingEvidence(evidence);
      if (!rows.length) {
        ctx.fillStyle = "rgba(148,163,184,.7)";
        ctx.font = "12px system-ui, sans-serif";
        ctx.fillText("No supporting evidence available", 16, height / 2);
        return;
      }

      const maxWeight = Math.max(0.01, ...rows.map((row) => row.weight));
      const barHeight = Math.min(28, (height - 24) / rows.length - 6);
      const labelWidth = Math.min(140, width * 0.32);
      const barStart = labelWidth + 12;
      const barMaxWidth = width - barStart - 48;

      rows.forEach((row, index) => {
        const y = 12 + index * (barHeight + 8);
        const labelText = row.label || "—";
        const weight = Number.isFinite(row.weight) ? row.weight : 0;
        const isSelected = Boolean(selectedLabel && labelText === selectedLabel);
        const barWidth = (weight / maxWeight) * barMaxWidth;

        ctx.fillStyle = isSelected ? "rgba(255,255,255,.9)" : "rgba(148,163,184,.85)";
        ctx.font = "11px system-ui, sans-serif";
        const label =
          labelText.length > 18 ? `${labelText.slice(0, 16)}…` : labelText;
        ctx.fillText(label, 12, y + barHeight * 0.72);

        ctx.fillStyle = "rgba(15,23,42,.9)";
        ctx.fillRect(barStart, y, barMaxWidth, barHeight);

        const gradient = ctx.createLinearGradient(barStart, 0, barStart + barWidth, 0);
        gradient.addColorStop(0, isSelected ? "#a78bfa" : "#7c3aed");
        gradient.addColorStop(1, isSelected ? "#38bdf8" : "#4f46e5");
        ctx.fillStyle = gradient;
        ctx.fillRect(barStart, y, barWidth, barHeight);

        ctx.strokeStyle = isSelected ? "rgba(167,139,250,.8)" : "rgba(255,255,255,.08)";
        ctx.lineWidth = isSelected ? 1.5 : 1;
        ctx.strokeRect(barStart, y, barMaxWidth, barHeight);

        ctx.fillStyle = "rgba(255,255,255,.85)";
        ctx.font = "10px ui-monospace, monospace";
        ctx.fillText(
          `${(weight * 100).toFixed(0)}%`,
          barStart + barMaxWidth + 8,
          y + barHeight * 0.72,
        );
      });
    };

    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(container);
    return () => observer.disconnect();
  }, [evidence, selectedLabel]);

  return (
    <div ref={containerRef} className="h-[220px] w-full overflow-hidden rounded-xl">
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}
