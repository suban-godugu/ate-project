#!/usr/bin/env python3
"""P21 — Parser verification CLI (delegates to pytest integration suite).

Usage (backend infra + ARQ worker must be running):
  python scripts/verify_parser_e2e.py

Equivalent:
  pytest tests/test_upload_pipeline.py -m integration -v
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_upload_pipeline.py",
        "-m",
        "integration",
        "-v",
        "--tb=short",
    ]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
