"""Phase 8 acceptance tests — FA-FR-002 pattern detection engine."""

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
from analytics.pattern_detection.pattern_engine import PatternEngine
from pattern_detection import PatternManifest


class Phase8PatternEngineTests(unittest.TestCase):
    def _records(self) -> list[TestRecord]:
        rows = []
        for i in range(6):
            rows.append(
                TestRecord(
                    lot_id=f"L{i % 3}",
                    wafer_id=f"W{i % 2}",
                    die_id=f"D{i}",
                    test_stage="CP",
                    tester_id="T1",
                    product_id="SOC",
                    timestamp="2026-07-10",
                    pass_fail="FAIL",
                    failing_patterns=["P1001" if i % 2 == 0 else "P1002"],
                    source_file="synthetic.log",
                    adapter_id="test",
                )
            )
        return rows

    def test_pipeline_produces_ranking_with_confidence(self) -> None:
        records = self._records()
        die_logs = test_records_to_die_logs(records)
        report = PatternEngine().analyze(die_logs=die_logs, test_records=records)
        self.assertGreater(report["failure_count"], 0)
        self.assertGreater(report["unique_patterns"], 0)
        self.assertTrue(report["pattern_ranking"])
        for row in report["pattern_ranking"]:
            self.assertIn("confidence", row)
            self.assertTrue(row["confidence_required"])
            self.assertIn("rank", row)
        self.assertIn("pattern_heatmap", report)
        self.assertLess(report["processing_ms"], 10000)

    def test_clustering_and_similarity_present(self) -> None:
        records = self._records()
        die_logs = test_records_to_die_logs(records)
        report = PatternEngine().analyze(die_logs=die_logs, test_records=records)
        self.assertIn("clusters", report)
        self.assertIn("similarity_pairs", report)
        self.assertIn("failure_distribution", report)

    def test_inferred_patterns_included(self) -> None:
        manifest = PatternManifest(
            test_to_pattern={"IDDQ": "000550"},
            pattern_ids={"000550"},
            source="test",
        )
        records = [
            TestRecord(
                lot_id="L1",
                wafer_id="W1",
                die_id="D1",
                test_stage="CP",
                tester_id="T1",
                product_id="SOC",
                timestamp="2026-07-10",
                pass_fail="FAIL",
                failing_tests=["IDDQ"],
                source_file="synthetic.log",
                adapter_id="test",
            )
        ]
        die_logs = test_records_to_die_logs(records)
        report = PatternEngine().analyze(
            die_logs=die_logs, test_records=records, manifest=manifest
        )
        pattern_ids = {row["pattern_id"] for row in report["pattern_ranking"]}
        self.assertIn("000550", pattern_ids)


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase8PatternApiTests(unittest.TestCase):
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
            "/api/v1/patterns/analyze",
            json={"upload_id": upload_id, "top_n": 10},
        )
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIn("analysis_id", body)
        self.assertTrue(body["pattern_ranking"])
        self.assertTrue(body["meets_performance_target"])

        top = self.client.get(f"/api/v1/patterns/top?analysis_id={body['analysis_id']}")
        self.assertEqual(top.status_code, 200)
        self.assertTrue(top.json()["patterns"])

        listing = self.client.get("/api/v1/patterns")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["analyses"])


if __name__ == "__main__":
    unittest.main()
