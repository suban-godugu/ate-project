"use client";

import type { RecommendationRlFields } from "@/types/recommendation";

function formatDelta(value: number | null | undefined): string {
  if (value == null || value === 0) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function recommendationRlColumns<T extends RecommendationRlFields>() {
  return [
    {
      key: "feedbackCount",
      label: "Feedback",
      render: (row: T) => row.feedbackCount ?? 0,
    },
    {
      key: "approvalRate",
      label: "Approval %",
      render: (row: T) => `${row.approvalRate ?? 0}%`,
    },
    {
      key: "applicationRate",
      label: "Applied %",
      render: (row: T) => `${row.applicationRate ?? 0}%`,
    },
    {
      key: "rewardScore",
      label: "Reward",
      render: (row: T) => (row.rewardScore != null ? row.rewardScore.toFixed(2) : "0.00"),
    },
    {
      key: "confidenceChange",
      label: "Conf. Δ",
      render: (row: T) => (
        <span
          className={
            (row.confidenceChange ?? 0) > 0
              ? "text-emerald-400"
              : (row.confidenceChange ?? 0) < 0
                ? "text-red-400"
                : "text-slate-400"
          }
        >
          {formatDelta(row.confidenceChange)}
        </span>
      ),
    },
  ] as const;
}
