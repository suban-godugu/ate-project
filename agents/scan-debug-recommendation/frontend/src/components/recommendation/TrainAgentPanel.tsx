"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Brain, Loader2 } from "lucide-react";
import { fetchAgentStatus, trainAgent } from "@/lib/kpiDrillDown/api";

export function TrainAgentPanel() {
  const [episodes, setEpisodes] = useState(500);
  const [log, setLog] = useState<string | null>(null);
  const [autoNote, setAutoNote] = useState<string | null>(null);
  const autoStarted = useRef(false);
  const queryClient = useQueryClient();
  const isLive = (process.env.NEXT_PUBLIC_API_MODE ?? "mock") === "live";

  const { data: status } = useQuery({
    queryKey: ["agent-status"],
    queryFn: fetchAgentStatus,
    enabled: isLive,
    refetchInterval: (q) => (q.state.data?.training_in_progress ? 5_000 : 20_000),
  });

  const trainMutation = useMutation({
    mutationFn: ({ force }: { force: boolean }) => trainAgent(episodes, { force }),
    onMutate: ({ force }) => {
      setLog(
        force
          ? "Manual re-train: running RL episodes and supervised pre-training…"
          : "Auto-train: updating DQN weights for current scan debug dataset…"
      );
    },
    onSuccess: (result, { force }) => {
      if (result.skipped) {
        setLog(result.status);
        setAutoNote("Weights already match current data — auto-train skipped.");
      } else {
        setLog(
          [
            result.status,
            `Source: ${force ? "manual re-train" : "automatic"}`,
            `Episodes: ${result.episodes_trained}`,
            `Avg reward: ${result.average_episode_reward.toFixed(2)}`,
            `Avg loss: ${result.average_loss.toFixed(4)}`,
            `Final epsilon: ${result.final_epsilon.toFixed(4)}`,
            `Weights saved: ${result.weights_saved ? "yes" : "no"}`,
          ].join("\n")
        );
        setAutoNote(
          force
            ? "Manual re-train finished."
            : "Automatic training finished — agent updated for live recommendations."
        );
      }
      queryClient.invalidateQueries({ queryKey: ["agent-status"] });
      queryClient.invalidateQueries({ queryKey: ["scan-debug-dashboard"] });
    },
    onError: (err: Error) => {
      setLog(`Training failed: ${err.message}`);
      setAutoNote(null);
    },
  });

  // Auto-train once when the dashboard loads and weights are stale / missing.
  useEffect(() => {
    if (!isLive || !status || autoStarted.current) return;
    if (status.training_in_progress) {
      setAutoNote("Training already running on the API…");
      return;
    }
    if (!status.needs_training) {
      setAutoNote("Agent weights are up to date with the current dataset.");
      autoStarted.current = true;
      return;
    }
    autoStarted.current = true;
    setAutoNote("Starting automatic DQN training…");
    trainMutation.mutate({ force: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once when status first says training is needed
  }, [isLive, status?.needs_training, status?.training_in_progress]);

  const busy = trainMutation.isPending || Boolean(status?.training_in_progress);

  return (
    <section className="glass-card gradient-border p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-primary">
            <Brain size={14} />
            DQN Policy Training
          </div>
          <h3 className="font-display text-lg font-semibold text-white">RL Agent Training</h3>
          <p className="mt-1 max-w-2xl text-sm text-muted">
            Trains automatically when the dashboard loads and weights are missing or stale, and also on
            API startup. Use <span className="text-white">Re-train Agent</span> anytime to force a
            fresh run.
          </p>
          {autoNote ? (
            <p className={`mt-2 text-xs ${busy ? "text-warning" : "text-success"}`}>{autoNote}</p>
          ) : null}
          {status?.auto_train_result && !status.auto_train_result.skipped ? (
            <p className="mt-2 text-xs text-muted">
              Last train: {status.auto_train_result.episodes_trained} episodes · avg reward{" "}
              {status.auto_train_result.average_episode_reward.toFixed(1)} ·{" "}
              {status.dataset_cases ?? 0} cases
            </p>
          ) : null}
          {status ? (
            <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
              <span className="rounded-full border border-border px-2 py-0.5 text-slate-300">
                Device: {status.device}
              </span>
              <span className="rounded-full border border-border px-2 py-0.5 text-slate-300">
                ε: {status.epsilon.toFixed(3)}
              </span>
              <span className="rounded-full border border-border px-2 py-0.5 text-slate-300">
                Buffer: {status.replay_buffer_size}
              </span>
              <span
                className={`rounded-full border px-2 py-0.5 ${
                  status.needs_training
                    ? "border-warning/40 text-warning"
                    : "border-success/40 text-success"
                }`}
              >
                {status.needs_training ? "Needs training" : "Weights current"}
              </span>
              <span
                className={`rounded-full border px-2 py-0.5 ${
                  status.model_weights_exist
                    ? "border-success/40 text-success"
                    : "border-warning/40 text-warning"
                }`}
              >
                Weights: {status.model_weights_exist ? "loaded" : "none"}
              </span>
              {busy ? (
                <span className="rounded-full border border-primary/40 px-2 py-0.5 text-primary">
                  Training…
                </span>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs text-slate-400">
            Episodes
            <input
              type="number"
              min={10}
              max={1000}
              value={episodes}
              onChange={(e) => setEpisodes(Number(e.target.value) || 500)}
              className="mt-1 block w-28 rounded-xl border border-border bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-primary/50"
            />
          </label>
          <button
            type="button"
            disabled={busy || !isLive}
            onClick={() => trainMutation.mutate({ force: true })}
            className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-medium text-white hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Training…
              </>
            ) : (
              "Re-train Agent"
            )}
          </button>
        </div>
      </div>

      {!isLive ? (
        <p className="mt-3 text-xs text-warning">
          Set <code>NEXT_PUBLIC_API_MODE=live</code> in <code>frontend/.env.local</code> to train against
          the FastAPI backend.
        </p>
      ) : null}

      {log ? (
        <pre className="mt-4 whitespace-pre-wrap rounded-xl border border-border/70 bg-black/30 p-3 text-xs text-slate-300">
          {log}
        </pre>
      ) : null}
    </section>
  );
}
