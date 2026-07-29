"""FA-FR-006 statistical, contract, benchmark, and API acceptance tests."""

from __future__ import annotations

import random
import time
import unittest
from pathlib import Path

from backend.correlation.production_engine import CorrelationConfig, ProductionCorrelationEngine
from backend.correlation.production_service import correlation_benchmarks


def _config(**updates: object) -> CorrelationConfig:
    values = {
        "version": "test-v1",
        "algorithm": "phi_coefficient",
        "coefficient_threshold": 0.1,
        "strong_threshold": 0.5,
        "very_strong_threshold": 0.7,
        "min_confidence": 0.5,
        "min_support": 0.01,
        "significance_level": 0.05,
        "min_sample_size": 20,
        "high_impact_threshold": 0.55,
        "trend_delta": 0.05,
        "batch_size": 10_000,
    }
    values.update(updates)
    return CorrelationConfig(**values)


def _sources() -> tuple[list[dict], dict[str, int], list[dict]]:
    rows: list[dict] = []
    for execution in ("old", "new"):
        for index in range(20):
            rows.append(_row(execution, index, "P1", "Scan Chain Failure"))
        for index in range(20, 30):
            rows.append(_row(execution, index, "P2", "Scan Chain Failure"))
        for index in range(30, 40):
            rows.append(_row(execution, index, "P1", "Timing Failure"))
    recurrence = [{
        "recurrence_id": "rec-1",
        "pattern_id": "P1",
        "fault_type": "Scan Chain Failure",
        "recurrence_frequency": 0.2,
        "confidence_score": 0.95,
    }]
    return rows, {"old": 100, "new": 100}, recurrence


def _row(execution: str, index: int, pattern: str, fault: str) -> dict:
    return {
        "execution_id": execution,
        "source_record_id": f"R{index}",
        "pattern_id": pattern,
        "fault_type": fault,
        "pattern_confidence": 0.96,
        "classification_confidence": 0.94,
        "x": index % 10,
        "y": index // 10,
        "lot_id": "LOT1",
        "wafer_id": "W1",
    }


class FaFr006StatisticalTests(unittest.TestCase):
    def test_phi_coefficient_significance_and_explainability(self) -> None:
        rows, counts, recurrence = _sources()
        result = ProductionCorrelationEngine(_config()).analyze(
            observations=rows,
            source_record_counts=counts,
            recurrences=recurrence,
            failure_rates={"P1": 30.0},
            analysis_id="analysis-1",
            current_execution_id="new",
        )
        correlation = result["correlations"][0]
        self.assertAlmostEqual(correlation["correlation_coefficient"], 0.52381, places=5)
        self.assertLess(correlation["p_value"], 0.05)
        self.assertEqual(correlation["correlation_strength"], "strong")
        self.assertTrue(correlation["recommendations"])
        self.assertEqual(result["matrix"]["patterns"], ["P1"])
        self.assertTrue(result["relationship_graph"]["edges"])

    def test_results_are_input_order_deterministic(self) -> None:
        rows, counts, recurrence = _sources()
        shuffled = list(rows)
        random.Random(42).shuffle(shuffled)
        kwargs = dict(
            source_record_counts=counts,
            recurrences=recurrence,
            failure_rates={"P1": 30.0},
            analysis_id="analysis-2",
            current_execution_id="new",
        )
        first = ProductionCorrelationEngine(_config()).analyze(observations=rows, **kwargs)
        second = ProductionCorrelationEngine(_config()).analyze(observations=shuffled, **kwargs)
        self.assertEqual(first, second)

    def test_invalid_threshold_filter_and_ground_truth_benchmarks(self) -> None:
        rows, counts, recurrence = _sources()
        result = ProductionCorrelationEngine(_config(coefficient_threshold=0.9)).analyze(
            observations=rows,
            source_record_counts=counts,
            recurrences=recurrence,
            failure_rates={"P1": 30.0},
            analysis_id="analysis-3",
            current_execution_id="new",
        )
        self.assertFalse(result["correlations"])
        metrics = correlation_benchmarks(
            [{"pattern_id": "P1", "fault_type": "F1"}, {"pattern_id": "N1", "fault_type": "F2"}],
            ["P1|F1"],
            ["N1|F2", "N2|F2"],
        )
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["false_positive_rate"], 0.5)

    def test_100k_observation_throughput(self) -> None:
        rows = [_row("old" if index < 50_000 else "new", index % 50_000, "P1", "F1") for index in range(100_000)]
        started = time.perf_counter()
        ProductionCorrelationEngine(_config(coefficient_threshold=0.0, significance_level=1.0)).analyze(
            observations=rows,
            source_record_counts={"old": 100_000, "new": 100_000},
            recurrences=[{"recurrence_id": "r", "pattern_id": "P1", "fault_type": "F1", "recurrence_frequency": 0.5, "confidence_score": 1.0}],
            failure_rates={"P1": 50.0},
            analysis_id="performance",
            current_execution_id="new",
        )
        self.assertLess(time.perf_counter() - started, 20.0)


