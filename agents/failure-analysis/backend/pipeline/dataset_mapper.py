"""Map unified dataset into Failure Analysis record-like dicts."""

from __future__ import annotations

from typing import Any


def dataset_to_test_records(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    meta_top = dataset.get("metadata") or {}
    default_source = str(meta_top.get("file_name") or meta_top.get("source") or "unified_dataset")
    for idx, r in enumerate(dataset.get("records") or []):
        row_meta = r.get("metadata") or {}
        lot = str(r.get("lot_id") or row_meta.get("lot_id") or "UNKNOWN_LOT")
        wafer = str(r.get("wafer_id") or row_meta.get("wafer_id") or "UNKNOWN_WAFER")
        die = str(r.get("die_id") or row_meta.get("die_id") or f"DIE_{idx}")
        pass_fail = str(r.get("pass_fail") or row_meta.get("pass_fail") or "UNKNOWN").upper()
        if pass_fail in ("P", "PASS", "PASSED", "GOOD"):
            pass_fail = "PASS"
        elif pass_fail in ("F", "FAIL", "FAILED", "BAD"):
            pass_fail = "FAIL"
        else:
            # STIL chain / info rows still need a short pass_fail for FA engines.
            pass_fail = "INFO" if pass_fail else "UNKNOWN"
            if len(pass_fail) > 16:
                pass_fail = pass_fail[:16]
        source = str(r.get("source_file") or row_meta.get("source_file") or default_source)
        if len(source) > 480:
            source = source[-480:]
        pattern = r.get("pattern") or row_meta.get("pattern")
        def _clip(val: Any, n: int) -> str:
            s = str(val or "")
            return s if len(s) <= n else s[:n]

        out.append(
            {
                "lot_id": _clip(lot, 120),
                "wafer_id": _clip(wafer, 120),
                "die_id": _clip(die, 120),
                "x": r.get("die_x") if r.get("die_x") is not None else r.get("x"),
                "y": r.get("die_y") if r.get("die_y") is not None else r.get("y"),
                "tester_id": _clip(r.get("tester") or r.get("tester_id") or "PLATFORM", 120),
                "test_stage": _clip(r.get("program") or r.get("test_stage") or "SCAN", 60),
                "pass_fail": pass_fail,
                "timestamp": _clip(r.get("timestamp") or row_meta.get("timestamp") or "1970-01-01T00:00:00Z", 60),
                "source_file": source,
                "adapter_id": "platform_unified_dataset",
                "soft_bin": _clip(r.get("soft_bin") or "", 64),
                "hard_bin": _clip(r.get("hard_bin") or "", 64),
                "product_id": _clip(r.get("product_id") or "", 64),
                "failing_patterns": [str(pattern)] if pattern else [],
                "scan_fail_data": row_meta.get("scan_fail_data") or {},
            }
        )
    return out
