"use client";

import { WAFER_COLORS } from "@/wafervision/utils/waferRender";

function Swatch({ color, label, outline = false }: { color: string; label: string; outline?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-slate-400">
      <span
        className="inline-block h-2.5 w-2.5 rounded-[2px]"
        style={
          outline
            ? { border: `1.5px solid ${color}`, background: "transparent" }
            : { background: color }
        }
      />
      {label}
    </span>
  );
}

export function BinMapLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <Swatch color={WAFER_COLORS.good} label="Good die" />
      <Swatch color={WAFER_COLORS.fail} label="Failed die" />
    </div>
  );
}

export function OverlayLegend() {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <Swatch color={WAFER_COLORS.goodOutline} label="Good" outline />
      <Swatch color={WAFER_COLORS.failOutline} label="Failed" outline />
      <Swatch color={WAFER_COLORS.selected} label="Selected" outline />
      <Swatch color={WAFER_COLORS.cluster} label="Cluster" outline />
    </div>
  );
}

export function DensityLegend() {
  return (
    <div className="space-y-1">
      <div
        className="h-1.5 w-full rounded-full"
        style={{
          background:
            "linear-gradient(90deg, #1D4ED8 0%, #16A34A 30%, #FACC15 58%, #F97316 80%, #DC2626 100%)",
        }}
      />
      <div className="flex justify-between text-[10px] text-slate-500">
        <span>Low</span>
        <span>Medium</span>
        <span>High</span>
        <span>Critical</span>
      </div>
    </div>
  );
}
