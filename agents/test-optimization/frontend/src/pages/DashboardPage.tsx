import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Play, RefreshCw } from "lucide-react";
import { RecommendationView } from "@/components/RecommendationView";
import { Card, ErrorState, Spinner } from "@/components/ui";
import { api } from "@/lib/api";
import { titleize } from "@/lib/format";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const [sample, setSample] = useState<string>("");

  const samples = useQuery({
    queryKey: ["samples"],
    queryFn: api.samples,
    staleTime: 5 * 60_000,
  });

  const generate = useMutation({
    mutationFn: (name: string) => api.optimizeSample(name, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
  });

  const available = samples.data?.samples ?? [];

  // Generate the first sample automatically so the workspace is never empty on open.
  const autoRan = useRef(false);
  const runSample = generate.mutate;
  useEffect(() => {
    if (autoRan.current || available.length === 0) return;
    autoRan.current = true;
    const first = available[0];
    setSample(first);
    runSample(first);
  }, [available, runSample]);

  if (samples.isLoading) return <Spinner label="Connecting to optimization engine…" />;
  if (samples.isError) {
    return (
      <ErrorState
        message={(samples.error as Error).message}
        onRetry={() => samples.refetch()}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Card
        title="Generate Optimization Strategy"
        subtitle="Run the agent against a built-in production context"
        actions={
          <button
            type="button"
            onClick={() => sample && generate.mutate(sample)}
            disabled={!sample || generate.isPending}
            className="inline-flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white transition hover:bg-brand-500 disabled:opacity-50"
          >
            {generate.isPending ? (
              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            {generate.isPending ? "Analyzing…" : "Run agent"}
          </button>
        }
      >
        <div className="flex flex-wrap gap-2">
          {available.map((name) => (
            <button
              key={name}
              type="button"
              onClick={() => {
                setSample(name);
                generate.mutate(name);
              }}
              className={`rounded-md border px-3 py-1.5 text-xs font-medium transition ${
                sample === name
                  ? "border-brand-500/50 bg-brand-600/20 text-brand-300"
                  : "border-white/10 bg-white/5 text-ink-300 hover:border-brand-500/30 hover:text-ink-100"
              }`}
            >
              {titleize(name)}
            </button>
          ))}
        </div>
      </Card>

      {generate.isPending && !generate.data && <Spinner label="Generating recommendation…" />}

      {generate.isError && (
        <ErrorState
          message={(generate.error as Error).message}
          onRetry={() => sample && generate.mutate(sample)}
        />
      )}

      {generate.data && <RecommendationView rec={generate.data} />}
    </div>
  );
}
