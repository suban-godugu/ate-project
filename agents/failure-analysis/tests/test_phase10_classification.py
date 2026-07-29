"""Phase 10 acceptance tests — FA-FR-004 enterprise fault classification."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.bridge import test_records_to_die_logs
from adapters.schema import TestRecord
from backend.classification.classification_engine import ClassificationEngine
from ingestor import DieLog, PatternResult

MINI_TAXONOMY = """
schema_version: test
unclassified_label: Unknown Failure
categories: [Functional Failure, Timing Failure, Leakage Failure, Unknown Failure]
category_definitions:
  Functional Failure: scan failures
  Timing Failure: timing failures
  Leakage Failure: leakage failures
thresholds:
  ir_drop_mv: 50
rules:
  - name: scan_shift
    when: {field: FAIL_TYPE, equals: SCAN_SHIFT}
    category: Functional Failure
  - name: timing_slack
    when: {field: SETUP_SLACK_PS, lt: 0}
    category: Timing Failure
  - name: iddq_test
    when: {field: failing_test, contains: IDDQ}
    category: Leakage Failure
engineering_recommendations:
  Functional Failure: Review scan diagnostics.
  Timing Failure: Run STA correlation.
  Leakage Failure: Retest IDDQ limits.
"""


class Phase10ClassificationEngineTests(unittest.TestCase):
    def _write_taxonomy(self) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8")
        handle.write(MINI_TAXONOMY)
        handle.close()
        return Path(handle.name)

    def _scan_shift_die(self) -> DieLog:
        pattern = PatternResult(
            pattern_id="P1",
            scan_chain_id="CH1",
            expected_signature="1",
            actual_signature="2",
            status="FAIL",
            raw_fields={"FAIL_TYPE": "SCAN_SHIFT"},
        )
        return DieLog(
            source_path="t.log",
            tester_name="T1",
            device_name="SOC",
            lot_id="L1",
            wafer_id="W1",
            die_id="D1",
            header_fields={},
            stored_failing=[pattern],
        )

    def test_rule_classification_with_confidence(self) -> None:
        tax = self._write_taxonomy()
        die = self._scan_shift_die()
        report = ClassificationEngine(
            taxonomy_path=tax, enable_ml=False, enable_llm=True
        ).analyze(die_logs=[die])
        fault = report["classified_faults"][0]
        self.assertEqual(fault["fault_category"], "Functional Failure")
        self.assertGreaterEqual(fault["classification_confidence"], 0.9)
        self.assertIn("engineering_recommendation", fault)
        self.assertIn("failure_signature", fault)
        self.assertIn("supporting_parameters", fault)
        self.assertTrue(report["meets_performance_target"])

    def test_unknown_when_no_rule_matches(self) -> None:
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
        report = ClassificationEngine(
            taxonomy_path=tax, enable_ml=False, enable_llm=False
        ).analyze(die_logs=[die])
        self.assertEqual(
            report["classified_faults"][0]["fault_category"], "Unknown Failure"
        )

    def test_bin_mapping_via_test_record(self) -> None:
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
        report = ClassificationEngine(enable_ml=False).analyze(
            die_logs=die_logs, test_records=[rec]
        )
        categories = {f["fault_category"] for f in report["classified_faults"]}
        self.assertTrue(
            "Leakage Failure" in categories or "Functional Failure" in categories
        )

    def test_classification_summary_output(self) -> None:
        die = self._scan_shift_die()
        report = ClassificationEngine(enable_ml=False).analyze(die_logs=[die])
        summary = report["classification_summary"]
        for key in ("total_faults", "unique_categories", "dominant_category"):
            self.assertIn(key, summary)
        self.assertIn("category_summary", report)
        self.assertIn("confidence_breakdown", report["classified_faults"][0])


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase10ClassificationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_analyze_after_upload(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(upload.status_code, 200)
        upload_id = upload.json()["upload"]["id"]

        analyze = self.client.post(
            "/api/v1/classification/analyze",
            json={"upload_id": upload_id, "enable_ml": True, "enable_llm": True},
        )
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIn("run_id", body)
        self.assertIn("classified_faults", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]
        fault_id = body["classified_faults"][0]["fault_id"]

        listing = self.client.get("/api/v1/classification")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        stats = self.client.get(f"/api/v1/classification/statistics?run_id={run_id}")
        self.assertEqual(stats.status_code, 200)
        self.assertIn("category_summary", stats.json())

        detail = self.client.get(f"/api/v1/classification/{fault_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["fault_id"], fault_id)
        self.assertIn("engineering_recommendation", detail.json())


if __name__ == "__main__":
    unittest.main()
