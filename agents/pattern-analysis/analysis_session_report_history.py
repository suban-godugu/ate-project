"""PA-FR-010.AS.5 Analysis Session report history metadata manager.

This module stores metadata only. It never imports Single Log history,
report generators, preview builders, report builders, or exporters.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from typing import Any, Dict, List, Mapping, Tuple


HISTORY_FILENAME = "PA-Analysis-Session_report_history.json"
HISTORY_VERSION = "1.0"
HISTORY_GENERATOR = "PA-FR-010.AS.5"
REPORT_MODEL_FILENAME = "PA-Analysis-Session_report_model.json"

RECORD_FIELDS = (
    "report_id",
    "session_hash",
    "generated_timestamp",
    "format",
    "model_hash",
    "validation_status",
    "report_version",
    "file_size_bytes",
    "export_type",
)
IDENTITY_FIELDS = ("session_hash", "model_hash", "format")
ALLOWED_FORMATS = {"html", "pdf", "excel"}

_HISTORY_LOCK = threading.RLock()


class AnalysisSessionReportHistoryError(RuntimeError):
    """Raised when session history metadata is invalid or cannot be persisted."""


def _build_report_id(record: Mapping[str, Any]) -> str:
    identity = {field: record.get(field) for field in IDENTITY_FIELDS}
    encoded = json.dumps(
        identity,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return f"RPT-{hashlib.sha256(encoded).hexdigest()[:20]}"


def _validate_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    if set(record) != set(RECORD_FIELDS):
        missing = sorted(set(RECORD_FIELDS) - set(record))
        extra = sorted(set(record) - set(RECORD_FIELDS))
        raise AnalysisSessionReportHistoryError(
            f"Invalid Analysis Session history fields; "
            f"missing={missing}, extra={extra}."
        )
    normalized = {field: record[field] for field in RECORD_FIELDS}
    string_fields = tuple(
        field for field in RECORD_FIELDS if field != "file_size_bytes"
    )
    if not all(isinstance(normalized[field], str) for field in string_fields):
        raise AnalysisSessionReportHistoryError(
            "Analysis Session history string fields must contain strings."
        )
    if normalized["format"] not in ALLOWED_FORMATS:
        raise AnalysisSessionReportHistoryError(
            f"Unsupported Analysis Session history format: "
            f"{normalized['format']}."
        )
    if (
        not isinstance(normalized["file_size_bytes"], int)
        or normalized["file_size_bytes"] < 0
    ):
        raise AnalysisSessionReportHistoryError(
            "Analysis Session history file_size_bytes must be non-negative."
        )
    expected_id = _build_report_id(normalized)
    if normalized["report_id"] != expected_id:
        raise AnalysisSessionReportHistoryError(
            "Analysis Session history report_id does not match its identity."
        )
    return normalized


def _empty_history() -> Dict[str, Any]:
    return {
        "generated_by": HISTORY_GENERATOR,
        "history_version": HISTORY_VERSION,
        "records": [],
    }


def _history_path(output_dir: str) -> str:
    return os.path.join(output_dir, HISTORY_FILENAME)


def _load_report_metadata(output_dir: str) -> Dict[str, str]:
    path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            model = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisSessionReportHistoryError(
            f"Unable to read {REPORT_MODEL_FILENAME} for history: {exc}"
        ) from exc
    if not isinstance(model, dict):
        raise AnalysisSessionReportHistoryError(
            f"{REPORT_MODEL_FILENAME} must contain an object."
        )
    metadata = model.get("metadata")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    validation = model.get("validation")
    validation = validation if isinstance(validation, Mapping) else {}
    generation = model.get("generation_metadata")
    generation = generation if isinstance(generation, Mapping) else {}
    hashes = model.get("hashes")
    hashes = hashes if isinstance(hashes, Mapping) else {}
    return {
        "session_hash": str(metadata.get("session_hash") or ""),
        "generated_timestamp": str(metadata.get("generated_timestamp") or ""),
        "model_hash": str(hashes.get("model_hash") or ""),
        "validation_status": str(validation.get("status") or "UNKNOWN"),
        "report_version": str(generation.get("report_version") or ""),
    }


def load_analysis_session_report_history(output_dir: str) -> Dict[str, Any]:
    """Load validated history; a missing artifact represents empty history."""
    path = _history_path(output_dir)
    if not os.path.exists(path):
        return _empty_history()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise AnalysisSessionReportHistoryError(
            f"Unable to read {HISTORY_FILENAME}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise AnalysisSessionReportHistoryError(
            "Analysis Session report history must contain an object."
        )
    if payload.get("generated_by") != HISTORY_GENERATOR:
        raise AnalysisSessionReportHistoryError(
            "Invalid Analysis Session report history generator."
        )
    if payload.get("history_version") != HISTORY_VERSION:
        raise AnalysisSessionReportHistoryError(
            "Unsupported Analysis Session report history version."
        )
    records = payload.get("records")
    if not isinstance(records, list):
        raise AnalysisSessionReportHistoryError(
            "Analysis Session report history records must be a list."
        )
    validated = [_validate_record(record) for record in records]
    ids = [record["report_id"] for record in validated]
    if len(ids) != len(set(ids)):
        raise AnalysisSessionReportHistoryError(
            "Analysis Session report history contains duplicate report IDs."
        )
    identities = [
        tuple(record[field] for field in IDENTITY_FIELDS)
        for record in validated
    ]
    if len(identities) != len(set(identities)):
        raise AnalysisSessionReportHistoryError(
            "Analysis Session report history contains duplicate report versions."
        )
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
        raise AnalysisSessionReportHistoryError(
            f"Output directory does not exist: {output_dir}"
        )
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
        raise AnalysisSessionReportHistoryError(
            f"Unable to write {HISTORY_FILENAME}: {exc}"
        ) from exc


def append_analysis_session_report_history(
    output_dir: str,
    *,
    format: str,
    model_hash: str,
    file_size_bytes: int,
    export_type: str,
) -> Tuple[Dict[str, Any], bool]:
    """Append one unique report version, or return its existing record."""
    model_metadata = _load_report_metadata(output_dir)
    if model_metadata["model_hash"] != str(model_hash):
        raise AnalysisSessionReportHistoryError(
            "Generated report model hash does not match the Analysis Session model."
        )
    record: Dict[str, Any] = {
        "session_hash": model_metadata["session_hash"],
        "generated_timestamp": model_metadata["generated_timestamp"],
        "format": str(format).strip().lower(),
        "model_hash": model_metadata["model_hash"],
        "validation_status": model_metadata["validation_status"],
        "report_version": model_metadata["report_version"],
        "file_size_bytes": int(file_size_bytes),
        "export_type": str(export_type),
    }
    record["report_id"] = _build_report_id(record)
    validated = _validate_record(record)

    with _HISTORY_LOCK:
        payload = load_analysis_session_report_history(output_dir)
        identity = tuple(validated[field] for field in IDENTITY_FIELDS)
        for existing in payload["records"]:
            existing_identity = tuple(
                existing[field] for field in IDENTITY_FIELDS
            )
            if existing_identity == identity:
                return existing, False
        payload["records"].append(validated)
        payload["records"].sort(
            key=lambda item: (
                item["generated_timestamp"],
                item["report_id"],
            ),
            reverse=True,
        )
        _write_history(output_dir, payload)
    return validated, True


def get_analysis_session_report_history(
    output_dir: str,
) -> List[Dict[str, Any]]:
    with _HISTORY_LOCK:
        return load_analysis_session_report_history(output_dir)["records"]


def get_analysis_session_report_history_entry(
    output_dir: str,
    report_id: str,
) -> Dict[str, Any] | None:
    with _HISTORY_LOCK:
        for record in load_analysis_session_report_history(output_dir)["records"]:
            if record["report_id"] == report_id:
                return record
    return None


def delete_analysis_session_report_history_entry(
    output_dir: str,
    report_id: str,
) -> Dict[str, Any] | None:
    with _HISTORY_LOCK:
        payload = load_analysis_session_report_history(output_dir)
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
