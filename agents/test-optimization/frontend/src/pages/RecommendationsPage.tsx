import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Trash2 } from "lucide-react";
import { Badge, Card, ConfidenceBar, EmptyState, ErrorState, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate, riskTone } from "@/lib/format";
import type { RiskLevel } from "@/lib/types";

const RISK_FILTERS: Array<RiskLevel | ""> = ["", "Low", "Medium", "High"];

export function RecommendationsPage() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [risk, setRisk] = useState<RiskLevel | "">("");

  const list = useQuery({
    queryKey: ["recommendations", { q, risk }],
    queryFn: () => api.listRecommendations({ q, risk_level: risk, limit: 100 }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.deleteRecommendation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  if (list.isLoading) return <Spinner label="Loading recommendations…" />;
  if (list.isError) {
    return <ErrorState message={(list.error as Error).message} onRetry={() => list.refetch()} />;
  }

  const items = list.data?.items ?? [];

  return (
    <Card
      title="Recommendation History"
      subtitle={`${list.data?.total ?? 0} stored recommendation${list.data?.total === 1 ? "" : "s"}`}
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-ink-400" />
            <input
              value={q}
              onChange={(event) => setQ(event.target.value)}
              placeholder="Search device, lot, summary…"
              className="w-56 rounded-md border border-white/10 bg-base-800 py-1.5 pl-8 pr-3 text-xs text-ink-100 placeholder:text-ink-400 focus:border-brand-500/50 focus:outline-none"
            />
          </div>
          <div className="flex gap-1">
            {RISK_FILTERS.map((level) => (
              <button
                key={level || "all"}
                type="button"
                onClick={() => setRisk(level)}
                className={`rounded-md border px-2.5 py-1.5 text-[11px] font-medium transition ${
                  risk === level
                    ? "border-brand-500/50 bg-brand-600/20 text-brand-300"
                    : "border-white/10 bg-white/5 text-ink-300 hover:text-ink-100"
                }`}
              >
                {level || "All"}
              </button>
            ))}
          </div>
        </div>
      }
    >
      {items.length === 0 ? (
        <EmptyState message="No recommendations match the current filters." />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-white/8 text-[11px] uppercase tracking-wide text-ink-400">
                <th className="px-3 py-2 font-medium">Device / Lot</th>
                <th className="px-3 py-2 font-medium">Risk</th>
                <th className="px-3 py-2 font-medium">Strategy</th>
                <th className="px-3 py-2 font-medium">Confidence</th>
                <th className="px-3 py-2 font-medium">Created</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {items.map((rec) => (
                <tr
                  key={rec.id}
                  className="border-b border-white/5 transition hover:bg-white/5"
                >
                  <td className="px-3 py-2.5">
                    <Link to={`/recommendations/${rec.id}`} className="block">
                      <span className="font-medium text-ink-100">{rec.device}</span>
                      <span className="num ml-2 text-ink-400">{rec.lot_id}</span>
                    </Link>
                  </td>
                  <td className="px-3 py-2.5">
                    <Badge tone={riskTone[rec.risk_level]}>{rec.risk_level}</Badge>
                  </td>
                  <td className="max-w-xs truncate px-3 py-2.5 text-ink-200">
                    {rec.adaptive_testing.flow_mode.toUpperCase()} · {rec.recommended_strategy}
                  </td>
                  <td className="px-3 py-2.5">
                    <ConfidenceBar value={rec.confidence} />
                  </td>
                  <td className="num px-3 py-2.5 text-ink-400">{formatDate(rec.created_at)}</td>
                  <td className="px-3 py-2.5 text-right">
                    <button
                      type="button"
                      onClick={() => remove.mutate(rec.id)}
                      disabled={remove.isPending}
                      title="Delete recommendation"
                      className="rounded-md border border-white/10 p-1.5 text-ink-400 transition hover:border-rose-500/40 hover:text-rose-300 disabled:opacity-50"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
