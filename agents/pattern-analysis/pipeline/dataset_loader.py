"""Shared helpers to load unified datasets from local path or HTTP URI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx


def load_dataset(path_or_uri: str) -> dict[str, Any]:
    if not path_or_uri:
        raise ValueError("dataset_path is required")
    p = Path(path_or_uri)
    if p.exists() and p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    # file:// URI
    if path_or_uri.startswith("file://"):
        local = Path(path_or_uri.replace("file:///", "").replace("file://", ""))
        return json.loads(local.read_text(encoding="utf-8"))
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(path_or_uri)
        resp.raise_for_status()
        return resp.json()
