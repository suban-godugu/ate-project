"""Map unified dataset records into Pattern Analysis internal view models."""

from __future__ import annotations

from typing import Any


def dataset_to_pattern_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in dataset.get("records") or []:
        rows.append(
            {
                "pattern_id": r.get("pattern") or r.get("die_id") or "",
                "chain_id": r.get("scan_chain") or "",
                "expected": r.get("expected") or "",
                "actual": r.get("actual") or "",
                "status": r.get("pass_fail") or "",
                "lot_id": r.get("lot_id") or "",
                "source_file": r.get("source_file") or "",
            }
        )
    return rows
