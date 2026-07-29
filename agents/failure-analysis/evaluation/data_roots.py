"""Resolve dataset / Verilumen data roots without hardcoded user paths."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def candidate_verilumen_roots() -> list[Path]:
    """
    Build candidate dataset directories from env and the current user home.

    Never embeds a fixed C:\\Users\\... path. Uses Path.home() instead.
    """
    candidates: list[Path] = []

    for env_key in ("DATASET_ROOT", "VERILUMEN_DATA_ROOT"):
        raw = os.getenv(env_key, "").strip()
        if raw:
            candidates.append(Path(raw).expanduser())

    env_roots = os.getenv("EVALUATION_DATA_ROOTS", "").strip()
    if env_roots:
        for part in env_roots.split(";"):
            part = part.strip()
            if part:
                candidates.append(Path(part).expanduser())

    home = Path.home()
    for relative in (
        Path("Desktop") / "verilumen labs",
        Path("Desktop") / "Verilumen Labs",
        Path("Documents") / "verilumen labs",
        Path("Documents") / "Verilumen Labs",
    ):
        candidates.append(home / relative)

    # Local project fixtures / sample data
    candidates.append(PROJECT_ROOT / "tests" / "fixtures")
    candidates.append(PROJECT_ROOT)

    resolved: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        try:
            path = path.resolve()
        except OSError:
            continue
        if path in seen:
            continue
        seen.add(path)
        resolved.append(path)
    return resolved


def primary_dataset_root() -> Path | None:
    """First existing directory that looks like a semiconductor dataset root."""
    for path in candidate_verilumen_roots():
        if not path.is_dir():
            continue
        # Prefer dirs that contain STIL or log corpora
        if any(path.rglob("*.stil")) or any(path.glob("LOT_*")) or any(path.rglob("*.log")):
            return path
    for path in candidate_verilumen_roots():
        if path.is_dir() and path != PROJECT_ROOT:
            return path
    return None


def default_stil_file(root: Path | None = None) -> Path | None:
    base = root or primary_dataset_root()
    if base is None:
        return None
    stil_files = sorted(base.glob("*.stil"))
    if not stil_files:
        stil_files = sorted(base.rglob("*.stil"))
    return stil_files[0] if stil_files else None
