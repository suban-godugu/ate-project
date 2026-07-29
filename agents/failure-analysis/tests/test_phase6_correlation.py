"""Phase 6 acceptance tests — FA-FR-006 multi-factor correlation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.schema import TestRecord
from ingestor import DieLog, PatternResult
from pattern_correlation import correlate_failures_with_patterns
from recurrence_detection import detect_recurrences


def _pattern(pattern_id: str, chain: str = "CH1") -> PatternResult:
    return PatternResult(
        pattern_id=pattern_id,
        scan_chain_id=chain,
        expected_signature="1",
        actual_signature="0",
        status="FAIL",
        raw_fields={},
    )


def _die(
    lot: str,
    wafer: str,
    die_id: str,
    patterns: list[PatternResult],
    *,
    header: dict[str, str] | None = None,
) -> DieLog:
    return DieLog(
        source_path=f"{lot}_{wafer}_{die_id}.log",
        tester_name="T1",
        device_name="SOC",
        lot_id=lot,
        wafer_id=wafer,
        die_id=die_id,
        header_fields=header or {},
        stored_failing=patterns,
        total_executions=len(patterns),
        pattern_test_counts={p.pattern_id: 1 for p in patterns},
        declared_patterns=len(patterns),
    )


class Phase6CorrelationTests(unittest.TestCase):
    def test_correlation_report_includes_factor_breakdown(self) -> None:
        dies = [
            _die("L1", "W01", "D1", [_pattern("P_HIGH")]),
            _die("L2", "W01", "D1", [_pattern("P_HIGH")]),
            _die("L3", "W01", "D1", [_pattern("P_HIGH")]),
            _die("L1", "W01", "D2", [_pattern("P_LOW")]),
        ]
        recurring = detect_recurrences(dies)
        result = correlate_failures_with_patterns(dies, recurring_failures=recurring)
        leader = result["correlation_report"][0]
        self.assertEqual(leader["pattern_id"], "P_HIGH")
        for key in (
            "factor_scores",
            "factor_contributions",
            "correlation_score",
            "status",
        ):
            self.assertIn(key, leader)
        self.assertEqual(
            set(leader["factor_scores"].keys()),
            {
                "failure_frequency",
                "normalized_failure_rate",
                "uniqueness",
                "co_failure_lift",
                "spatial_concentration",
                "cross_lot_persistence",
            },
        )

    def test_factor_contributions_sum_to_correlation_score(self) -> None:
        dies = [
            _die("L1", "W01", "D1", [_pattern("P1")], header={"DIE_X": "1", "DIE_Y": "2"}),
            _die("L2", "W01", "D1", [_pattern("P1")], header={"DIE_X": "1", "DIE_Y": "2"}),
        ]
        result = correlate_failures_with_patterns(dies)
        row = result["correlation_report"][0]
        total = round(sum(row["factor_contributions"].values()), 4)
        self.assertEqual(total, row["correlation_score"])

    def test_uniqueness_boosts_single_pattern_dies(self) -> None:
        unique_die = _die("L1", "W01", "D1", [_pattern("P_UNIQUE")])
        mixed_die = _die("L1", "W01", "D2", [_pattern("P_A"), _pattern("P_B")])
        result = correlate_failures_with_patterns([unique_die, mixed_die])
        by_id = {row["pattern_id"]: row for row in result["correlation_report"]}
        self.assertGreater(
            by_id["P_UNIQUE"]["factor_scores"]["uniqueness"],
            by_id["P_A"]["factor_scores"]["uniqueness"],
        )

    def test_spatial_handoff_present_for_clustered_coordinates(self) -> None:
        dies = [
            _die("L1", "W01", f"D{i}", [_pattern("P1")], header={"DIE_X": "5", "DIE_Y": "5"})
            for i in range(3)
        ]
        result = correlate_failures_with_patterns(dies)
        handoff = result["correlation_report"][0]["spatial_ai_handoff"]
        self.assertEqual(handoff["status"], "ready")
        self.assertEqual(handoff["agent"], "Spatial AI Agent")
        self.assertGreater(result["correlation_report"][0]["factor_scores"]["spatial_concentration"], 0.5)

    def test_downstream_export_for_agents(self) -> None:
        dies = [
            _die("L1", "W01", "D1", [_pattern("P1")]),
            _die("L2", "W01", "D1", [_pattern("P1")]),
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
        result = correlate_failures_with_patterns(dies, test_records=records)
        export = result["downstream_export"]
        self.assertEqual(export["requirement"], "FA-FR-006")
        self.assertTrue(export["patterns"])
        self.assertIn("factor_contributions", export["patterns"][0])


if __name__ == "__main__":
    unittest.main()
