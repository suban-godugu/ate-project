"""Production FA-FR-003 computation, API, and performance tests."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tests.pg_env  # noqa: F401

from fastapi.testclient import TestClient  # noqa: E402

from analytics.failure_rates.computation_engine import (  # noqa: E402
    FailureRateComputationEngine,
    FailureRateComputationError,
)
from analytics.failure_rates.production_service import (  # noqa: E402
    validate_computation_source,
    validate_metric_accuracy,
)
from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class ComputationEngineTests(unittest.TestCase):
    def test_failure_percentage_formula(self) -> None:
        records = [
            {
                "record_key": f"r{i}",
                "lot_id": "LOT1",
                "wafer_id": "W1",
                "die_id": f"D{i}",
                "device_id": "SOC",
                "test_program": "CP1",
                "pass_fail": "FAIL" if i < 2 else "PASS",
            }
            for i in range(10)
        ]
        patterns = [{"id": "pat-1", "pattern_id": "P1001", "category": "scan", "confidence": 0.9}]
        occurrences = [
            {"detected_pattern_id": "pat-1", "source_record_id": "r0"},
            {"detected_pattern_id": "pat-1", "source_record_id": "r1"},
        ]
        metrics = FailureRateComputationEngine().compute(
            records=records,
            patterns=patterns,
            occurrences=occurrences,
            aggregation_levels=["pattern", "lot", "batch"],
            baselines={},
            batch_key="batch-1",
            window_size=5,
        )
        pattern_metric = next(m for m in metrics if m["aggregation_level"] == "pattern")
        self.assertEqual(pattern_metric["total_tests"], 10)
        self.assertEqual(pattern_metric["fail_count"], 2)
        self.assertEqual(pattern_metric["pass_count"], 8)
        self.assertAlmostEqual(pattern_metric["failure_percentage"], 20.0)
        self.assertEqual(validate_metric_accuracy(metrics), 1.0)

    def test_rejects_division_by_zero_and_incomplete_traceability(self) -> None:
        with self.assertRaises(FailureRateComputationError):
            FailureRateComputationEngine().compute(
                records=[],
                patterns=[{"id": "pat-1", "pattern_id": "P1"}],
                occurrences=[],
                aggregation_levels=["pattern"],
                baselines={},
                batch_key="b",
                window_size=5,
            )
        issues, _, _ = validate_computation_source(
            [{"record_key": "a", "pass_fail": "FAIL"}],
            [{"id": "pat-1", "pattern_id": ""}],
            [],
        )
        codes = {issue["code"] for issue in issues}
        self.assertIn("MISSING_PATTERN_ID", codes)
        self.assertIn("MISSING_PATTERN_OCCURRENCES", codes)

    def test_historical_baseline_and_abnormal_trend(self) -> None:
        records = [
            {
                "record_key": f"r{i}",
                "lot_id": "LOT1",
                "wafer_id": "W1",
                "die_id": f"D{i}",
                "device_id": "SOC",
                "test_program": "CP1",
                "pass_fail": "FAIL" if i < 4 else "PASS",
            }
            for i in range(10)
        ]
        patterns = [{"id": "pat-1", "pattern_id": "P1001"}]
        occurrences = [
            {"detected_pattern_id": "pat-1", "source_record_id": f"r{i}"} for i in range(4)
        ]
        baselines = {
            ("P1001", "pattern", "P1001"): [
                {"computation_id": "old-1", "failure_percentage": 5.0},
                {"computation_id": "old-2", "failure_percentage": 6.0},
            ]
        }
        metrics = FailureRateComputationEngine().compute(
            records=records,
            patterns=patterns,
            occurrences=occurrences,
            aggregation_levels=["pattern"],
            baselines=baselines,
            batch_key="batch-1",
            window_size=5,
        )
        metric = metrics[0]
        self.assertAlmostEqual(metric["baseline_percentage"], 5.5)
        self.assertEqual(metric["trend_status"], "worsening")
        self.assertIn(metric["threshold_status"], {"warning", "critical"})

    def test_throughput_smoke(self) -> None:
        records = [
            {
                "record_key": f"r{i}",
                "lot_id": f"L{i % 20}",
                "wafer_id": f"W{i % 50}",
                "die_id": f"D{i}",
                "device_id": f"DEV{i % 5}",
                "test_program": "CP1",
                "pass_fail": "FAIL" if i % 17 == 0 else "PASS",
            }
            for i in range(20_000)
        ]
        patterns = [{"id": "pat-1", "pattern_id": "P1001"}]
        occurrences = [
            {"detected_pattern_id": "pat-1", "source_record_id": f"r{i}"}
            for i in range(0, 20_000, 17)
        ]
        started = time.perf_counter()
        metrics = FailureRateComputationEngine().compute(
            records=records,
            patterns=patterns,
            occurrences=occurrences,
            aggregation_levels=["pattern", "lot", "wafer", "batch"],
            baselines={},
            batch_key="batch-perf",
            window_size=5,
        )
        elapsed = time.perf_counter() - started
        self.assertGreater(len(metrics), 0)
        self.assertLess(elapsed, 8.0)


class FailureRateApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _prepare_source(self) -> str:
        stil = (FIXTURES / "minimal_scan.stil").read_bytes()
        log = (FIXTURES / "generic_datalog_sample.log").read_bytes()
        dataset = self.client.post(
            "/api/v1/datasets/upload",
            data={"name": f"fr003-{time.time_ns()}", "async_process": "false"},
            files=[
                ("files", ("minimal_scan.stil", stil, "application/octet-stream")),
                ("files", ("generic_datalog_sample.log", log, "text/plain")),
            ],
        )
        self.assertEqual(dataset.status_code, 200, dataset.text)
        dataset_id = dataset.json()["dataset_id"]
        detect = self.client.post(
            "/api/v1/patterns/detect",
            json={"dataset_id": dataset_id, "incremental": False},
        )
        self.assertEqual(detect.status_code, 200, detect.text)
        return dataset_id

    def test_compute_list_trends_statistics_and_pattern_detail(self) -> None:
        dataset_id = self._prepare_source()
        compute = self.client.post(
            "/api/v1/failure-rate/compute",
            json={"dataset_id": dataset_id, "window_size": 5},
        )
        self.assertEqual(compute.status_code, 200, compute.text)
        body = compute.json()
        self.assertEqual(body["status"], "completed")
        self.assertGreaterEqual(body["metric_count"], 1)
        self.assertEqual(body["benchmark_metrics"]["computation_accuracy"], 1.0)

        listing = self.client.get("/api/v1/failure-rate?aggregation_level=pattern")
        self.assertEqual(listing.status_code, 200)
        metrics = listing.json()["metrics"]
        self.assertTrue(metrics)
        pattern_id = metrics[0]["pattern_id"]

        detail = self.client.get(f"/api/v1/failure-rate/{pattern_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertTrue(detail.json()["metrics"])

        trends = self.client.get("/api/v1/failure-rate/trends")
        self.assertEqual(trends.status_code, 200)
        self.assertTrue(trends.json()["trends"])

        stats = self.client.get("/api/v1/failure-rate/statistics")
        self.assertEqual(stats.status_code, 200)
        self.assertGreater(stats.json()["total_metrics"], 0)

        history = self.client.get("/api/v1/failure-rate/history")
        self.assertEqual(history.status_code, 200)
        self.assertTrue(history.json()["history"])

    def test_invalid_source_contract(self) -> None:
        response = self.client.post("/api/v1/failure-rate/compute", json={})
        self.assertEqual(response.status_code, 422)

    def test_requires_completed_pattern_detection(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(upload.status_code, 200)
        upload_id = upload.json()["upload"]["id"]
        response = self.client.post(
            "/api/v1/failure-rate/compute",
            json={"upload_id": upload_id},
        )
        self.assertEqual(response.status_code, 409)

    def test_openapi_contract(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/failure-rate/compute",
            "/api/v1/failure-rate",
            "/api/v1/failure-rate/{pattern_id}",
            "/api/v1/failure-rate/trends",
            "/api/v1/failure-rate/statistics",
        ):
            self.assertIn(path, paths)

    def test_legacy_calculate_still_works(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        upload_id = upload.json()["upload"]["id"]
        calc = self.client.post(
            "/api/v1/failure-rates/calculate",
            json={"upload_id": upload_id},
        )
        self.assertEqual(calc.status_code, 200)


if __name__ == "__main__":
    unittest.main()
