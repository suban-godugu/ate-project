"""Phase 5 acceptance tests — FA-FR-005 recurrence detection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.schema import TestRecord
from ingestor import DieLog, PatternResult
from recurrence_detection import detect_recurrences


def _die(
    lot: str,
    wafer: str,
    die_id: str,
    *,
    pattern_id: str = "P1",
    tester: str = "T1",
    header: dict[str, str] | None = None,
) -> DieLog:
    pattern = PatternResult(
        pattern_id=pattern_id,
        scan_chain_id="CH1",
        expected_signature="1",
        actual_signature="0",
        status="FAIL",
        raw_fields={},
    )
    return DieLog(
        source_path=f"{lot}_{wafer}_{die_id}.log",
        tester_name=tester,
        device_name="SOC",
        lot_id=lot,
        wafer_id=wafer,
        die_id=die_id,
        header_fields=header or {},
        stored_failing=[pattern],
        total_executions=1,
    )


class Phase5RecurrenceTests(unittest.TestCase):
    def test_pattern_recurrence_across_lots(self) -> None:
        dies = [
            _die("L1", "W01", "D1", pattern_id="P42"),
            _die("L2", "W01", "D1", pattern_id="P42"),
        ]
        result = detect_recurrences(dies)
        pattern_events = [
            e for e in result["recurrence_events"] if e["signature_type"] == "pattern_recurrence"
        ]
        self.assertEqual(len(pattern_events), 1)
        self.assertEqual(pattern_events[0]["entity_key"], "P42")
        self.assertGreaterEqual(pattern_events[0]["confidence"], 0.5)

    def test_die_position_recurrence(self) -> None:
        dies = [
            _die("L1", "W01", "D1", header={"DIE_X": "3", "DIE_Y": "7"}),
            _die("L1", "W02", "D2", header={"DIE_X": "3", "DIE_Y": "7"}),
            _die("L1", "W03", "D3", header={"DIE_X": "3", "DIE_Y": "7"}),
        ]
        result = detect_recurrences(dies)
        events = [
            e
            for e in result["recurrence_events"]
            if e["signature_type"] == "die_position_recurrence"
        ]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["entity_key"], "(3,7)")
        self.assertIn("recommendation", events[0])

    def test_bin_recurrence_with_test_records(self) -> None:
        dies = [
            _die("L1", "W01", "D1"),
            _die("L2", "W01", "D1"),
            _die("L3", "W01", "D1"),
        ]
        records = [
            TestRecord(
                lot_id=die.lot_id,
                wafer_id=die.wafer_id,
                die_id=die.die_id,
                test_stage="CP",
                tester_id="T1",
                pass_fail="FAIL",
                timestamp="2026-07-10 08:00:00",
                source_file=die.source_path,
                adapter_id="test",
                hard_bin="5",
            )
            for die in dies
        ]
        result = detect_recurrences(dies, test_records=records)
        events = [e for e in result["recurrence_events"] if e["signature_type"] == "bin_recurrence"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["entity_key"], "5")

    def test_equipment_recurrence_flags_high_rate_tester(self) -> None:
        dies = [_die("L1", "W01", f"D{i}", tester="BAD") for i in range(4)]
        dies.extend(_die(f"L{i}", "W01", "D1", tester=f"G{i}") for i in range(4))
        for die in dies[4:]:
            die.stored_failing = []
        result = detect_recurrences(dies)
        events = [
            e for e in result["recurrence_events"] if e["signature_type"] == "equipment_recurrence"
        ]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["entity_key"], "BAD")

    def test_entity_index_maps_die_flags(self) -> None:
        dies = [
            _die("L1", "W01", "D1", pattern_id="P42"),
            _die("L2", "W01", "D1", pattern_id="P42"),
        ]
        result = detect_recurrences(dies)
        die_flags = result["entity_index"]["dies"].get("L1|W01|D1", [])
        self.assertTrue(any(item["signature_type"] == "pattern_recurrence" for item in die_flags))


if __name__ == "__main__":
    unittest.main()
