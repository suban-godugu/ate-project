#!/usr/bin/env python3
"""Restore VERILUMEN PostgreSQL from a gzip pg_dump backup.

Usage:
  python scripts/restore_db.py backups/verilumen_20260706T120000Z.sql.gz

Requires: psql on PATH, DATABASE_URL in environment.
"""

from __future__ import annotations

import argparse
import gzip
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def sync_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://verilumen:verilumen@localhost:5432/verilumen")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def restore_backup(backup_path: Path) -> None:
    if not backup_path.exists():
        raise FileNotFoundError(backup_path)

    url = sync_db_url()
    with tempfile.TemporaryDirectory() as tmp:
        sql_path = Path(tmp) / "restore.sql"
        with gzip.open(backup_path, "rb") as src, sql_path.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        if sql_path.stat().st_size < 50:
            raise RuntimeError("Backup file too small to restore")
        subprocess.run(["psql", url, "-v", "ON_ERROR_STOP=1", "-f", str(sql_path)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore VERILUMEN PostgreSQL database")
    parser.add_argument("backup_file", type=Path, help="Path to .sql.gz backup")
    args = parser.parse_args()
    try:
        restore_backup(args.backup_file)
        print(f"Restore completed from {args.backup_file}")
        return 0
    except FileNotFoundError as exc:
        print(f"Missing file or psql: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"psql restore failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
