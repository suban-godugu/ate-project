"use client";

import { useMemo, useState } from "react";
import { Search, ZoomIn, ZoomOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { KpiTopologyEdge, KpiTopologyNode } from "@/types/kpiDrillDown";

const STATUS_COLORS: Record<KpiTopologyNode["status"], string> = {
  broken: "#EF4444",
  "failing-cell": "#F97316",
  debug: "#06B6D4",
  warning: "#EAB308",
  healthy: "#22C55E",
};

interface KpiTopologyPanelProps {
  nodes: KpiTopologyNode[];
  edges: KpiTopologyEdge[];
  highlightChainId?: string;
}

export function KpiTopologyPanel({ nodes, edges, highlightChainId }: KpiTopologyPanelProps) {
  const [query, setQuery] = useState("");
  const [zoom, setZoom] = useState(1);

  const positioned = useMemo(
    () =>
      nodes.map((node, i) => ({
        ...node,
        x: 60 + i * 92,
        y: 80 + (i % 3) * 52,
      })),
    [nodes]
  );

  const filtered = query
    ? positioned.filter((n) => n.label.toLowerCase().includes(query.toLowerCase()))
    : positioned;

  return (
    <div className="rounded-xl border border-[rgba(139,92,246,0.25)] bg-[#0A1020]/60 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-3">
          {[
            { label: "Broken Chains", color: STATUS_COLORS.broken },
            { label: "Failing Cells", color: STATUS_COLORS["failing-cell"] },
            { label: "Debug", color: STATUS_COLORS.debug },
            { label: "Healthy", color: STATUS_COLORS.healthy },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-[#94A3B8]">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
              {item.label}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#64748B]" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search chain..."
              className="h-8 w-40 pl-8 text-xs"
            />
          </div>
          <Button type="button" variant="outline" size="icon-sm" onClick={() => setZoom((z) => Math.min(z + 0.15, 1.6))}>
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
          <Button type="button" variant="outline" size="icon-sm" onClick={() => setZoom((z) => Math.max(z - 0.15, 0.7))}>
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
      <div className="h-[300px] overflow-hidden rounded-lg bg-[#060912]/80">
        <svg width="100%" height="100%" viewBox="0 0 800 280" preserveAspectRatio="xMidYMid meet" style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}>
          {edges.map((edge) => {
            const from = positioned.find((n) => n.id === edge.from);
            const to = positioned.find((n) => n.id === edge.to);
            if (!from || !to) return null;
            return (
              <line
                key={`${edge.from}-${edge.to}`}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={edge.broken ? "#EF4444" : "#334155"}
                strokeWidth={edge.broken ? 2.5 : 2}
                strokeDasharray={edge.broken ? "6 4" : undefined}
              />
            );
          })}
          {filtered.map((node) => {
            const color = STATUS_COLORS[node.status];
            const highlighted = highlightChainId === node.id;
            return (
              <g key={node.id}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={highlighted ? 24 : 20}
                  fill={color}
                  fillOpacity={0.22}
                  stroke={color}
                  strokeWidth={highlighted ? 3 : 2}
                />
                <text x={node.x} y={node.y + 4} textAnchor="middle" fill="#E2E8F0" fontSize={10} fontWeight={600}>
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
