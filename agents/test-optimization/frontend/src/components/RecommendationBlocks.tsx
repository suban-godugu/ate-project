import { Badge, Card, ConfidenceBar } from "./ui";
import { flowTone, formatImpactValue, titleize } from "@/lib/format";
import type { OptimizationRecommendation, RecommendationItem } from "@/lib/types";

function Detail({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div>
      <dt className="text-[11px] font-medium uppercase tracking-wide text-ink-400">{label}</dt>
      <dd className="mt-0.5 text-xs leading-relaxed text-ink-200">{value}</dd>
    </div>
  );
}

export function StrategyBlocks({ rec }: { rec: OptimizationRecommendation }) {
  const { adaptive_testing: adaptive, test_stop: stop, risk_based_testing: riskBased } = rec;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card title="Adaptive Testing">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={flowTone[adaptive.flow_mode]}>{adaptive.flow_mode.toUpperCase()}</Badge>
            {adaptive.applicable_to && <Badge>{adaptive.applicable_to}</Badge>}
          </div>
          <p className="text-sm font-medium text-ink-100">{adaptive.recommendation}</p>
          <ConfidenceBar value={adaptive.confidence} />
          <dl className="space-y-2 border-t border-white/8 pt-3">
            <Detail label="Rationale" value={adaptive.rationale} />
            <Detail label="Trade-offs" value={adaptive.trade_offs} />
            <Detail label="Business impact" value={adaptive.business_impact} />
          </dl>
        </div>
      </Card>

      <Card title="Test Stop">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              tone={
                stop.early_stop
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                  : "border-white/10 bg-white/5 text-ink-200"
              }
            >
              {stop.early_stop ? "EARLY STOP" : "RUN TO TARGET"}
            </Badge>
            {stop.stop_coverage_pct !== null && (
              <Badge>Stop @ {stop.stop_coverage_pct}%</Badge>
            )}
          </div>
          <p className="text-sm font-medium text-ink-100">{stop.recommendation}</p>
          <ConfidenceBar value={stop.confidence} />
          <dl className="space-y-2 border-t border-white/8 pt-3">
            <Detail label="Rationale" value={stop.rationale} />
            <Detail label="Trade-offs" value={stop.trade_offs} />
            <Detail label="Business impact" value={stop.business_impact} />
          </dl>
        </div>
      </Card>

      <Card title="Risk-Based Testing">
        <div className="space-y-3">
          {riskBased.high_risk_lots.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {riskBased.high_risk_lots.map((lot) => (
                <Badge key={lot} tone="border-rose-500/30 bg-rose-500/10 text-rose-300">
                  {lot}
                </Badge>
              ))}
            </div>
          )}
          <p className="text-sm font-medium text-ink-100">{riskBased.recommendation}</p>
          <ConfidenceBar value={riskBased.confidence} />
          <dl className="space-y-2 border-t border-white/8 pt-3">
            <Detail label="High-risk action" value={riskBased.action_for_high_risk} />
            <Detail label="Low-risk action" value={riskBased.action_for_low_risk} />
            <Detail label="Rationale" value={riskBased.rationale} />
          </dl>
        </div>
      </Card>
    </div>
  );
}

export function RecommendationItems({
  title,
  items,
}: {
  title: string;
  items: RecommendationItem[];
}) {
  if (items.length === 0) return null;

  return (
    <Card title={title} subtitle={`${items.length} action${items.length === 1 ? "" : "s"}`}>
      <ul className="space-y-3">
        {items.map((item, index) => {
          const impact = Object.entries(item.estimated_impact);
          return (
            <li
              key={`${item.action}-${index}`}
              className="rounded-lg border border-white/8 bg-base-800/60 p-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <p className="text-sm font-medium text-ink-100">{item.action}</p>
                <ConfidenceBar value={item.confidence} />
              </div>
              <dl className="mt-2 space-y-2">
                <Detail label="Rationale" value={item.rationale} />
                <Detail label="Trade-offs" value={item.trade_offs} />
                <Detail label="Business impact" value={item.business_impact} />
              </dl>
              {impact.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5 border-t border-white/8 pt-2">
                  {impact.map(([key, value]) => (
                    <Badge key={key}>
                      {titleize(key)}: <span className="num ml-1">{formatImpactValue(value)}</span>
                    </Badge>
                  ))}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

export function MultiSiteCard({ rec }: { rec: OptimizationRecommendation }) {
  const site = rec.multi_site_optimization;
  if (!site) return null;

  return (
    <Card title="Multi-Site Optimization">
      <div className="space-y-3">
        <p className="text-sm font-medium text-ink-100">{site.recommendation}</p>
        <ConfidenceBar value={site.confidence} />
        {site.site_actions.length > 0 && (
          <ul className="space-y-1.5 border-t border-white/8 pt-3">
            {site.site_actions.map((action) => (
              <li key={action} className="flex gap-2 text-xs text-ink-200">
                <span className="text-brand-400">•</span>
                {action}
              </li>
            ))}
          </ul>
        )}
        <dl className="space-y-2 border-t border-white/8 pt-3">
          <Detail label="Rationale" value={site.rationale} />
          <Detail label="Trade-offs" value={site.trade_offs} />
          <Detail label="Business impact" value={site.business_impact} />
        </dl>
      </div>
    </Card>
  );
}

export function AssumptionsCard({ rec }: { rec: OptimizationRecommendation }) {
  if (rec.assumptions.length === 0 && rec.data_gaps.length === 0) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {rec.assumptions.length > 0 && (
        <Card title="Assumptions">
          <ul className="space-y-1.5">
            {rec.assumptions.map((item) => (
              <li key={item} className="flex gap-2 text-xs text-ink-200">
                <span className="text-brand-400">•</span>
                {item}
              </li>
            ))}
          </ul>
        </Card>
      )}
      {rec.data_gaps.length > 0 && (
        <Card title="Data Gaps" subtitle="Missing inputs that limit confidence">
          <ul className="space-y-1.5">
            {rec.data_gaps.map((item) => (
              <li key={item} className="flex gap-2 text-xs text-amber-200">
                <span className="text-amber-400">•</span>
                {item}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
