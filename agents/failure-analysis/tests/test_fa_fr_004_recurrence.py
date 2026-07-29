"""Production FA-FR-005 engine, API, benchmark, and performance tests."""

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

from backend.main import app  # noqa: E402
from backend.recurring.production_engine import (  # noqa: E402
    ProductionRecurrenceEngine,
    RecurrenceComputationError,
)
from backend.recurring.production_service import (  # noqa: E402
    recurrence_benchmarks,
    validate_recurrence_source,
)

FIXTURES = ROOT / "tests" / "fixtures"


def observation(
    index: int,
    *,
    execution: str,
    source: str,
    pattern: str = "P2001",
    frequency_code: str = "SCAN",
) -> dict:
    return {
        "occurrence_id": f"{execution}-{index}",
        "execution_id": execution,
        "computation_id": f"comp-{execution}",
        "source_id": source,
        "source_record_id": f"{execution}-record-{index}",
        "detected_pattern_id": f"detected-{execution}-{pattern}",
        "pattern_id": pattern,
        "pattern_name": f"Explicit pattern {pattern}",
        "pattern_confidence": 0.96,
        "classification_execution_id": f"class-{execution}",
        "fault_type": "Scan Chain Failure",
        "classification_confidence": 0.94,
        "failure_category": "scan",
        "failure_code": frequency_code,
        "device_id": "SOC",
        "die_id": f"D{index}",
        "wafer_id": f"W{index % 3}",
        "lot_id": source,
        "test_program": "CP1",
        "test_stage": "CP1",
        "x": 5,
        "y": 6,
        "timestamp": f"2026-07-{10 + (0 if execution == 'old' else 1):02d}T08:00:00Z",
    }


class RecurrenceEngineTests(unittest.TestCase):
    def test_recurrence_frequency_confidence_trend_and_hotspot(self) -> None:
        rows = [
            observation(0, execution="old", source="LOT1"),
            observation(0, execution="new", source="LOT2"),
            observation(1, execution="new", source="LOT2"),
        ]
        result = ProductionRecurrenceEngine().analyze(
            observations=rows,
            current_execution_id="new",
            source_record_counts={"old": 100, "new": 100},
            failure_rates={"P2001": 2.0},
            incremental=True,
        )
        self.assertEqual(len(result["recurrences"]), 1)
        recurrence = result["recurrences"][0]
        self.assertEqual(recurrence["recurrence_count"], 3)
        self.assertAlmostEqual(recurrence["recurrence_frequency"], 0.02)
        self.assertAlmostEqual(recurrence["recurrence_percentage"], 2.0)
        self.assertEqual(recurrence["fault_type"], "Scan Chain Failure")
        self.assertEqual(recurrence["trend_direction"], "increasing")
        self.assertGreater(recurrence["confidence_score"], 0)
        self.assertTrue(recurrence["engineering_recommendation"])
        self.assertTrue(result["hotspots"])

    def test_zero_fills_absent_historical_executions(self) -> None:
        rows = [
            observation(0, execution="old", source="LOT1"),
            observation(0, execution="new", source="LOT3"),
        ]
        result = ProductionRecurrenceEngine().analyze(
            observations=rows,
            current_execution_id="new",
            source_record_counts={"old": 100, "gap": 100, "new": 100},
            failure_rates={"P2001": 1.0},
            incremental=True,
        )
        series = result["recurrences"][0]["time_series"]
        self.assertEqual(
            next(item for item in series if item["execution_id"] == "gap")["frequency"],
            0.0,
        )

    def test_similarity_grouping_and_ground_truth_benchmarks(self) -> None:
        rows = []
        for pattern in ("P1", "P2"):
            rows.extend(
                [
                    observation(0, execution="old", source="LOT1", pattern=pattern),
                    observation(0, execution="new", source="LOT2", pattern=pattern),
                ]
            )
        result = ProductionRecurrenceEngine().analyze(
            observations=rows,
            current_execution_id="new",
            source_record_counts={"old": 10, "new": 10},
            failure_rates={"P1": 10.0, "P2": 10.0},
            incremental=False,
        )
        groups = {row["similarity_group"] for row in result["recurrences"]}
        self.assertEqual(len(groups), 1)
        metrics = recurrence_benchmarks(result["recurrences"], ["P1", "P3"])
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 0.5)
        self.assertEqual(metrics["f1_score"], 0.5)

    def test_validation_and_missing_history_rejection(self) -> None:
        row = observation(0, execution="new", source="LOT2")
        issues, warnings = validate_recurrence_source(
            observations=[row],
            current_execution_id="new",
            current_source_count=1,
            detection_source_count=1,
            computation_source_count=1,
        )
        self.assertFalse(issues)
        self.assertFalse(warnings)
        with self.assertRaises(RecurrenceComputationError):
            ProductionRecurrenceEngine().analyze(
                observations=[row],
                current_execution_id="new",
                source_record_counts={"new": 1},
                failure_rates={"P2001": 100.0},
                incremental=False,
            )

    def test_100k_observation_throughput(self) -> None:
        rows = [
            observation(
                index,
                execution="old" if index < 50_000 else "new",
                source="LOT1" if index < 50_000 else "LOT2",
            )
            for index in range(100_000)
        ]
        started = time.perf_counter()
        result = ProductionRecurrenceEngine().analyze(
            observations=rows,
            current_execution_id="new",
            source_record_counts={"old": 100_000, "new": 100_000},
            failure_rates={"P2001": 50.0},
            incremental=True,
        )
        self.assertTrue(result["recurrences"])
        self.assertLess(time.perf_counter() - started, 20.0)


class RecurrenceApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _prepare_upload(self, index: int, *, classify: bool = True) -> str:
        content = (FIXTURES / "csv_die_results_sample.csv").read_text(encoding="utf-8")
        content = content.replace("LOT_SYN_002", f"LOT_FR004_{time.time_ns()}_{index}")
        upload = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={
                "file": (
                    f"recurrence-{index}.csv",
                    content.encode("utf-8"),
                    "text/csv",
                )
            },
        )
        self.assertEqual(upload.status_code, 200, upload.text)
        upload_id = upload.json()["upload"]["id"]
        detect = self.client.post(
            "/api/v1/patterns/detect",
            json={"upload_id": upload_id, "incremental": False},
        )
        self.assertEqual(detect.status_code, 200, detect.text)
        compute = self.client.post(
            "/api/v1/failure-rate/compute",
            json={"upload_id": upload_id, "window_size": 5},
        )
        self.assertEqual(compute.status_code, 200, compute.text)
        if classify:
            classification = self.client.post(
                "/api/v1/classification/analyze",
                json={"upload_id": upload_id, "enable_ml": False, "enable_llm": False},
            )
            self.assertEqual(classification.status_code, 200, classification.text)
        return upload_id

    def test_analyze_query_trends_hotspots_history_and_detail(self) -> None:
        self._prepare_upload(1)
        current_upload = self._prepare_upload(2)
        analyze = self.client.post(
            "/api/v1/recurrence/analyze",
            json={
                "upload_id": current_upload,
                "incremental": True,
                "expected_recurring_pattern_ids": ["P2001", "P2002"],
            },
        )
        self.assertEqual(analyze.status_code, 200, analyze.text)
        body = analyze.json()
        self.assertEqual(body["status"], "completed")
        self.assertGreater(body["recurrence_count"], 0)
        self.assertTrue(body["benchmark_metrics"]["ground_truth_available"])
        self.assertTrue(body["benchmark_metrics"]["api_sla_met"])
        self.assertTrue(body["recurrences"][0]["fault_type"])
        self.assertGreaterEqual(body["recurrences"][0]["recurrence_percentage"], 0)

        listing = self.client.get(
            f"/api/v1/recurrence?analysis_id={body['execution_id']}"
        )
        self.assertEqual(listing.status_code, 200)
        rows = listing.json()["recurrences"]
        self.assertTrue(rows)
        detail = self.client.get(
            f"/api/v1/recurrence/{rows[0]['recurrence_id']}"
        )
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertIn("traceability", detail.json())
        self.assertTrue(detail.json()["engineering_recommendations"])

        for endpoint, key in (
            ("/api/v1/recurrence/trends", "trends"),
            ("/api/v1/recurrence/hotspots", "hotspots"),
            ("/api/v1/recurrence/history", "history"),
        ):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn(key, response.json())
        stats = self.client.get("/api/v1/recurrence/statistics")
        self.assertEqual(stats.status_code, 200)
        self.assertGreater(stats.json()["total_recurrences"], 0)

    def test_async_analysis_is_audited(self) -> None:
        self._prepare_upload(3)
        current_upload = self._prepare_upload(4)
        response = self.client.post(
            "/api/v1/recurrence/analyze",
            json={"upload_id": current_upload, "async_execution": True},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "queued")
        history = self.client.get("/api/v1/recurrence/history").json()["history"]
        execution = next(
            item for item in history if item["execution_id"] == body["execution_id"]
        )
        self.assertIn(execution["status"], {"queued", "processing", "completed"})

    def test_contract_and_upstream_gate(self) -> None:
        invalid = self.client.post("/api/v1/recurrence/analyze", json={})
        self.assertEqual(invalid.status_code, 422)
        forbidden = self.client.get(
            "/api/v1/recurrence", headers={"X-Role": "viewer"}
        )
        self.assertEqual(forbidden.status_code, 403)
        content = (
            FIXTURES / "csv_die_results_sample.csv"
        ).read_bytes()
        upload = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("gate.csv", content, "text/csv")},
        )
        upload_id = upload.json()["upload"]["id"]
        rejected = self.client.post(
            "/api/v1/recurrence/analyze", json={"upload_id": upload_id}
        )
        self.assertEqual(rejected.status_code, 409)

        unclassified_upload = self._prepare_upload(9, classify=False)
        unclassified = self.client.post(
            "/api/v1/recurrence/analyze",
            json={"upload_id": unclassified_upload},
        )
        self.assertEqual(unclassified.status_code, 409, unclassified.text)

        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/recurrence/analyze",
            "/api/v1/recurrence",
            "/api/v1/recurrence/{recurrence_id}",
            "/api/v1/recurrence/trends",
            "/api/v1/recurrence/hotspots",
            "/api/v1/recurrence/history",
        ):
            self.assertIn(path, paths)

    def test_legacy_recurring_api_remains_mounted(self) -> None:
        response = self.client.get("/api/v1/recurring")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
