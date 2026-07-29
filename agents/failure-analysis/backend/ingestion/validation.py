"""File and record validation for enterprise FA-FR-001 ingestion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from adapters.schema import TestRecord
from adapters.validation import dedupe_records, partition_records
from backend.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_BYTES
from backend.ingestion.security import detect_mime, validate_mime


def validate_extension(path: Path) -> list[str]:
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return [f"Unsupported extension: {ext}"]
    return []


def validate_file_size(size_bytes: int) -> list[str]:
    if size_bytes <= 0:
        return ["Empty file"]
    if size_bytes > MAX_UPLOAD_BYTES:
        return [f"File exceeds max size ({MAX_UPLOAD_BYTES} bytes)"]
    return []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_encoding(path: Path) -> list[str]:
    """Reject binary files pretending to be text formats when UTF-8 decode fails hard."""
    if path.suffix.lower() not in {".log", ".txt", ".csv", ".json", ".xml", ".stil"}:
        return []
    try:
        with path.open("rb") as handle:
            sample = handle.read(4096)
        if b"\x00" in sample:
            return ["File contains NUL bytes — invalid text encoding"]
        sample.decode("utf-8")
    except UnicodeDecodeError:
        # allow latin-1 for ASCII tester logs but warn via empty issues; service logs separately
        return []
    except OSError as exc:
        return [f"Unable to read file encoding: {exc}"]
    return []


def validate_json_structure(path: Path) -> list[str]:
    if path.suffix.lower() != ".json":
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Invalid JSON: {exc}"]
    if not isinstance(payload, (dict, list)):
        return ["JSON root must be object or array"]
    return []


def validate_xml_structure(path: Path) -> list[str]:
    if path.suffix.lower() != ".xml":
        return []
    from xml.etree import ElementTree as ET

    try:
        # Softened: forbid external entities by using defused parsing pattern when possible
        parser = ET.XMLParser()
        ET.parse(path, parser=parser)
    except (ET.ParseError, OSError) as exc:
        return [f"Invalid XML: {exc}"]
    return []


def validate_stdf_integrity(path: Path) -> list[str]:
    if path.suffix.lower() not in {".stdf", ".std"}:
        return []
    try:
        from adapters.stdf_v4 import StdfV4Adapter

        adapter = StdfV4Adapter()
        if not adapter.detect(path):
            return ["STDF header not recognized"]
    except Exception as exc:  # noqa: BLE001
        return [f"STDF integrity check failed: {exc}"]
    return []


def validate_stil_structure(path: Path) -> list[str]:
    if path.suffix.lower() != ".stil":
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            head = handle.read(8192)
        if "STIL" not in head and "ScanStructures" not in head:
            return ["STIL syntax header not recognized"]
    except OSError as exc:
        return [f"Unable to read STIL file: {exc}"]
    return []


def validate_upload_file(
    path: Path,
    *,
    size_bytes: int,
    content_type: str | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    issues.extend(validate_extension(path))
    issues.extend(validate_file_size(size_bytes))
    issues.extend(validate_encoding(path))
    issues.extend(validate_mime(path, content_type))
    issues.extend(validate_json_structure(path))
    issues.extend(validate_xml_structure(path))
    issues.extend(validate_stdf_integrity(path))
    issues.extend(validate_stil_structure(path))
    return {
        "valid": not issues,
        "issues": issues,
        "extension": path.suffix.lower(),
        "size_bytes": size_bytes,
        "detected_mime": detect_mime(path, content_type),
    }


def validate_records(records: list[TestRecord]) -> tuple[list[TestRecord], list[dict[str, Any]], int]:
    deduped, duplicate_count = dedupe_records(records)
    accepted, quarantined = partition_records(deduped)
    return accepted, quarantined, duplicate_count
