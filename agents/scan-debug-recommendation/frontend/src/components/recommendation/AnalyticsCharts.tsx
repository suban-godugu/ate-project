"use client";

import { useCallback, useId, useRef, useState } from "react";
import type { ScanDebugDashboardData } from "@/types/kpiDrillDown";

type Slice = { name: string; value: number; fill: string };

function ChartCard({
  title,
  children,
  tall = false,
}: {
  title: string;
  children: React.ReactNode;
  tall?: boolean;
}) {
  return (
    <div className="glass-card gradient-border p-4">
      <h3 className="mb-3 text-sm font-medium text-slate-200">{title}</h3>
      <div className={tall ? "min-h-[15rem]" : "h-52"}>{children}</div>
    </div>
  );
}

function ChartTooltip({
  visible,
  x,
  y,
  containerRef,
  children,
}: {
  visible: boolean;
  x: number;
  y: number;
  containerRef: React.RefObject<HTMLDivElement | null>;
  children: React.ReactNode;
}) {
  if (!visible || !containerRef.current) return null;
  const rect = containerRef.current.getBoundingClientRect();
  const left = Math.min(Math.max(x - rect.left + 12, 8), rect.width - 168);
  const top = Math.max(y - rect.top - 48, 8);

  return (
    <div
      className="pointer-events-none absolute z-20 min-w-[140px] rounded-xl border border-border/80 bg-[#111827]/95 px-3 py-2 text-xs shadow-xl backdrop-blur-sm"
      style={{ left, top }}
    >
      {children}
    </div>
  );
}

