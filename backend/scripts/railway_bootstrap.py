"""One-shot Railway bootstrap: migrate DB schema + seed demo user/data.

Usage (Railway Console, from /app):
  python scripts/railway_bootstrap.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    print("==> alembic upgrade head")
    upgrade = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        check=False,
    )
    if upgrade.returncode != 0:
        print("alembic failed", file=sys.stderr)
        return upgrade.returncode

    print("==> seed demo data")
    seed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "seed.py")],
        cwd=ROOT,
        check=False,
    )
    if seed.returncode != 0:
        print("seed failed", file=sys.stderr)
        return seed.returncode

    print("OK — login with alex@verilumen.ai / changeme123")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
