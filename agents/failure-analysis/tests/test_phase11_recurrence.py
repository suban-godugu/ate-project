"""Phase 11 acceptance tests — FA-FR-005 recurring failure detection engine."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.schema import TestRecord
from backend.recurring.recurring_engine import RecurringEngine
from ingestor import DieLog, PatternResult


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


class Phase11RecurringEngineTests(unittest.TestCase):
    def test_pattern_recurrence_in_pipeline(self) -> None:
        dies = [
            _die("L1", "W01", "D1", pattern_id="P42"),
            _die("L2", "W01", "D1", pattern_id="P42"),
        ]
        report = RecurringEngine().analyze(die_logs=dies)
        self.assertEqual(report["requirement"], "FA-FR-005")
        self.assertTrue(report["recurring_failure_list"])
        self.assertIn("frequency_distribution", report)
        self.assertIn("severity_ranking", report)
        self.assertTrue(report["meets_performance_target"])

    def test_correlations_present(self) -> None:
        dies = [
            _die("L1", "W01", "D1", pattern_id="P42"),
            _die("L2", "W01", "D1", pattern_id="P42"),
            _die("L3", "W01", "D1", pattern_id="P42"),
        ]
        report = RecurringEngine().analyze(die_logs=dies)
        correlations = report["correlations"]
        for key in (
            "failure_frequency",
            "lot_correlation",
            "wafer_correlation",
            "die_correlation",
            "device_correlation",
            "product_correlation",
            "tester_correlation",
            "time_correlation",
        ):
            self.assertIn(key, correlations)

    def test_die_position_and_deduplication(self) -> None:
        dies = [
            _die("L1", "W01", "D1", header={"DIE_X": "3", "DIE_Y": "7"}),
            _die("L1", "W02", "D2", header={"DIE_X": "3", "DIE_Y": "7"}),
            _die("L1", "W03", "D3", header={"DIE_X": "3", "DIE_Y": "7"}),
        ]
        report = RecurringEngine().analyze(die_logs=dies)
        types = {e["signature_type"] for e in report["recurrence_events"]}
        self.assertIn("die_position_recurrence", types)
        keys = {
            f"{e['signature_type']}::{e['entity_key']}" for e in report["recurrence_events"]
        }
        self.assertEqual(len(keys), len(report["recurrence_events"]))

    def test_engineering_alerts_and_impacted_lots(self) -> None:
        dies = [
            _die(f"L{i}", "W01", "D1", pattern_id="P99") for i in range(1, 5)
        ]
        report = RecurringEngine().analyze(die_logs=dies)
        self.assertTrue(report["engineering_alerts"])
        self.assertTrue(report["impacted_lots"])
        self.assertIn("trend_analysis", report)

    def test_bin_recurrence_with_records(self) -> None:
        dies = [_die(f"L{i}", "W01", "D1") for i in range(1, 4)]
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
        report = RecurringEngine().analyze(die_logs=dies, test_records=records)
        types = {e["signature_type"] for e in report["recurrence_events"]}
        self.assertIn("bin_recurrence", types)


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase11RecurringApiTests(unittest.TestCase):
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
            "/api/v1/recurring/analyze",
            json={"upload_id": upload_id, "incremental": False},
        )
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIn("run_id", body)
        self.assertIn("recurring_failure_list", body)
        self.assertIn("engineering_alerts", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]

        listing = self.client.get("/api/v1/recurring")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        dashboard = self.client.get(f"/api/v1/recurring/dashboard?run_id={run_id}")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("dashboard", dashboard.json())
        self.assertIn("recurring_failure_list", dashboard.json()["dashboard"])


if __name__ == "__main__":
    unittest.main()
