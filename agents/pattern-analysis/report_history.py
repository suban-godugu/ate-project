"""PA-FR-010.5 single-log report history metadata manager.

This module stores metadata only. It does not import report builders,
presentations, exporters, analysis engines, or Analysis Session modules.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any, Dict, List, Mapping, Tuple

HISTORY_FILENAME = "PA-FR-010_report_history.json"
HISTORY_VERSION = "1.0"
HISTORY_GENERATOR = "PA-FR-010.5"

RECORD_FIELDS = (
    "report_id",
    "report_name",
    "generated_from",
    "generated_timestamp",
    "format",
    "model_hash",
    "file_size",
    "status",
    "download_name",
    "generation_duration_ms",
    "validation_status",
)
IDENTITY_FIELDS = tuple(field for field in RECORD_FIELDS if field != "report_id")
ALLOWED_FORMATS = {"html", "pdf", "excel"}
ALLOWED_STATUSES = {"SUCCESS"}

_HISTORY_LOCK = threading.RLock()


class ReportHistoryError(RuntimeError):
    """Raised when history metadata is invalid or cannot be persisted."""


def build_report_id(record: Mapping[str, Any]) -> str:
    """Build a deterministic ID from canonical record metadata."""
    identity = {field: record.get(field) for field in IDENTITY_FIELDS}
    encoded = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"RPT-{hashlib.sha256(encoded).hexdigest()[:20]}"


def create_history_record(
    *,
    report_name: str,
    generated_from: str,
    generated_timestamp: str,
    format: str,
    model_hash: str,
    file_size: int,
    status: str,
    download_name: str,
    generation_duration_ms: float,
    validation_status: str,
) -> Dict[str, Any]:
    """Create and validate one metadata-only history record."""
    record: Dict[str, Any] = {
        "report_name": str(report_name),
        "generated_from": str(generated_from),
        "generated_timestamp": str(generated_timestamp),
        "format": str(format).lower(),
        "model_hash": str(model_hash),
        "file_size": int(file_size),
        "status": str(status).upper(),
        "download_name": str(download_name),
        "generation_duration_ms": round(float(generation_duration_ms), 3),
        "validation_status": str(validation_status),
    }
    record["report_id"] = build_report_id(record)
    return _validate_record(record)


def _validate_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    if set(record) != set(RECORD_FIELDS):
        missing = sorted(set(RECORD_FIELDS) - set(record))
        extra = sorted(set(record) - set(RECORD_FIELDS))
        raise ReportHistoryError(
            f"Invalid history record fields; missing={missing}, extra={extra}."
        )
    normalized = {field: record[field] for field in RECORD_FIELDS}
    if not all(
        isinstance(normalized[field], str)
        for field in (
            "report_id",
            "report_name",
            "generated_from",
            "generated_timestamp",
            "format",
            "model_hash",
            "status",
            "download_name",
            "validation_status",
        )
    ):
        raise ReportHistoryError("History string fields must contain strings.")
    if normalized["format"] not in ALLOWED_FORMATS:
        raise ReportHistoryError(f"Unsupported history format: {normalized['format']}.")
    if normalized["status"] not in ALLOWED_STATUSES:
        raise ReportHistoryError(f"Unsupported history status: {normalized['status']}.")
    if not isinstance(normalized["file_size"], int) or normalized["file_size"] < 0:
        raise ReportHistoryError("History file_size must be a non-negative integer.")
    if (
        not isinstance(normalized["generation_duration_ms"], (int, float))
        or normalized["generation_duration_ms"] < 0
    ):
        raise ReportHistoryError(
            "History generation_duration_ms must be non-negative."
        )
    expected_id = build_report_id(normalized)
    if normalized["report_id"] != expected_id:
        raise ReportHistoryError("History report_id does not match record metadata.")
    return normalized


def empty_history() -> Dict[str, Any]:
    return {
        "generated_by": HISTORY_GENERATOR,
        "history_version": HISTORY_VERSION,
        "records": [],
    }


def _history_path(output_dir: str) -> str:
    return os.path.join(output_dir, HISTORY_FILENAME)


def load_history(output_dir: str) -> Dict[str, Any]:
    """Load and validate history; a missing artifact is an empty history."""
    path = _history_path(output_dir)
    if not os.path.exists(path):
        return empty_history()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportHistoryError(f"Unable to read {HISTORY_FILENAME}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReportHistoryError("Report history must contain an object.")
    if payload.get("generated_by") != HISTORY_GENERATOR:
        raise ReportHistoryError("Invalid report history generator.")
    if payload.get("history_version") != HISTORY_VERSION:
        raise ReportHistoryError("Unsupported report history version.")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ReportHistoryError("Report history records must be a list.")
    validated = [_validate_record(record) for record in records]
    ids = [record["report_id"] for record in validated]
    if len(ids) != len(set(ids)):
        raise ReportHistoryError("Report history contains duplicate report IDs.")
    validated.sort(
        key=lambda record: (
            record["generated_timestamp"],
            record["report_id"],
        ),
        reverse=True,
    )
    return {
        "generated_by": HISTORY_GENERATOR,
        "history_version": HISTORY_VERSION,
        "records": validated,
    }


def _write_history(output_dir: str, payload: Mapping[str, Any]) -> None:
    if not os.path.isdir(output_dir):
        raise ReportHistoryError(f"Output directory does not exist: {output_dir}")
    path = _history_path(output_dir)
    temporary_path = f"{path}.tmp"
    try:
        with open(temporary_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                payload,
                handle,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")
        os.replace(temporary_path, path)
    except OSError as exc:
        try:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)
        except OSError:
            pass
        raise ReportHistoryError(f"Unable to write {HISTORY_FILENAME}: {exc}") from exc


def add_history_entry(
    output_dir: str,
    record: Mapping[str, Any],
) -> Tuple[Dict[str, Any], bool]:
    """Append one unique record and persist deterministically."""
    validated = _validate_record(record)
    with _HISTORY_LOCK:
        payload = load_history(output_dir)
        for existing in payload["records"]:
            if existing["report_id"] == validated["report_id"]:
                return existing, False
        payload["records"].append(validated)
        payload["records"].sort(
            key=lambda item: (item["generated_timestamp"], item["report_id"]),
            reverse=True,
        )
        _write_history(output_dir, payload)
    return validated, True


def list_history(output_dir: str) -> List[Dict[str, Any]]:
    with _HISTORY_LOCK:
        return load_history(output_dir)["records"]


def get_history_entry(output_dir: str, report_id: str) -> Dict[str, Any] | None:
    with _HISTORY_LOCK:
        for record in load_history(output_dir)["records"]:
            if record["report_id"] == report_id:
                return record
    return None


def delete_history_entry(output_dir: str, report_id: str) -> Dict[str, Any] | None:
    with _HISTORY_LOCK:
        payload = load_history(output_dir)
        deleted = next(
            (
                record
                for record in payload["records"]
                if record["report_id"] == report_id
            ),
            None,
        )
        if deleted is None:
            return None
        payload["records"] = [
            record
            for record in payload["records"]
            if record["report_id"] != report_id
        ]
        _write_history(output_dir, payload)
        return deleted
