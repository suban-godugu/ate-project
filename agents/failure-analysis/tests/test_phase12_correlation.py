"""Phase 12 acceptance tests — FA-FR-006 failure pattern correlation engine."""

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
from backend.correlation.correlation_engine import CorrelationEngine
from backend.correlation.statistical_analysis import (
    build_feature_table,
    compute_correlation_matrix,
    mine_association_rules,
)
from ingestor import DieLog, PatternResult


def _pattern(pattern_id: str, chain: str = "CH1") -> PatternResult:
    return PatternResult(
        pattern_id=pattern_id,
        scan_chain_id=chain,
        expected_signature="1",
        actual_signature="0",
        status="FAIL",
        raw_fields={},
    )


def _die(
    lot: str,
    wafer: str,
    die_id: str,
    patterns: list[PatternResult],
    *,
    header: dict[str, str] | None = None,
    tester: str = "T1",
) -> DieLog:
    return DieLog(
        source_path=f"{lot}_{wafer}_{die_id}.log",
        tester_name=tester,
        device_name="SOC",
        lot_id=lot,
        wafer_id=wafer,
        die_id=die_id,
        header_fields=header or {},
        stored_failing=patterns,
        total_executions=len(patterns),
        pattern_test_counts={p.pattern_id: 1 for p in patterns},
        declared_patterns=len(patterns),
    )


class Phase12CorrelationEngineTests(unittest.TestCase):
    def test_full_pipeline_outputs(self) -> None:
        dies = [
            _die("L1", "W01", "D1", [_pattern("P_HIGH")]),
            _die("L2", "W01", "D1", [_pattern("P_HIGH")]),
            _die("L3", "W01", "D1", [_pattern("P_HIGH")]),
            _die("L1", "W01", "D2", [_pattern("P_LOW")]),
        ]
        report = CorrelationEngine().analyze(die_logs=dies)
        self.assertEqual(report["requirement"], "FA-FR-006")
        self.assertIn("correlation_matrix", report)
        self.assertIn("failure_dependency_graph", report)
        self.assertIn("pattern_relationships", report)
        self.assertIn("engineering_insights", report)
        self.assertTrue(report["meets_performance_target"])
        self.assertEqual(report["correlation_report"][0]["pattern_id"], "P_HIGH")

    def test_statistical_methods_present(self) -> None:
        dies = [
            _die("L1", "W01", "D1", [_pattern("P1")], header={"DIE_X": "1", "DIE_Y": "2"}),
            _die("L2", "W01", "D1", [_pattern("P1")], header={"DIE_X": "1", "DIE_Y": "2"}),
        ]
        report = CorrelationEngine().analyze(die_logs=dies)
        methods = report["statistical_methods"]
        self.assertIn("pearson", methods)
        self.assertIn("spearman", methods)
        self.assertIn("chi_square", methods)
        self.assertIn("association_rules", methods)

    def test_factor_contributions_preserved_from_legacy(self) -> None:
        dies = [
            _die("L1", "W01", "D1", [_pattern("P1")]),
            _die("L2", "W01", "D1", [_pattern("P1")]),
        ]
        report = CorrelationEngine().analyze(die_logs=dies)
        row = report["correlation_report"][0]
        total = round(sum(row["factor_contributions"].values()), 4)
        self.assertEqual(total, row["correlation_score"])

    def test_dimension_correlations(self) -> None:
        dies = [
            _die(f"L{i}", "W01", "D1", [_pattern("P1")], tester="T1") for i in range(1, 4)
        ]
        report = CorrelationEngine().analyze(die_logs=dies)
        self.assertIsInstance(report["dimension_correlations"], dict)

    def test_feature_table_and_matrix(self) -> None:
        rows = [
            {
                "pattern_id": "P1",
                "tester_id": "T1",
                "product_id": "SOC",
                "wafer_id": "W1",
                "die_id": "D1",
                "lot_id": "L1",
                "equipment_id": "T1",
                "machine_id": "M1",
                "operator_id": "OP1",
                "process_step": "CP",
                "shift": "2026-07-10 shift-1",
                "temperature": 25.0,
                "voltage": 1.2,
            }
        ]
        table = build_feature_table(rows)
        matrix = compute_correlation_matrix(table, threshold=0.0)
        self.assertIn("pearson", matrix)
        rules = mine_association_rules(table, min_support=0.01, min_confidence=0.5)
        self.assertIsInstance(rules, list)


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase12CorrelationApiTests(unittest.TestCase):
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
            "/api/v1/correlation/analyze",
            json={"upload_id": upload_id, "top_n": 25},
        )
        self.assertEqual(analyze.status_code, 200)
        body = analyze.json()
        self.assertIn("run_id", body)
        self.assertIn("correlation_matrix", body)
        self.assertIn("failure_dependency_graph", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]

        listing = self.client.get("/api/v1/correlation")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        matrix = self.client.get(f"/api/v1/correlation/matrix?run_id={run_id}")
        self.assertEqual(matrix.status_code, 200)
        self.assertIn("correlation_matrix", matrix.json())

        network = self.client.get(f"/api/v1/correlation/network?run_id={run_id}")
        self.assertEqual(network.status_code, 200)
        self.assertIn("failure_dependency_graph", network.json())


if __name__ == "__main__":
    unittest.main()
