"""FA-FR-008 wafer yield, radial, determinism, benchmark, and API acceptance tests."""

from __future__ import annotations

import hashlib
import random
import time
import unittest
from pathlib import Path

from backend.wafer_analysis.production_engine import (
    ProductionWaferAnalysisEngine,
    WaferAnalysisConfig,
)
from backend.wafer_analysis.production_service import (
    validate_wafer_source,
    wafer_benchmarks,
)


def _config(**updates: object) -> WaferAnalysisConfig:
    values = {
        "version": "test-v1",
        "algorithm": "deterministic_grid_aggregate",
        "hotspot_density": 0.15,
        "hotspot_min_dies": 3,
        "grid_cell_size": 1.0,
        "edge_radius_fraction": 0.67,
        "center_radius_fraction": 0.34,
        "radial_bins": 8,
        "min_confidence": 0.5,
        "health_critical": 0.35,
        "health_high": 0.55,
        "health_medium": 0.75,
        "trend_delta": 0.05,
        "yield_outlier_delta": 10.0,
        "min_sample_size": 1,
        "batch_size": 10_000,
        "max_grid_export": 500,
        "compatible_formula_prefix": "failure-rate-v1",
        "require_same_tenant": True,
        "require_product_overlap": True,
        "require_test_stage_overlap": True,
    }
    values.update(updates)
    return WaferAnalysisConfig(**values)


def _die(
    *,
    die_id: str,
    x: float,
    y: float,
    lot_id: str = "LOT1",
    wafer_id: str = "W1",
    failing: bool = True,
) -> dict:
    return {
        "die_result_id": f"dr-{die_id}",
        "lot_id": lot_id,
        "wafer_id": wafer_id,
        "die_id": die_id,
        "canonical_die_key": hashlib.sha256(
            f"{lot_id.lower()}|{wafer_id.lower()}|{die_id.lower()}".encode()
        ).hexdigest(),
        "x": x,
        "y": y,
        "failure_count": 1 if failing else 0,
        "failure_density": 1.0 if failing else 0.0,
        "is_failing": failing,
        "health_score": 0.4 if failing else 1.0,
        "severity": "high" if failing else "low",
        "confidence_score": 0.9,
    }


def _fixture() -> tuple[list[dict], list[dict], dict[str, float]]:
    dies = [
        _die(die_id="D1", x=1.0, y=1.0),
        _die(die_id="D2", x=2.0, y=1.0),
        _die(die_id="D3", x=1.0, y=2.0),
        _die(die_id="D4", x=2.0, y=2.0),
        _die(die_id="D5", x=10.0, y=10.0),
        _die(die_id="D6", x=1.0, y=1.0, wafer_id="W2", failing=False),
        _die(die_id="D7", x=2.0, y=2.0, wafer_id="W2", failing=False),
    ]
    die_hotspots = [
        {
            "hotspot_id": "hs1",
            "lot_id": "LOT1",
            "wafer_id": "W1",
            "center_x": 1.5,
            "center_y": 1.5,
            "radius": 1.0,
            "die_count": 4,
            "failure_count": 4,
            "density": 0.8,
            "severity": "high",
            "confidence_score": 0.9,
            "member_die_ids": ["D1", "D2", "D3", "D4"],
        }
    ]
    historical = {
        hashlib.sha256(b"lot1|w1").hexdigest(): 90.0,
    }
    return dies, die_hotspots, historical


