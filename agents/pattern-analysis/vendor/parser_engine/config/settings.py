"""Shared defaults for Parser Engine (independent of any agent backend)."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent

ADAPTER_CONFIG_DIR: Path = PACKAGE_ROOT / "config" / "adapters"
MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024 * 1024  # 5 GB
ALLOWED_EXTENSIONS = {
    ".stil",
    ".stdf",
    ".std",
    ".log",
    ".txt",
    ".dat",
    ".csv",
    ".xml",
    ".json",
}