function polar(cx: number, cy: number, r: number, deg: number) {
  const rad = ((deg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function ringSegment(
  cx: number,
  cy: number,
  rInner: number,
  rOuter: number,
  start: number,
  end: number
) {
  if (end - start >= 359.99) end = start + 359.99;
  const outerStart = polar(cx, cy, rOuter, end);
  const outerEnd = polar(cx, cy, rOuter, start);
  const innerEnd = polar(cx, cy, rInner, start);
  const innerStart = polar(cx, cy, rInner, end);
  const large = end - start > 180 ? 1 : 0;
  return [
    `M ${outerStart.x} ${outerStart.y}`,
    `A ${rOuter} ${rOuter} 0 ${large} 0 ${outerEnd.x} ${outerEnd.y}`,
    `L ${innerEnd.x} ${innerEnd.y}`,
    `A ${rInner} ${rInner} 0 ${large} 1 ${innerStart.x} ${innerStart.y}`,
    "Z",
  ].join(" ");
}

function DonutChart({
  data,
  centerValue,
  centerLabel,
  activeKey,
  onActiveKey,
}: {
  data: Slice[];
  centerValue: number;
  centerLabel: string;
  activeKey: string | null;
  onActiveKey: (key: string | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0 });
  const total = Math.max(data.reduce((sum, d) => sum + d.value, 0), 1);
  const cx = 84;
  const cy = 84;
  const rInner = 49;
  const rOuter = 67;
  let angle = 0;

  const segments = data.map((d, i) => {
    const sweep = (d.value / total) * 360;
    const start = angle;
    const end = angle + sweep;
    angle = end;
    return { ...d, start, end, key: `${d.name}-${i}` };
  });

  const active = segments.find((s) => s.key === activeKey) ?? null;

  const showTooltip = (key: string, clientX: number, clientY: number) => {
    onActiveKey(key);
    setTooltip({ visible: true, x: clientX, y: clientY });
  };

  return (
    <div
      ref={containerRef}
      className="relative flex h-full items-center justify-center"
      onMouseLeave={() => {
        onActiveKey(null);
        setTooltip((t) => ({ ...t, visible: false }));
      }}
    >
      <svg width="168" height="168" viewBox="0 0 168 168" className="overflow-visible">
        <circle cx={cx} cy={cy} r={(rInner + rOuter) / 2} fill="none" stroke="#1f2937" strokeWidth={rOuter - rInner} />
        {segments.map((s) => {
          const dimmed = activeKey !== null && activeKey !== s.key;
          return (
            <path
              key={s.key}
              d={ringSegment(cx, cy, rInner, rOuter, s.start, s.end)}
              fill={s.fill}
              opacity={dimmed ? 0.35 : 1}
              className="cursor-pointer transition-opacity duration-150"
              style={{
                filter: activeKey === s.key ? `drop-shadow(0 0 6px ${s.fill})` : undefined,
                transform: activeKey === s.key ? "scale(1.02)" : undefined,
                transformOrigin: `${cx}px ${cy}px`,
              }}
              onMouseEnter={(e) => showTooltip(s.key, e.clientX, e.clientY)}
              onMouseMove={(e) => showTooltip(s.key, e.clientX, e.clientY)}
            />
          );
        })}
      </svg>

      <div className="pointer-events-none absolute inset-0 grid place-items-center">
        <div className="text-center transition-all duration-150">
          {active ? (
            <>
              <div className="font-display text-xl font-semibold text-white">{active.value}</div>
              <div className="max-w-[88px] truncate text-[9px] uppercase tracking-wide text-muted">
                {active.name}
              </div>
              <div className="text-[10px] text-success">{((active.value / total) * 100).toFixed(1)}%</div>
            </>
          ) : (
            <>
              <div className="font-display text-2xl font-semibold text-white">{centerValue}</div>
              <div className="text-[10px] uppercase tracking-wide text-muted">{centerLabel}</div>
            </>
          )}
        </div>
      </div>

      <ChartTooltip visible={tooltip.visible} x={tooltip.x} y={tooltip.y} containerRef={containerRef}>
        {active ? (
          <>
            <div className="font-medium text-white">{active.name}</div>
            <div className="mt-1 text-slate-400">
              Count: <span className="text-white">{active.value}</span>
            </div>
            <div className="text-slate-400">
              Share: <span className="text-success">{((active.value / total) * 100).toFixed(1)}%</span>
            </div>
          </>
        ) : null}
      </ChartTooltip>
    </div>
  );
}

function RootCauseLegend({
  data,
  activeKey,
  onActiveKey,
}: {
  data: Slice[];
  activeKey: string | null;
  onActiveKey: (key: string | null) => void;
}) {
  const total = Math.max(data.reduce((sum, d) => sum + d.value, 0), 1);
  return (
    <div className="mt-2 space-y-1.5 px-1">
      {data.slice(0, 5).map((d, i) => {
        const key = `${d.name}-${i}`;
        const active = activeKey === key;
        return (
          <button
            key={key}
            type="button"
            className={`flex w-full items-center justify-between gap-2 rounded-lg px-1 py-0.5 text-left text-[11px] transition ${
              active ? "bg-white/10" : "hover:bg-white/5"
            }`}
            onMouseEnter={() => onActiveKey(key)}
            onMouseLeave={() => onActiveKey(null)}
            onFocus={() => onActiveKey(key)}
            onBlur={() => onActiveKey(null)}
          >
            <div className="flex min-w-0 items-center gap-2">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: d.fill }} />
              <span className={`truncate ${active ? "text-white" : "text-slate-400"}`}>{d.name}</span>
            </div>
            <span className="text-slate-300">
              {d.value}{" "}
              <span className="text-muted">({((d.value / total) * 100).toFixed(0)}%)</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

function HorizontalBars({
  data,
  activeKey,
  onActiveKey,
}: {
  data: Slice[];
  activeKey: string | null;
  onActiveKey: (key: string | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0 });
  const max = Math.max(...data.map((d) => d.value), 1);
  const total = data.reduce((sum, d) => sum + d.value, 0);

  const active = data.find((d) => d.name === activeKey) ?? null;

  return (
    <div
      ref={containerRef}
      className="relative flex h-full flex-col justify-center gap-3 px-1"
      onMouseLeave={() => {
        onActiveKey(null);
        setTooltip((t) => ({ ...t, visible: false }));
      }}
    >
      {data.map((d) => {
        const pct = (d.value / max) * 100;
        const active = activeKey === d.name;
        const dimmed = activeKey !== null && !active;
        return (
          <button
            key={d.name}
            type="button"
            className={`grid w-full grid-cols-[72px_1fr_36px] items-center gap-2 rounded-lg px-1 py-1 text-left text-xs transition ${
              active ? "bg-white/10" : "hover:bg-white/5"
            } ${dimmed ? "opacity-50" : "opacity-100"}`}
            onMouseEnter={(e) => {
              onActiveKey(d.name);
              setTooltip({ visible: true, x: e.clientX, y: e.clientY });
            }}
            onMouseMove={(e) => setTooltip({ visible: true, x: e.clientX, y: e.clientY })}
            onMouseLeave={() => onActiveKey(null)}
          >
            <span className={`truncate ${active ? "font-medium text-white" : "text-slate-400"}`}>
              {d.name}
            </span>
            <div className="h-3 overflow-hidden rounded-full bg-white/5">
              <div
                className="h-full rounded-full transition-all duration-200"
                style={{
                  width: `${pct}%`,
                  backgroundColor: d.fill,
                  boxShadow: active ? `0 0 10px ${d.fill}88` : undefined,
                }}
              />
            </div>
            <span className="text-right text-slate-300">{d.value}</span>
          </button>
        );
      })}

      <ChartTooltip visible={tooltip.visible && !!active} x={tooltip.x} y={tooltip.y} containerRef={containerRef}>
        {active ? (
          <>
            <div className="font-medium text-white">{active.name} Priority</div>
            <div className="mt-1 text-slate-400">
              Cases: <span className="text-white">{active.value}</span>
            </div>
            <div className="text-slate-400">
              Share:{" "}
              <span className="text-success">{total ? ((active.value / total) * 100).toFixed(1) : 0}%</span>
            </div>
          </>
        ) : null}
      </ChartTooltip>
    </div>
  );
}

function TrendArea({ data }: { data: { date: string; value: number }[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gradientId = useId().replace(/:/g, "");
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0 });

  const values = data.map((d) => d.value);
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = Math.max(max - min, 1);
  const w = 320;
  const h = 140;

  const points = data.map((d, i) => {
    const x = (i / Math.max(data.length - 1, 1)) * w;
    const y = h - ((d.value - min) / range) * (h - 12) - 6;
    return { ...d, x, y, i };
  });

  const line = points.map((p) => `${p.x},${p.y}`).join(" ");
  const area = `M0,${h} L${line.replace(/ /g, " L")} L${w},${h} Z`;
  const active = hoverIdx !== null ? points[hoverIdx] : null;

  const pickIndex = useCallback(
    (clientX: number, clientY: number) => {
      if (!containerRef.current) return;
      const svg = containerRef.current.querySelector("svg");
      if (!svg) return;
      const rect = svg.getBoundingClientRect();
      const relX = ((clientX - rect.left) / rect.width) * w;
      let nearest = 0;
      let dist = Infinity;
      points.forEach((p, i) => {
        const d = Math.abs(p.x - relX);
        if (d < dist) {
          dist = d;
          nearest = i;
        }
      });
      setHoverIdx(nearest);
      setTooltip({ visible: true, x: clientX, y: clientY });
    },
    [points, w]
  );

  return (
    <div
      ref={containerRef}
      className="relative flex h-full flex-col"
      onMouseLeave={() => {
        setHoverIdx(null);
        setTooltip((t) => ({ ...t, visible: false }));
      }}
    >
      <div className="mb-2 text-[10px] uppercase tracking-wide text-muted">Last 30 days</div>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        className="h-full w-full cursor-crosshair"
        onMouseMove={(e) => pickIndex(e.clientX, e.clientY)}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#7C3AED" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d={area} fill={`url(#${gradientId})`} />
        <polyline fill="none" stroke="#7C3AED" strokeWidth="2.5" points={line} />

        {active ? (
          <>
            <line
              x1={active.x}
              x2={active.x}
              y1={0}
              y2={h}
              stroke="#7C3AED"
              strokeWidth="1"
              strokeDasharray="4 4"
              opacity={0.5}
            />
            <circle cx={active.x} cy={active.y} r="5" fill="#7C3AED" stroke="#fff" strokeWidth="2" />
          </>
        ) : null}

        {points.map((p) => (
          <circle
            key={p.i}
            cx={p.x}
            cy={p.y}
            r="8"
            fill="transparent"
            className="cursor-pointer"
          />
        ))}
      </svg>

      <ChartTooltip visible={tooltip.visible && !!active} x={tooltip.x} y={tooltip.y} containerRef={containerRef}>
        {active ? (
          <>
            <div className="font-medium text-white">{active.date}</div>
            <div className="mt-1 text-slate-400">
              Recommendations: <span className="text-white">{active.value}</span>
            </div>
          </>
        ) : null}
      </ChartTooltip>
    </div>
  );
}

export function AnalyticsCharts({ data }: { data: ScanDebugDashboardData }) {
  const [donutActive, setDonutActive] = useState<string | null>(null);
  const [barActive, setBarActive] = useState<string | null>(null);

  const rootCause = data.rootCauseDistribution ?? [];
  const priority = data.recommendationPriority ?? [];
  const trend = data.recommendationTrend ?? [];
  const totalRootCauses = rootCause.reduce((sum, d) => sum + d.value, 0);

  const pieData = (rootCause.length ? rootCause : [{ name: "None", value: 1, fill: "#334155" }]).map(
    (d) => ({ ...d, fill: d.fill ?? "#7C3AED" })
  );

  const barData = (priority.length ? priority : [{ name: "None", value: 0, fill: "#334155" }]).map(
    (d) => ({ ...d, fill: d.fill ?? "#7C3AED" })
  );

  const trendData = trend.length ? trend : [{ date: "-", value: 0 }];

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <ChartCard title="Failure Root Cause Distribution" tall>
        <div className="h-40">
          <DonutChart
            data={pieData}
            centerValue={totalRootCauses}
            centerLabel="Root Causes"
            activeKey={donutActive}
            onActiveKey={setDonutActive}
          />
        </div>
        <RootCauseLegend data={pieData} activeKey={donutActive} onActiveKey={setDonutActive} />
      </ChartCard>

      <ChartCard title="Debug Recommendation Priority">
        <HorizontalBars data={barData} activeKey={barActive} onActiveKey={setBarActive} />
      </ChartCard>

      <ChartCard title="Recommendation Trend">
        <TrendArea data={trendData} />
      </ChartCard>
    </div>
  );
}
