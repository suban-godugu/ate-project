"""Unified dataset schema — input to every Scan Chain agent."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class UnifiedDatasetRecord(BaseModel):
    upload_id: str = ""
    file_id: str = ""
    lot_id: str = ""
    wafer_id: str = ""
    die_x: int | None = None
    die_y: int | None = None
    die_id: str = ""
    site: str = ""
    tester: str = ""
    program: str = ""
    device: str = ""
    pattern: str = ""
    scan_chain: str = ""
    test_number: str = ""
    test_name: str = ""
    expected: str = ""
    actual: str = ""
    pass_fail: str = ""
    soft_bin: str = ""
    hard_bin: str = ""
    timestamp: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    parse_confidence: float = 1.0
    quarantine_reason: str = ""
    parser_id: str = ""
    source_file: str = ""


class UnifiedDataset(BaseModel):
    upload_id: str
    schema_version: str = "2.0.0"
    record_count: int = 0
    records: list[UnifiedDatasetRecord] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def from_enterprise_record(rec: Any, *, upload_id: str, file_id: str) -> UnifiedDatasetRecord:
    """Map parser_engine EnterpriseRecord → UnifiedDatasetRecord."""
    failing_patterns = list(getattr(rec, "failing_patterns", None) or [])
    pattern = failing_patterns[0] if failing_patterns else ""
    return UnifiedDatasetRecord(
        upload_id=upload_id,
        file_id=file_id,
        lot_id=str(getattr(rec, "lot_id", "") or ""),
        wafer_id=str(getattr(rec, "wafer_id", "") or ""),
        die_x=getattr(rec, "x", None),
        die_y=getattr(rec, "y", None),
        die_id=str(getattr(rec, "die_id", "") or ""),
        site=str(getattr(rec, "tester_id", "") or ""),
        tester=str(getattr(rec, "tester_id", "") or ""),
        program=str(getattr(rec, "test_stage", "") or ""),
        device=str(getattr(rec, "product_id", "") or ""),
        pattern=pattern,
        scan_chain=str(getattr(rec, "chain_id", "") or ""),
        test_number="",
        test_name=",".join(getattr(rec, "failing_tests", None) or []),
        expected=str(getattr(rec, "expected_signature", "") or ""),
        actual=str(getattr(rec, "actual_signature", "") or ""),
        pass_fail=str(getattr(rec, "pass_fail", "") or ""),
        soft_bin=str(getattr(rec, "soft_bin", "") or ""),
        hard_bin=str(getattr(rec, "hard_bin", "") or ""),
        timestamp=str(getattr(rec, "timestamp", "") or ""),
        metadata={
            "scan_fail_data": dict(getattr(rec, "scan_fail_data", None) or {}),
            "parametric": dict(getattr(rec, "parametric", None) or {}),
            "raw_fields": dict(getattr(rec, "raw_fields", None) or {}),
            "fail_flop_id": str(getattr(rec, "fail_flop_id", "") or ""),
            "fail_type": str(getattr(rec, "fail_type", "") or ""),
            "record_key": str(getattr(rec, "record_key", "") or ""),
        },
        parse_confidence=float(getattr(rec, "parse_confidence", 1.0) or 1.0),
        quarantine_reason=str(getattr(rec, "quarantine_reason", "") or ""),
        parser_id=str(getattr(rec, "parser_id", "") or ""),
        source_file=str(getattr(rec, "source_file", "") or ""),
    )
