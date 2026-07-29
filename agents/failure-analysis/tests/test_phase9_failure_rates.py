"""Phase 9 acceptance tests — FA-FR-003 failure rate analytics engine."""

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
from analytics.failure_rates.dashboard_service import build_dashboard_dataset
from analytics.failure_rates.rate_engine import FailureRateEngine
from analytics.failure_rates.statistics import attach_statistics, bucket_summary, compute_statistics


class Phase9FailureRateEngineTests(unittest.TestCase):
    def _records(self) -> list[TestRecord]:
        rows = []
        for i in range(20):
            rows.append(
                TestRecord(
                    lot_id=f"L{i % 4}",
                    wafer_id=f"W{i % 3}",
                    die_id=f"D{i}",
                    test_stage="CP",
                    tester_id=f"T{i % 2}",
                    product_id="SOC",
                    timestamp=f"2026-07-10 {8 + (i % 8):02d}:00:00",
                    pass_fail="FAIL" if i % 5 == 0 else "PASS",
                    failing_patterns=["P1001"] if i % 5 == 0 else [],
                    source_file="synthetic.log",
                    adapter_id="test",
                )
            )
        return rows

    def test_all_hierarchy_levels_present(self) -> None:
        records = self._records()
        die_logs = test_records_to_die_logs(records)
        report = FailureRateEngine().calculate(
            die_logs=die_logs,
            test_records=records,
            upload_id="upload-test",
        )
        self.assertEqual(report["requirement"], "FA-FR-003")
        for level in (
            "device_level",
            "die_level",
            "wafer_level",
            "lot_level",
            "product_level",
            "tester_level",
            "shift_level",
            "production_level",
        ):
            self.assertIn(level, report)
            self.assertIn("entities", report[level])
            self.assertIn("statistics", report[level])

    def test_statistics_metrics(self) -> None:
        summary = bucket_summary(100, 5)
        self.assertEqual(summary["pass_count"], 95)
        self.assertEqual(summary["fail_count"], 5)
        self.assertAlmostEqual(summary["failure_percentage"], 5.0)
        self.assertAlmostEqual(summary["yield_percentage"], 95.0)

        stats = compute_statistics([1.0, 2.0, 3.0, 4.0])
        self.assertEqual(stats["mean"], 2.5)
        self.assertEqual(stats["median"], 2.5)
        self.assertGreater(stats["sigma_level"], 0)

    def test_dashboard_dataset(self) -> None:
        records = self._records()
        die_logs = test_records_to_die_logs(records)
        report = FailureRateEngine().calculate(die_logs=die_logs, test_records=records)
        dashboard = build_dashboard_dataset(report)
        self.assertIn("overall_yield", dashboard)
        self.assertIn("device_failure_rate", dashboard)
        self.assertIn("trend_graphs", dashboard)
        self.assertIn("plotly_ready", dashboard)
        self.assertIn("recharts_ready", dashboard)

    def test_overall_manufacturing_yield(self) -> None:
        records = self._records()
        die_logs = test_records_to_die_logs(records)
        report = FailureRateEngine().calculate(die_logs=die_logs, test_records=records)
        yield_block = report["overall_manufacturing_yield"]
        self.assertIn("yield_pct", yield_block)
        self.assertIn("failure_rate_pct", yield_block)
        self.assertGreater(yield_block["total_dies_tested"], 0)

    def test_attach_statistics_on_level(self) -> None:
        level = {
            "A": bucket_summary(10, 1),
            "B": bucket_summary(10, 3),
        }
        enriched = attach_statistics(level)
        self.assertEqual(enriched["statistics"]["count"], 2)
        self.assertAlmostEqual(enriched["statistics"]["mean"], 20.0)


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase9FailureRateApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_calculate_after_upload(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(upload.status_code, 200)
        upload_id = upload.json()["upload"]["id"]

        calc = self.client.post(
            "/api/v1/failure-rates/calculate",
            json={"upload_id": upload_id},
        )
        self.assertEqual(calc.status_code, 200)
        body = calc.json()
        self.assertIn("run_id", body)
        self.assertIn("failure_rate_report", body)
        self.assertIn("dashboard_dataset", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]

        listing = self.client.get("/api/v1/failure-rates")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        device = self.client.get(f"/api/v1/failure-rates/device?run_id={run_id}")
        self.assertEqual(device.status_code, 200)
        self.assertIn("device_level", device.json())

        wafer = self.client.get(f"/api/v1/failure-rates/wafer?run_id={run_id}")
        self.assertEqual(wafer.status_code, 200)
        self.assertIn("wafer_level", wafer.json())

        lot = self.client.get(f"/api/v1/failure-rates/lot?run_id={run_id}")
        self.assertEqual(lot.status_code, 200)
        self.assertIn("lot_level", lot.json())

        dashboard = self.client.get(f"/api/v1/failure-rates/dashboard?run_id={run_id}")
        self.assertEqual(dashboard.status_code, 200)
        self.assertIn("dashboard", dashboard.json())
        self.assertIn("overall_yield", dashboard.json()["dashboard"])


if __name__ == "__main__":
    unittest.main()
