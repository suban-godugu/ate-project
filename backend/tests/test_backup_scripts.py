"""Backup script unit tests (no live pg_dump required)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("backup_db", ROOT / "scripts" / "backup_db.py")
_backup = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_backup)
apply_retention = _backup.apply_retention


def test_retention_keeps_recent_files(tmp_path: Path):
    files = []
    for i in range(5):
        p = tmp_path / f"verilumen_2026070{i}T120000Z.sql.gz"
        p.write_bytes(b"x" * 200)
        files.append(p)
    apply_retention(tmp_path, daily=3, weekly=2, monthly=1)
    remaining = list(tmp_path.glob("verilumen_*.sql.gz"))
    assert len(remaining) >= 3
