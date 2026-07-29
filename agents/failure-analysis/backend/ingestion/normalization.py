"""Normalize parsed records into unified canonical schema."""

from __future__ import annotations

from typing import Any

from adapters.schema import SCHEMA_VERSION, TestRecord


def normalize_record(record: TestRecord) -> TestRecord:
    record.lot_id = str(record.lot_id).strip()
    record.wafer_id = str(record.wafer_id).strip()
    record.die_id = str(record.die_id).strip()
    record.test_stage = str(record.test_stage).strip() or "UNKNOWN"
    record.tester_id = str(record.tester_id).strip() or "UNKNOWN"
    record.pass_fail = str(record.pass_fail).strip().upper()
    record.timestamp = str(record.timestamp).strip()
    record.source_file = str(record.source_file).strip()
    record.adapter_id = str(record.adapter_id).strip()
    record.product_id = str(record.product_id).strip()
    record.hard_bin = str(record.hard_bin).strip()
    record.soft_bin = str(record.soft_bin).strip()
    record.failing_tests = [str(v).strip() for v in record.failing_tests if str(v).strip()]
    record.failing_patterns = [str(v).strip() for v in record.failing_patterns if str(v).strip()]
    if not record.record_key:
        record.record_key = record.build_record_key()
    return record


def normalize_records(records: list[TestRecord]) -> list[TestRecord]:
    return [normalize_record(record) for record in records]


def records_to_payload(records: list[TestRecord]) -> list[dict[str, Any]]:
    return [normalize_record(record).to_dict() for record in records]


def dataset_summary(records: list[TestRecord]) -> dict[str, Any]:
    lots = {r.lot_id for r in records if r.lot_id}
    wafers = {r.wafer_id for r in records if r.wafer_id}
    failing = sum(1 for r in records if r.pass_fail.upper() == "FAIL")
    return {
        "schema_version": SCHEMA_VERSION,
        "record_count": len(records),
        "unique_lots": len(lots),
        "unique_wafers": len(wafers),
        "failing_records": failing,
        "passing_records": len(records) - failing,
    }
