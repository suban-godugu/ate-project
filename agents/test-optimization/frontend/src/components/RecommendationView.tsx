import { Clock, DollarSign, ShieldAlert, TrendingUp } from "lucide-react";
import { Badge, Card, StatCard } from "./ui";
import { ConfidenceBars, RiskScoreGauge } from "./charts";
import {
  AssumptionsCard,
  MultiSiteCard,
  RecommendationItems,
  StrategyBlocks,
} from "./RecommendationBlocks";
import { formatDate, pct, riskTone } from "@/lib/format";
import type { OptimizationRecommendation } from "@/lib/types";

export function RecommendationView({ rec }: { rec: OptimizationRecommendation }) {
  const confidenceRows = [
    { name: "Adaptive Testing", value: Math.round(rec.adaptive_testing.confidence * 100) },
    { name: "Test Stop", value: Math.round(rec.test_stop.confidence * 100) },
    { name: "Risk-Based", value: Math.round(rec.risk_based_testing.confidence * 100) },
    ...(rec.multi_site_optimization
      ? [{ name: "Multi-Site", value: Math.round(rec.multi_site_optimization.confidence * 100) }]
      : []),
  ];

  return (
    <div className="space-y-4">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={riskTone[rec.risk_level]}>{rec.risk_level} risk</Badge>
              <Badge>{rec.device}</Badge>
              <Badge>{rec.lot_id}</Badge>
              <Badge
                tone={
                  rec.engine === "llm"
                    ? "border-brand-500/30 bg-brand-500/10 text-brand-300"
                    : "border-white/10 bg-white/5 text-ink-200"
                }
              >
                {rec.engine === "llm" ? "LLM" : "Heuristic"}
              </Badge>
            </div>
            <p className="mt-2 text-sm leading-relaxed text-ink-100">{rec.summary}</p>
            <p className="mt-1 text-xs text-ink-400">
              Generated {formatDate(rec.created_at)} · <span className="num">{rec.id}</span>
            </p>
          </div>
        </div>
        <div className="mt-3 rounded-lg border border-brand-500/20 bg-brand-600/10 p-3">
          <p className="text-[11px] font-medium uppercase tracking-wide text-brand-300">
            Recommended strategy
          </p>
          <p className="num mt-1 text-sm text-ink-100">{rec.recommended_strategy}</p>
        </div>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Confidence"
          value={pct(rec.confidence)}
          hint="Overall recommendation confidence"
          icon={<ShieldAlert className="h-4 w-4" />}
        />
        <StatCard
          label="Time reduction"
          value={rec.estimated_time_reduction}
          hint="Estimated test time impact"
          icon={<Clock className="h-4 w-4" />}
        />
        <StatCard
          label="Cost reduction"
          value={rec.estimated_cost_reduction}
          hint="Estimated cost of test impact"
          icon={<DollarSign className="h-4 w-4" />}
        />
        <StatCard
          label="Yield improvement"
          value={rec.expected_yield_improvement}
          hint="Expected yield delta"
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Risk Score" subtitle={`${rec.risk_level} · ${rec.risk_score}/100`}>
          <div className="relative">
            <RiskScoreGauge score={rec.risk_score} level={rec.risk_level} />
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center pt-4">
              <span className="num text-3xl font-semibold text-ink-100">{rec.risk_score}</span>
              <span className="text-[11px] text-ink-400">of 100</span>
            </div>
          </div>
        </Card>
        <Card
          title="Confidence by Decision Block"
          subtitle="Per-block agent confidence"
          className="lg:col-span-2"
        >
          <ConfidenceBars data={confidenceRows} />
        </Card>
      </div>

      <StrategyBlocks rec={rec} />

      {rec.business_impact && (
        <Card title="Business Impact">
          <p className="text-sm leading-relaxed text-ink-200">{rec.business_impact}</p>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <RecommendationItems title="Yield Recommendations" items={rec.yield_recommendations} />
        <RecommendationItems title="Cost Recommendations" items={rec.cost_recommendations} />
        <RecommendationItems title="Coverage Recommendations" items={rec.coverage_recommendations} />
        <RecommendationItems
          title="Production Recommendations"
          items={rec.production_recommendations}
        />
      </div>

      <MultiSiteCard rec={rec} />
      <AssumptionsCard rec={rec} />
    </div>
  );
}
