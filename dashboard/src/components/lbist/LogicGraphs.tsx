"use client";

import { ChartCard } from "@/components/scan-chain/ChartCard";
import { useFilteredLbistData } from "@/hooks/useLbistData";

const statusColors: Record<string, string> = {
  failed: "#EF4444",
  warning: "#EAB308",
  healthy: "#22C55E",
};

export function LogicConnectivityGraph() {
  const { connectivityNodes } = useFilteredLbistData();
  const { nodes, edges } = connectivityNodes;
  const nodePositions = nodes.map((node, i) => ({ ...node, x: 70 + i * 130, y: 80 + (i % 2) * 60 }));

  return (
    <ChartCard title="Logic Connectivity Graph" subtitle="Inter-block failure correlation paths">
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
              <text x={node.x} y={node.y + 40} textAnchor="middle" fill="#94A3B8" fontSize="9">{node.label}</text>
            </g>
          ))}
        </svg>
      </div>
    </ChartCard>
  );
}

export function CoverageCorrelationChart() {
  return (
    <ChartCard title="Coverage Correlation" subtitle="Coverage vs. diagnosis confidence">
      <div className="relative h-[200px] overflow-hidden rounded-xl bg-[#0A1020]/60 p-4">
        <svg width="100%" height="100%" viewBox="0 0 600 160">
          <line x1="60" y1="140" x2="560" y2="140" stroke="#2D3748" strokeWidth={1} />
          <line x1="60" y1="20" x2="60" y2="140" stroke="#2D3748" strokeWidth={1} />
          {[{ x: 120, y: 100 }, { x: 220, y: 85 }, { x: 320, y: 70 }, { x: 420, y: 55 }, { x: 520, y: 40 }].map((p, i) => (
            <circle key={i} cx={p.x} cy={p.y} r={8} fill="#7C3AED" fillOpacity={0.4} stroke="#7C3AED" />
          ))}
          <polyline points="120,100 220,85 320,70 420,55 520,40" fill="none" stroke="#7C3AED" strokeWidth={2} />
        </svg>
      </div>
    </ChartCard>
  );
}
