"use client";

import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#7C3AED", "#EF4444", "#22C55E", "#F59E0B", "#38BDF8", "#A78BFA", "#FB7185", "#34D399"];

function countBy<T>(items: T[], keyFn: (item: T) => string): { label: string; value: number }[] {
  const map = new Map<string, number>();
  for (const item of items) {
    const key = keyFn(item) || "Unknown";
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return [...map.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value);
}

function ChartPanel({
  title,
  subtitle,
  children,
  tall = false,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  tall?: boolean;
}) {
  return (
    <div className="rounded-2xl border border-border/60 bg-[#0E1528]/70 p-4">
      <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-primary">{title}</div>
      {subtitle ? <p className="mb-3 text-xs text-slate-500">{subtitle}</p> : <div className="mb-3" />}
      <div className={tall ? "h-56" : "h-48"}>{children}</div>
    </div>
  );
}

const tooltipStyle = {
  background: "#111827",
  border: "1px solid #2D3748",
  borderRadius: 12,
  fontSize: 12,
};

function CountBarTooltip({
  active,
  payload,
  valueLabel,
}: {
  active?: boolean;
  payload?: { payload?: { label: string; value: number } }[];
  valueLabel: string;
}) {
  if (!active || !payload?.[0]?.payload) return null;
  const { label, value } = payload[0].payload;
  return (
    <div style={tooltipStyle} className="px-3 py-2">
      <div className="font-medium text-white">{label}</div>
      <div className="mt-1 text-slate-300">
        {value} {valueLabel}
      </div>
    </div>
  );
}

function SliceTooltip({
  active,
  payload,
  valueLabel,
}: {
  active?: boolean;
  payload?: { name?: string; value?: number }[];
  valueLabel: string;
}) {
  if (!active || !payload?.[0]) return null;
  const name = payload[0].name ?? "";
  const value = payload[0].value ?? 0;
  return (
    <div style={tooltipStyle} className="px-3 py-2">
      <div className="font-medium text-white">{name}</div>
      <div className="mt-1 text-slate-300">
        {value} {valueLabel}
      </div>
    </div>
  );
}

function shortenAxisLabel(label: string): string {
  return label
    .replace(/^Chain\s+/i, "Ch")
    .replace(/^LOT_/i, "L")
    .replace(/^channel/i, "Ch");
}

function axisLayout(barCount: number, labels: string[]) {
  const maxLen = Math.max(...labels.map((l) => shortenAxisLabel(l).length), 1);
  if (barCount <= 4 && maxLen <= 6) {
    return { angle: 0, textAnchor: "middle" as const, height: 28, bottom: 16, fontSize: 10 };
  }
  if (barCount <= 6 && maxLen <= 8) {
    return { angle: -32, textAnchor: "end" as const, height: 52, bottom: 40, fontSize: 9 };
  }
  return { angle: -48, textAnchor: "end" as const, height: 64, bottom: 52, fontSize: 9 };
}

function DistributionBarChart({
  data,
  color = "#7C3AED",
  maxBars = 8,
  valueLabel = "items",
  yAxisLabel,
}: {
  data: { label: string; value: number }[];
  color?: string;
  maxBars?: number;
  valueLabel?: string;
  yAxisLabel?: string;
}) {
  if (data.length === 0) {
    return <div className="grid h-full place-items-center text-sm text-slate-500">No data</div>;
  }
  const trimmed = data.slice(0, maxBars).map((d) => ({
    ...d,
    axisLabel: shortenAxisLabel(d.label),
  }));
  const layout = axisLayout(trimmed.length, trimmed.map((d) => d.label));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={trimmed}
        margin={{ top: 8, right: 8, left: 0, bottom: layout.bottom }}
        barCategoryGap="18%"
      >
        <XAxis
          dataKey="axisLabel"
          tick={{ fill: "#94A3B8", fontSize: layout.fontSize }}
          interval={0}
          angle={layout.angle}
          textAnchor={layout.textAnchor}
          height={layout.height}
          tickMargin={6}
          dy={layout.angle === 0 ? 0 : 4}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "#64748B", fontSize: 10 }}
          width={36}
          label={
            yAxisLabel
              ? {
                  value: yAxisLabel,
                  angle: -90,
                  position: "insideLeft",
                  fill: "#64748B",
                  fontSize: 9,
                }
              : undefined
          }
        />
        <Tooltip content={<CountBarTooltip valueLabel={valueLabel} />} />
        <Bar dataKey="value" fill={color} radius={[6, 6, 0, 0]} maxBarSize={42} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function SplitDonutChart({
  data,
  centerLabel,
  valueLabel = "items",
}: {
  data: { label: string; value: number }[];
  centerLabel: string;
  valueLabel?: string;
}) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) {
    return <div className="grid h-full place-items-center text-sm text-slate-500">No data</div>;
  }
  return (
    <div className="relative h-full">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="label"
            innerRadius="58%"
            outerRadius="82%"
            paddingAngle={2}
          >
            {data.map((_, i) => (
              <Cell key={data[i].label} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<SliceTooltip valueLabel={valueLabel} />} />
        </PieChart>
      </ResponsiveContainer>
      <div className="pointer-events-none absolute inset-0 grid place-items-center">
        <div className="text-center">
          <div className="font-display text-xl font-semibold text-white">{total}</div>
          <div className="text-[10px] uppercase tracking-wide text-slate-500">{centerLabel}</div>
        </div>
      </div>
    </div>
  );
}

function Legend({
  items,
  unit,
}: {
  items: { label: string; color: string; value: number }[];
  unit: string;
}) {
  return (
    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5 text-[11px] text-slate-400">
          <span className="h-2 w-2 rounded-full" style={{ background: item.color }} />
          <span>
            {item.label}: {item.value} {unit}
          </span>
        </div>
      ))}
    </div>
  );
}

