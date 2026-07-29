from app.services.rl_feedback_consumer import (
    REWARD_APPLIED,
    REWARD_APPROVED,
    REWARD_IGNORED,
    REWARD_REJECTED,
    aggregate_feedback,
    compute_reward_value,
    confidence_target_from_aggregate,
    priority_from_confidence,
    update_confidence_wma,
)


def test_approved_reward():
    assert compute_reward_value("approved") == REWARD_APPROVED


def test_applied_default():
    assert compute_reward_value("applied") == REWARD_APPLIED


def test_applied_scaled():
    assert compute_reward_value("applied", 0.5) == 1.0
    assert compute_reward_value("applied", 1.0) == REWARD_APPLIED


def test_rejected():
    assert compute_reward_value("rejected") == REWARD_REJECTED


def test_ignored():
    assert compute_reward_value("ignored") == REWARD_IGNORED


def test_aggregate_feedback():
    rows = [
        ("approved", 1.0),
        ("applied", 2.0),
        ("rejected", -1.5),
    ]
    agg = aggregate_feedback(rows)
    assert agg.total == 3
    assert agg.approvals == 1
    assert agg.applications == 1
    assert agg.rejections == 1
    assert agg.reward_sum == 1.5
    assert agg.approval_rate == 33.33


def test_confidence_wma_clamps():
    agg = aggregate_feedback([("applied", 2.0), ("applied", 2.0)])
    target = confidence_target_from_aggregate(agg)
    updated = update_confidence_wma(95.0, target)
    assert 0 <= updated <= 100


def test_confidence_increases_with_approvals():
    positive = aggregate_feedback([("approved", 1.0), ("applied", 2.0)])
    negative = aggregate_feedback([("rejected", -1.5), ("rejected", -1.5)])
    pos_conf = update_confidence_wma(75.0, confidence_target_from_aggregate(positive))
    neg_conf = update_confidence_wma(75.0, confidence_target_from_aggregate(negative))
    assert pos_conf > neg_conf


def test_priority_from_confidence():
    assert priority_from_confidence(90) == "Critical"
    assert priority_from_confidence(75) == "High"
    assert priority_from_confidence(55) == "Medium"
    assert priority_from_confidence(30) == "Low"
