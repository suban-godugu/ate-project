"""Phase 14 acceptance tests — FA-FR-008 wafer-level failure analytics engine."""

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
from backend.wafer_analysis.wafer_engine import WaferAnalysisEngine
from failure_rate_engine import compute_failure_rates
from ingestor import DieLog, PatternResult


def _pattern(pid: str = "P1") -> PatternResult:
    return PatternResult(
        pattern_id=pid,
        scan_chain_id="CH1",
        expected_signature="1",
        actual_signature="0",
        status="FAIL",
        raw_fields={},
    )


def _die(
    lot: str,
    wafer: str,
    die_id: str,
    *,
    fail: bool = True,
    x: int = 1,
    y: int = 2,
) -> DieLog:
    return DieLog(
        source_path=f"{lot}_{wafer}_{die_id}.log",
        tester_name="T1",
        device_name="SOC",
        lot_id=lot,
        wafer_id=wafer,
        die_id=die_id,
        header_fields={"DIE_X": str(x), "DIE_Y": str(y)},
        stored_failing=[_pattern()] if fail else [],
        total_executions=1,
        pattern_test_counts={"P1": 1} if fail else {},
        declared_patterns=1 if fail else 0,
    )


class Phase14WaferEngineTests(unittest.TestCase):
    def test_full_pipeline_outputs(self) -> None:
        dies = [
            _die("LOT1", "WF01", f"D{i}", fail=i % 2 == 0, x=i, y=i % 5)
            for i in range(10)
        ]
        report = WaferAnalysisEngine().analyze(die_logs=dies)
        self.assertEqual(report["requirement"], "FA-FR-008")
        self.assertIn("wafer_heatmap", report)
        self.assertIn("hotspot_analysis", report)
        self.assertIn("cluster_report", report)
        self.assertIn("radial_failure_analysis", report)
        self.assertIn("edge_center_analysis", report)
        self.assertIn("engineering_dashboard", report)
        self.assertTrue(report["meets_performance_target"])

    def test_wafer_yield_and_bin_distribution(self) -> None:
        dies = [_die("LOT1", "WF01", f"D{i}", fail=i < 3) for i in range(6)]
        records = [
            TestRecord(
                lot_id="LOT1",
                wafer_id="WF01",
                die_id=f"D{i}",
                x=i,
                y=0,
                test_stage="CP",
                tester_id="T1",
                timestamp="2026-07-10",
                pass_fail="FAIL" if i < 3 else "PASS",
                hard_bin="5" if i < 3 else "1",
                source_file="t.log",
                adapter_id="test",
            )
            for i in range(6)
        ]
        report = WaferAnalysisEngine().analyze(die_logs=dies, test_records=records)
        self.assertGreater(report["total_wafers"], 0)
        self.assertIn("bin_distribution", report)
        self.assertIn("yield_distribution", report)

    def test_outlier_detection_preserved(self) -> None:
        records = []
        for waf in ("WF01", "WF02", "WF03"):
            for i in range(2):
                records.append(
                    TestRecord(
                        lot_id="LOT1",
                        wafer_id=waf,
                        die_id=f"{waf}_P{i}",
                        x=i,
                        y=0,
                        test_stage="CP",
                        tester_id="T1",
                        timestamp="2026-07-10",
                        pass_fail="PASS",
                        source_file="t.log",
                        adapter_id="test",
                    )
                )
        for i in range(4):
            records.append(
                TestRecord(
                    lot_id="LOT1",
                    wafer_id="WF_BAD",
                    die_id=f"B{i}",
                    x=i,
                    y=0,
                    test_stage="CP",
                    tester_id="T1",
                    timestamp="2026-07-10",
                    pass_fail="FAIL",
                    failing_patterns=["PX"],
                    source_file="t.log",
                    adapter_id="test",
                )
            )
        die_logs = test_records_to_die_logs(records)
        report = WaferAnalysisEngine().analyze(die_logs=die_logs, test_records=records)
        self.assertGreaterEqual(report["outlier_wafer_count"], 1)

    def test_radial_and_edge_center(self) -> None:
        dies = [_die("LOT1", "WF01", f"D{i}", x=i * 2, y=0) for i in range(8)]
        report = WaferAnalysisEngine().analyze(die_logs=dies)
        radial = report["radial_failure_analysis"]
        edge = report["edge_center_analysis"]
        self.assertIn("per_wafer", radial)
        self.assertIn("per_wafer", edge)
        self.assertIn("global_edge_failures", edge)

    def test_plotly_ready_maps(self) -> None:
        dies = [_die("LOT1", "WF01", f"D{i}", x=i, y=i) for i in range(5)]
        report = WaferAnalysisEngine().analyze(die_logs=dies)
        self.assertIn("plotly_ready", report["wafer_heatmap"])


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase14WaferApiTests(unittest.TestCase):
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
            "/api/v1/wafer/analyze",
            json={"upload_id": upload_id},
        )
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIn("run_id", body)
        self.assertIn("wafer_heatmap", body)
        self.assertIn("engineering_dashboard", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]

        listing = self.client.get("/api/v1/wafer")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        wmap = self.client.get(f"/api/v1/wafer/map?run_id={run_id}")
        self.assertEqual(wmap.status_code, 200)
        self.assertIn("wafer_map", wmap.json())

        hotspots = self.client.get(f"/api/v1/wafer/hotspots?run_id={run_id}")
        self.assertEqual(hotspots.status_code, 200)
        self.assertIn("hotspot_analysis", hotspots.json())

        stats = self.client.get(f"/api/v1/wafer/statistics?run_id={run_id}")
        self.assertEqual(stats.status_code, 200)
        self.assertIn("wafer_statistics", stats.json())


if __name__ == "__main__":
    unittest.main()
