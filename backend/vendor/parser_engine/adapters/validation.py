"""Record validation and quarantine handling (FA-FR-001)."""

from __future__ import annotations

import hashlib
from typing import Any

from parser_engine.adapters.schema import MANDATORY_FIELDS, TestRecord


def partition_records(
    records: list[TestRecord],
) -> tuple[list[TestRecord], list[dict[str, Any]]]:
    """Split records into accepted vs quarantined based on mandatory fields."""
    accepted: list[TestRecord] = []
    quarantined: list[dict[str, Any]] = []

    for record in records:
        missing = record.missing_mandatory()
        if missing:
            quarantined.append(
                {
                    "record": record.to_dict(),
                    "reason": f"Missing mandatory field(s): {', '.join(missing)}",
                    "missing_fields": missing,
                }
            )
            continue
        if not record.record_key:
            record.record_key = record.build_record_key()
        accepted.append(record)

    return accepted, quarantined


def dedupe_records(records: list[TestRecord]) -> tuple[list[TestRecord], int]:
    """Idempotent re-ingestion: dedupe on record_key."""
    seen: set[str] = set()
    unique: list[TestRecord] = []
    duplicates = 0
    for record in records:
        key = record.record_key or record.build_record_key()
        record.record_key = key
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        unique.append(record)
    return unique, duplicates


def source_file_hash(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]


def validate_mandatory_field_names() -> tuple[str, ...]:
    return MANDATORY_FIELDS
