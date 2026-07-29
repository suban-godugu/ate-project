"""Historical trend analysis for failure rates."""

from __future__ import annotations

from typing import Any


def build_trend_report(
  *,
  lot_level: dict[str, dict[str, Any]],
  wafer_level: dict[str, dict[str, Any]],
  time_window_level: dict[str, dict[str, Any]] | None = None,
  historical_runs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
  lot_sorted = sorted(
    lot_level.items(),
    key=lambda item: item[1].get("failure_rate_pct", 0.0),
    reverse=True,
  )
  wafer_sorted = sorted(
    wafer_level.items(),
    key=lambda item: item[1].get("failure_rate_pct", 0.0),
    reverse=True,
  )
  time_series = []
  if time_window_level:
    for window, stats in sorted(time_window_level.items()):
      time_series.append(
        {
          "window": window,
          "failure_rate_pct": stats.get("failure_rate_pct", 0.0),
          "yield_pct": stats.get("yield_percentage", stats.get("pass_rate_pct", 0.0)),
          "tested": stats.get("tested", 0),
        }
      )

  historical_comparison = []
  if historical_runs:
    for run in historical_runs[:10]:
      summary = run.get("summary", {})
      historical_comparison.append(
        {
          "run_id": run.get("run_id"),
          "created_at": run.get("created_at"),
          "overall_yield_pct": summary.get("overall_yield_pct", 0.0),
          "overall_failure_rate_pct": summary.get("overall_failure_rate_pct", 0.0),
        }
      )

  return {
    "worst_lots": [
      {"lot_id": k, **{key: v.get(key) for key in ("failure_rate_pct", "yield_percentage", "tested")}}
      for k, v in lot_sorted[:10]
    ],
    "worst_wafers": [
      {"wafer_id": k, **{key: v.get(key) for key in ("failure_rate_pct", "yield_percentage", "tested", "lot_id")}}
      for k, v in wafer_sorted[:10]
    ],
    "time_series": time_series,
    "historical_comparison": historical_comparison,
    "trend_direction": _trend_direction(time_series),
  }


def _trend_direction(time_series: list[dict[str, Any]]) -> str:
  if len(time_series) < 2:
    return "insufficient_data"
  first = time_series[0]["failure_rate_pct"]
  last = time_series[-1]["failure_rate_pct"]
  if last > first + 0.5:
    return "worsening"
  if last < first - 0.5:
    return "improving"
  return "stable"
