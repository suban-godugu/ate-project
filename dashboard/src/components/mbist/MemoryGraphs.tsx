"use client";

import { ChartCard } from "@/components/scan-chain/ChartCard";
import { useFilteredMbistData } from "@/hooks/useMbistData";

const statusColors: Record<string, string> = {
  failed: "#EF4444",
  warning: "#EAB308",
  healthy: "#22C55E",
};

export function MemoryConnectivityGraph() {
  const { connectivityNodes } = useFilteredMbistData();
  const { nodes, edges } = connectivityNodes;
  const nodePositions = nodes.map((node, i) => ({ ...node, x: 70 + i * 130, y: 80 + (i % 2) * 60 }));

  return (
    <ChartCard title="Memory Connectivity" subtitle="Inter-instance failure correlation paths">
      <div className="relative h-[200px] overflow-hidden rounded-xl bg-[#0A1020]/60">
        <svg width="100%" height="100%" viewBox="0 0 720 200">
          {edges.map((edge) => {
            const from = nodePositions.find((n) => n.id === edge.from);
            const to = nodePositions.find((n) => n.id === edge.to);
            if (!from || !to) return null;
            return <line key={`${edge.from}-${edge.to}`} x1={from.x} y1={from.y} x2={to.x} y2={to.y} stroke="#2D3748" strokeWidth={2} />;
          })}
          {nodePositions.map((node) => (
            <g key={node.id}>
              <circle cx={node.x} cy={node.y} r={22} fill={statusColors[node.status] ?? "#64748B"} fillOpacity={0.2} stroke={statusColors[node.status] ?? "#64748B"} strokeWidth={2} />
              <text x={node.x} y={node.y + 40} textAnchor="middle" fill="#94A3B8" fontSize="10">{node.label}</text>
            </g>
          ))}
        </svg>
      </div>
    </ChartCard>
  );
}

export function RootCauseGraph() {
  return (
    <ChartCard title="Root Cause Graph" subtitle="Failure propagation across memory hierarchy">
      <div className="relative h-[200px] overflow-hidden rounded-xl bg-[#0A1020]/60 p-4">
        <svg width="100%" height="100%" viewBox="0 0 600 160">
          <line x1="300" y1="20" x2="150" y2="80" stroke="#7C3AED" strokeWidth={2} />
          <line x1="300" y1="20" x2="450" y2="80" stroke="#7C3AED" strokeWidth={2} />
          <line x1="150" y1="80" x2="100" y2="140" stroke="#F97316" strokeWidth={2} />
          <line x1="150" y1="80" x2="200" y2="140" stroke="#F97316" strokeWidth={2} />
          <line x1="450" y1="80" x2="400" y2="140" stroke="#EF4444" strokeWidth={2} />
          <line x1="450" y1="80" x2="500" y2="140" stroke="#EF4444" strokeWidth={2} />
          <circle cx="300" cy="20" r="16" fill="#7C3AED" fillOpacity={0.3} stroke="#7C3AED" />
          <text x="300" y="24" textAnchor="middle" fill="white" fontSize="9">Decoder</text>
          {[{ x: 150, y: 80, l: "Bank-0" }, { x: 450, y: 80, l: "Bank-2" }].map((n) => (
            <g key={n.l}>
              <circle cx={n.x} cy={n.y} r="14" fill="#EAB308" fillOpacity={0.3} stroke="#EAB308" />
              <text x={n.x} y={n.y + 4} textAnchor="middle" fill="white" fontSize="8">{n.l}</text>
            </g>
          ))}
          {[{ x: 100, l: "BL-142" }, { x: 200, l: "WL-089" }, { x: 400, l: "Cell-034" }, { x: 500, l: "Cell-201" }].map((n) => (
            <g key={n.l}>
              <circle cx={n.x} cy="140" r="12" fill="#EF4444" fillOpacity={0.3} stroke="#EF4444" />
              <text x={n.x} y="144" textAnchor="middle" fill="white" fontSize="7">{n.l}</text>
            </g>
          ))}
        </svg>
      </div>
    </ChartCard>
  );
}
