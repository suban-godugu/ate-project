#!/usr/bin/env python3
"""PostgreSQL backup utility (pg_dump + gzip + retention).

Usage:
  python scripts/backup_db.py
  python scripts/backup_db.py --output-dir backups

Requires: pg_dump on PATH, DATABASE_URL in environment.
"""

from __future__ import annotations

import argparse
import gzip
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def sync_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://verilumen:verilumen@localhost:5432/verilumen")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def pg_dump_url(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://")


def run_backup(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    raw_path = output_dir / f"verilumen_{stamp}.sql"
    gz_path = output_dir / f"verilumen_{stamp}.sql.gz"

    url = pg_dump_url(sync_db_url())
    cmd = ["pg_dump", url, "--no-owner", "--no-acl", "-f", str(raw_path)]
    subprocess.run(cmd, check=True)

    with raw_path.open("rb") as src, gzip.open(gz_path, "wb") as dst:
        shutil.copyfileobj(src, dst)
    raw_path.unlink()

    if gz_path.stat().st_size < 100:
        raise RuntimeError("Backup file suspiciously small — aborting")
    return gz_path


def apply_retention(output_dir: Path, daily: int, weekly: int, monthly: int) -> None:
    files = sorted(output_dir.glob("verilumen_*.sql.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    now = datetime.now(UTC)
    keep: set[Path] = set()

    # Keep newest N daily
    keep.update(files[:daily])

    # Weekly: one per ISO week
    weeks: dict[tuple[int, int], Path] = {}
    for f in files:
        ts = datetime.fromtimestamp(f.stat().st_mtime, tz=UTC)
        key = (ts.isocalendar().year, ts.isocalendar().week)
        weeks.setdefault(key, f)
    keep.update(list(weeks.values())[:weekly])

    # Monthly: one per month
    months: dict[tuple[int, int], Path] = {}
    for f in files:
        ts = datetime.fromtimestamp(f.stat().st_mtime, tz=UTC)
        key = (ts.year, ts.month)
        months.setdefault(key, f)
    keep.update(list(months.values())[:monthly])

    for f in files:
        if f not in keep and (now - datetime.fromtimestamp(f.stat().st_mtime, tz=UTC)) > timedelta(days=daily):
            f.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup VERILUMEN PostgreSQL database")
    parser.add_argument("--output-dir", default=os.environ.get("BACKUP_DIR", "backups"))
    parser.add_argument("--retention-daily", type=int, default=int(os.environ.get("BACKUP_RETENTION_DAILY", "7")))
    parser.add_argument("--retention-weekly", type=int, default=int(os.environ.get("BACKUP_RETENTION_WEEKLY", "4")))
    parser.add_argument("--retention-monthly", type=int, default=int(os.environ.get("BACKUP_RETENTION_MONTHLY", "3")))
    args = parser.parse_args()

    out = Path(args.output_dir)
    try:
        path = run_backup(out)
        apply_retention(out, args.retention_daily, args.retention_weekly, args.retention_monthly)
        print(f"Backup written: {path}")
        return 0
    except FileNotFoundError:
        print("pg_dump not found — install PostgreSQL client tools", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"pg_dump failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
