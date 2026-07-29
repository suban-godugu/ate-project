"""Unit tests for RL training worker logic (no Redis/DB)."""

from app.services.rl_feedback_consumer import (
    aggregate_feedback,
    confidence_target_from_aggregate,
    priority_from_confidence,
    update_confidence_wma,
)


def test_train_pipeline_updates_confidence():
    feedback = [
        ("approved", 1.0),
        ("applied", 2.0),
    ]
    agg = aggregate_feedback(feedback)
    before = 70.0
    after = update_confidence_wma(before, confidence_target_from_aggregate(agg))
    assert after > before
    assert priority_from_confidence(after) in ("High", "Critical", "Medium")


def test_train_pipeline_rejections_lower_confidence():
    feedback = [("rejected", -1.5) for _ in range(3)]
    agg = aggregate_feedback(feedback)
    before = 80.0
    after = update_confidence_wma(before, confidence_target_from_aggregate(agg))
    assert after < before


def test_aggregate_reward_average():
    feedback = [("approved", 1.0), ("rejected", -1.5)]
    agg = aggregate_feedback(feedback)
    assert agg.reward_avg == -0.25
    assert agg.total == 2
