"""Tests for shared KPI ML module."""

from __future__ import annotations

import pytest

from src.data.dataset_builder import build_compiled_dataset
from src.data.scan_chain_confidence import clear_fr002_cache, compute_scan_chain_confidence
from src.models.kpi_ml import (
    KPI_SCAN_CHAIN,
    build_training_samples,
    predict_confidence,
    predict_priority,
    rank_score,
    row_feature_vector,
    train_kpi_ml_models,
    warm_kpi_ml_models,
)


@pytest.fixture(scope="module")
def dataset():
    clear_fr002_cache()
    return build_compiled_dataset(write=False)


def test_row_feature_vector_shape():
    vec = row_feature_vector(KPI_SCAN_CHAIN, {"rule_score": 0.5, "patternConsistency": 0.8})
    assert vec.shape == (18,)
    assert vec.min() >= 0.0


def test_build_training_samples_nonempty(dataset):
    samples = build_training_samples(dataset)
    assert len(samples) >= 8
    assert all("confidence_label" in s for s in samples)


def test_train_and_predict_confidence(dataset):
    bundle = train_kpi_ml_models(dataset)
    assert bundle["confidence_model"] is not None
    assert bundle["priority_model"] is not None
    assert bundle["rank_model"] is not None

    out = predict_confidence(
        KPI_SCAN_CHAIN,
        {"rule_score": 0.7, "patternConsistency": 0.6, "ambiguityGroup": 2},
    )
    assert 0.0 <= out["confidenceScore"] <= 0.99
    assert out["ruleScore"] == 0.7


def test_predict_priority_labels():
    out = predict_priority(KPI_SCAN_CHAIN, {"rule_priority": "P1", "fail_count": 10})
    assert out["priority"] in ("P0", "P1", "P2")


def test_rank_score_monotonic_with_confidence():
    low = rank_score(KPI_SCAN_CHAIN, {"rule_score": 0.3, "consistencyRatio": 0.2})
    high = rank_score(KPI_SCAN_CHAIN, {"rule_score": 0.8, "consistencyRatio": 0.9})
    assert high >= low


def test_warm_kpi_ml_models(dataset, tmp_path):
    from src.config import get_settings

    settings = get_settings()
    settings.kpi_ml_model_path = str(tmp_path / "kpi_ml_models.joblib")
    settings.kpi_ml_auto_train = True
    settings.kpi_ml_enabled = True

    result = warm_kpi_ml_models(dataset)
    assert result["status"] in ("trained", "loaded")
    assert (tmp_path / "kpi_ml_models.joblib").exists()


def test_scan_chain_confidence_rule_only_when_ml_disabled(dataset):
    from src.config import get_settings

    settings = get_settings()
    settings.kpi_ml_enabled = False
    case = next(c for c in dataset if c.get("has_break"))
    row = compute_scan_chain_confidence(case)
    assert row["mlBlended"] is False
    assert row["confidenceScore"] == row["ruleScore"]
