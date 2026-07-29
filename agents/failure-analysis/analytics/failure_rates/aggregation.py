"""Multi-level record aggregation for failure rates."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from adapters.schema import TestRecord
from analytics.failure_rates.statistics import bucket_summary
from ingestor import DieLog


def aggregate_all_levels(
    die_logs: list[DieLog],
    test_records: list[TestRecord] | None = None,
    *,
    shift_hours: int = 8,
) -> dict[str, dict[str, dict[str, Any]]]:
    record_index = _index_records(test_records)

    device: dict[str, list[bool]] = defaultdict(list)
    die: dict[str, list[bool]] = defaultdict(list)
    wafer: dict[str, list[bool]] = defaultdict(list)
    lot: dict[str, list[bool]] = defaultdict(list)
    product: dict[str, list[bool]] = defaultdict(list)
    tester: dict[str, list[bool]] = defaultdict(list)
    shift: dict[str, list[bool]] = defaultdict(list)
    production: dict[str, list[bool]] = defaultdict(list)
    wafer_lot: dict[str, str] = {}

    for d in die_logs:
        is_fail = d.is_failing_die
        rec = record_index.get((d.lot_id, d.wafer_id, d.die_id))
        die_key = f"{d.lot_id}|{d.wafer_id}|{d.die_id}"
        wafer_lot[d.wafer_id] = d.lot_id

        device[d.device_name or "UNKNOWN"].append(is_fail)
        die[die_key].append(is_fail)
        wafer[d.wafer_id].append(is_fail)
        lot[d.lot_id].append(is_fail)
        product[(rec.product_id if rec else d.device_name) or "UNKNOWN"].append(is_fail)
        tester[(rec.tester_id if rec else d.tester_name) or "UNKNOWN"].append(is_fail)

        ts = rec.timestamp if rec else d.header_fields.get("TIMESTAMP", "")
        shift[_shift_bucket(ts, shift_hours)].append(is_fail)
        stage = (rec.test_stage if rec else d.header_fields.get("TEST_STAGE", "UNKNOWN"))
        production[f"stage:{stage}"].append(is_fail)
        production["manufacturing"].append(is_fail)

    return {
        "device_level": _serialize(device),
        "die_level": _serialize(die),
        "wafer_level": _serialize_wafer(wafer, wafer_lot),
        "lot_level": _serialize(lot),
        "product_level": _serialize(product),
        "tester_level": _serialize(tester),
        "shift_level": _serialize(shift),
        "production_level": _serialize(production),
    }


def _serialize(groups: dict[str, list[bool]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, outcomes in sorted(groups.items()):
        tested = len(outcomes)
        failed = sum(1 for x in outcomes if x)
        result[key] = bucket_summary(tested, failed)
    return result


def _serialize_wafer(
    wafer: dict[str, list[bool]],
    wafer_lot: dict[str, str],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, outcomes in sorted(wafer.items()):
        tested = len(outcomes)
        failed = sum(1 for x in outcomes if x)
        row = bucket_summary(tested, failed)
        row["lot_id"] = wafer_lot.get(key, "")
        result[key] = row
    return result


def _shift_bucket(timestamp: str, shift_hours: int) -> str:
    if not timestamp:
        return "unknown-shift"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(timestamp[:19], fmt)
            shift_index = dt.hour // max(shift_hours, 1)
            return f"{dt.date()} shift-{shift_index}"
        except ValueError:
            continue
    return timestamp[:10] if len(timestamp) >= 10 else "unknown-shift"


def _index_records(
    test_records: list[TestRecord] | None,
) -> dict[tuple[str, str, str], TestRecord]:
    index: dict[tuple[str, str, str], TestRecord] = {}
    if not test_records:
        return index
    for rec in test_records:
        index[(rec.lot_id, rec.wafer_id, rec.die_id)] = rec
    return index
