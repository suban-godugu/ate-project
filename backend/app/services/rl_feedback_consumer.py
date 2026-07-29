"""Deterministic reward scoring and confidence updates from recommendation_feedback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

# Reward policy (Prompt 22 — deterministic, explainable)
REWARD_APPROVED = 1.0
REWARD_APPLIED = 2.0
REWARD_REJECTED = -1.5
REWARD_IGNORED = 0.0

WMA_ALPHA = 0.3  # weight on new target vs historical confidence
DEFAULT_CONFIDENCE = 75.0


def compute_reward_value(action_taken: str, outcome_value: float | None = None) -> float:
    """Map engineer feedback action to a scalar reward."""
    action = (action_taken or "").lower().strip()
    if action in ("approved", "approve"):
        return REWARD_APPROVED
    if action == "applied":
        if outcome_value is not None:
            magnitude = abs(float(outcome_value))
            return round(REWARD_APPLIED * max(0.5, min(magnitude, 1.5)), 4)
        return REWARD_APPLIED
    if action == "rejected":
        return REWARD_REJECTED
    if action == "ignored":
        return REWARD_IGNORED
    return 0.0


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


@dataclass
class FeedbackAggregate:
    total: int
    approvals: int
    rejections: int
    applications: int
    ignored: int
    reward_sum: float
    reward_avg: float
    approval_rate: float
    rejection_rate: float
    application_rate: float


def aggregate_feedback(
    rows: Iterable[tuple[str, float | None]],
) -> FeedbackAggregate:
    """Aggregate (action_taken, reward_value) tuples."""
    approvals = rejections = applications = ignored = 0
    reward_sum = 0.0
    count = 0
    for action, reward in rows:
        count += 1
        action_l = (action or "").lower()
        if action_l in ("approved", "approve"):
            approvals += 1
        elif action_l == "applied":
            applications += 1
        elif action_l == "rejected":
            rejections += 1
        elif action_l == "ignored":
            ignored += 1
        if reward is not None:
            reward_sum += float(reward)
    total = count or 1
    return FeedbackAggregate(
        total=count,
        approvals=approvals,
        rejections=rejections,
        applications=applications,
        ignored=ignored,
        reward_sum=round(reward_sum, 4),
        reward_avg=round(reward_sum / total, 4) if count else 0.0,
        approval_rate=round(100.0 * approvals / total, 2),
        rejection_rate=round(100.0 * rejections / total, 2),
        application_rate=round(100.0 * applications / total, 2),
    )


def confidence_target_from_aggregate(agg: FeedbackAggregate) -> float:
    """Derive target confidence (0–100) from feedback rates."""
    if agg.total == 0:
        return DEFAULT_CONFIDENCE
    target = (
        50.0
        + agg.approval_rate * 0.25
        + agg.application_rate * 0.35
        - agg.rejection_rate * 0.45
    )
    return _clamp(target)


def update_confidence_wma(current: float | None, target: float) -> float:
    """Weighted moving average toward target; clamp 0–100."""
    base = float(current) if current is not None else DEFAULT_CONFIDENCE
    updated = base * (1.0 - WMA_ALPHA) + target * WMA_ALPHA
    return round(_clamp(updated), 2)


def priority_from_confidence(confidence: float) -> str:
    if confidence >= 85:
        return "Critical"
    if confidence >= 70:
        return "High"
    if confidence >= 50:
        return "Medium"
    return "Low"