class FaFr008EngineTests(unittest.TestCase):
    def test_aggregates_every_wafer_with_yield_radial_and_recommendations(self) -> None:
        dies, die_hotspots, historical = _fixture()
        result = ProductionWaferAnalysisEngine(_config()).analyze(
            dies=dies,
            die_hotspots=die_hotspots,
            historical_wafer_yields=historical,
            analysis_id="analysis-1",
            die_analysis_id="die-1",
        )
        self.assertEqual(result["statistics"]["total_wafers"], 2)
        by_wafer = {item["wafer_id"]: item for item in result["wafers"]}
        self.assertEqual(by_wafer["W1"]["total_dies"], 5)
        self.assertEqual(by_wafer["W1"]["failing_dies"], 5)
        self.assertEqual(by_wafer["W2"]["yield_pct"], 100.0)
        self.assertIn("profile", by_wafer["W1"]["radial_distribution"])
        self.assertTrue(by_wafer["W1"]["recommendations"])
        self.assertIn(by_wafer["W1"]["severity"], {"critical", "high", "medium", "low"})
        self.assertIn("lot_comparison", by_wafer["W1"])

    def test_hotspot_detection_is_deterministic(self) -> None:
        dies, die_hotspots, historical = _fixture()
        kwargs = dict(
            die_hotspots=die_hotspots,
            historical_wafer_yields=historical,
            analysis_id="analysis-2",
            die_analysis_id="die-2",
        )
        engine = ProductionWaferAnalysisEngine(
            _config(hotspot_density=0.1, hotspot_min_dies=2)
        )
        first = engine.analyze(dies=dies, **kwargs)
        shuffled = list(dies)
        random.Random(11).shuffle(shuffled)
        second = engine.analyze(dies=shuffled, **kwargs)
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first["hotspots"]), 1)

    def test_deterministic_wafer_identity(self) -> None:
        dies, die_hotspots, historical = _fixture()
        result = ProductionWaferAnalysisEngine(_config()).analyze(
            dies=dies,
            die_hotspots=die_hotspots,
            historical_wafer_yields=historical,
            analysis_id="analysis-ids",
            die_analysis_id="die-ids",
        )
        keys = {item["canonical_wafer_key"] for item in result["wafers"]}
        self.assertEqual(len(keys), len(result["wafers"]))
        ids = {item["wafer_result_id"] for item in result["wafers"]}
        self.assertEqual(len(ids), len(result["wafers"]))

    def test_missing_wafer_id_validation(self) -> None:
        dies, die_hotspots, _historical = _fixture()
        bad = dict(dies[0])
        bad["wafer_id"] = ""
        source = {
            "dies": dies + [bad],
            "die_hotspots": die_hotspots,
            "die_audit": type("A", (), {"analysis_id": "die-1"})(),
            "warnings": [],
        }
        issues, _warnings = validate_wafer_source(source)
        self.assertIn("MISSING_WAFER_ID", {item["code"] for item in issues})

    def test_duplicate_record_validation(self) -> None:
        dies, die_hotspots, _historical = _fixture()
        duplicate = dict(dies[0])
        source = {
            "dies": dies + [duplicate],
            "die_hotspots": die_hotspots,
            "die_audit": type("A", (), {"analysis_id": "die-1"})(),
            "warnings": [],
        }
        issues, _warnings = validate_wafer_source(source)
        self.assertIn("DUPLICATE_RECORDS", {item["code"] for item in issues})

    def test_coordinate_conflict_validation(self) -> None:
        dies, die_hotspots, _historical = _fixture()
        conflict = dict(dies[0])
        conflict["x"] = 99.0
        conflict["die_result_id"] = "dr-conflict"
        source = {
            "dies": dies + [conflict],
            "die_hotspots": die_hotspots,
            "die_audit": type("A", (), {"analysis_id": "die-1"})(),
            "warnings": [],
        }
        issues, _warnings = validate_wafer_source(source)
        self.assertIn("COORDINATE_CONFLICT", {item["code"] for item in issues})

    def test_yield_metrics_and_trend(self) -> None:
        dies, die_hotspots, historical = _fixture()
        result = ProductionWaferAnalysisEngine(_config()).analyze(
            dies=dies,
            die_hotspots=die_hotspots,
            historical_wafer_yields=historical,
            analysis_id="analysis-yield",
            die_analysis_id="die-yield",
        )
        metrics = {item["wafer_id"]: item for item in result["yield_metrics"]}
        self.assertIn("W1", metrics)
        self.assertIn(metrics["W1"]["trend_status"], {"decreasing", "stable", "increasing", "unknown"})

    def test_ground_truth_benchmarks(self) -> None:
        metrics = wafer_benchmarks(
            [
                {"wafer_id": "W1", "failing_dies": 3},
                {"wafer_id": "W2", "failing_dies": 0},
            ],
            ["W1"],
            ["W2"],
        )
        self.assertEqual(metrics["precision"], 1.0)
        self.assertEqual(metrics["recall"], 1.0)

    def test_100k_die_aggregation_throughput(self) -> None:
        dies = [
            _die(
                die_id=f"D{index}",
                x=float(index % 100),
                y=float((index // 100) % 100),
                wafer_id=f"W{index % 50}",
                lot_id=f"LOT{index % 5}",
            )
            for index in range(100_000)
        ]
        started = time.perf_counter()
        ProductionWaferAnalysisEngine(
            _config(hotspot_density=0.01, hotspot_min_dies=2)
        ).analyze(
            dies=dies,
            die_hotspots=[],
            historical_wafer_yields={},
            analysis_id="performance",
            die_analysis_id="die-performance",
        )
        self.assertLess(time.perf_counter() - started, 30.0)


import tests.pg_env  # noqa: E402,F401
from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FaFr008ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _prepare(self, index: int) -> str:
        content = (FIXTURES / "csv_die_results_sample.csv").read_text(encoding="utf-8")
        content = content.replace("LOT_SYN_002", f"LOT_FR008_{time.time_ns()}_{index}")
        uploaded = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": (f"wafer-{index}.csv", content.encode(), "text/csv")},
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

    def _run_die_analysis(self, upload_id: str) -> dict:
        recurrence = self.client.post(
            "/api/v1/recurrence/analyze", json={"upload_id": upload_id}
        )
        self.assertEqual(recurrence.status_code, 200, recurrence.text)
        correlation = self.client.post(
            "/api/v1/correlation/analyze",
            json={
                "upload_id": upload_id,
                "recurrence_analysis_id": recurrence.json()["execution_id"],
            },
        )
        self.assertEqual(correlation.status_code, 200, correlation.text)
        analyzed = self.client.post(
            "/api/v1/die-analysis/analyze",
            json={
                "upload_id": upload_id,
                "recurrence_analysis_id": recurrence.json()["execution_id"],
                "correlation_analysis_id": correlation.json()["execution_id"],
            },
        )
        self.assertEqual(analyzed.status_code, 200, analyzed.text)
        return analyzed.json()

    def test_full_upstream_gate_analysis_queries_and_openapi(self) -> None:
        self._prepare(1)
        current = self._prepare(2)
        die_body = self._run_die_analysis(current)
        analyzed = self.client.post(
            "/api/v1/wafer-analysis/analyze",
            json={
                "upload_id": current,
                "die_analysis_id": die_body["execution_id"],
            },
        )
        self.assertEqual(analyzed.status_code, 200, analyzed.text)
        body = analyzed.json()
        self.assertEqual(body["status"], "completed")
        self.assertIn("wafers", body)
        self.assertIn("hotspots", body)
        self.assertIn("yield_metrics", body)
        self.assertIn("statistics", body)
        for endpoint, key in (
            ("/api/v1/wafer-analysis", "wafers"),
            ("/api/v1/wafer-analysis/hotspots", "hotspots"),
            ("/api/v1/wafer-analysis/yield", "yield_metrics"),
        ):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn(key, response.json())
        self.assertEqual(
            self.client.get("/api/v1/wafer-analysis/statistics").status_code, 200
        )
        if body["wafers"]:
            detail = self.client.get(
                f"/api/v1/wafer-analysis/{body['wafers'][0]['wafer_result_id']}"
            )
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertIn("traceability", detail.json())
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/wafer-analysis/analyze",
            "/api/v1/wafer-analysis",
            "/api/v1/wafer-analysis/{wafer_result_id}",
            "/api/v1/wafer-analysis/hotspots",
            "/api/v1/wafer-analysis/statistics",
            "/api/v1/wafer-analysis/yield",
            "/api/v1/wafer/analyze",
        ):
            self.assertIn(path, paths)

    def test_validation_rbac_and_upstream_gate(self) -> None:
        self.assertEqual(
            self.client.post("/api/v1/wafer-analysis/analyze", json={}).status_code, 422
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/wafer-analysis", headers={"X-Role": "viewer"}
            ).status_code,
            403,
        )
        content = (FIXTURES / "csv_die_results_sample.csv").read_bytes()
        upload = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("gate-wafer.csv", content, "text/csv")},
        )
        rejected = self.client.post(
            "/api/v1/wafer-analysis/analyze",
            json={"upload_id": upload.json()["upload"]["id"]},
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)


if __name__ == "__main__":
    unittest.main()
