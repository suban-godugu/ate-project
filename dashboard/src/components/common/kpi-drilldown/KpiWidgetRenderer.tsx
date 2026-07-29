"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import { cn } from "@/lib/utils";
import type { KpiWidgetSpec } from "@/types/kpiDrillDown";

const CHART_TOOLTIP = {
  contentStyle: {
    background: "#111827",
    border: "1px solid rgba(139,92,246,0.35)",
    borderRadius: 10,
    fontSize: 12,
  },
};

function seeded(seed: number, i: number): number {
  const x = Math.sin(seed + i * 777) * 10000;
  return x - Math.floor(x);
}

function seriesFromSeed(seed: number, count: number, base = 50) {
  return Array.from({ length: count }, (_, i) => ({
    name: `P${i + 1}`,
    value: Math.round(base * (0.7 + seeded(seed, i) * 0.5)),
    x: i,
    y: Math.round(base * (0.6 + seeded(seed, i + 10) * 0.6)),
    z: Math.round(20 + seeded(seed, i + 20) * 80),
  }));
}

function HeatmapGrid({ seed }: { seed: number }) {
  const rows = 8;
  const cols = 12;
  return (
    <div className="grid gap-0.5" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
      {Array.from({ length: rows * cols }, (_, i) => {
        const intensity = seeded(seed, i);
        return (
          <div
            key={i}
            className="aspect-square rounded-[3px] transition-transform hover:scale-110"
            style={{
              background: `rgba(139,92,246,${0.15 + intensity * 0.75})`,
              boxShadow: intensity > 0.75 ? "0 0 8px rgba(239,68,68,0.5)" : undefined,
            }}
            title={`Die ${i}: ${(intensity * 100).toFixed(0)}%`}
          />
        );
      })}
    </div>
  );
}

function WaferMap({ seed }: { seed: number }) {
  const size = 9;
  const cx = 4;
  const cy = 4;
  const r = 4.2;
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[220px]">
      <svg viewBox="0 0 9 9" className="h-full w-full">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(139,92,246,0.4)" strokeWidth="0.08" />
        {Array.from({ length: size * size }, (_, i) => {
          const x = i % size;
          const y = Math.floor(i / size);
          const dx = x - cx;
          const dy = y - cy;
          if (dx * dx + dy * dy > r * r) return null;
          const fail = seeded(seed, i) > 0.82;
          return (
            <rect
              key={i}
              x={x + 0.12}
              y={y + 0.12}
              width={0.76}
              height={0.76}
              rx={0.1}
              fill={fail ? "rgba(239,68,68,0.85)" : `rgba(16,185,129,${0.25 + seeded(seed, i) * 0.5})`}
            />
          );
        })}
      </svg>
    </div>
  );
}

function GaugeArc({ seed }: { seed: number }) {
  const pct = Math.round(55 + seeded(seed, 1) * 40);
  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative h-32 w-32">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          <circle cx="50" cy="50" r="42" fill="none" stroke="#1e293b" strokeWidth="8" />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="#8B5CF6"
            strokeWidth="8"
            strokeDasharray={`${pct * 2.64} 264`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{pct}%</span>
          <span className="text-[10px] text-slate-400">Target Attainment</span>
        </div>
      </div>
    </div>
  );
}

