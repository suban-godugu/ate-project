"""Phase 13 acceptance tests — FA-FR-007 die-level failure analytics engine."""

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
from backend.die_analysis.die_engine import DieAnalysisEngine
from backend.die_analysis.spatial_statistics import compute_failure_density, map_coordinates
from ingestor import DieLog, PatternResult


class Phase13DieEngineTests(unittest.TestCase):
    def _record(self, die_id: str, *, x: int = 1, y: int = 2, fail: bool = True) -> TestRecord:
        return TestRecord(
            lot_id="LOT_P13",
            wafer_id="WF01",
            die_id=die_id,
            x=x,
            y=y,
            test_stage="CP",
            tester_id="T1",
            product_id="SOC",
            timestamp="2026-07-10T00:00:00Z",
            pass_fail="FAIL" if fail else "PASS",
            hard_bin="5" if fail else "1",
            failing_patterns=["P1"] if fail else [],
            failing_tests=["IDDQ"] if fail else [],
            source_file="t.log",
            adapter_id="test",
        )

    def test_full_pipeline_outputs(self) -> None:
        records = [self._record(f"D{i}", x=i, y=i % 3) for i in range(6)]
        die_logs = test_records_to_die_logs(records)
        report = DieAnalysisEngine().analyze(die_logs=die_logs, test_records=records)
        self.assertEqual(report["requirement"], "FA-FR-007")
        self.assertIn("die_heatmap", report)
        self.assertIn("hotspot_analysis", report)
        self.assertIn("cluster_report", report)
        self.assertIn("yield_distribution", report)
        self.assertIn("engineering_dashboard", report)
        self.assertTrue(report["meets_performance_target"])

    def test_coordinate_mapping_and_zones(self) -> None:
        points = [
            {"die_id": "D1", "wafer_id": "W1", "x": 0, "y": 0, "is_failing": True},
            {"die_id": "D2", "wafer_id": "W1", "x": 10, "y": 10, "is_failing": True},
            {"die_id": "D3", "wafer_id": "W1", "x": 1, "y": 1, "is_failing": False},
        ]
        mapped = map_coordinates(points)
        self.assertGreater(mapped["total_with_coordinates"], 0)
        self.assertIn("edge_failures", mapped)
        self.assertIn("center_failures", mapped)

    def test_failure_density_grid(self) -> None:
        points = [
            {"x": i, "y": j, "is_failing": (i + j) % 2 == 0}
            for i in range(5)
            for j in range(5)
        ]
        density = compute_failure_density(points, grid_resolution=5)
        self.assertTrue(density["grid"])
        self.assertGreaterEqual(density["max_density"], 0.0)

    def test_die_profiles_preserved_from_legacy(self) -> None:
        records = [self._record("D1")]
        die_logs = test_records_to_die_logs(records)
        report = DieAnalysisEngine().analyze(die_logs=die_logs, test_records=records)
        profile = report["die_profiles"][0]
        self.assertEqual(profile["x"], 1)
        self.assertEqual(profile["y"], 2)
        self.assertIn("failing_patterns", profile)

    def test_spatial_ai_handoff_present(self) -> None:
        records = [self._record("D1"), self._record("D2", fail=False)]
        die_logs = test_records_to_die_logs(records)
        report = DieAnalysisEngine().analyze(die_logs=die_logs, test_records=records)
        self.assertEqual(len(report["spatial_ai_handoff"]), 2)
        self.assertIn("plotly_ready", report["die_heatmap"])


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase13DieApiTests(unittest.TestCase):
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
            "/api/v1/die/analyze",
            json={"upload_id": upload_id},
        )
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIn("run_id", body)
        self.assertIn("die_heatmap", body)
        self.assertIn("engineering_dashboard", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]

        listing = self.client.get("/api/v1/die")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        heatmap = self.client.get(f"/api/v1/die/heatmap?run_id={run_id}")
        self.assertEqual(heatmap.status_code, 200)
        self.assertIn("heatmap", heatmap.json())

        hotspots = self.client.get(f"/api/v1/die/hotspots?run_id={run_id}")
        self.assertEqual(hotspots.status_code, 200)
        self.assertIn("hotspot_analysis", hotspots.json())

        stats = self.client.get(f"/api/v1/die/statistics?run_id={run_id}")
        self.assertEqual(stats.status_code, 200)
        self.assertIn("yield_distribution", stats.json())


if __name__ == "__main__":
    unittest.main()
