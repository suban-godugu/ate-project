"""Verilumen scan-chain ATE log adapter (wraps existing ingestor)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from parser_engine.adapters.base import AdapterParseResult, LogAdapter
from parser_engine.adapters.schema import TestRecord
from parser_engine.parsers.ate.ingestor import (
    LogIngestionError,
    _looks_like_compact_format,
    _looks_like_new_format,
    read_log_file,
)

logger = logging.getLogger(__name__)


class VerilumenScanAdapter(LogAdapter):
    adapter_id = "verilumen_scan_v1"

    def detect(self, path: Path) -> bool:
        if path.suffix.lower() != ".log":
            return False
        try:
            if _looks_like_compact_format(path) or _looks_like_new_format(path):
                return True
            # Legacy bracket format
            sample = path.read_text(encoding="utf-8", errors="replace")[:2048]
            return "[PATTERN_ID" in sample and "DEVICE_NAME" in sample
        except OSError:
            return False

    def parse(self, path: Path) -> AdapterParseResult:
        errors: list[dict[str, str]] = []
        try:
            die = read_log_file(path)
        except (LogIngestionError, OSError, ValueError) as exc:
            return AdapterParseResult(errors=[{"file": str(path), "error": str(exc)}])

        timestamp = die.header_fields.get("TEST_DATE", "") or datetime.now(timezone.utc).isoformat()
        failing_patterns = sorted({p.pattern_id for p in die.failing_patterns})
        failing_tests = sorted(
            {p.raw_fields.get("FAIL_TYPE", p.scan_chain_id) for p in die.failing_patterns if p.scan_chain_id}
        )

        scan_fail: dict = {}
        if die.failing_patterns:
            first = die.failing_patterns[0]
            scan_fail = {
                "scan_chain_id": first.scan_chain_id,
                "expected": first.expected_signature,
                "actual": first.actual_signature,
                "fail_count": len(die.failing_patterns),
            }

        record = TestRecord(
            lot_id=die.lot_id,
            wafer_id=die.wafer_id,
            die_id=die.die_id,
            x=_parse_int(die.header_fields.get("DIE_X")),
            y=_parse_int(die.header_fields.get("DIE_Y")),
            test_stage=die.header_fields.get("TEST_STAGE", "SCAN"),
            tester_id=die.tester_name or die.header_fields.get("TESTER_NAME", "UNKNOWN"),
            product_id=die.device_name,
            timestamp=timestamp,
            pass_fail="FAIL" if die.is_failing_die else "PASS",
            hard_bin=die.header_fields.get("HARD_BIN", ""),
            soft_bin=die.header_fields.get("SOFT_BIN", ""),
            failing_tests=[t for t in failing_tests if t],
            failing_patterns=failing_patterns,
            scan_fail_data=scan_fail,
            parametric=_extract_parametric(die),
            source_file=str(path),
            adapter_id=self.adapter_id,
            raw_fields=dict(die.header_fields),
        )
        record.record_key = record.build_record_key()

        return AdapterParseResult(
            records=[record],
            metadata={
                "execution_count": die.execution_count,
                "failing_count": len(die.failing_patterns),
                "malformed_blocks": die.malformed_blocks,
            },
        )


def _parse_int(value: str | None) -> int | None:
    if value is None or not str(value).strip():
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _extract_parametric(die) -> dict[str, float | str]:
    parametric: dict[str, float | str] = {}
    if not die.failing_patterns:
        return parametric
    sample = die.failing_patterns[0].raw_fields
    for key in ("IR_DROP_MV", "THERMAL_C", "SETUP_SLACK_PS", "HOLD_SLACK_PS"):
        if key in sample:
            raw = sample[key]
            try:
                parametric[key.lower()] = float(raw)
            except ValueError:
                parametric[key.lower()] = raw
    return parametric