function CorrelationMatrix({ seed }: { seed: number }) {
  const labels = ["SC-1", "SC-2", "SC-3", "SC-4", "SC-5"];
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-center text-[10px]">
        <thead>
          <tr>
            <th />
            {labels.map((l) => (
              <th key={l} className="p-1 text-slate-500">
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {labels.map((row, ri) => (
            <tr key={row}>
              <td className="p-1 text-slate-500">{row}</td>
              {labels.map((_, ci) => {
                const v = ri === ci ? 1 : seeded(seed, ri * 10 + ci) * 2 - 1;
                const abs = Math.abs(v);
                return (
                  <td key={ci} className="p-0.5">
                    <div
                      className="rounded px-1 py-2 tabular-nums"
                      style={{
                        background:
                          v > 0
                            ? `rgba(139,92,246,${abs * 0.6})`
                            : `rgba(239,68,68,${abs * 0.5})`,
                      }}
                    >
                      {v.toFixed(2)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NetworkGraph({ seed }: { seed: number }) {
  const nodes = [
    { id: 0, x: 50, y: 20, label: "M1" },
    { id: 1, x: 20, y: 50, label: "SC-A" },
    { id: 2, x: 80, y: 50, label: "SC-B" },
    { id: 3, x: 35, y: 80, label: "PAT-1" },
    { id: 4, x: 65, y: 80, label: "PAT-2" },
  ];
  const edges = [
    [0, 1],
    [0, 2],
    [1, 3],
    [2, 4],
    [1, 2],
  ];
  return (
    <svg viewBox="0 0 100 100" className="h-full w-full">
      {edges.map(([a, b], i) => (
        <line
          key={i}
          x1={nodes[a].x}
          y1={nodes[a].y}
          x2={nodes[b].x}
          y2={nodes[b].y}
          stroke={seeded(seed, i) > 0.7 ? "#EF4444" : "rgba(139,92,246,0.5)"}
          strokeWidth="0.6"
        />
      ))}
      {nodes.map((n) => (
        <g key={n.id}>
          <circle cx={n.x} cy={n.y} r="6" fill="#121826" stroke="#8B5CF6" strokeWidth="1" />
          <text x={n.x} y={n.y + 12} textAnchor="middle" fill="#94A3B8" fontSize="4">
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}

function SankeyFlow({ seed }: { seed: number }) {
  const stages = [
    { label: "Patterns", count: 342 },
    { label: "Chains", count: 128 },
    { label: "Cells", count: 47 },
    { label: "Fails", count: 12 + Math.floor(seeded(seed, 1) * 8) },
  ];
  return (
    <div className="flex h-full items-stretch gap-2">
      {stages.map((s, i) => (
        <div key={s.label} className="flex flex-1 flex-col items-center gap-2">
          <div
            className="w-full flex-1 rounded-lg bg-gradient-to-b from-[#8B5CF6]/40 to-[#8B5CF6]/10"
            style={{ minHeight: 40 + (s.count / 342) * 120 }}
          />
          <span className="text-[10px] text-slate-400">{s.label}</span>
          <span className="text-xs font-semibold text-white">{s.count}</span>
          {i < stages.length - 1 && (
            <span className="absolute text-purple-400" aria-hidden="true">
              →
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

export function KpiWidgetRenderer({ widget }: { widget: KpiWidgetSpec }) {
  const seed = (widget.data.seed as number) ?? 42;
  const data = seriesFromSeed(seed, 12, 60);

  const chart = (() => {
    switch (widget.type) {
      case "line":
        return (
          <LineChart data={data}>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} />
            <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
            <Tooltip {...CHART_TOOLTIP} />
            <Line type="monotone" dataKey="value" stroke="#8B5CF6" strokeWidth={2} dot={false} />
          </LineChart>
        );
      case "area":
        return (
          <AreaChart data={data}>
            <defs>
              <linearGradient id={`grad-${widget.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} />
            <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
            <Tooltip {...CHART_TOOLTIP} />
            <Area type="monotone" dataKey="value" stroke="#8B5CF6" fill={`url(#grad-${widget.id})`} />
          </AreaChart>
        );
      case "bar":
      case "histogram":
      case "pareto":
      case "stacked-bar":
        return (
          <BarChart data={data}>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} />
            <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
            <Tooltip {...CHART_TOOLTIP} />
            <Bar dataKey="value" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
            {widget.type === "stacked-bar" && (
              <Bar dataKey="y" fill="#6366F1" radius={[4, 4, 0, 0]} opacity={0.6} />
            )}
          </BarChart>
        );
      case "scatter":
      case "bubble":
        return (
          <ScatterChart>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="x" stroke="#64748B" fontSize={10} tickLine={false} />
            <YAxis dataKey="y" stroke="#64748B" fontSize={10} tickLine={false} />
            {widget.type === "bubble" && <ZAxis dataKey="z" range={[40, 400]} />}
            <Tooltip {...CHART_TOOLTIP} />
            <Scatter data={data} fill="#8B5CF6" />
          </ScatterChart>
        );
      case "radar":
        return (
          <RadarChart data={data.slice(0, 6)}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis dataKey="name" tick={{ fill: "#64748B", fontSize: 9 }} />
            <PolarRadiusAxis tick={{ fill: "#64748B", fontSize: 8 }} />
            <Radar dataKey="value" stroke="#8B5CF6" fill="#8B5CF6" fillOpacity={0.25} />
          </RadarChart>
        );
      case "distribution":
        return (
          <AreaChart data={data}>
            <CartesianGrid stroke="#1e293b" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#64748B" fontSize={10} tickLine={false} />
            <YAxis stroke="#64748B" fontSize={10} tickLine={false} />
            <Tooltip {...CHART_TOOLTIP} />
            <Area type="basis" dataKey="value" stroke="#A78BFA" fill="rgba(167,139,250,0.2)" />
          </AreaChart>
        );
      case "treemap":
        return (
          <PieChart>
            <Pie data={data.slice(0, 5)} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={70} label>
              {data.slice(0, 5).map((_, i) => (
                <Cell key={i} fill={["#8B5CF6", "#6366F1", "#7C3AED", "#A78BFA", "#4F46E5"][i]} />
              ))}
            </Pie>
            <Tooltip {...CHART_TOOLTIP} />
          </PieChart>
        );
      case "heatmap":
        return <HeatmapGrid seed={seed} />;
      case "wafer-map":
        return <WaferMap seed={seed} />;
      case "gauge":
        return <GaugeArc seed={seed} />;
      case "correlation-matrix":
      case "similarity-matrix":
        return <CorrelationMatrix seed={seed} />;
      case "cluster":
        return <HeatmapGrid seed={seed + 99} />;
      case "network":
        return <NetworkGraph seed={seed} />;
      case "sankey":
        return <SankeyFlow seed={seed} />;
      case "timeline-mini":
        return (
          <div className="flex h-full items-end gap-1 px-2">
            {data.slice(0, 10).map((d, i) => (
              <div key={i} className="flex flex-1 flex-col items-center gap-1">
                <div
                  className="w-full rounded-t bg-[#8B5CF6]/70 transition-all hover:bg-[#8B5CF6]"
                  style={{ height: `${(d.value / 80) * 100}%`, minHeight: 8 }}
                />
                <span className="text-[8px] text-slate-500">{i + 1}</span>
              </div>
            ))}
          </div>
        );
      default:
        return (
          <LineChart data={data}>
            <Line type="monotone" dataKey="value" stroke="#8B5CF6" dot={false} />
          </LineChart>
        );
    }
  })();

  const isCustom = ["heatmap", "wafer-map", "gauge", "correlation-matrix", "similarity-matrix", "network", "sankey", "timeline-mini", "cluster"].includes(
    widget.type
  );

  return (
    <div
      className={cn(
        "glass-card group flex flex-col overflow-hidden rounded-xl border border-[rgba(139,92,246,0.2)] bg-[#0A1020]/60 p-4 transition-all hover:border-[rgba(139,92,246,0.45)]",
        widget.span === 2 ? "col-span-2" : "col-span-1"
      )}
      style={{ minHeight: widget.height }}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <div>
          <h4 className="text-sm font-semibold text-white">{widget.title}</h4>
        </div>
        <span className="rounded-md bg-[rgba(139,92,246,0.12)] px-2 py-0.5 text-[10px] uppercase tracking-wider text-[#A78BFA]">
          {widget.type}
        </span>
      </div>
      <div className={cn("min-h-0 flex-1", !isCustom && "h-[calc(100%-48px)]")}>
        {isCustom ? (
          <div className="flex h-full items-center justify-center">{chart}</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {chart}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
