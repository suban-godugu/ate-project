"use client";

import { ChartCard } from "@/components/scan-chain/ChartCard";
import { useFilteredScanChainData } from "@/hooks/useScanChainData";

const statusColors: Record<string, string> = {
  failing: "#EF4444",
  warning: "#EAB308",
  healthy: "#22C55E",
  unknown: "#64748B",
};

export function ConnectivityGraph() {
  const { connectivityGraphData } = useFilteredScanChainData();
  const { nodes, edges } = connectivityGraphData;
  const nodePositions = nodes.map((node, i) => ({
    ...node,
    x: 60 + i * 120,
    y: 80 + (i % 2) * 60,
  }));

  return (
    <ChartCard
      title="Chain Connectivity Graph"
      subtitle="Scan chain dependency and propagation paths"
    >
      <div className="relative h-[200px] overflow-hidden rounded-xl bg-[#0A1020]/60">
        <svg width="100%" height="100%" viewBox="0 0 720 200">
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
                stroke="#2D3748"
                strokeWidth={2}
              />
            );
          })}
          {nodePositions.map((node) => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r={22}
                fill={statusColors[node.status] ?? "#64748B"}
                fillOpacity={0.2}
                stroke={statusColors[node.status] ?? "#64748B"}
                strokeWidth={2}
              />
              <text
                x={node.x}
                y={node.y + 40}
                textAnchor="middle"
                fill="#94A3B8"
                fontSize="10"
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
