"""Heatmap and distribution visualization payloads."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_pattern_heatmap(failures: list[dict[str, Any]]) -> dict[str, Any]:
    """Lot x pattern intensity matrix for dashboard rendering."""
    matrix: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    patterns: set[str] = set()
    lots: set[str] = set()
    for row in failures:
        lot = str(row.get("lot_id", "UNKNOWN"))
        pid = str(row.get("pattern_id", "UNKNOWN"))
        matrix[lot][pid] += 1
        patterns.add(pid)
        lots.add(lot)

    pattern_list = sorted(patterns)
    lot_list = sorted(lots)
    cells = [
        {"lot_id": lot, "pattern_id": pid, "intensity": matrix[lot][pid]}
        for lot in lot_list
        for pid in pattern_list
        if matrix[lot][pid] > 0
    ]
    return {
        "type": "lot_pattern_heatmap",
        "lots": lot_list,
        "patterns": pattern_list,
        "cells": cells,
        "max_intensity": max((c["intensity"] for c in cells), default=0),
    }


def build_wafer_pattern_map(failures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in failures:
        rows.append(
            {
                "lot_id": row.get("lot_id"),
                "wafer_id": row.get("wafer_id"),
                "die_id": row.get("die_id"),
                "pattern_id": row.get("pattern_id"),
                "confidence": row.get("confidence", 0.0),
            }
        )
    return rows
