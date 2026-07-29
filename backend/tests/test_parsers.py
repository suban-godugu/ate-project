"""Unit tests for STDF/LOG parsers (no database required)."""

from pathlib import Path

import pytest

from app.parsers.file_detection import DetectedFormat, detect_file_format
from app.parsers.log_parser import parse_log_file
from app.parsers.stdf_parser import parse_stdf_bytes

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def stdf_bytes() -> bytes:
    path = FIXTURES / "sample.stdf"
    if not path.exists():
        pytest.skip("Run python scripts/build_stdf_fixture.py first")
    return path.read_bytes()


def test_detect_stdf(stdf_bytes: bytes):
    assert detect_file_format("lot.stdf", stdf_bytes) == DetectedFormat.stdf


def test_parse_stdf(stdf_bytes: bytes):
    result = parse_stdf_bytes(stdf_bytes)
    assert result.lot_id == "LOT-PARSER-001"
    assert result.product_code == "PROD-X1"
    assert result.tester_code == "TTR-ADV-01"
    assert len(result.failures) == 1
    assert result.failures[0].chain_id == "SC-4821"
    assert result.failures[0].pattern_id == "P-101"
    assert result.yield_pct == pytest.approx(94.0)


def test_parse_log():
    text = (FIXTURES / "sample_ate.log").read_text(encoding="utf-8")
    assert detect_file_format("run.log", text.encode()) == DetectedFormat.log
    result = parse_log_file(text)
    assert result.lot_id == "LOT-PARSER-001"
    assert result.patterns_found == 18
    assert result.scan_chains == 6
    assert result.yield_pct == pytest.approx(94.5)
    assert len(result.failures) >= 2
