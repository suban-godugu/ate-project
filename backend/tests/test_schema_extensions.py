"""Prompt 28 — parser-driven schema verification (no speculative migrations)."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from app.parsers.log_parser import parse_log_file
from app.parsers.stdf_parser import parse_stdf_bytes
from app.parsers.stil_parser import parse_stil_bytes
from app.parsers.wgl_parser import parse_wgl_bytes
from tests.helpers.pipeline import sync_db_url

FIXTURES = Path(__file__).parent / "fixtures"
ALEMBIC_VERSIONS = Path(__file__).resolve().parent.parent / "alembic" / "versions"

# Parser field → existing storage (must stay in sync with PARSER_SCHEMA_ANALYSIS.md)
PARSER_DESTINATIONS: dict[str, dict[str, str]] = {
    "stdf": {
        "lot_id": "lots",
        "product_code": "products",
        "tester_code": "testers",
        "yield_pct": "ai_log_summaries",
        "failures": "scan_chain_failures",
        "patterns": "ai_log_summaries.raw_summary_json",
    },
    "log": {
        "lot_id": "lots",
        "patterns_found": "ai_log_summaries",
        "failures": "scan_chain_failures",
        "estimated_cost": "ai_log_summaries",
    },
    "stil": {
        "patterns_found": "ai_log_summaries",
        "waveform_tables": "minio:metadata.json",
        "timing_sets": "minio:metadata.json",
        "scan_structures": "minio:scan-chains.json",
    },
    "wgl": {
        "patterns_found": "ai_log_summaries",
        "waveforms": "minio:waveforms.json",
        "timing_sets": "minio:metadata.json",
        "scan_chains": "minio:scan-chains.json",
    },
    "pat": {
        "patterns": "deferred:unsupported_pat_format",
    },
}


def test_no_parser_schema_migration_file():
    """Prompt 28 decision: no 004_parser_schema_extensions until parsers require it."""
    parser_migrations = list(ALEMBIC_VERSIONS.glob("*parser_schema*"))
    assert parser_migrations == [], f"Unexpected parser migration: {parser_migrations}"


def test_alembic_head_is_rl_training():
    """003 is RL training — not parser extensions."""
    heads = [p.name for p in ALEMBIC_VERSIONS.glob("003_*.py")]
    assert any("rl_training" in h for h in heads)
    assert not any("parser_schema" in h for h in heads)


@pytest.mark.parametrize("parser,fields", PARSER_DESTINATIONS.items())
def test_parser_fields_have_destinations(parser: str, fields: dict[str, str]):
    for field, dest in fields.items():
        assert dest, f"{parser}.{field} must map to a storage destination"


def test_stil_summary_fits_ai_log_summary_json():
    path = FIXTURES / "sample.stil"
    if not path.exists():
        pytest.skip("Run python scripts/build_stil_fixture.py first")
    result = parse_stil_bytes(path.read_bytes(), "sample.stil")
    summary = result.to_summary_dict()
    payload = {"format": "stil", **summary}
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["format"] == "stil"
    assert decoded["patterns_found"] >= 1
    assert "pattern_names" in decoded


def test_wgl_summary_fits_ai_log_summary_json():
    path = FIXTURES / "sample.wgl"
    if not path.exists():
        pytest.skip("Run python scripts/build_wgl_fixture.py first")
    result = parse_wgl_bytes(path.read_bytes(), "sample.wgl")
    summary = result.to_summary_dict()
    payload = {"format": "wgl", **summary}
    json.dumps(payload)  # must serialize for JSONB column


def test_stdf_failure_shape_fits_scan_chain_failures():
    path = FIXTURES / "sample.stdf"
    if not path.exists():
        pytest.skip("Run python scripts/build_stdf_fixture.py first")
    result = parse_stdf_bytes(path.read_bytes())
    assert result.failures
    f = result.failures[0]
    row = {
        "chain_id": f.chain_id[:64],
        "pattern_id": (f.pattern_id or "")[:64],
        "fail_cycle": f.fail_cycle,
        "fail_type": f.fail_type[:64],
        "root_cause": f.root_cause,
    }
    assert row["chain_id"]
    assert row["pattern_id"]


def test_log_summary_fits_ai_log_summary_columns():
    path = FIXTURES / "sample_ate.log"
    if not path.exists():
        pytest.skip("sample_ate.log fixture missing")
    result = parse_log_file(path.read_text(encoding="utf-8"))
    assert result.patterns_found is not None
    assert result.scan_chains is not None
    assert result.lot_id


@pytest.mark.integration
def test_scan_chain_failure_insert_query_rollback():
    """Verify FK-backed insert + rollback on existing schema (no new tables)."""
    lot_id = uuid.uuid4()
    engine = create_engine(sync_db_url())
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Postgres not reachable: {exc}")

    failure_id = uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO lots (id, lot_code) VALUES (:id, :code)
                """
            ),
            {"id": str(lot_id), "code": f"SCHEMA-TEST-{lot_id.hex[:8]}"},
        )
        conn.execute(
            text(
                """
                INSERT INTO scan_chain_failures
                  (id, chain_id, pattern_id, fail_type, root_cause, lot_id, diagnosis_status)
                VALUES
                  (:id, 'SC-TEST', 'P-TEST', 'functional', 'pytest schema test', :lot_id, 'pending')
                """
            ),
            {"id": str(failure_id), "lot_id": str(lot_id)},
        )
        row = conn.execute(
            text("SELECT chain_id, pattern_id FROM scan_chain_failures WHERE id = :id"),
            {"id": str(failure_id)},
        ).one()
        assert row[0] == "SC-TEST"
        assert row[1] == "P-TEST"

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM scan_chain_failures WHERE id = :id"), {"id": str(failure_id)})
        conn.execute(text("DELETE FROM lots WHERE id = :id"), {"id": str(lot_id)})

    with engine.connect() as conn:
        gone = conn.execute(
            text("SELECT 1 FROM scan_chain_failures WHERE id = :id"),
            {"id": str(failure_id)},
        ).scalar()
        assert gone is None


