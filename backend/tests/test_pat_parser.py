"""Unit tests for PAT parser framework (no vendor grammar registered)."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from app.parsers.file_detection import DetectedFormat, detect_file_format
from app.parsers.pat_parser import (
    PatMalformedGrammar,
    PatParseError,
    PatUnsupportedFormat,
    framework_status,
    identify_pat_vendor,
    looks_like_pat_content,
    parse_pat_bytes,
)

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "sample.pat"


@pytest.fixture(scope="module")
def sample_pat() -> bytes:
    if not SAMPLE.exists():
        pytest.skip("Run python scripts/build_pat_fixture.py first")
    return SAMPLE.read_bytes()


def test_framework_ready():
    status = framework_status()
    assert status["framework_ready"] is True
    assert status["requires_real_sample"] is True
    assert status["supported_vendors"] == []


def test_detect_pat_by_content_signature(sample_pat: bytes):
    assert detect_file_format("pattern.pat", sample_pat) == DetectedFormat.pat


def test_detect_pat_gz(sample_pat: bytes):
    gz = gzip.compress(sample_pat)
    assert detect_file_format("pattern.pat.gz", gz) == DetectedFormat.pat


def test_detect_pat_not_stil_or_wgl(sample_pat: bytes):
    fmt = detect_file_format("pattern.pat", sample_pat)
    assert fmt not in (DetectedFormat.stil, DetectedFormat.wgl, DetectedFormat.stdf)


def test_extension_alone_insufficient():
    plain = b"hello world text without pat markers"
    assert detect_file_format("file.pat", plain) != DetectedFormat.pat


def test_parse_unsupported_format(sample_pat: bytes):
    with pytest.raises(PatUnsupportedFormat) as exc:
        parse_pat_bytes(sample_pat, "sample.pat")
    assert exc.value.code == "unsupported_pat_format"
    assert exc.value.vendor_hint == "generic_pat_text"


def test_teradyne_hint_unsupported():
    text = b"! IG-XL pattern export\nPATTERN foo\n"
    assert identify_pat_vendor(text) == "teradyne"
    with pytest.raises(PatUnsupportedFormat) as exc:
        parse_pat_bytes(text, "teradyne.pat")
    assert exc.value.vendor_hint == "teradyne"


def test_advantest_hint_unsupported():
    text = b"! V93000 pattern\nPAT_FILE adv_pat\n"
    with pytest.raises(PatUnsupportedFormat) as exc:
        parse_pat_bytes(text, "adv.pat")
    assert exc.value.vendor_hint in ("advantest", "generic_pat_text")


def test_malformed_not_pat():
    with pytest.raises(PatMalformedGrammar):
        parse_pat_bytes(b"random text without pat signatures", "x.pat")


def test_empty_file():
    with pytest.raises(PatParseError):
        parse_pat_bytes(b"", "empty.pat")


def test_looks_like_pat_content(sample_pat: bytes):
    assert looks_like_pat_content(sample_pat, "sample.pat") is True
