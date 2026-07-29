"""Unit tests for TSSI WGL parser."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from app.parsers.file_detection import DetectedFormat, detect_file_format
from app.parsers.wgl_parser import (
    WglMalformedGrammar,
    WglParseError,
    parse_wgl_bytes,
    parse_wgl_text,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "sample.wgl"


@pytest.fixture(scope="module")
def sample_wgl() -> bytes:
    if not SAMPLE.exists():
        pytest.skip("Run python scripts/build_wgl_fixture.py first")
    return SAMPLE.read_bytes()


def test_detect_wgl_by_extension(sample_wgl: bytes):
    assert detect_file_format("pattern.wgl", sample_wgl) == DetectedFormat.wgl


def test_detect_wgl_gz(sample_wgl: bytes):
    gz = gzip.compress(sample_wgl)
    assert detect_file_format("pattern.wgl.gz", gz) == DetectedFormat.wgl


def test_detect_wgl_not_stil(sample_wgl: bytes):
    assert detect_file_format("pattern.wgl", sample_wgl) != DetectedFormat.stil


def test_parse_sample_metadata(sample_wgl: bytes):
    result = parse_wgl_bytes(sample_wgl, "sample.wgl")
    assert result.header.get("Device") == "PROD-X1"
    assert result.header.get("Tester") == "TTR-ADV-01"
    assert result.patterns_found == 1
    assert result.patterns[0].name == "core_scan_pat"
    assert result.patterns[0].vector_count == 2
    assert result.patterns[0].pattern_group == "scan-chain"
    assert result.scan_chain_count == 1
    assert result.scan_chains[0].name == "SC_CORE"
    assert len(result.pins) == 5
    assert len(result.waveforms) == 1
    assert result.waveforms[0].period == "100ns"
    assert "clk" in result.clock_pins


def test_no_invented_test_results(sample_wgl: bytes):
    summary = parse_wgl_bytes(sample_wgl).to_summary_dict()
    assert "yield_pct" not in summary
    assert "failure_count" not in summary


def test_malformed_missing_waveform():
    with pytest.raises(WglMalformedGrammar):
        parse_wgl_text("signal\n  clk : input;\nend\n")


def test_unsupported_extension_continues_with_warning():
    text = """waveform

CTLMode
  vendor;
end

signal
  clk : input;
end

end
"""
    result = parse_wgl_text(text)
    assert "CTLMode" in result.unsupported_extensions
    assert len(result.pins) == 1
    assert any("CTLMode" in w for w in result.warnings)


def test_empty_file():
    with pytest.raises(WglParseError):
        parse_wgl_bytes(b"", "empty.wgl")


def test_waveform_and_chains_exports(sample_wgl: bytes):
    result = parse_wgl_bytes(sample_wgl)
    wf = result.to_waveform_dict()
    assert wf["waveforms"][0]["name"] == "wgl_default"
    chains = result.to_chains_dict()
    assert chains["chains"][0]["chain_id"] == "SC_CORE"
