"""FA-FR-007 statistical, spatial, contract, benchmark, and API acceptance tests."""

from __future__ import annotations

import random
import time
import unittest
from pathlib import Path

from backend.die_analysis.production_engine import (
    DieAnalysisConfig,
    ProductionDieAnalysisEngine,
)
from backend.die_analysis.production_service import die_benchmarks, validate_die_source


def _config(**updates: object) -> DieAnalysisConfig:
    values = {
        "version": "test-v1",
        "algorithm": "grid_union_find",
        "hotspot_density": 0.15,
        "hotspot_min_dies": 3,
        "cluster_eps": 2.5,
        "cluster_min_samples": 3,
        "grid_cell_size": 1.0,
        "neighbor_radius": 1.5,
        "isolated_neighbor_max": 0,
        "min_confidence": 0.5,
        "health_critical": 0.35,
        "health_high": 0.55,
        "health_medium": 0.75,
        "trend_delta": 0.05,
        "min_sample_size": 1,
        "batch_size": 10_000,
        "max_coordinate_export": 500,
        "compatible_formula_prefix": "failure-rate-v1",
        "require_same_tenant": True,
        "require_product_overlap": True,
        "require_test_stage_overlap": True,
    }
    values.update(updates)
    return DieAnalysisConfig(**values)


def _row(
    *,
    execution: str,
    index: int,
    die_id: str,
    x: float,
    y: float,
    pattern: str = "P1",
    fault: str = "Scan Chain Failure",
    lot_id: str = "LOT1",
    wafer_id: str = "W1",
) -> dict:
    return {
        "execution_id": execution,
        "occurrence_id": f"O-{execution}-{index}",
        "source_record_id": f"R-{execution}-{index}",
        "detected_pattern_id": f"DP-{pattern}",
        "pattern_id": pattern,
        "fault_type": fault,
        "pattern_confidence": 0.96,
        "classification_confidence": 0.94,
        "lot_id": lot_id,
        "wafer_id": wafer_id,
        "die_id": die_id,
        "x": x,
        "y": y,
    }


def _fixture() -> tuple[list[dict], dict[str, int], list[dict], list[dict]]:
    rows: list[dict] = []
    # Current clustered failures around (1,1)/(2,1)/(1,2)/(2,2)
    for index, (die_id, x, y) in enumerate(
        [
            ("D1", 1.0, 1.0),
            ("D2", 2.0, 1.0),
            ("D3", 1.0, 2.0),
            ("D4", 2.0, 2.0),
            ("D5", 10.0, 10.0),  # isolated
        ]
    ):
        rows.append(
            _row(execution="new", index=index, die_id=die_id, x=x, y=y)
        )
    # Historical lower density for D1..D4, none for D5
    for index, (die_id, x, y) in enumerate(
        [
            ("D1", 1.0, 1.0),
            ("D2", 2.0, 1.0),
            ("D3", 1.0, 2.0),
            ("D4", 2.0, 2.0),
        ]
    ):
        rows.append(
            _row(execution="old", index=index, die_id=die_id, x=x, y=y)
        )
    correlations = [
        {
            "correlation_id": "c1",
            "pattern_id": "P1",
            "fault_type": "Scan Chain Failure",
            "confidence_score": 0.92,
            "severity": "high",
            "trend_status": "increasing",
        }
    ]
    recurrences = [
        {
            "recurrence_id": "r1",
            "pattern_id": "P1",
            "fault_type": "Scan Chain Failure",
            "confidence_score": 0.9,
            "recurrence_frequency": 0.2,
        }
    ]
    return rows, {"old": 40, "new": 40}, correlations, recurrences


