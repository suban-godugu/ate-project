import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Gauge, Layers, Percent, TrendingUp } from "lucide-react";
import { CategoryCountBars, RiskDonut } from "@/components/charts";
import { Badge, Card, EmptyState, ErrorState, Spinner, StatCard } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate, num, pct, riskHex, riskTone } from "@/lib/format";
import type { RiskLevel } from "@/lib/types";

export function AnalyticsPage() {
  const analytics = useQuery({
    queryKey: ["analytics"],
    queryFn: api.analytics,
  });

  if (analytics.isLoading) return <Spinner label="Loading analytics…" />;
  if (analytics.isError) {
    return (
      <ErrorState message={(analytics.error as Error).message} onRetry={() => analytics.refetch()} />
    );
  }
  if (!analytics.data) return null;

  const data = analytics.data;

  const actionMix = data.recent.length
    ? [
        {
          name: "Yield",
          value: data.recent.reduce((sum, r) => sum + r.yield_recommendations.length, 0),
        },
        {
          name: "Cost",
          value: data.recent.reduce((sum, r) => sum + r.cost_recommendations.length, 0),
        },
        {
          name: "Coverage",
          value: data.recent.reduce((sum, r) => sum + r.coverage_recommendations.length, 0),
        },
        {
          name: "Production",
          value: data.recent.reduce((sum, r) => sum + r.production_recommendations.length, 0),
        },
      ]
    : [];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total recommendations"
          value={String(data.total_recommendations)}
          hint="Persisted by the agent"
          icon={<Layers className="h-4 w-4" />}
        />
        <StatCard
          label="Avg confidence"
          value={pct(data.avg_confidence)}
          hint="Across all recommendations"
          icon={<Gauge className="h-4 w-4" />}
        />
        <StatCard
          label="Avg yield"
          value={data.avg_yield === null ? "N/A" : `${num(data.avg_yield)}%`}
          hint="From supplied yield data"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          label="High-risk share"
          value={
            data.total_recommendations > 0
              ? pct((data.risk_distribution.High ?? 0) / data.total_recommendations)
              : "0%"
          }
          hint="Lots flagged high risk"
          icon={<Percent className="h-4 w-4" />}
          tone="text-rose-300"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Risk Distribution" subtitle="Recommendations by risk level">
          <RiskDonut data={data.risk_distribution} />
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            {Object.entries(data.risk_distribution).map(([level, count]) => (
              <span key={level} className="flex items-center gap-1.5 text-xs text-ink-300">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: riskHex[level as RiskLevel] ?? "#818cf8" }}
                />
                {level}
                <span className="num text-ink-100">{count}</span>
              </span>
            ))}
          </div>
        </Card>

        <Card
          title="Action Mix"
          subtitle="Recommended actions by category (recent)"
          className="lg:col-span-2"
        >
          {actionMix.length === 0 ? (
            <EmptyState message="No recent recommendations to summarize." />
          ) : (
            <CategoryCountBars data={actionMix} />
          )}
        </Card>
      </div>

      <Card title="Recent Recommendations" subtitle="Latest agent decisions">
        {data.recent.length === 0 ? (
          <EmptyState message="No recommendations generated yet." />
        ) : (
          <ul className="space-y-2">
            {data.recent.map((rec) => (
              <li key={rec.id}>
                <Link
                  to={`/recommendations/${rec.id}`}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-white/8 bg-base-800/60 p-3 transition hover:border-brand-500/40"
                >
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={riskTone[rec.risk_level]}>{rec.risk_level}</Badge>
                      <span className="text-sm font-medium text-ink-100">{rec.device}</span>
                      <span className="num text-xs text-ink-400">{rec.lot_id}</span>
                    </div>
                    <p className="mt-1 line-clamp-1 text-xs text-ink-300">{rec.summary}</p>
                  </div>
                  <span className="num text-[11px] text-ink-400">
                    {formatDate(rec.created_at)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