import tests.pg_env  # noqa: E402,F401
from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FaFr006ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _prepare(self, index: int) -> str:
        content = (FIXTURES / "csv_die_results_sample.csv").read_text(encoding="utf-8")
        content = content.replace("LOT_SYN_002", f"LOT_FR006_{time.time_ns()}_{index}")
        uploaded = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": (f"correlation-{index}.csv", content.encode(), "text/csv")},
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        upload_id = uploaded.json()["upload"]["id"]
        for path, payload in (
            ("/api/v1/patterns/detect", {"upload_id": upload_id, "incremental": False}),
            ("/api/v1/failure-rate/compute", {"upload_id": upload_id, "window_size": 5}),
            ("/api/v1/classification/analyze", {"upload_id": upload_id, "enable_ml": False, "enable_llm": False}),
        ):
            response = self.client.post(path, json=payload)
            self.assertEqual(response.status_code, 200, response.text)
        return upload_id

    def test_full_upstream_gate_analysis_queries_and_openapi(self) -> None:
        self._prepare(1)
        current = self._prepare(2)
        recurrence = self.client.post("/api/v1/recurrence/analyze", json={"upload_id": current})
        self.assertEqual(recurrence.status_code, 200, recurrence.text)
        analyzed = self.client.post(
            "/api/v1/correlation/analyze",
            json={"upload_id": current, "recurrence_analysis_id": recurrence.json()["execution_id"]},
        )
        self.assertEqual(analyzed.status_code, 200, analyzed.text)
        body = analyzed.json()
        self.assertEqual(body["status"], "completed")
        self.assertIn("matrix", body)
        self.assertIn("relationship_graph", body)
        for endpoint, key in (
            ("/api/v1/correlation", "correlations"),
            ("/api/v1/correlation/history", "history"),
            ("/api/v1/correlation/trends", "trends"),
        ):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn(key, response.json())
        self.assertEqual(self.client.get("/api/v1/correlation/statistics").status_code, 200)
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/correlation/analyze",
            "/api/v1/correlation",
            "/api/v1/correlation/{correlation_id}",
            "/api/v1/correlation/history",
            "/api/v1/correlation/statistics",
            "/api/v1/correlation/trends",
        ):
            self.assertIn(path, paths)

    def test_validation_rbac_and_upstream_gate(self) -> None:
        self.assertEqual(self.client.post("/api/v1/correlation/analyze", json={}).status_code, 422)
        self.assertEqual(self.client.get("/api/v1/correlation", headers={"X-Role": "viewer"}).status_code, 403)
        content = (FIXTURES / "csv_die_results_sample.csv").read_bytes()
        upload = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("gate-correlation.csv", content, "text/csv")},
        )
        rejected = self.client.post(
            "/api/v1/correlation/analyze",
            json={"upload_id": upload.json()["upload"]["id"]},
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)


if __name__ == "__main__":
    unittest.main()
