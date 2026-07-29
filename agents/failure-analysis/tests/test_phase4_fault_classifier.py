"""Phase 4 acceptance tests — FA-FR-004 fault classification."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.bridge import test_records_to_die_logs
from adapters.schema import TestRecord
from fault_classifier import classify_fault_type, classify_fault_types
from ingestor import DieLog, PatternResult


MINI_TAXONOMY = """
schema_version: test
unclassified_label: Unclassified
categories: [Scan Chain, Timing, Leakage, Unclassified]
category_definitions:
  Scan Chain: scan failures
  Timing: timing failures
  Leakage: leakage failures
thresholds:
  ir_drop_mv: 50
rules:
  - name: scan_shift
    when: {field: FAIL_TYPE, equals: SCAN_SHIFT}
    category: Scan Chain
  - name: timing_slack
    when: {field: SETUP_SLACK_PS, lt: 0}
    category: Timing
  - name: iddq_test
    when: {field: failing_test, contains: IDDQ}
    category: Leakage
"""


class Phase4FaultClassifierTests(unittest.TestCase):
    def _write_taxonomy(self) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        handle.write(MINI_TAXONOMY)
        handle.close()
        return Path(handle.name)

    def test_rule_classification_scan_shift(self) -> None:
        tax = self._write_taxonomy()
        pattern = PatternResult(
            pattern_id="P1",
            scan_chain_id="CH1",
            expected_signature="1",
            actual_signature="2",
            status="FAIL",
            raw_fields={"FAIL_TYPE": "SCAN_SHIFT"},
        )
        die = DieLog(
            source_path="t.log",
            tester_name="T1",
            device_name="SOC",
            lot_id="L1",
            wafer_id="W1",
            die_id="D1",
            header_fields={},
            stored_failing=[pattern],
        )
        result = classify_fault_types([die], taxonomy_path=tax, enable_ml=False)
        row = result["classified_failures"][0]
        self.assertEqual(row["fault_type"], "Scan Chain")
        self.assertEqual(row["method"], "rule")
        self.assertEqual(row["confidence"], 1.0)
        self.assertIn("Matched rule", row["explanation"])

    def test_bin_mapping_via_test_record(self) -> None:
        tax = Path(ROOT / "config" / "fault_taxonomy.yaml")
        rec = TestRecord(
            lot_id="L1",
            wafer_id="W1",
            die_id="D1",
            test_stage="CP",
            tester_id="T1",
            product_id="SOC",
            timestamp="2026-07-10",
            pass_fail="FAIL",
            hard_bin="5",
            failing_tests=["IDDQ"],
            failing_patterns=["P1"],
            source_file="t.log",
            adapter_id="test",
        )
        die_logs = test_records_to_die_logs([rec])
        result = classify_fault_types(die_logs, test_records=[rec], enable_ml=False)
        types = {row["fault_type"] for row in result["classified_failures"]}
        self.assertTrue("Leakage" in types or "Scan Chain" in types)

    def test_unclassified_when_no_rule_matches(self) -> None:
        tax = self._write_taxonomy()
        pattern = PatternResult(
            pattern_id="P9",
            scan_chain_id="",
            expected_signature="",
            actual_signature="",
            status="FAIL",
            raw_fields={},
        )
        die = DieLog(
            source_path="t.log",
            tester_name="T1",
            device_name="SOC",
            lot_id="L1",
            wafer_id="W1",
            die_id="D9",
            header_fields={},
            stored_failing=[pattern],
        )
        result = classify_fault_types([die], taxonomy_path=tax, enable_ml=False)
        self.assertEqual(result["classified_failures"][0]["fault_type"], "Unclassified")
        self.assertEqual(result["die_classifications"][0]["method"], "unclassified")

    def test_die_classification_output_shape(self) -> None:
        tax = self._write_taxonomy()
        pattern = PatternResult(
            pattern_id="P1",
            scan_chain_id="CH1",
            expected_signature="1",
            actual_signature="2",
            status="FAIL",
            raw_fields={"FAIL_TYPE": "SCAN_SHIFT"},
        )
        die = DieLog(
            source_path="t.log",
            tester_name="T1",
            device_name="SOC",
            lot_id="L1",
            wafer_id="W1",
            die_id="D1",
            header_fields={},
            stored_failing=[pattern],
        )
        result = classify_fault_types([die], taxonomy_path=tax, enable_ml=False)
        die_row = result["die_classifications"][0]
        for key in ("fault_type", "confidence", "method", "explanation"):
            self.assertIn(key, die_row)

    def test_classify_fault_type_helper(self) -> None:
        tax = self._write_taxonomy()
        pattern = PatternResult(
            pattern_id="P1",
            scan_chain_id="CH1",
            expected_signature="1",
            actual_signature="2",
            status="FAIL",
            raw_fields={"SETUP_SLACK_PS": "-5"},
        )
        label = classify_fault_type(pattern, taxonomy_path=tax)
        self.assertEqual(label, "Timing")


if __name__ == "__main__":
    unittest.main()
