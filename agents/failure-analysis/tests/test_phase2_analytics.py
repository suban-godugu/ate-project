"""Phase 2 acceptance tests — FA-FR-002 detection + FA-FR-003 failure rates."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.bridge import test_records_to_die_logs
from adapters.schema import TestRecord
from failure_rate_engine import (
    FAILURE_RATE_TOLERANCE_PCT,
    compute_failure_rates,
    verify_rates_against_reference,
)
from pattern_detection import (
    PatternManifest,
    detect_failing_patterns,
    measure_detection_accuracy,
)


class Phase2AnalyticsTests(unittest.TestCase):
    def _make_record(
        self,
        *,
        die_id: str,
        pass_fail: str = "FAIL",
        failing_patterns: list[str] | None = None,
        failing_tests: list[str] | None = None,
    ) -> TestRecord:
        return TestRecord(
            lot_id="LOT_T",
            wafer_id="WF_T",
            die_id=die_id,
            test_stage="CP",
            tester_id="TESTER_A",
            product_id="SOC",
            timestamp="2026-07-10T00:00:00Z",
            pass_fail=pass_fail,
            hard_bin="5" if pass_fail == "FAIL" else "1",
            failing_patterns=failing_patterns or [],
            failing_tests=failing_tests or [],
            source_file="synthetic.log",
            adapter_id="test",
        )

    def test_deterministic_detection_100_percent(self) -> None:
        records = [
            self._make_record(die_id="D1", failing_patterns=["P1001", "P1002"]),
            self._make_record(die_id="D2", pass_fail="PASS"),
        ]
        die_logs = test_records_to_die_logs(records)
        failures = detect_failing_patterns(die_logs, test_records=records)
        self.assertEqual(len(failures), 2)
        self.assertTrue(all(f["detection_method"] == "deterministic" for f in failures))
        self.assertTrue(all(f["confidence"] == 1.0 for f in failures))
        accuracy = measure_detection_accuracy(die_logs, failures)
        self.assertTrue(accuracy["meets_deterministic_threshold"])

    def test_inferred_detection_with_manifest(self) -> None:
        manifest = PatternManifest(
            test_to_pattern={"MEMORY_BIST": "002001", "IDDQ": "000550"},
            pattern_ids={"002001", "000550"},
            source="test",
        )
        records = [
            self._make_record(die_id="D3", failing_tests=["MEMORY_BIST"]),
        ]
        die_logs = test_records_to_die_logs(records)
        failures = detect_failing_patterns(
            die_logs, manifest=manifest, test_records=records
        )
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["pattern_id"], "002001")
        self.assertEqual(failures[0]["detection_method"], "inferred")
        self.assertGreaterEqual(failures[0]["confidence"], 0.95)
        accuracy = measure_detection_accuracy(die_logs, failures)
        self.assertTrue(accuracy["meets_inferred_precision"])

    def test_failure_rates_match_reference_within_tolerance(self) -> None:
        records = [
            self._make_record(die_id="D1", pass_fail="FAIL", failing_patterns=["P1"]),
            self._make_record(die_id="D2", pass_fail="PASS"),
            self._make_record(die_id="D3", pass_fail="FAIL", failing_patterns=["P2"]),
            self._make_record(die_id="D4", pass_fail="PASS"),
        ]
        die_logs = test_records_to_die_logs(records)
        computed = compute_failure_rates(die_logs, test_records=records)

        reference = {
            "lot_level": {
                "LOT_T": {
                    "tested": 4,
                    "failed": 2,
                    "failure_rate_pct": 50.0,
                }
            }
        }
        check = verify_rates_against_reference(computed, reference)
        self.assertTrue(check["passed"], check["mismatches"])
        self.assertEqual(computed["summary"]["overall_failure_rate_pct"], 50.0)
        self.assertEqual(computed["tolerance_pct"], FAILURE_RATE_TOLERANCE_PCT)

    def test_alerts_fire_on_threshold_breach(self) -> None:
        records = [
            self._make_record(die_id=f"D{i}", pass_fail="FAIL", failing_patterns=[f"P{i}"])
            for i in range(5)
        ] + [self._make_record(die_id="D_PASS", pass_fail="PASS")]
        die_logs = test_records_to_die_logs(records)
        rates = compute_failure_rates(die_logs, test_records=records, alert_threshold_pct=50.0)
        lot_alerts = [a for a in rates["alerts"] if a["level"] == "lot"]
        self.assertGreaterEqual(len(lot_alerts), 1)
        self.assertEqual(lot_alerts[0]["alert_type"], "THRESHOLD_BREACH")

    def test_multi_level_aggregation_present(self) -> None:
        records = [self._make_record(die_id="D1", pass_fail="FAIL", failing_patterns=["PX"])]
        die_logs = test_records_to_die_logs(records)
        rates = compute_failure_rates(die_logs, test_records=records)
        for level in (
            "device_level",
            "lot_level",
            "wafer_level",
            "pattern_level",
            "bin_level",
            "tester_level",
            "product_level",
            "test_stage_level",
            "time_window_level",
        ):
            self.assertIn(level, rates, f"missing {level}")


if __name__ == "__main__":
    unittest.main()
