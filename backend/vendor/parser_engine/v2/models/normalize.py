"""Normalize v1 parser outputs into EnterpriseRecord lists."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from parser_engine.v2.models.enterprise_record import EnterpriseRecord


def from_test_record(rec: Any, *, parser_id: str = "") -> EnterpriseRecord:
    scan = getattr(rec, "scan_fail_data", None) or {}
    er = EnterpriseRecord(
        lot_id=str(getattr(rec, "lot_id", "") or ""),
        wafer_id=str(getattr(rec, "wafer_id", "") or ""),
        die_id=str(getattr(rec, "die_id", "") or ""),
        test_stage=str(getattr(rec, "test_stage", "") or ""),
        tester_id=str(getattr(rec, "tester_id", "") or ""),
        pass_fail=str(getattr(rec, "pass_fail", "") or ""),
        timestamp=str(getattr(rec, "timestamp", "") or ""),
        source_file=str(getattr(rec, "source_file", "") or ""),
        parser_id=parser_id or str(getattr(rec, "adapter_id", "") or ""),
        product_id=str(getattr(rec, "product_id", "") or ""),
        hard_bin=str(getattr(rec, "hard_bin", "") or ""),
        soft_bin=str(getattr(rec, "soft_bin", "") or ""),
        x=getattr(rec, "x", None),
        y=getattr(rec, "y", None),
        failing_tests=list(getattr(rec, "failing_tests", []) or []),
        failing_patterns=list(getattr(rec, "failing_patterns", []) or []),
        chain_id=str(scan.get("chain_id") or scan.get("SCAN_CHAIN_ID") or ""),
        fail_flop_id=str(scan.get("fail_flop_id") or scan.get("FAIL_FLOP_ID") or ""),
        fail_type=str(scan.get("fail_type") or scan.get("FAIL_TYPE") or ""),
        scan_fail_data=dict(scan),
        parametric=dict(getattr(rec, "parametric", {}) or {}),
        raw_fields=dict(getattr(rec, "raw_fields", {}) or {}),
        record_key=str(getattr(rec, "record_key", "") or ""),
    )
    if not er.record_key:
        er.record_key = er.build_record_key()
    return er


def from_parser_result(result: Any, *, parser_id: str) -> list[EnterpriseRecord]:
    records = getattr(result, "records", None) or []
    return [from_test_record(r, parser_id=parser_id) for r in records]


def from_diagnosis_dataframe(df: Any, *, source_file: str, parser_id: str) -> list[EnterpriseRecord]:
    if df is None or getattr(df, "empty", True):
        return []
    out: list[EnterpriseRecord] = []
    for row in df.to_dict(orient="records"):
        er = EnterpriseRecord(
            lot_id=str(row.get("lot_id") or ""),
            wafer_id=str(row.get("wafer_id") or ""),
            die_id=str(row.get("die_id") or ""),
            test_stage="SCAN",
            tester_id=str(row.get("tester_name") or row.get("tester_id") or ""),
            pass_fail=str(row.get("status") or "FAIL"),
            source_file=str(row.get("source_file") or source_file),
            parser_id=parser_id,
            chain_id=str(row.get("chain_id") or row.get("chain") or ""),
            fail_flop_id=str(row.get("fail_flop_id") or ""),
            fail_type=str(row.get("fail_type") or ""),
            expected_signature=str(row.get("expected_signature") or ""),
            actual_signature=str(row.get("actual_signature") or ""),
            parametric={
                k: row[k]
                for k in ("ir_drop_mv", "thermal_c", "ai_severity_score")
                if k in row and row[k] is not None
            },
            raw_fields={k: str(v) for k, v in row.items() if v is not None},
        )
        er.record_key = er.build_record_key()
        out.append(er)
    return out


def from_pattern_ate_map(data: dict[str, Any], *, source_file: str, parser_id: str) -> list[EnterpriseRecord]:
    out: list[EnterpriseRecord] = []
    for pattern_id, channels in (data or {}).items():
        for channel_id, payload in (channels or {}).items():
            er = EnterpriseRecord(
                die_id=str(pattern_id),
                test_stage="ATE",
                pass_fail=str((payload or {}).get("status") or ""),
                source_file=source_file,
                parser_id=parser_id,
                failing_patterns=[str(pattern_id)],
                chain_id=str(channel_id),
                expected_signature=str((payload or {}).get("expected") or "")[:256],
                actual_signature=str((payload or {}).get("actual") or "")[:256],
                scan_fail_data=dict(payload or {}),
            )
            er.record_key = er.build_record_key()
            out.append(er)
    return out


def from_stil_cpm(cpm: dict[str, Any], *, source_file: str, parser_id: str) -> list[EnterpriseRecord]:
    meta = (cpm or {}).get("metadata") or {}
    status = str((cpm or {}).get("status") or "PASS")
    er = EnterpriseRecord(
        lot_id=str(meta.get("source") or "STIL"),
        wafer_id="SCAN",
        die_id=Path(source_file).stem,
        test_stage="STIL",
        tester_id="ATE",
        pass_fail="PASS" if status.upper() == "PASS" else "FAIL",
        source_file=source_file,
        parser_id=parser_id,
        product_id=str(meta.get("title") or Path(source_file).stem),
        parametric={
            "pattern_count": float(meta.get("pattern_count") or 0),
            "chain_count": float(meta.get("chain_count") or 0),
            "vector_count": float(meta.get("vector_count") or 0),
        },
        raw_fields={k: str(v) for k, v in meta.items()},
        parse_confidence=1.0 if status.upper() == "PASS" else 0.7,
    )
    er.record_key = er.build_record_key()
    return [er]
