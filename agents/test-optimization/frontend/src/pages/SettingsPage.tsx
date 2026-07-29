import { useQuery } from "@tanstack/react-query";
import { Badge, Card, ErrorState, Spinner } from "@/components/ui";
import { api } from "@/lib/api";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-white/5 py-2.5 last:border-0">
      <span className="text-xs text-ink-400">{label}</span>
      <span className="num text-xs text-ink-100">{value}</span>
    </div>
  );
}

export function SettingsPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: api.health });

  if (health.isLoading) return <Spinner label="Reading engine configuration…" />;
  if (health.isError) {
    return <ErrorState message={(health.error as Error).message} onRetry={() => health.refetch()} />;
  }
  if (!health.data) return null;

  const data = health.data;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card title="Engine" subtitle="Active inference configuration">
        <div className="mb-3">
          <Badge
            tone={
              data.llm_enabled
                ? "border-brand-500/30 bg-brand-500/10 text-brand-300"
                : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
            }
          >
            {data.llm_enabled ? "LLM reasoning enabled" : "Deterministic heuristic fallback"}
          </Badge>
        </div>
        <dl>
          <Row label="Status" value={data.status} />
          <Row label="Agent" value={data.agent} />
          <Row label="Version" value={data.version} />
          <Row label="Model" value={data.model ?? "—"} />
          <Row label="Environment" value={data.environment} />
        </dl>
      </Card>

      <Card title="About This Agent" subtitle="Scope and boundaries">
        <p className="text-xs leading-relaxed text-ink-200">
          The Test Optimization Recommendation Agent is the final enterprise decision layer for ATE
          scan test. It consumes upstream Pattern Recommendation and Scan Debug Recommendation
          outputs plus yield, cost, coverage, wafer and production telemetry, then returns an
          adaptive test strategy as structured JSON.
        </p>
        <p className="mt-3 text-xs leading-relaxed text-ink-300">
          It does not perform pattern analysis, ATPG, scan debug, or failure diagnosis. When no LLM
          key is configured the agent uses a deterministic rule engine that never invents metrics —
          missing inputs are reported as data gaps instead.
        </p>
      </Card>
    </div>
  );
}
