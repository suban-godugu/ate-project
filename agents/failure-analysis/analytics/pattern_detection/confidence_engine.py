"""Confidence score calculation — statistical separate from AI."""

from __future__ import annotations

from typing import Any


def statistical_confidence(
    pattern_id: str,
    *,
    frequency_row: dict[str, Any],
    cluster_info: dict[str, Any] | None,
) -> float:
    """Rule/statistical confidence from frequency and cluster membership."""
    freq = float(frequency_row.get("failure_frequency", 0.0))
    die_rate = float(frequency_row.get("die_failure_rate", 0.0))
    lot_spread = min(1.0, int(frequency_row.get("lot_count", 0)) / 5.0)
    base = 0.4 * min(1.0, freq * 5.0) + 0.35 * min(1.0, die_rate * 3.0) + 0.25 * lot_spread
    if cluster_info and cluster_info.get("cluster_id", -1) >= 0:
        base = min(1.0, base + 0.05)
    return round(min(1.0, base), 4)


def ai_confidence(
    pattern_id: str,
    similar_pairs: list[dict[str, Any]],
) -> float:
    """AI similarity contribution — isolated from statistical score."""
    scores = [
        float(pair.get("similarity_score", 0.0))
        for pair in similar_pairs
        if pattern_id in (pair.get("pattern_a"), pair.get("pattern_b"))
        and str(pair.get("method", "")).startswith("ai_")
    ]
    if not scores:
        return 0.0
    return round(min(1.0, max(scores)), 4)


def combine_confidence(
    *,
    detection_confidence: float,
    statistical: float,
    ai: float,
    weights: dict[str, float],
) -> dict[str, Any]:
    stat_w = float(weights.get("statistical", 0.6))
    clust_w = float(weights.get("clustering", 0.2))
    sim_w = float(weights.get("similarity", 0.2))
    composite = (
        stat_w * statistical
        + clust_w * min(1.0, detection_confidence)
        + sim_w * max(ai, statistical * 0.5)
    )
    composite = round(min(1.0, composite), 4)
    return {
        "confidence": composite,
        "confidence_breakdown": {
            "detection": round(detection_confidence, 4),
            "statistical": statistical,
            "ai_similarity": ai,
            "weights": weights,
        },
    }


def attach_confidence_to_patterns(
    ranked_patterns: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ensure every pattern has a confidence score (requirement)."""
    for row in ranked_patterns:
        if "confidence" not in row or row["confidence"] is None:
            row["confidence"] = 0.0
        row["confidence_required"] = True
    return ranked_patterns