class FaFr007EngineTests(unittest.TestCase):
    def test_aggregates_every_die_with_health_neighbors_and_recommendations(self) -> None:
        rows, counts, correlations, recurrences = _fixture()
        result = ProductionDieAnalysisEngine(_config()).analyze(
            observations=rows,
            source_record_counts=counts,
            correlations=correlations,
            recurrences=recurrences,
            failure_rates={"P1": 25.0},
            analysis_id="analysis-1",
            current_execution_id="new",
        )
        self.assertEqual(result["statistics"]["total_dies"], 5)
        self.assertEqual(result["statistics"]["failing_dies"], 5)
        self.assertGreaterEqual(result["statistics"]["isolated_failures"], 1)
        by_die = {item["die_id"]: item for item in result["dies"]}
        self.assertEqual(by_die["D5"]["is_isolated"], True)
        self.assertGreaterEqual(by_die["D1"]["neighbor_failure_count"], 1)
        self.assertTrue(by_die["D1"]["recommendations"])
        self.assertIn(by_die["D1"]["severity"], {"critical", "high", "medium", "low"})
        self.assertTrue(0.0 <= by_die["D1"]["health_score"] <= 1.0)
        self.assertIn("lot_comparison", by_die["D1"])
        self.assertIn("wafer_comparison", by_die["D1"])

    def test_hotspot_and_cluster_detection_are_deterministic(self) -> None:
        rows, counts, correlations, recurrences = _fixture()
        kwargs = dict(
            source_record_counts=counts,
            correlations=correlations,
            recurrences=recurrences,
            failure_rates={"P1": 25.0},
            analysis_id="analysis-2",
            current_execution_id="new",
        )
        engine = ProductionDieAnalysisEngine(
            _config(hotspot_density=0.1, hotspot_min_dies=3, cluster_min_samples=3)
        )
        first = engine.analyze(observations=rows, **kwargs)
        shuffled = list(rows)
        random.Random(7).shuffle(shuffled)
        second = engine.analyze(observations=shuffled, **kwargs)
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first["clusters"]), 1)
        self.assertGreaterEqual(len(first["hotspots"]), 1)

    def test_coordinate_conflict_validation(self) -> None:
        rows, counts, correlations, recurrences = _fixture()
        conflict = dict(rows[0])
        conflict["x"] = 99.0
        conflict["occurrence_id"] = "conflict"
        conflict["source_record_id"] = "conflict-record"
        source = {
            "observations": rows + [conflict],
            "correlations": correlations,
            "detection": type("D", (), {"analysis_id": "new"})(),
            "warnings": [],
        }
        issues, _warnings = validate_die_source(source)
        codes = {item["code"] for item in issues}
        self.assertIn("COORDINATE_CONFLICT", codes)

    def test_duplicate_record_validation(self) -> None:
        rows, _counts, correlations, _recurrences = _fixture()
        duplicate = dict(rows[0])
        source = {
            "observations": rows + [duplicate],
            "correlations": correlations,
            "detection": type("D", (), {"analysis_id": "new"})(),
            "warnings": [],
        }
        issues, _warnings = validate_die_source(source)
        self.assertIn("DUPLICATE_RECORDS", {item["code"] for item in issues})

    def test_deterministic_die_identity(self) -> None:
        rows, counts, correlations, recurrences = _fixture()
        result = ProductionDieAnalysisEngine(_config()).analyze(
            observations=rows,
            source_record_counts=counts,
            correlations=correlations,
            recurrences=recurrences,
            failure_rates={"P1": 25.0},
            analysis_id="analysis-ids",
            current_execution_id="new",
        )
        keys = {item["canonical_die_key"] for item in result["dies"]}
        self.assertEqual(len(keys), len(result["dies"]))
        ids = {item["die_result_id"] for item in result["dies"]}
        self.assertEqual(len(ids), len(result["dies"]))

    def test_ground_truth_benchmarks(self) -> None:
        metrics = die_benchmarks(
            [
                {"die_id": "D1", "is_failing": True},
                {"die_id": "D2", "is_failing": True},
                {"die_id": "D3", "is_failing": False},
            ],
            ["D1"],
            ["D2", "D3"],
        )
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["false_positive_rate"], 0.5)

    def test_100k_observation_throughput(self) -> None:
        rows = [
            _row(
                execution="old" if index < 50_000 else "new",
                index=index % 50_000,
                die_id=f"D{index % 5_000}",
                x=float(index % 100),
                y=float((index // 100) % 100),
            )
            for index in range(100_000)
        ]
        started = time.perf_counter()
        ProductionDieAnalysisEngine(
            _config(hotspot_density=0.01, hotspot_min_dies=2, cluster_min_samples=2)
        ).analyze(
            observations=rows,
            source_record_counts={"old": 100_000, "new": 100_000},
            correlations=[
                {
                    "correlation_id": "c",
                    "pattern_id": "P1",
                    "fault_type": "Scan Chain Failure",
                    "confidence_score": 1.0,
                }
            ],
            recurrences=[
                {
                    "recurrence_id": "r",
                    "pattern_id": "P1",
                    "fault_type": "Scan Chain Failure",
                    "confidence_score": 1.0,
                    "recurrence_frequency": 0.5,
                }
            ],
            failure_rates={"P1": 50.0},
            analysis_id="performance",
            current_execution_id="new",
        )
        self.assertLess(time.perf_counter() - started, 25.0)


import tests.pg_env  # noqa: E402,F401
from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FaFr007ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _prepare(self, index: int) -> str:
        content = (FIXTURES / "csv_die_results_sample.csv").read_text(encoding="utf-8")
        content = content.replace("LOT_SYN_002", f"LOT_FR007_{time.time_ns()}_{index}")
        uploaded = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": (f"die-{index}.csv", content.encode(), "text/csv")},
        )
        self.assertEqual(uploaded.status_code, 200, uploaded.text)
        upload_id = uploaded.json()["upload"]["id"]
        for path, payload in (
            ("/api/v1/patterns/detect", {"upload_id": upload_id, "incremental": False}),
            ("/api/v1/failure-rate/compute", {"upload_id": upload_id, "window_size": 5}),
            (
                "/api/v1/classification/analyze",
                {"upload_id": upload_id, "enable_ml": False, "enable_llm": False},
            ),
        ):
            response = self.client.post(path, json=payload)
            self.assertEqual(response.status_code, 200, response.text)
        return upload_id

    def test_full_upstream_gate_analysis_queries_and_openapi(self) -> None:
        self._prepare(1)
        current = self._prepare(2)
        recurrence = self.client.post(
            "/api/v1/recurrence/analyze", json={"upload_id": current}
        )
        self.assertEqual(recurrence.status_code, 200, recurrence.text)
        correlation = self.client.post(
            "/api/v1/correlation/analyze",
            json={
                "upload_id": current,
                "recurrence_analysis_id": recurrence.json()["execution_id"],
            },
        )
        self.assertEqual(correlation.status_code, 200, correlation.text)
        analyzed = self.client.post(
            "/api/v1/die-analysis/analyze",
            json={
                "upload_id": current,
                "recurrence_analysis_id": recurrence.json()["execution_id"],
                "correlation_analysis_id": correlation.json()["execution_id"],
            },
        )
        self.assertEqual(analyzed.status_code, 200, analyzed.text)
        body = analyzed.json()
        self.assertEqual(body["status"], "completed")
        self.assertIn("dies", body)
        self.assertIn("hotspots", body)
        self.assertIn("clusters", body)
        self.assertIn("statistics", body)
        for endpoint, key in (
            ("/api/v1/die-analysis", "dies"),
            ("/api/v1/die-analysis/hotspots", "hotspots"),
            ("/api/v1/die-analysis/clusters", "clusters"),
        ):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn(key, response.json())
        self.assertEqual(
            self.client.get("/api/v1/die-analysis/statistics").status_code, 200
        )
        if body["dies"]:
            detail = self.client.get(
                f"/api/v1/die-analysis/{body['dies'][0]['die_result_id']}"
            )
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertIn("traceability", detail.json())
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/die-analysis/analyze",
            "/api/v1/die-analysis",
            "/api/v1/die-analysis/{die_result_id}",
            "/api/v1/die-analysis/hotspots",
            "/api/v1/die-analysis/clusters",
            "/api/v1/die-analysis/statistics",
            "/api/v1/die/analyze",
        ):
            self.assertIn(path, paths)

    def test_validation_rbac_and_upstream_gate(self) -> None:
        self.assertEqual(
            self.client.post("/api/v1/die-analysis/analyze", json={}).status_code, 422
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/die-analysis", headers={"X-Role": "viewer"}
            ).status_code,
            403,
        )
        content = (FIXTURES / "csv_die_results_sample.csv").read_bytes()
        upload = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("gate-die.csv", content, "text/csv")},
        )
        rejected = self.client.post(
            "/api/v1/die-analysis/analyze",
            json={"upload_id": upload.json()["upload"]["id"]},
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)


if __name__ == "__main__":
    unittest.main()
