"""Filesystem helpers for dataset discovery (no content parsing)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

FileValidationStatus = Literal["available", "missing", "invalid"]


def classify_dataset_type(file_name: str, type_rules: list[tuple[str, str]]) -> str:
    """Classify a file using configurable prefix/substring rules."""
    for prefix, dataset_type in type_rules:
        if file_name.startswith(prefix) or prefix in file_name:
            return dataset_type
    return "unknown"


def validate_dataset_file(path: Path) -> tuple[FileValidationStatus, str]:
    """
    Validate existence, readability, and non-empty size.

    Does not open or parse file contents.
    """
    if not path.exists():
        return "missing", "File does not exist"
    if not path.is_file():
        return "invalid", "Path exists but is not a regular file"
    try:
        readable = os.access(path, os.R_OK)
    except OSError as exc:
        return "invalid", f"Unable to check permissions: {exc}"
    if not readable:
        return "invalid", "File is not readable"
    try:
        size = path.stat().st_size
    except OSError as exc:
        return "invalid", f"Unable to read file metadata: {exc}"
    if size <= 0:
        return "invalid", "File is empty"
    return "available", "ok"


def collect_file_metadata(path: Path) -> dict[str, object]:
    """Collect filesystem metadata without reading file contents."""
    stats = path.stat()
    modified = datetime.fromtimestamp(stats.st_mtime, tz=timezone.utc).isoformat()
    return {
        "size_bytes": int(stats.st_size),
        "last_modified": modified,
        "extension": path.suffix.lower().lstrip("."),
    }


def unique_dataset_name(stem: str, existing: set[str]) -> str:
    """Ensure registry keys stay unique when duplicate stems appear."""
    if stem not in existing:
        return stem
    index = 2
    while f"{stem}_{index}" in existing:
        index += 1
    return f"{stem}_{index}"
