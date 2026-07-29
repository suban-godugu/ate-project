"""Map unified dataset into Scan Diagnosis frame-like rows."""

from __future__ import annotations

from typing import Any


def dataset_to_diagnosis_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for r in dataset.get("records") or []:
        meta = r.get("metadata") or {}
        rows.append(
            {
                "lot_id": r.get("lot_id") or "",
                "wafer_id": r.get("wafer_id") or "",
                "die_id": r.get("die_id") or "",
                "chain_id": r.get("scan_chain") or "",
                "fail_flop_id": meta.get("fail_flop_id") or "",
                "fail_type": meta.get("fail_type") or "",
                "expected_signature": r.get("expected") or "",
                "actual_signature": r.get("actual") or "",
                "status": r.get("pass_fail") or "FAIL",
                "source_file": r.get("source_file") or "",
            }
        )
    return rows
