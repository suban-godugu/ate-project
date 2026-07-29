"use client";

import { ChartCard } from "@/components/scan-chain/ChartCard";
import type { TopologyGraphEdge, TopologyGraphNode } from "@/types/scanChain";

const statusColors: Record<TopologyGraphNode["status"], string> = {
  broken: "#EF4444",
  "failing-cell": "#F97316",
  debug: "#06B6D4",
  warning: "#EAB308",
  healthy: "#22C55E",
};

const legendItems: { label: string; color: string }[] = [
  { label: "Broken Chains", color: statusColors.broken },
  { label: "Failing Cells", color: statusColors["failing-cell"] },
  { label: "Debug Locations", color: statusColors.debug },
  { label: "Warning", color: statusColors.warning },
  { label: "Healthy", color: statusColors.healthy },
];

interface ScanTopologyViewerProps {
  nodes: TopologyGraphNode[];
  edges: TopologyGraphEdge[];
}

export function ScanTopologyViewer({ nodes, edges }: ScanTopologyViewerProps) {
  const nodePositions = nodes.map((node, i) => ({
    ...node,
    x: 50 + i * 88,
    y: 70 + (i % 3) * 48,
  }));

  return (
    <ChartCard
      title="Scan Chain Topology Viewer"
      subtitle="Interactive graph — broken chains, failing cells, and debug locations"
    >
      <div className="mb-3 flex flex-wrap gap-3">
        {legendItems.map((item) => (
          <div key={item.label} className="flex items-center gap-1.5 text-[10px] text-slate-400">
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{ backgroundColor: item.color }}
            />
            {item.label}
          </div>
        ))}
      </div>
      <div className="relative h-[240px] overflow-hidden rounded-xl bg-[#0A1020]/60">
        <svg width="100%" height="100%" viewBox="0 0 720 240" preserveAspectRatio="xMidYMid meet">
          {edges.map((edge) => {
            const from = nodePositions.find((n) => n.id === edge.from);
            const to = nodePositions.find((n) => n.id === edge.to);
            if (!from || !to) return null;
            return (
              <line
                key={`${edge.from}-${edge.to}`}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={edge.broken ? "#EF4444" : "#2D3748"}
                strokeWidth={edge.broken ? 2.5 : 2}
                strokeDasharray={edge.broken ? "6 4" : undefined}
              />
            );
          })}
          {nodePositions.map((node) => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={20}
                fill={statusColors[node.status]}
                fillOpacity={0.25}
                stroke={statusColors[node.status]}
                strokeWidth={2}
              />
              <text
                x={node.x}
                y={node.y + 36}
                textAnchor="middle"
                fill="#94A3B8"
                fontSize="9"
              >
                {node.label}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </ChartCard>
  );
}
