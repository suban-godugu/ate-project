"""Unit tests for IEEE 1450 STIL parser."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from app.parsers.file_detection import DetectedFormat, detect_file_format
from app.parsers.stil_parser import (
    StilMalformedGrammar,
    StilParseError,
    StilUnsupportedExtension,
    parse_stil_bytes,
    parse_stil_text,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "sample.stil"


@pytest.fixture(scope="module")
def sample_stil() -> bytes:
    if not SAMPLE.exists():
        pytest.skip("Run python scripts/build_stil_fixture.py first")
    return SAMPLE.read_bytes()


def test_detect_stil_by_extension(sample_stil: bytes):
    assert detect_file_format("pattern.stil", sample_stil) == DetectedFormat.stil


def test_detect_stil_gz(sample_stil: bytes):
    gz = gzip.compress(sample_stil)
    assert detect_file_format("pattern.stil.gz", gz) == DetectedFormat.stil


def test_detect_stil_rejects_stdf(sample_stil: bytes):
    assert detect_file_format("pattern.stil", sample_stil) != DetectedFormat.stdf


def test_parse_sample_metadata(sample_stil: bytes):
    result = parse_stil_bytes(sample_stil, "sample.stil")
    assert result.stil_version == "1.0"
    assert result.header.get("Title") == "VERILUMEN STIL Parser Fixture"
    assert result.patterns_found == 1
    assert result.patterns[0].name == "core_scan_pat"
    assert result.patterns[0].timing_wft == "wft_default"
    assert result.patterns[0].vector_count == 1
    assert result.scan_chains == 1
    assert result.scan_structures[0].name == "SC_CORE"
    assert result.scan_structures[0].chain_length == 8
    assert result.scan_structures[0].scan_in == "scan_in"
    assert len(result.signals) == 5
    assert "clk" in result.clock_signals
    assert "reset" in result.reset_signals
    assert len(result.waveform_tables) == 1
    assert result.waveform_tables[0]["period"] == "100ns"


def test_parse_does_not_invent_failures(sample_stil: bytes):
    result = parse_stil_bytes(sample_stil, "sample.stil")
    summary = result.to_summary_dict()
    assert "failure_count" not in summary
    assert "yield_pct" not in summary
    chains = result.to_chains_dict()
    assert all(c.get("status") == "defined" for c in chains["chains"])


def test_malformed_missing_version():
    with pytest.raises(StilMalformedGrammar):
        parse_stil_text("Header { Title \"x\"; }")


def test_malformed_unclosed_block():
    with pytest.raises(StilMalformedGrammar):
        parse_stil_text("STIL 1.0;\nHeader {\n  Title \"x\";\n")


def test_unsupported_vendor_extension():
    text = """STIL 1.0;
CTLMode {
  some vendor data;
}
"""
    with pytest.raises(StilUnsupportedExtension) as exc:
        parse_stil_text(text)
    assert "CTLMode" in exc.value.extensions


def test_empty_file():
    with pytest.raises(StilParseError):
        parse_stil_bytes(b"", "empty.stil")


def test_to_metadata_and_chains(sample_stil: bytes):
    result = parse_stil_bytes(sample_stil, "sample.stil")
    meta = result.to_metadata_dict()
    assert meta["patterns"][0]["name"] == "core_scan_pat"
    chains = result.to_chains_dict()
    assert chains["chains"][0]["chain_id"] == "SC_CORE"
    assert chains["chains"][0]["status"] == "defined"