type BreakRow = {
  chain?: string;
  lotId?: string;
  bit?: number | null;
  scanLength?: number;
};

export function BrokenChainsAnalytics({ rows }: { rows: BreakRow[] }) {
  const byChain = countBy(rows, (r) => r.chain ?? "Unknown");
  const byLot = countBy(rows, (r) => r.lotId ?? "Unknown");

  const positionBuckets = { "Scan-in": 0, "Mid-chain": 0, "Scan-out": 0, Unknown: 0 };
  for (const row of rows) {
    const bit = row.bit;
    const len = row.scanLength && row.scanLength > 1 ? row.scanLength : 234;
    if (bit == null) {
      positionBuckets.Unknown += 1;
      continue;
    }
    const frac = bit / (len - 1);
    if (frac <= 0.33) positionBuckets["Scan-in"] += 1;
    else if (frac >= 0.67) positionBuckets["Scan-out"] += 1;
    else positionBuckets["Mid-chain"] += 1;
  }
  const byPosition = Object.entries(positionBuckets)
    .filter(([, v]) => v > 0)
    .map(([label, value]) => ({ label, value }));

  const bitSeries = rows
    .filter((r) => r.bit != null && r.chain)
    .slice(0, 10)
    .map((r) => ({
      label: `${r.chain}`.replace("Chain ", "Ch"),
      value: r.bit as number,
    }));

  const positionLegend = byPosition.map((d, i) => ({
    label: d.label,
    color: COLORS[i % COLORS.length],
    value: d.value,
  }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          How breaks are spread across chains, lots, and positions on the scan path
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel
          title="Breaks by Chain"
          subtitle="Number of dies with a break on each scan chain"
          tall
        >
          <DistributionBarChart
            data={byChain}
            color="#EF4444"
            valueLabel="dies with a break"
            yAxisLabel="Dies"
          />
        </ChartPanel>
        <ChartPanel title="Breaks by Lot" subtitle="Number of broken dies in each production lot" tall>
          <DistributionBarChart
            data={byLot}
            color="#7C3AED"
            valueLabel="broken dies"
            yAxisLabel="Dies"
          />
        </ChartPanel>
        <ChartPanel
          title="Where the Break Sits"
          subtitle="Near scan-in, middle of chain, or near scan-out"
        >
          <SplitDonutChart data={byPosition} centerLabel="total breaks" valueLabel="breaks" />
          <Legend items={positionLegend} unit="breaks" />
        </ChartPanel>
        <ChartPanel
          title="Break Bit Position"
          subtitle="Exact bit index where the break was found (top cases)"
          tall
        >
          <DistributionBarChart
            data={bitSeries}
            color="#F59E0B"
            valueLabel="bit position"
            yAxisLabel="Bit #"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

export function ScanChainConfidenceAnalytics({
  rows,
}: {
  rows: {
    confidencePct?: number;
    patternConsistent?: number;
    patternTotal?: number;
    ambiguityGroup?: number;
    historicalMatchCount?: number;
    chain?: string;
  }[];
}) {
  const byChain = countBy(rows, (r) => r.chain ?? "Unknown");
  const confidenceBands = [
    { label: "High (≥70%)", value: rows.filter((r) => (r.confidencePct ?? 0) >= 70).length },
    {
      label: "Medium (30–69%)",
      value: rows.filter((r) => (r.confidencePct ?? 0) >= 30 && (r.confidencePct ?? 0) < 70).length,
    },
    { label: "Low (<30%)", value: rows.filter((r) => (r.confidencePct ?? 0) < 30).length },
  ].filter((d) => d.value > 0);

  const patternRatio = rows.slice(0, 10).map((r, i) => ({
    label: `R${r.confidencePct ?? i}`,
    value:
      r.patternTotal && r.patternTotal > 0
        ? Math.round(((r.patternConsistent ?? 0) / r.patternTotal) * 100)
        : 0,
  }));

  const histSplit = [
    { label: "With past match", value: rows.filter((r) => (r.historicalMatchCount ?? 0) > 0).length },
    { label: "No past match", value: rows.filter((r) => (r.historicalMatchCount ?? 0) === 0).length },
  ].filter((d) => d.value > 0);

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Confidence spread, pattern agreement %, and historical match coverage
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="Confidence Bands" subtitle="How many dies fall in each confidence range">
          <SplitDonutChart data={confidenceBands} centerLabel="dies" valueLabel="dies" />
        </ChartPanel>
        <ChartPanel title="Dies Scored per Chain" subtitle="Confidence rows per scan chain">
          <DistributionBarChart data={byChain} color="#7C3AED" valueLabel="dies scored" yAxisLabel="Dies" />
        </ChartPanel>
        <ChartPanel
          title="Pattern Agreement %"
          subtitle="Consistent failing patterns / total shift patterns"
          tall
        >
          <DistributionBarChart
            data={patternRatio}
            color="#22C55E"
            maxBars={10}
            valueLabel="% patterns consistent"
            yAxisLabel="%"
          />
        </ChartPanel>
        <ChartPanel title="Historical Match" subtitle="Dies with similar past debug cases">
          <SplitDonutChart data={histSplit} centerLabel="dies" valueLabel="dies" />
        </ChartPanel>
      </div>
    </section>
  );
}

export function ConstraintViolationsAnalytics({
  rows,
}: {
  rows: {
    fanoutSignal?: string;
    heldPins?: string;
    failingPatternCount?: number;
    totalFailingPatterns?: number;
    usedLotDifferential?: boolean;
    lotId?: string;
    affectedDies?: number;
    constraintCategory?: string;
    constraintCategoryLabel?: string;
  }[];
}) {
  const byCategory = countBy(rows, (r) => r.constraintCategoryLabel ?? r.constraintCategory ?? "Other");
  const byFanout = countBy(rows, (r) => r.fanoutSignal ?? "Unknown");
  const categoryLegend = byCategory.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));

  const patternCoverage = rows.slice(0, 10).map((r) => ({
    label: `${r.constraintCategoryLabel ?? "?"}/${r.fanoutSignal ?? "?"}`,
    value: r.failingPatternCount ?? 0,
  }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Reset vs Scan Enable vs Clock constraint violations
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Constraint Type" subtitle="Reset / Scan Enable / Clock">
          <SplitDonutChart data={byCategory} centerLabel="violations" valueLabel="violations" />
          <Legend items={categoryLegend} unit="violations" />
        </ChartPanel>
        <ChartPanel title="Category Counts" subtitle="How many typed violations in each class">
          <DistributionBarChart
            data={byCategory}
            color="#7C3AED"
            valueLabel="violations"
            yAxisLabel="Count"
          />
        </ChartPanel>
        <ChartPanel title="Fan-outs Hit" subtitle="Scan-in cones under typed constraints">
          <DistributionBarChart
            data={byFanout}
            color="#EF4444"
            valueLabel="violations"
            yAxisLabel="Count"
          />
        </ChartPanel>
        <ChartPanel
          title="Strongest Clusters"
          subtitle="Failing patterns in top typed violations"
          tall
        >
          <DistributionBarChart
            data={patternCoverage}
            color="#F59E0B"
            maxBars={10}
            valueLabel="patterns"
            yAxisLabel="Patterns"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

type RecRow = {
  chain?: string;
  faultType?: string;
  diagnosisRank?: number;
  historicalMatchCount?: number;
  historicalSimilarity?: number;
  failCount?: number;
};

export function ScanChainRecsAnalytics({ rows }: { rows: RecRow[] }) {
  const byChain = countBy(rows, (r) => r.chain ?? "Unknown");
  const byFault = countBy(rows, (r) => r.faultType ?? "unknown");

  let highHist = 0;
  let lowHist = 0;
  let noHist = 0;
  for (const row of rows) {
    const sim = row.historicalSimilarity ?? 0;
    const count = row.historicalMatchCount ?? 0;
    if (count === 0) noHist += 1;
    else if (sim >= 0.78) highHist += 1;
    else lowHist += 1;
  }
  const histSplit = [
    { label: "Strong past match", value: highHist },
    { label: "Weak past match", value: lowHist },
    { label: "No past match", value: noHist },
  ].filter((d) => d.value > 0);

  const topRanks = [...rows]
    .sort((a, b) => (a.diagnosisRank ?? 999) - (b.diagnosisRank ?? 999))
    .slice(0, 10)
    .map((r) => ({
      label: `Rank ${r.diagnosisRank ?? "?"}`,
      value: r.failCount ?? 1,
    }));
  const topRankCount = topRanks.length;

  const faultLegend = byFault.map((d, i) => ({
    label: d.label,
    color: COLORS[i % COLORS.length],
    value: d.value,
  }));

  const histLegend = histSplit.map((d, i) => ({
    label: d.label,
    color: COLORS[i % COLORS.length],
    value: d.value,
  }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Fault types, which chains need inspection, past debug matches, and most urgent dies
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel
          title="Fault Type"
          subtitle="How many dies show stuck-at-0 vs stuck-at-1 (from failure logs)"
        >
          <SplitDonutChart data={byFault} centerLabel="total dies" valueLabel="dies" />
          <Legend items={faultLegend} unit="dies" />
        </ChartPanel>
        <ChartPanel
          title="Dies to Inspect per Chain"
          subtitle="How many dies need Inspect Scan Chain on each chain"
        >
          <DistributionBarChart
            data={byChain}
            color="#7C3AED"
            valueLabel="dies to inspect"
            yAxisLabel="Dies"
          />
        </ChartPanel>
        <ChartPanel
          title="Past Debug Case Match"
          subtitle="Whether similar failures were seen and fixed before"
        >
          <SplitDonutChart data={histSplit} centerLabel="total recs" valueLabel="recommendations" />
          <Legend items={histLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel
          title="Most Urgent Dies"
          subtitle={`Top ${topRankCount} inspect priorities — taller bar = more scan mismatches`}
          tall
        >
          <DistributionBarChart
            data={topRanks}
            color="#EF4444"
            maxBars={10}
            valueLabel="scan mismatches"
            yAxisLabel="Mismatches"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

export function ConstraintReviewRecsAnalytics({
  rows,
}: {
  rows: {
    constraintCategory?: string;
    constraintCategoryLabel?: string;
    fanoutSignal?: string;
    historicalMatchCount?: number;
    recommendedAction?: string;
    failingPatternCount?: number;
  }[];
}) {
  const byCategory = countBy(rows, (r) => r.constraintCategoryLabel ?? r.constraintCategory ?? "Other");
  const byAction = countBy(rows, (r) => r.recommendedAction ?? "Review");
  const histSplit = [
    { label: "With historical cite", value: rows.filter((r) => (r.historicalMatchCount ?? 0) > 0).length },
    { label: "No historical cite", value: rows.filter((r) => (r.historicalMatchCount ?? 0) === 0).length },
  ].filter((d) => d.value > 0);
  const categoryLegend = byCategory.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const histLegend = histSplit.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const topPatterns = rows.slice(0, 10).map((r) => ({
    label: `${r.constraintCategoryLabel ?? "?"}/${r.fanoutSignal ?? "?"}`,
    value: r.failingPatternCount ?? 0,
  }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Review recommendations by constraint type, action, and historical cite coverage
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Constraint Type" subtitle="Reset / Scan Enable / Clock reviews">
          <SplitDonutChart data={byCategory} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={categoryLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Recommended Action" subtitle="Relax vs Tighten vs Review">
          <DistributionBarChart data={byAction} color="#7C3AED" valueLabel="recs" yAxisLabel="Count" />
        </ChartPanel>
        <ChartPanel title="Historical Cite" subtitle="Recommendations backed by past outcomes">
          <SplitDonutChart data={histSplit} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={histLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Strongest Evidence" subtitle="Failing patterns in top recommendations" tall>
          <DistributionBarChart
            data={topPatterns}
            color="#F59E0B"
            maxBars={10}
            valueLabel="patterns"
            yAxisLabel="Patterns"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

export function CoverageImpactAnalytics({
  rows,
}: {
  rows: {
    constraintCategory?: string;
    constraintCategoryLabel?: string;
    signature?: string;
    fanoutSignal?: string;
    coverageImpactPct?: number;
    associatedPatterns?: number;
    totalFailingPatterns?: number;
  }[];
}) {
  const byCategory = countBy(rows, (r) => r.constraintCategoryLabel ?? r.constraintCategory ?? "Other");
  const categoryLegend = byCategory.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const topPct = [...rows]
    .sort((a, b) => (b.coverageImpactPct ?? 0) - (a.coverageImpactPct ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.fanoutSignal ?? r.signature ?? "?",
      value: Math.round(Number(r.coverageImpactPct ?? 0) * 10) / 10,
    }));
  const bands = [
    { label: "≥10%", value: rows.filter((r) => (r.coverageImpactPct ?? 0) >= 10).length },
    {
      label: "5–9.9%",
      value: rows.filter((r) => (r.coverageImpactPct ?? 0) >= 5 && (r.coverageImpactPct ?? 0) < 10).length,
    },
    { label: "<5%", value: rows.filter((r) => (r.coverageImpactPct ?? 0) < 5).length },
  ].filter((d) => d.value > 0);

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Failing-pattern share per constraint signature (estimate only)
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="Signatures by Type" subtitle="Reset / Scan Enable / Clock">
          <SplitDonutChart data={byCategory} centerLabel="sigs" valueLabel="signatures" />
          <Legend items={categoryLegend} unit="sigs" />
        </ChartPanel>
        <ChartPanel title="Impact Bands" subtitle="How large each signature share is">
          <DistributionBarChart data={bands} color="#7C3AED" valueLabel="signatures" yAxisLabel="Count" />
        </ChartPanel>
        <ChartPanel title="Top Impact %" subtitle="Highest failing-pattern shares" tall>
          <DistributionBarChart
            data={topPct}
            color="#EF4444"
            maxBars={10}
            valueLabel="% of failing patterns"
            yAxisLabel="%"
          />
        </ChartPanel>
        <ChartPanel title="Note" subtitle="Proxy method">
          <p className="mt-6 text-sm leading-relaxed text-slate-300">
            Denominator = unique failing patterns across fail dies (ATE/bitmap proxy). Not full ATPG
            fault coverage.
          </p>
        </ChartPanel>
      </div>
    </section>
  );
}

export function TimingViolationsAnalytics({
  rows,
}: {
  rows: {
    kind?: string;
    worstSlackPs?: number;
    captureEdgeSpacingNs?: number;
    fastFrequencyMhz?: number;
    nearMinimumMargin?: boolean;
    patternLabel?: string;
  }[];
}) {
  const byKind = countBy(rows, (r) => (r.kind ? r.kind.charAt(0).toUpperCase() + r.kind.slice(1) : "Timing"));
  const kindLegend = byKind.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const marginSplit = [
    { label: "Near min margin", value: rows.filter((r) => r.nearMinimumMargin).length },
    { label: "Within band", value: rows.filter((r) => !r.nearMinimumMargin).length },
  ].filter((d) => d.value > 0);
  const worstSlack = [...rows]
    .sort((a, b) => (a.worstSlackPs ?? 0) - (b.worstSlackPs ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: Math.abs(Math.round(Number(r.worstSlackPs ?? 0))),
    }));
  const spacing = rows[0]?.captureEdgeSpacingNs;
  const freq = rows[0]?.fastFrequencyMhz;

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          At-speed / timing-correlated pattern fails vs STIL WaveformTable margin
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Kind" subtitle="Setup vs Hold">
          <SplitDonutChart data={byKind} centerLabel="patterns" valueLabel="patterns" />
          <Legend items={kindLegend} unit="patterns" />
        </ChartPanel>
        <ChartPanel title="Margin Proxy" subtitle="Near minimum defined margin">
          <DistributionBarChart data={marginSplit} color="#EF4444" valueLabel="patterns" yAxisLabel="Count" />
        </ChartPanel>
        <ChartPanel title="Worst Slack" subtitle="|slack| (ps) for top patterns" tall>
          <DistributionBarChart
            data={worstSlack}
            color="#F59E0B"
            maxBars={10}
            valueLabel="ps"
            yAxisLabel="|slack| ps"
          />
        </ChartPanel>
        <ChartPanel title="STIL Timing" subtitle="WaveformTable proxy">
          <p className="mt-6 text-sm leading-relaxed text-slate-300">
            Fast set ≈ {freq ?? "—"}MHz · capture edge spacing ≈ {spacing ?? "—"}ns (relative
            launch/capture edge delta from WaveformTable).
          </p>
        </ChartPanel>
      </div>
    </section>
  );
}

export function TimingDebugRecsAnalytics({
  rows,
}: {
  rows: {
    kind?: string;
    historicalMatchCount?: number;
    clockDomain?: string;
    diagnosisTransitionPathDelay?: boolean;
    patternLabel?: string;
  }[];
}) {
  const byKind = countBy(rows, (r) => (r.kind ? r.kind.charAt(0).toUpperCase() + r.kind.slice(1) : "Timing"));
  const kindLegend = byKind.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const histSplit = [
    { label: "With historical cite", value: rows.filter((r) => (r.historicalMatchCount ?? 0) > 0).length },
    { label: "No historical cite", value: rows.filter((r) => (r.historicalMatchCount ?? 0) === 0).length },
  ].filter((d) => d.value > 0);
  const histLegend = histSplit.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const diagSplit = [
    {
      label: "Transition/path-delay",
      value: rows.filter((r) => r.diagnosisTransitionPathDelay).length,
    },
    {
      label: "Other timing",
      value: rows.filter((r) => !r.diagnosisTransitionPathDelay).length,
    },
  ].filter((d) => d.value > 0);
  const topHist = [...rows]
    .sort((a, b) => (b.historicalMatchCount ?? 0) - (a.historicalMatchCount ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: r.historicalMatchCount ?? 0,
    }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Capture-window reviews by kind, diagnosis flag, and historical frequency cites
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Kind" subtitle="Setup vs Hold recommendations">
          <SplitDonutChart data={byKind} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={kindLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Historical Cite" subtitle="Recommendations with frequency history">
          <SplitDonutChart data={histSplit} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={histLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Diagnosis Flag" subtitle="Transition / path-delay from diagnosis">
          <DistributionBarChart data={diagSplit} color="#7C3AED" valueLabel="recs" yAxisLabel="Count" />
        </ChartPanel>
        <ChartPanel title="Top Historical Counts" subtitle="Patterns with most frequency cites" tall>
          <DistributionBarChart
            data={topHist}
            color="#F59E0B"
            maxBars={10}
            valueLabel="historical cases"
            yAxisLabel="Cases"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

export function WorstSlackAnalytics({
  rows,
}: {
  rows: {
    kind?: string;
    worstSlackPs?: number;
    frequencyMarginPct?: number;
    failFrequencyMhz?: number;
    passFrequencyMhz?: number;
    patternLabel?: string;
  }[];
}) {
  const byKind = countBy(rows, (r) => (r.kind ? r.kind.charAt(0).toUpperCase() + r.kind.slice(1) : "Timing"));
  const kindLegend = byKind.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const worstSlack = [...rows]
    .sort((a, b) => (a.worstSlackPs ?? 0) - (b.worstSlackPs ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: Math.abs(Math.round(Number(r.worstSlackPs ?? 0))),
    }));
  const margins = [...rows]
    .sort((a, b) => (a.frequencyMarginPct ?? 0) - (b.frequencyMarginPct ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: Math.round(Number(r.frequencyMarginPct ?? 0) * 10) / 10,
    }));
  const sample = rows[0];

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Fail vs pass MHz frequency margin proxy and worst slack (ps)
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Kind" subtitle="Setup vs Hold">
          <SplitDonutChart data={byKind} centerLabel="patterns" valueLabel="patterns" />
          <Legend items={kindLegend} unit="patterns" />
        </ChartPanel>
        <ChartPanel title="Worst Slack" subtitle="|slack| (ps)" tall>
          <DistributionBarChart
            data={worstSlack}
            color="#EF4444"
            maxBars={10}
            valueLabel="ps"
            yAxisLabel="|slack| ps"
          />
        </ChartPanel>
        <ChartPanel title="Freq Margin %" subtitle="(f_fail − f_pass) / f_fail" tall>
          <DistributionBarChart
            data={margins}
            color="#F59E0B"
            maxBars={10}
            valueLabel="% margin"
            yAxisLabel="%"
          />
        </ChartPanel>
        <ChartPanel title="Timing Sets" subtitle="Fail / pass frequencies">
          <p className="mt-6 text-sm leading-relaxed text-slate-300">
            Fails at {sample?.failFrequencyMhz ?? "—"}MHz, passes at {sample?.passFrequencyMhz ?? "—"}
            MHz — margin proxy from timing-set spacing.
          </p>
        </ChartPanel>
      </div>
    </section>
  );
}

export function PowerViolationsAnalytics({
  rows,
  summary,
}: {
  rows: {
    kind?: string;
    irDropMv?: number;
    thermalC?: number;
    flaggedDespitePass?: boolean;
    patternLabel?: string;
    status?: string;
  }[];
  summary?: {
    count?: number;
    totalPatternsInRun?: number;
    flaggedDespitePass?: number;
    byKind?: Record<string, number>;
  };
}) {
  const kindLabels: Record<string, string> = {
    ir_drop: "IR Drop",
    thermal: "Thermal",
    both: "IR+Thermal",
  };

  // Prefer full unique-pattern summary (not the truncated top-N workspace rows).
  const byKind =
    summary?.byKind && Object.keys(summary.byKind).length > 0
      ? Object.entries(summary.byKind)
          .map(([key, value]) => ({
            label: kindLabels[key] ?? key,
            value: Number(value) || 0,
          }))
          .filter((d) => d.value > 0)
          .sort((a, b) => b.value - a.value)
      : countBy(rows, (r) => {
          if (r.kind === "ir_drop") return "IR Drop";
          if (r.kind === "thermal") return "Thermal";
          if (r.kind === "both") return "IR+Thermal";
          return "Other";
        });

  const kindLegend = byKind.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));

  const totalFlagged = summary?.count ?? rows.length;
  const despitePass =
    summary?.flaggedDespitePass ?? rows.filter((r) => r.flaggedDespitePass).length;
  const statusSplit = [
    { label: "Despite PASS", value: despitePass },
    { label: "STATUS=FAIL", value: Math.max(0, totalFlagged - despitePass) },
  ].filter((d) => d.value > 0);

  const topIr = [...rows]
    .filter((r) => r.irDropMv != null)
    .sort((a, b) => (b.irDropMv ?? 0) - (a.irDropMv ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: Math.round(Number(r.irDropMv ?? 0)),
    }));
  const topTh = [...rows]
    .filter((r) => r.thermalC != null)
    .sort((a, b) => (b.thermalC ?? 0) - (a.thermalC ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: Math.round(Number(r.thermalC ?? 0)),
    }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Full unique-pattern totals out of {summary?.totalPatternsInRun ?? 1000} (IR / thermal /
          PASS status). Bar charts below use the top severity sample.
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Kind" subtitle="IR vs Thermal vs both (all unique patterns)">
          <SplitDonutChart data={byKind} centerLabel="patterns" valueLabel="patterns" />
          <Legend items={kindLegend} unit="patterns" />
        </ChartPanel>
        <ChartPanel title="Status" subtitle="PASS vs FAIL among flagged">
          <DistributionBarChart data={statusSplit} color="#7C3AED" valueLabel="patterns" yAxisLabel="Count" />
        </ChartPanel>
        <ChartPanel title="Highest IR Drop" subtitle="mV (top patterns in view)" tall>
          <DistributionBarChart data={topIr} color="#EF4444" maxBars={10} valueLabel="mV" yAxisLabel="mV" />
        </ChartPanel>
        <ChartPanel title="Highest Thermal" subtitle="°C (top patterns in view)" tall>
          <DistributionBarChart data={topTh} color="#F59E0B" maxBars={10} valueLabel="°C" yAxisLabel="°C" />
        </ChartPanel>
      </div>
    </section>
  );
}

export function PowerDebugRecsAnalytics({
  rows,
  summary,
}: {
  rows: {
    kind?: string;
    historicalMatchCount?: number;
    pctAboveThreshold?: number;
    flaggedDespitePass?: boolean;
    patternLabel?: string;
    irDropMv?: number;
  }[];
  summary?: { count?: number; workspaceRows?: number };
}) {
  const kindLabels: Record<string, string> = {
    ir_drop: "IR Drop",
    thermal: "Thermal",
    both: "IR+Thermal",
  };
  const byKind = countBy(rows, (r) => kindLabels[r.kind ?? ""] ?? (r.kind ? String(r.kind) : "Other"));
  const kindLegend = byKind.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const histSplit = [
    { label: "With historical cite", value: rows.filter((r) => (r.historicalMatchCount ?? 0) > 0).length },
    { label: "No historical cite", value: rows.filter((r) => (r.historicalMatchCount ?? 0) === 0).length },
  ].filter((d) => d.value > 0);
  const histLegend = histSplit.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const statusSplit = [
    { label: "Despite PASS", value: rows.filter((r) => r.flaggedDespitePass).length },
    { label: "STATUS=FAIL", value: rows.filter((r) => !r.flaggedDespitePass).length },
  ].filter((d) => d.value > 0);
  const topHist = [...rows]
    .sort((a, b) => (b.historicalMatchCount ?? 0) - (a.historicalMatchCount ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: r.historicalMatchCount ?? 0,
    }));
  const total = summary?.count ?? rows.length;

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          IR-drop capture checks by kind and historical precedent ({total} recommendations
          {summary?.workspaceRows != null && summary.workspaceRows < total
            ? `; showing ${summary.workspaceRows}`
            : ""}
          )
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <ChartPanel title="By Kind" subtitle="IR vs Thermal vs both">
          <SplitDonutChart data={byKind} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={kindLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Historical Cite" subtitle="Similar IR-drop fail precedents">
          <SplitDonutChart data={histSplit} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={histLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Status" subtitle="PASS vs FAIL among recommended">
          <DistributionBarChart data={statusSplit} color="#7C3AED" valueLabel="recs" yAxisLabel="Count" />
        </ChartPanel>
        <ChartPanel title="Top Historical Counts" subtitle="Patterns with most IR-fail cites" tall>
          <DistributionBarChart
            data={topHist}
            color="#F59E0B"
            maxBars={10}
            valueLabel="historical cases"
            yAxisLabel="Cases"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

export function PeakSwitchingAnalytics({
  rows,
  summary,
}: {
  rows: {
    patternLabel?: string;
    irDropMv?: number;
    avgIrDropMv?: number;
    deltaVsAvgMv?: number;
    isPeak?: boolean;
  }[];
  summary?: {
    peakIrDropMv?: number;
    avgIrDropMv?: number;
    patternCount?: number;
  };
}) {
  const peak = summary?.peakIrDropMv ?? rows.find((r) => r.isPeak)?.irDropMv ?? rows[0]?.irDropMv;
  const avg = summary?.avgIrDropMv ?? rows[0]?.avgIrDropMv;
  const vsAvg = [
    { label: "Peak IR", value: Math.round(Number(peak ?? 0)) },
    { label: "Run avg", value: Math.round(Number(avg ?? 0)) },
  ].filter((d) => d.value > 0);
  const topIr = [...rows]
    .sort((a, b) => (b.irDropMv ?? 0) - (a.irDropMv ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.patternLabel ?? "?",
      value: Math.round(Number(r.irDropMv ?? 0)),
    }));
  const aboveAvg = rows.filter((r) => (r.deltaVsAvgMv ?? 0) > 0).length;
  const belowAvg = rows.filter((r) => (r.deltaVsAvgMv ?? 0) <= 0).length;
  const split = [
    { label: "Above avg", value: aboveAvg },
    { label: "At/below avg", value: belowAvg },
  ].filter((d) => d.value > 0);
  const splitLegend = split.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          IR_DROP_MV as switching-activity proxy — peak vs run average
          {summary?.patternCount != null ? ` across ${summary.patternCount} patterns` : ""}
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <ChartPanel title="Peak vs Average" subtitle="mV (switching proxy)">
          <DistributionBarChart data={vsAvg} color="#EF4444" valueLabel="mV" yAxisLabel="mV" />
        </ChartPanel>
        <ChartPanel title="Vs Run Average" subtitle="Patterns in view">
          <SplitDonutChart data={split} centerLabel="patterns" valueLabel="patterns" />
          <Legend items={splitLegend} unit="patterns" />
        </ChartPanel>
        <ChartPanel title="Highest IR Drop" subtitle="mV by pattern" tall>
          <DistributionBarChart data={topIr} color="#F59E0B" maxBars={10} valueLabel="mV" yAxisLabel="mV" />
        </ChartPanel>
      </div>
    </section>
  );
}

export function DefectSuspectsAnalytics({
  rows,
  summary,
}: {
  rows: {
    netId?: string;
    rootCause?: string;
    consistencyRatio?: number;
    consistentPatterns?: number;
    totalFailingPatterns?: number;
    confidencePct?: number;
    diagnosisRank?: number;
  }[];
  summary?: {
    count?: number;
    byRootCause?: Record<string, number>;
    topConsistency?: string;
  };
}) {
  const byRoot =
    summary?.byRootCause && Object.keys(summary.byRootCause).length > 0
      ? Object.entries(summary.byRootCause)
          .map(([label, value]) => ({ label, value: Number(value) || 0 }))
          .filter((d) => d.value > 0)
          .sort((a, b) => b.value - a.value)
      : countBy(rows, (r) => r.rootCause || "Unknown");
  const rootLegend = byRoot.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const topConsistency = [...rows]
    .sort((a, b) => (b.consistencyRatio ?? 0) - (a.consistencyRatio ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.netId ?? `R${r.diagnosisRank ?? "?"}`,
      value: Math.round((r.consistencyRatio ?? 0) * 100),
    }));
  const topConf = [...rows]
    .sort((a, b) => (b.confidencePct ?? 0) - (a.confidencePct ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.netId ?? "?",
      value: Math.round(Number(r.confidencePct ?? 0)),
    }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Ranked diagnosis nets by root-cause class and failing-pattern consistency
          {summary?.count != null ? ` (${summary.count} top suspects)` : ""}
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <ChartPanel title="By Root Cause" subtitle="Physical defect classes">
          <SplitDonutChart data={byRoot} centerLabel="suspects" valueLabel="suspects" />
          <Legend items={rootLegend} unit="suspects" />
        </ChartPanel>
        <ChartPanel title="Pattern Consistency" subtitle="% of failing patterns" tall>
          <DistributionBarChart
            data={topConsistency}
            color="#7C3AED"
            maxBars={10}
            valueLabel="%"
            yAxisLabel="%"
          />
        </ChartPanel>
        <ChartPanel title="Diagnosis Confidence" subtitle="FR-002 confidence %" tall>
          <DistributionBarChart data={topConf} color="#F59E0B" maxBars={10} valueLabel="%" yAxisLabel="%" />
        </ChartPanel>
      </div>
    </section>
  );
}

export function InvestigationRecsAnalytics({
  rows,
  summary,
}: {
  rows: {
    faultHypothesis?: string;
    powerInducedRuledOut?: boolean;
    historicalMatchCount?: number;
    transitionFaultCount?: number;
    irDropMv?: number;
    netId?: string;
    pfaTechnique?: string;
  }[];
  summary?: {
    count?: number;
    byFaultHypothesis?: Record<string, number>;
    ruledOutCount?: number;
    transitionFaultCount?: number;
    irDropMv?: number;
    irThresholdMv?: number;
  };
}) {
  const byHyp =
    summary?.byFaultHypothesis && Object.keys(summary.byFaultHypothesis).length > 0
      ? Object.entries(summary.byFaultHypothesis)
          .map(([label, value]) => ({ label, value: Number(value) || 0 }))
          .filter((d) => d.value > 0)
          .sort((a, b) => b.value - a.value)
      : countBy(rows, (r) => r.faultHypothesis || "Unknown");
  const hypLegend = byHyp.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const ruled = [
    {
      label: "Power false-fail ruled out",
      value: summary?.ruledOutCount ?? rows.filter((r) => r.powerInducedRuledOut).length,
    },
    {
      label: "Needs verify",
      value: rows.filter((r) => !r.powerInducedRuledOut).length,
    },
  ].filter((d) => d.value > 0);
  const ruledLegend = ruled.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const topHist = [...rows]
    .sort((a, b) => (b.historicalMatchCount ?? 0) - (a.historicalMatchCount ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.netId ?? "?",
      value: r.historicalMatchCount ?? 0,
    }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Fault hypotheses, TF/IR power false-fail cross-check
          {summary?.transitionFaultCount != null
            ? ` (TF count=${summary.transitionFaultCount}`
            : ""}
          {summary?.irDropMv != null ? `, IR ${summary.irDropMv}mV` : ""}
          {summary?.transitionFaultCount != null || summary?.irDropMv != null ? ")" : ""}
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <ChartPanel title="Fault Hypothesis" subtitle="Suspected defect class">
          <SplitDonutChart data={byHyp} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={hypLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Power Cross-Check" subtitle="TF present + normal IR">
          <SplitDonutChart data={ruled} centerLabel="recs" valueLabel="recommendations" />
          <Legend items={ruledLegend} unit="recs" />
        </ChartPanel>
        <ChartPanel title="Historical PFA Cites" subtitle="Matching diagnosis signatures" tall>
          <DistributionBarChart
            data={topHist}
            color="#F59E0B"
            maxBars={10}
            valueLabel="historical cases"
            yAxisLabel="Cases"
          />
        </ChartPanel>
      </div>
    </section>
  );
}

export function DefectLocalizationAnalytics({
  rows,
  summary,
}: {
  rows: {
    netId?: string;
    confidencePct?: number;
    debugPriority?: string;
    xyAvailable?: boolean;
    powerInducedRuledOut?: boolean;
  }[];
  summary?: {
    averageConfidencePct?: number;
    byPriority?: Record<string, number>;
    xyAvailableCount?: number;
    count?: number;
  };
}) {
  const byPri =
    summary?.byPriority && Object.keys(summary.byPriority).length > 0
      ? Object.entries(summary.byPriority)
          .map(([label, value]) => ({ label, value: Number(value) || 0 }))
          .filter((d) => d.value > 0)
          .sort((a, b) => b.value - a.value)
      : countBy(rows, (r) => r.debugPriority || "Medium");
  const priLegend = byPri.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const xySplit = [
    {
      label: "XY localized",
      value: summary?.xyAvailableCount ?? rows.filter((r) => r.xyAvailable).length,
    },
    {
      label: "No XY",
      value: rows.filter((r) => !r.xyAvailable).length,
    },
  ].filter((d) => d.value > 0);
  const xyLegend = xySplit.map((d, i) => ({
    label: d.label,
    value: d.value,
    color: COLORS[i % COLORS.length],
  }));
  const topConf = [...rows]
    .sort((a, b) => (b.confidencePct ?? 0) - (a.confidencePct ?? 0))
    .slice(0, 10)
    .map((r) => ({
      label: r.netId ?? "?",
      value: r.confidencePct ?? 0,
    }));

  return (
    <section className="mb-2">
      <div className="mb-3">
        <div className="text-[10px] uppercase tracking-[0.16em] text-primary">Analytics</div>
        <p className="mt-1 text-sm text-slate-400">
          Localization confidence from analyzed recommendations
          {summary?.averageConfidencePct != null
            ? ` — average ${summary.averageConfidencePct}%`
            : ""}
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        <ChartPanel title="Debug Priority" subtitle="FR-009 priority class">
          <SplitDonutChart data={byPri} centerLabel="nets" valueLabel="nets" />
          <Legend items={priLegend} unit="nets" />
        </ChartPanel>
        <ChartPanel title="XY Availability" subtitle="Die-local / wafer coordinates">
          <SplitDonutChart data={xySplit} centerLabel="nets" valueLabel="nets" />
          <Legend items={xyLegend} unit="nets" />
        </ChartPanel>
        <ChartPanel title="Top Confidence" subtitle="Localization % by net" tall>
          <DistributionBarChart data={topConf} color="#7C3AED" maxBars={10} valueLabel="%" yAxisLabel="%" />
        </ChartPanel>
      </div>
    </section>
  );
}
