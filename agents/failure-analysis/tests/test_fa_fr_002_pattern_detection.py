"""Production acceptance, rule, API, and benchmark tests for FA-FR-002."""

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

from adapters.schema import TestRecord  # noqa: E402
from analytics.pattern_detection.detection_service import (  # noqa: E402
    benchmark_metrics,
    validate_normalized_source,
)
from analytics.pattern_detection.rule_engine import (  # noqa: E402
    EngineeringRuleEngine,
    RuleSet,
)
from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


def record(
    index: int,
    *,
    pattern: str | None = "P1001",
    failing_test: str | None = None,
) -> TestRecord:
    item = TestRecord(
        lot_id="LOT1",
        wafer_id=f"W{index % 2}",
        die_id=f"D{index}",
        test_stage="CP1",
        tester_id="T1",
        pass_fail="FAIL",
        timestamp="2026-07-15T00:00:00Z",
        source_file="fixture.log",
        adapter_id="test",
        product_id="SOC",
        x=index,
        y=index,
        failing_patterns=[pattern] if pattern else [],
        failing_tests=[failing_test] if failing_test else [],
    )
    item.record_key = item.build_record_key()
    return item


class RuleEngineTests(unittest.TestCase):
    def test_known_rule_groups_explicit_patterns(self) -> None:
        detections = EngineeringRuleEngine().detect(
            [record(1, pattern="P1001"), record(2, pattern="P1001")]
        )
        known = [d for d in detections if d["pattern_id"] == "P1001"]
        self.assertEqual(len(known), 1)
        self.assertEqual(known[0]["occurrence_count"], 2)
        self.assertEqual(known[0]["detection_method"], "engineering_rule")
        self.assertGreaterEqual(known[0]["confidence"], 0.95)

    def test_recurring_unknown_is_flagged_for_review(self) -> None:
        detections = EngineeringRuleEngine().detect(
            [
                record(1, pattern=None, failing_test=None),
                record(2, pattern=None, failing_test=None),
            ]
        )
        unknown = [d for d in detections if d["pattern_category"] == "unknown"]
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]["detection_method"], "unknown_recurring")
        self.assertIn("engineering review", unknown[0]["explanation"].lower())

    def test_rule_set_is_versioned_and_complete(self) -> None:
        rules = RuleSet.load()
        self.assertTrue(rules.version)
        self.assertGreaterEqual(len(rules.rules), 4)
        self.assertTrue(all(rule.get("explanation") for rule in rules.rules))

    def test_duplicate_normalized_records_are_rejected(self) -> None:
        item = record(1)
        source = {"payload": item.to_dict()}
        issues, _ = validate_normalized_source([item, item], [source, source])
        self.assertIn("DUPLICATE_RECORD", {issue["code"] for issue in issues})

    def test_benchmark_metrics_from_ground_truth(self) -> None:
        metrics = benchmark_metrics(
            [{"pattern_id": "P1"}, {"pattern_id": "P2"}],
            expected_pattern_ids=["P1", "P3"],
            processing_ms=100,
            source_count=100,
        )
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 0.5)
        self.assertEqual(metrics["f1_score"], 0.5)
        self.assertGreater(metrics["throughput_records_per_minute"], 0)

    def test_rule_engine_throughput_smoke(self) -> None:
        records = [record(i, pattern=f"P{i % 10}") for i in range(10_000)]
        started = time.perf_counter()
        detections = EngineeringRuleEngine().detect(records)
        elapsed = time.perf_counter() - started
        self.assertEqual(len(detections), 10)
        self.assertLess(elapsed, 10.0)


class PatternDetectionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _create_dataset(self) -> str:
        stil = (FIXTURES / "minimal_scan.stil").read_bytes()
        log = (FIXTURES / "generic_datalog_sample.log").read_bytes()
        response = self.client.post(
            "/api/v1/datasets/upload",
            data={"name": f"fr002-{time.time_ns()}", "async_process": "false"},
            files=[
                ("files", ("minimal_scan.stil", stil, "application/octet-stream")),
                ("files", ("generic_datalog_sample.log", log, "text/plain")),
            ],
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["dataset_id"]

    def test_detect_persist_query_and_history(self) -> None:
        dataset_id = self._create_dataset()
        response = self.client.post(
            "/api/v1/patterns/detect",
            json={
                "dataset_id": dataset_id,
                "incremental": False,
                "expected_pattern_ids": ["P1001", "P1002"],
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "completed")
        self.assertGreaterEqual(body["pattern_count"], 2)
        self.assertEqual(body["benchmark_metrics"]["recall"], 1.0)

        listing = self.client.get("/api/v1/patterns?search=Explicit")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["patterns"])
        pattern_id = listing.json()["patterns"][0]["id"]

        detail = self.client.get(f"/api/v1/patterns/{pattern_id}")
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertTrue(detail.json()["occurrences"])
        self.assertIn("confidence_record", detail.json())

        statistics = self.client.get("/api/v1/patterns/statistics")
        self.assertEqual(statistics.status_code, 200)
        self.assertGreater(statistics.json()["total_patterns"], 0)

        history = self.client.get("/api/v1/patterns/history")
        self.assertEqual(history.status_code, 200)
        self.assertTrue(history.json()["history"])

    def test_invalid_source_contract(self) -> None:
        response = self.client.post("/api/v1/patterns/detect", json={})
        self.assertEqual(response.status_code, 422)

    def test_openapi_contract(self) -> None:
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/patterns/detect",
            "/api/v1/patterns",
            "/api/v1/patterns/{pattern_row_id}",
            "/api/v1/patterns/statistics",
            "/api/v1/patterns/history",
        ):
            self.assertIn(path, paths)


if __name__ == "__main__":
    unittest.main()
