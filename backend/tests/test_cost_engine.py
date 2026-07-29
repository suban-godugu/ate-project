"""Cost Intelligence Engine — formula and aggregation tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.models.recommendations import Recommendation
from app.parsers.log_parser import parse_log_file
from app.services.cost_engine import (
    CostFacts,
    aggregate_cost_facts,
    allocate_module_costs,
    build_overview_kpis,
    build_product_cost_rows,
    build_tab_kpis,
    build_wafer_cost_rows,
    compute_retest_cost,
    compute_roi,
    compute_yield_loss_cost,
    equipment_cost_from_processing_ms,
    parse_dollar_amount,
    recommendation_savings_score,
)
from app.services.log_enrichment import merge_log_into_summary_fields

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_dollar_amount():
    assert parse_dollar_amount("$42K savings") == 42_000
    assert parse_dollar_amount("1.2M") == 1_200_000
    assert parse_dollar_amount("no money") is None


def test_log_fixture_extracts_cost_and_counts():
    text = (FIXTURES / "sample_ate.log").read_text(encoding="utf-8")
    result = parse_log_file(text)
    assert result.estimated_cost == pytest.approx(118500.0)
    assert result.estimated_savings == pytest.approx(392000.0)
    assert result.patterns_found == 18
    assert result.scan_chains == 6
    assert result.wafer_count == 1
    assert result.memory_blocks == 10
    assert result.logic_blocks == 4
    assert result.defects_found == 2
    assert len(result.failures) >= 2


def test_roi_formula():
    assert compute_roi(100_000, 25_000) == pytest.approx(0.25)
    assert compute_roi(0, 1000) is None


def test_yield_loss_cost():
    facts = CostFacts(
        upload_job_id="1",
        estimated_cost=100_000,
        estimated_savings=None,
        patterns_found=10,
        scan_chains=6,
        memory_blocks=10,
        logic_blocks=4,
        wafer_count=1,
        defects_found=2,
        yield_pct=94.5,
        processing_ms=None,
        file_format="log",
        product_code="PROD-X1",
        lot_code="LOT-1",
        wafer_code="W-1",
        total_dies=None,
        created_at=datetime.now(UTC),
    )
    assert compute_yield_loss_cost(facts) == pytest.approx(5500.0)


def test_retest_cost():
    facts = CostFacts(
        upload_job_id="1",
        estimated_cost=118_500,
        estimated_savings=None,
        patterns_found=18,
        scan_chains=6,
        memory_blocks=10,
        logic_blocks=4,
        wafer_count=1,
        defects_found=2,
        yield_pct=94.5,
        processing_ms=None,
        file_format="log",
        product_code=None,
        lot_code=None,
        wafer_code=None,
        total_dies=None,
        created_at=datetime.now(UTC),
    )
    assert compute_retest_cost(facts) == pytest.approx(118_500 * (2 / 18))


def test_module_allocation_weights():
    facts = CostFacts(
        upload_job_id="1",
        estimated_cost=1000,
        estimated_savings=200,
        patterns_found=18,
        scan_chains=6,
        memory_blocks=10,
        logic_blocks=4,
        wafer_count=1,
        defects_found=2,
        yield_pct=90,
        processing_ms=120_000,
        file_format="log",
        product_code="P",
        lot_code="L",
        wafer_code="W",
        total_dies=1000,
        created_at=datetime.now(UTC),
    )
    alloc = allocate_module_costs(facts)
    assert sum(alloc.values()) == pytest.approx(1000.0, rel=1e-3)
    assert alloc["mbist"] > alloc["lbist"]


def test_aggregate_from_log_shaped_facts():
    facts = [
        CostFacts(
            upload_job_id="a",
            estimated_cost=118_500,
            estimated_savings=392_000,
            patterns_found=18,
            scan_chains=6,
            memory_blocks=10,
            logic_blocks=4,
            wafer_count=1,
            defects_found=2,
            yield_pct=94.5,
            processing_ms=None,
            file_format="log",
            product_code="PROD-X1",
            lot_code="LOT-PARSER-001",
            wafer_code="WAF-12",
            total_dies=None,
            created_at=datetime.now(UTC),
        )
    ]
    agg = aggregate_cost_facts(facts)
    assert agg.total_cost == pytest.approx(118_500)
    assert agg.total_savings == pytest.approx(392_000)
    kpis = build_overview_kpis(agg)
    assert kpis[0]["id"] == "total-cost"
    rows = build_product_cost_rows(facts)
    assert len(rows) == 1
    assert rows[0]["product"] == "PROD-X1"


def test_equipment_cost_requires_config(monkeypatch):
    from app.core.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("COST_TESTER_USD_PER_HOUR", "120")
    get_settings.cache_clear()
    assert equipment_cost_from_processing_ms(3_600_000) == pytest.approx(120.0)
    get_settings.cache_clear()


def test_recommendation_savings_ranking():
    high = Recommendation(
        agent_type="test-optimization",
        category="Cost",
        priority="High",
        confidence=80,
        expected_impact="$120K savings",
        action_text="Reduce retest",
        status="pending",
    )
    low = Recommendation(
        agent_type="pattern",
        category="Pattern",
        priority="Low",
        confidence=90,
        expected_impact="minor",
        action_text="Keep",
        status="pending",
    )
    assert recommendation_savings_score(high) > recommendation_savings_score(low)


def test_cost_artifacts_saved_under_personal_roots(tmp_path, monkeypatch):
    from app.core.config import get_settings
    from app.services import artifact_store

    get_settings.cache_clear()
    monkeypatch.setenv("UPLOAD_INPUT_ROOT", str(tmp_path / "input all file"))
    monkeypatch.setenv("AGENT_OUTPUT_ROOT", str(tmp_path / "agent and parser output"))
    get_settings.cache_clear()

    jid = "job-cost-io"
    inp = artifact_store.upload_input_job_dir(jid)
    (inp / "run.log").write_text("Test Cost: 10\n", encoding="utf-8")
    artifact_store.save_cost_intelligence_artifacts(
        jid,
        summary={"estimated_cost": 10},
        scan_chain={"rows": []},
        wafer={"rows": []},
        input_manifest={"files": ["run.log"]},
    )
    out = artifact_store.job_root(jid) / "cost"
    assert (out / "log_cost_summary.json").exists()
    assert (out / "scan_chain_cost.json").exists()
    assert (out / "wafer_cost.json").exists()
    assert (inp / "run.log").exists()
    get_settings.cache_clear()


def _sample_log_facts(**overrides) -> CostFacts:
    base = dict(
        upload_job_id="a",
        estimated_cost=118_500.0,
        estimated_savings=392_000.0,
        patterns_found=18,
        scan_chains=6,
        memory_blocks=10,
        logic_blocks=4,
        wafer_count=1,
        defects_found=2,
        yield_pct=94.5,
        processing_ms=180_000,
        file_format="log",
        product_code="PROD-X1",
        lot_code="LOT-PARSER-001",
        wafer_code="WAF-12",
        total_dies=2500,
        created_at=datetime.now(UTC),
    )
    base.update(overrides)
    return CostFacts(**base)


def test_merge_log_into_summary_fields():
    text = (FIXTURES / "sample_ate.log").read_text(encoding="utf-8")
    parsed = parse_log_file(text)
    merged = merge_log_into_summary_fields({"patterns_found": 1}, parsed)
    assert merged["estimated_cost"] == pytest.approx(118500.0)
    assert merged["wafer_count"] == 1
    assert merged["scan_chains"] == 6


def test_wafer_tab_rows_and_kpis():
    facts = [_sample_log_facts()]
    agg = aggregate_cost_facts(facts)
    rows = build_wafer_cost_rows(facts, agg)
    kpis = build_tab_kpis(agg, "wafer")
    assert len(rows) == 1
    assert rows[0]["wafer"] == "WAF-12"
    assert rows[0]["yield"] == "94.5%"
    assert kpis
    assert any(k["id"] == "wafer:total" for k in kpis)


def test_scan_chain_tab_kpis_allocate_budget():
    facts = [_sample_log_facts()]
    agg = aggregate_cost_facts(facts)
    kpis = build_tab_kpis(agg, "scan-chain")
    assert any(k["id"] == "scan-chain:total" for k in kpis)
    assert agg.module_costs.get("scan_chain", 0) > 0
