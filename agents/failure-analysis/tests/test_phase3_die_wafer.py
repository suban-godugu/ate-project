"""Phase 3 acceptance tests — FA-FR-007 die + FA-FR-008 wafer analytics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.bridge import test_records_to_die_logs
from adapters.schema import TestRecord
from die_wafer_analytics import (
    SEVERITY_NOT_DETERMINABLE,
    analyze_die_level_failures,
    analyze_wafer_level_failures,
)
from failure_rate_engine import compute_failure_rates
from ingestor import DieLog, PatternResult


class Phase3DieWaferTests(unittest.TestCase):
    def _record(self, die_id: str, *, fail: bool = True) -> TestRecord:
        return TestRecord(
            lot_id="LOT_P3",
            wafer_id="WF01",
            die_id=die_id,
            x=1,
            y=2,
            test_stage="CP",
            tester_id="T1",
            product_id="SOC",
            timestamp="2026-07-10T00:00:00Z",
            pass_fail="FAIL" if fail else "PASS",
            hard_bin="5" if fail else "1",
            soft_bin="10" if fail else "1",
            failing_patterns=["P1"] if fail else [],
            failing_tests=["IDDQ"] if fail else [],
            source_file="t.log",
            adapter_id="test",
        )

    def test_severity_not_determinable_without_supporting_data(self) -> None:
        records = [self._record("D1")]
        die_logs = test_records_to_die_logs(records)
        result = analyze_die_level_failures(die_logs, test_records=records)
        die = result["dashboard_feed"][0]
        self.assertFalse(die["severity_determinable"])
        self.assertEqual(die["severity_label"], SEVERITY_NOT_DETERMINABLE)
        self.assertIsNone(die["die_failure_severity"])

    def test_severity_determinable_with_ai_score(self) -> None:
        rec = self._record("D2")
        die_logs = test_records_to_die_logs([rec])
        die = die_logs[0]
        die.stored_failing = [
            PatternResult(
                pattern_id="P1",
                scan_chain_id="CH1",
                expected_signature="0x1",
                actual_signature="0x2",
                status="FAIL",
                raw_fields={"AI_SEVERITY_SCORE": "0.85"},
            )
        ]
        result = analyze_die_level_failures(die_logs, test_records=[rec])
        profile = result["dashboard_feed"][0]
        self.assertTrue(profile["severity_determinable"])
        self.assertEqual(profile["severity_class"], "CATASTROPHIC_FAIL")

    def test_die_profile_includes_drill_down_fields(self) -> None:
        records = [self._record("D3")]
        die_logs = test_records_to_die_logs(records)
        result = analyze_die_level_failures(die_logs, test_records=records)
        die = result["dashboard_feed"][0]
        self.assertEqual(die["x"], 1)
        self.assertEqual(die["y"], 2)
        self.assertIn("hard_bin", die["bin_history"])
        self.assertIn("P1", die["failing_patterns"])
        self.assertIn("IDDQ", die["failing_tests"])
        self.assertEqual(len(result["spatial_ai_handoff"]), 1)

    def test_wafer_outlier_flagged_vs_lot_siblings(self) -> None:
        records = []
        for waf in ("WF01", "WF02", "WF03"):
            for i in range(2):
                records.append(
                    TestRecord(
                        lot_id="LOT_P3",
                        wafer_id=waf,
                        die_id=f"{waf}_P{i}",
                        test_stage="CP",
                        tester_id="T1",
                        product_id="SOC",
                        timestamp="2026-07-10",
                        pass_fail="PASS",
                        source_file="t.log",
                        adapter_id="test",
                    )
                )
        for i in range(4):
            records.append(
                TestRecord(
                    lot_id="LOT_P3",
                    wafer_id="WF_BAD",
                    die_id=f"B{i}",
                    test_stage="CP",
                    tester_id="T1",
                    product_id="SOC",
                    timestamp="2026-07-10",
                    pass_fail="FAIL",
                    failing_patterns=["PX"],
                    source_file="t.log",
                    adapter_id="test",
                )
            )
        die_logs = test_records_to_die_logs(records)
        rates = compute_failure_rates(die_logs, test_records=records)
        wafer = analyze_wafer_level_failures(
            die_logs, test_records=records, failure_rates_engine=rates
        )
        outliers = [w for w in wafer["dashboard_feed"] if w["is_outlier"]]
        self.assertGreaterEqual(len(outliers), 1)
        self.assertGreaterEqual(wafer["outlier_wafer_count"], 1)
        self.assertTrue(any("bin_pareto" in w for w in wafer["dashboard_feed"]))

    def test_wafer_has_pareto_and_trend(self) -> None:
        records = [self._record("D1"), self._record("D2", fail=False)]
        die_logs = test_records_to_die_logs(records)
        wafer = analyze_wafer_level_failures(die_logs, test_records=records)
        self.assertIn("lot_sequence_trends", wafer)
        feed = wafer["dashboard_feed"][0]
        self.assertIn("dominant_fault_types", feed)
        self.assertIn("failing_pattern_pareto", feed)
        self.assertIn("yield_pct", feed)


if __name__ == "__main__":
    unittest.main()