@pytest.mark.integration
def test_ai_log_summary_jsonb_round_trip():
    """STIL-shaped raw_summary_json inserts into existing ai_log_summaries."""
    path = FIXTURES / "sample.stil"
    if not path.exists():
        pytest.skip("Run python scripts/build_stil_fixture.py first")

    job_id = uuid.uuid4()
    summary_id = uuid.uuid4()
    stil = parse_stil_bytes(path.read_bytes(), "sample.stil")
    raw_json = {"format": "stil", **stil.to_summary_dict()}

    engine = create_engine(sync_db_url())
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Postgres not reachable: {exc}")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO upload_jobs
                  (id, kind, module, status, file_name, size_bytes, minio_bucket, minio_object_key)
                VALUES
                  (:id, 'data', 'scan-chain', 'completed', 'sample.stil', 100,
                   'verilumen-raw-uploads', 'test/sample.stil')
                """
            ),
            {"id": str(job_id)},
        )
        conn.execute(
            text(
                """
                INSERT INTO ai_log_summaries
                  (id, upload_job_id, patterns_found, scan_chains, raw_summary_json)
                VALUES
                  (:id, :job_id, :patterns, :chains, CAST(:raw AS jsonb))
                """
            ),
            {
                "id": str(summary_id),
                "job_id": str(job_id),
                "patterns": stil.patterns_found,
                "chains": stil.scan_chains,
                "raw": json.dumps(raw_json),
            },
        )
        fetched = conn.execute(
            text(
                """
                SELECT patterns_found, raw_summary_json->>'format', raw_summary_json->>'title'
                FROM ai_log_summaries WHERE id = :id
                """
            ),
            {"id": str(summary_id)},
        ).one()
        assert fetched[0] == stil.patterns_found
        assert fetched[1] == "stil"

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM ai_log_summaries WHERE id = :id"), {"id": str(summary_id)})
        conn.execute(text("DELETE FROM upload_jobs WHERE id = :id"), {"id": str(job_id)})
