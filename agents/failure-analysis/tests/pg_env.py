"""Shared PostgreSQL environment bootstrap for automated tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env", override=False)

# Drop any legacy SQLite overrides so tests use PostgreSQL exclusively.
existing = os.environ.get("DATABASE_URL", "")
if existing and "sqlite" in existing.lower():
    del os.environ["DATABASE_URL"]

# Build DATABASE_URL from parts when not provided.
if not os.environ.get("DATABASE_URL"):
    host = os.environ.get("DATABASE_HOST", "localhost")
    port = os.environ.get("DATABASE_PORT", "5432")
    name = os.environ.get("DATABASE_NAME", "failure_analysis_db")
    user = os.environ.get("DATABASE_USER", "postgres")
    password = os.environ.get("DATABASE_PASSWORD", "")
    if not password or password in {"CHANGE_ME", "changeme"}:
        raise RuntimeError(
            "PostgreSQL tests require DATABASE_PASSWORD in .env "
            "(or a postgresql+asyncpg DATABASE_URL)."
        )
    from urllib.parse import quote_plus

    os.environ["DATABASE_URL"] = (
        f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )

if "sqlite" in os.environ["DATABASE_URL"].lower():
    raise RuntimeError("SQLite is not supported for tests. Configure PostgreSQL.")
