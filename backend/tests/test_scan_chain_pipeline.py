"""Unit tests for Scan Chain pipeline domain + aggregator + recommendation."""

from __future__ import annotations

from app.domain.pipeline_stages import STAGE_PERCENT, PipelineStage
from app.domain.unified_dataset import UnifiedDatasetRecord, from_enterprise_record
from app.orchestration.aggregator import ResultAggregator
from app.orchestration.retry import normalize_retry_stage
from app.services.recommendation_engine import RecommendationEngine


class _FakeER:
    lot_id = "L1"
    wafer_id = "W1"
    die_id = "D1"
    x = 1
    y = 2
    tester_id = "T1"
    test_stage = "FT"
    product_id = "P1"
    failing_patterns = ["PAT_A"]
    failing_tests = ["t1"]
    chain_id = "C0"
    expected_signature = "01"
    actual_signature = "00"
    pass_fail = "FAIL"
    soft_bin = "2"
    hard_bin = "8"
    timestamp = ""
    scan_fail_data = {"fail_flop_id": "F9"}
    parametric = {}
    raw_fields = {}
    fail_flop_id = "F9"
    fail_type = "stuck_at"
    record_key = "k"
    parse_confidence = 0.9
    quarantine_reason = ""
    parser_id = "ate_log"
    source_file = "a.log"


def test_unified_mapping():
    rec = from_enterprise_record(_FakeER(), upload_id="u1", file_id="f1")
    assert isinstance(rec, UnifiedDatasetRecord)
    assert rec.lot_id == "L1"
    assert rec.scan_chain == "C0"
    assert rec.pattern == "PAT_A"
    assert rec.die_x == 1


def test_stage_percent_complete():
    assert STAGE_PERCENT[PipelineStage.completed] == 100
    assert STAGE_PERCENT[PipelineStage.parsing] == 30


def test_aggregator_and_recommendations():
    merged = ResultAggregator().merge(
        upload_id="u1",
        pattern={"kpis": {"failing_chains": 2, "compression_ratio": 0.1}, "report": {"ok": True}},
        failure={"kpis": {"yield_pct": 80.0}, "yield_report": {"yield_pct": 80.0}, "report": {}},
        diagnosis={"confidence": 0.5, "kpis": {}, "recommendations": [{"code": "X", "severity": "info", "message": "m"}], "report": {"root_cause": "chain"}},
    )
    rec = RecommendationEngine().build(merged)
    assert rec["kpis"]["recommendation_count"] >= 2
    assert any(r["code"] == "YIELD_BELOW_TARGET" for r in rec["recommendations"])


def test_normalize_retry_stage():
    assert normalize_retry_stage(None, PipelineStage.running_scan_diagnosis) == PipelineStage.running_scan_diagnosis
    assert normalize_retry_stage(PipelineStage.aggregating, None) == PipelineStage.aggregating
