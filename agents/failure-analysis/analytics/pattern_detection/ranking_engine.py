"""Statistical ranking of detected failure patterns."""

from __future__ import annotations

from typing import Any


def rank_patterns(
    frequency_table: dict[str, dict[str, Any]],
    confidence_map: dict[str, dict[str, Any]],
    *,
    cluster_map: dict[str, dict[str, Any]],
    anomaly_patterns: set[str],
    weights: dict[str, float],
) -> list[dict[str, Any]]:
    w_freq = float(weights.get("frequency", 0.35))
    w_density = float(weights.get("density", 0.20))
    w_conf = float(weights.get("confidence", 0.30))
    w_anom = float(weights.get("anomaly_penalty", 0.15))

    max_count = max((row["failure_count"] for row in frequency_table.values()), default=1)
    ranked: list[dict[str, Any]] = []

    for pid, freq_row in frequency_table.items():
        conf = confidence_map.get(pid, {})
        cluster = cluster_map.get(pid, {})
        freq_score = freq_row["failure_count"] / max_count
        density_score = float(freq_row.get("die_failure_rate", 0.0))
        confidence_score = float(conf.get("confidence", 0.0))
        anomaly_penalty = 1.0 if pid in anomaly_patterns else 0.0
        rank_score = round(
            w_freq * freq_score
            + w_density * density_score
            + w_conf * confidence_score
            - w_anom * anomaly_penalty,
            6,
        )
        ranked.append(
            {
                "pattern_id": pid,
                "rank_score": rank_score,
                "failure_count": freq_row["failure_count"],
                "failure_frequency": freq_row["failure_frequency"],
                "die_failure_rate": freq_row["die_failure_rate"],
                "lot_count": freq_row["lot_count"],
                "wafer_count": freq_row["wafer_count"],
                "confidence": confidence_score,
                "confidence_breakdown": conf.get("confidence_breakdown", {}),
                "cluster_id": cluster.get("cluster_id"),
                "is_anomaly": pid in anomaly_patterns,
                "dominant_failure_mode": cluster.get("dominant_pattern") == pid,
                "similar_patterns": conf.get("similar_patterns", []),
            }
        )

    ranked.sort(key=lambda row: (row["rank_score"], row["failure_count"]), reverse=True)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = idx
    return ranked
