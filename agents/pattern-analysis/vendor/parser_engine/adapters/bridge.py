"""Bridge canonical TestRecord objects to legacy DieLog for the analytics pipeline."""

from __future__ import annotations

from collections import defaultdict

from parser_engine.adapters.schema import TestRecord
from parser_engine.parsers.ate.ingestor import DieLog, PatternResult


def test_records_to_die_logs(records: list[TestRecord]) -> list[DieLog]:
    """Group accepted test records by die and build DieLog objects."""
    groups: dict[tuple[str, str, str, str], list[TestRecord]] = defaultdict(list)
    for record in records:
        key = (record.source_file, record.lot_id, record.wafer_id, record.die_id)
        groups[key].append(record)

    die_logs: list[DieLog] = []
    for (source_file, lot_id, wafer_id, die_id), group in groups.items():
        header = group[0].raw_fields.copy()
        header.setdefault("LOT_ID", lot_id)
        header.setdefault("WAFER_ID", wafer_id)
        header.setdefault("DIE_ID", die_id)
        header.setdefault("DEVICE_NAME", group[0].product_id)
        header.setdefault("TESTER_NAME", group[0].tester_id)
        if group[0].x is not None:
            header.setdefault("DIE_X", str(group[0].x))
        if group[0].y is not None:
            header.setdefault("DIE_Y", str(group[0].y))
        raw = group[0].raw_fields or {}
        if "DIE_X" not in header:
            for key in ("DIE_X", "DIE_COL", "WAFER_X", "X1"):
                if raw.get(key) is not None:
                    header.setdefault("DIE_X", str(raw[key]))
                    break
        if "DIE_Y" not in header:
            for key in ("DIE_Y", "DIE_ROW", "WAFER_Y", "Y1"):
                if raw.get(key) is not None:
                    header.setdefault("DIE_Y", str(raw[key]))
                    break
        if group[0].hard_bin:
            header.setdefault("HARD_BIN", str(group[0].hard_bin))

        patterns: list[PatternResult] = []
        failing: list[PatternResult] = []
        pattern_counts: dict[str, int] = defaultdict(int)

        for rec in group:
            if rec.failing_patterns:
                for pid in rec.failing_patterns:
                    pattern_counts[pid] += 1
                    pr = PatternResult(
                        pattern_id=pid,
                        scan_chain_id=rec.scan_fail_data.get("scan_chain_id", ""),
                        expected_signature=str(rec.scan_fail_data.get("expected", "")),
                        actual_signature=str(rec.scan_fail_data.get("actual", "")),
                        status="FAIL",
                        raw_fields={k: str(v) for k, v in rec.parametric.items()},
                    )
                    patterns.append(pr)
                    failing.append(pr)
            else:
                pattern_counts["SUMMARY"] = pattern_counts.get("SUMMARY", 0) + 1

        is_fail = any(r.pass_fail.upper() == "FAIL" for r in group)
        has_failing_tests = any(rec.failing_tests for rec in group)
        if not patterns and is_fail and not has_failing_tests:
            pr = PatternResult(
                pattern_id="UNKNOWN",
                scan_chain_id="",
                expected_signature="",
                actual_signature="",
                status="FAIL",
                raw_fields={},
            )
            patterns = [pr]
            failing = [pr]

        die_logs.append(
            DieLog(
                source_path=source_file,
                tester_name=group[0].tester_id,
                device_name=group[0].product_id,
                lot_id=lot_id,
                wafer_id=wafer_id,
                die_id=die_id,
                header_fields=header,
                patterns=patterns if patterns else [],
                stored_failing=failing if failing else None,
                total_executions=sum(pattern_counts.values()) or len(group),
                pattern_test_counts=dict(pattern_counts),
                declared_patterns=len(pattern_counts),
            )
        )

    return die_logs
