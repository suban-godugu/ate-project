"""Resolve project paths and ensure ``src/`` is importable.

Platform layout:
  Inputs  → UPLOAD_INPUT_ROOT  (C:\\personal\\input all file)
  Outputs → AGENT_OUTPUT_ROOT  (C:\\personal\\agent and parser output\\<job>\\scan)
  Live UI still uses DATA_DIR/stil + DATA_DIR/logs as hardlink views of inputs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = API_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"

UPLOAD_INPUT_ROOT = Path(
    os.environ.get("UPLOAD_INPUT_ROOT", r"C:\personal\input all file")
)
AGENT_OUTPUT_ROOT = Path(
    os.environ.get("AGENT_OUTPUT_ROOT", r"C:\personal\agent and parser output")
)
# Default Scan agent-local output; platform jobs redirect via SCAN_OUTPUT_DIR / job folder.
OUTPUT_DIR = Path(
    os.environ.get("SCAN_OUTPUT_DIR", str(PROJECT_ROOT / "output"))
)


def job_scan_output_dir(job_id: str) -> Path:
    path = AGENT_OUTPUT_ROOT / str(job_id) / "scan"
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_src_on_path() -> Path:
    src = str(SRC_DIR)
    if src not in sys.path:
        sys.path.insert(0, src)
    return SRC_DIR
