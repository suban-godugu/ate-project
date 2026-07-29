"""Security helpers for FA-FR-001 ingestion."""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._\-]+")

ALLOWED_MIME_PREFIXES = (
    "text/",
    "application/json",
    "application/xml",
    "application/octet-stream",
    "application/x-",
)

EXTENSION_MIME_HINTS = {
    ".stil": {"text/plain", "application/octet-stream", "text/x-stil"},
    ".log": {"text/plain", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".dat": {"text/plain", "application/octet-stream"},
    ".csv": {"text/csv", "text/plain", "application/vnd.ms-excel", "application/octet-stream"},
    ".json": {"application/json", "text/plain", "application/octet-stream"},
    ".xml": {"application/xml", "text/xml", "text/plain", "application/octet-stream"},
    ".stdf": {"application/octet-stream"},
    ".std": {"application/octet-stream"},
}


def sanitize_filename(name: str) -> str:
    """Prevent directory traversal and unsafe characters in stored display names."""
    base = Path(name.replace("\\", "/")).name
    cleaned = _SAFE_NAME.sub("_", base).strip("._")
    return cleaned[:240] or "upload.bin"


def detect_mime(path: Path, client_content_type: str | None = None) -> str:
    guessed, _ = mimetypes.guess_type(str(path))
    if guessed:
        return guessed
    if client_content_type:
        return client_content_type.split(";")[0].strip()
    return "application/octet-stream"


def validate_mime(path: Path, content_type: str | None) -> list[str]:
    mime = detect_mime(path, content_type)
    ext = path.suffix.lower()
    allowed = EXTENSION_MIME_HINTS.get(ext)
    if allowed and mime not in allowed and not any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        return [f"MIME type '{mime}' is not allowed for extension {ext}"]
    return []


def safe_relative_path(raw: str | None) -> str | None:
    if not raw:
        return None
    normalized = raw.replace("\\", "/").lstrip("/")
    parts = []
    for part in normalized.split("/"):
        if part in {"", ".", ".."}:
            continue
        parts.append(sanitize_filename(part))
    return "/".join(parts) if parts else None
