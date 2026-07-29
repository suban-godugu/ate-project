"""FA-FR-009 fault prediction determinism, benchmark, gate, and API acceptance tests."""

from __future__ import annotations

import hashlib
import random
import time
import unittest
from pathlib import Path

from backend.root_cause.production_engine import (
    FaultPredictionConfig,
    ProductionFaultPredictionEngine,
)
from backend.root_cause.production_service import (
    prediction_benchmarks,
    validate_prediction_source,
)


def _config(**updates: object) -> FaultPredictionConfig:
    values = {
        "version": "test-v1",
        "algorithm": "rule_based_explainable_scoring",
        "model_version": "rule-test",
        "model_type": "rule_based",
        "top_k_alternatives": 5,
        "min_confidence": 0.35,
        "high_confidence": 0.75,
        "min_probability": 0.05,
        "recurrence_boost": 0.12,
        "correlation_boost": 0.15,
        "failure_rate_boost": 0.10,
        "die_severity_boost": 0.08,
        "wafer_health_penalty": 0.06,
        "min_sample_size": 1,
        "weight_correlation": 0.30,
        "weight_recurrence": 0.20,
        "weight_classification": 0.20,
        "weight_failure_rate": 0.15,
        "weight_die": 0.10,
        "weight_wafer": 0.05,
        "batch_size": 10_000,
        "max_patterns_per_batch": 50_000,
        "compatible_formula_prefix": "failure-rate-v1",
        "require_same_tenant": True,
        "require_product_overlap": True,
        "require_test_stage_overlap": True,
        "feedback_enabled": True,
        "default_learning_weight": 1.0,
    }
    values.update(updates)
    return FaultPredictionConfig(**values)


def _fixture() -> dict:
    patterns = [
        {"pattern_id": "PAT_TIMING_01", "fault_type": "TIMING_VIOLATION"},
        {"pattern_id": "PAT_POWER_02", "fault_type": "POWER_IR_DROP_FAULT"},
    ]
    correlations = [
        {
            "pattern_id": "PAT_TIMING_01",
            "fault_type": "TIMING_VIOLATION",
            "correlation_coefficient": 0.82,
            "correlation_strength": "strong",
        },
        {
            "pattern_id": "PAT_POWER_02",
            "fault_type": "POWER_IR_DROP_FAULT",
            "correlation_coefficient": 0.71,
            "correlation_strength": "moderate",
        },
    ]
    recurrences = [
        {
            "pattern_id": "PAT_TIMING_01",
            "fault_type": "TIMING_VIOLATION",
            "recurrence_percentage": 45.0,
            "recurrence_count": 3,
        }
    ]
    classifications = [
        {
            "pattern_id": "PAT_TIMING_01",
            "fault_type": "TIMING_VIOLATION",
            "confidence": 0.8,
        }
    ]
    failure_rates = {"PAT_TIMING_01": 12.5, "PAT_POWER_02": 8.0}
    dies = [
        {
            "lot_id": "LOT1",
            "wafer_id": "W1",
            "is_failing": True,
            "health_score": 0.4,
        }
    ]
    wafers = [
        {
            "lot_id": "LOT1",
            "wafer_id": "W1",
            "health_score": 0.5,
            "severity": "high",
        }
    ]
    return {
        "patterns": patterns,
        "correlations": correlations,
        "recurrences": recurrences,
        "classifications": classifications,
        "failure_rates": failure_rates,
        "dies": dies,
        "wafers": wafers,
        "feedback_signals": [],
    }


class FaFr009EngineTests(unittest.TestCase):
    def test_ranked_predictions_with_explanations_and_steps(self) -> None:
        data = _fixture()
        result = ProductionFaultPredictionEngine(_config()).predict(
            patterns=data["patterns"],
            correlations=data["correlations"],
            recurrences=data["recurrences"],
            classifications=data["classifications"],
            failure_rates=data["failure_rates"],
            dies=data["dies"],
            wafers=data["wafers"],
            feedback_signals=[],
            execution_id="exec-1",
            wafer_analysis_id="wafer-1",
        )
        self.assertEqual(result["statistics"]["total_predictions"], 2)
        top = result["predictions"][0]
        self.assertIn("predicted_fault_type", top)
        self.assertTrue(top["alternative_fault_types"])
        self.assertTrue(top["supporting_evidence"])
        self.assertIn("Probable fault type", top["engineering_explanation"])
        self.assertNotIn("definitive root cause", top["engineering_explanation"].lower())
        self.assertTrue(top["investigation_steps"])

    def test_deterministic_prediction_identity(self) -> None:
        data = _fixture()
        kwargs = dict(
            patterns=data["patterns"],
            correlations=data["correlations"],
            recurrences=data["recurrences"],
            classifications=data["classifications"],
            failure_rates=data["failure_rates"],
            dies=data["dies"],
            wafers=data["wafers"],
            feedback_signals=[],
            execution_id="exec-deterministic",
            wafer_analysis_id="wafer-deterministic",
        )
        first = ProductionFaultPredictionEngine(_config()).predict(**kwargs)
        shuffled = list(data["patterns"])
        random.Random(17).shuffle(shuffled)
        second = ProductionFaultPredictionEngine(_config()).predict(
            **{**kwargs, "patterns": shuffled}
        )
        self.assertEqual(
            {item["prediction_id"] for item in first["predictions"]},
            {item["prediction_id"] for item in second["predictions"]},
        )
        for item in first["predictions"]:
            expected = hashlib.sha256(item["pattern_id"].lower().encode()).hexdigest()
            self.assertEqual(item["canonical_prediction_key"], expected)

    def test_missing_pattern_id_validation(self) -> None:
        source = {
            "patterns": [{"pattern_id": ""}],
            "correlations": [],
            "wafers": [{"health_score": 1.0}],
            "warnings": [],
        }
        issues, _warnings = validate_prediction_source(source, _config())
        self.assertIn("MISSING_PATTERN_ID", {item["code"] for item in issues})

    def test_duplicate_pattern_validation(self) -> None:
        source = {
            "patterns": [
                {"pattern_id": "P1"},
                {"pattern_id": "P1"},
            ],
            "correlations": [],
            "wafers": [{"health_score": 1.0}],
            "warnings": [],
        }
        issues, _warnings = validate_prediction_source(source, _config())
        self.assertIn("DUPLICATE_PATTERN_ID", {item["code"] for item in issues})

    def test_invalid_threshold_validation(self) -> None:
        source = {
            "patterns": [{"pattern_id": "P1"}],
            "correlations": [{"pattern_id": "P1"}],
            "wafers": [{"health_score": 1.0}],
            "warnings": [],
        }
        issues, _warnings = validate_prediction_source(
            source, _config(min_confidence=1.5)
        )
        self.assertIn("INVALID_THRESHOLD", {item["code"] for item in issues})

    def test_top_k_and_benchmark_metrics(self) -> None:
        data = _fixture()
        result = ProductionFaultPredictionEngine(_config()).predict(
            patterns=data["patterns"],
            correlations=data["correlations"],
            recurrences=data["recurrences"],
            classifications=data["classifications"],
            failure_rates=data["failure_rates"],
            dies=data["dies"],
            wafers=data["wafers"],
            feedback_signals=[],
            execution_id="exec-bench",
            wafer_analysis_id="wafer-bench",
        )
        metrics = prediction_benchmarks(
            result["predictions"],
            {"PAT_TIMING_01": "TIMING_VIOLATION"},
        )
        self.assertTrue(metrics["ground_truth_available"])
        self.assertEqual(metrics["top1_accuracy"], 1.0)

    def test_100k_pattern_throughput(self) -> None:
        patterns = [
            {"pattern_id": f"PAT_{index:06d}", "fault_type": "UNKNOWN"}
            for index in range(1000)
        ]
        correlations = [
            {
                "pattern_id": f"PAT_{index:06d}",
                "fault_type": "TIMING_VIOLATION" if index % 2 == 0 else "LEAKAGE_IDDQ",
                "correlation_coefficient": 0.5,
                "correlation_strength": "moderate",
            }
            for index in range(1000)
        ]
        started = time.perf_counter()
        ProductionFaultPredictionEngine(_config()).predict(
            patterns=patterns,
            correlations=correlations,
            recurrences=[],
            classifications=[],
            failure_rates={},
            dies=[],
            wafers=[{"health_score": 0.8}],
            feedback_signals=[],
            execution_id="perf",
            wafer_analysis_id="wafer-perf",
        )
        self.assertLess(time.perf_counter() - started, 10.0)


import tests.pg_env  # noqa: E402,F401
from fastapi.testclient import TestClient  # noqa: E402
from backend.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class FaFr009ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.__exit__(None, None, None)

    def _prepare(self, index: int) -> str:
        content = (FIXTURES / "csv_die_results_sample.csv").read_text(encoding="utf-8")
        content = content.replace("LOT_SYN_002", f"LOT_FR009_{time.time_ns()}_{index}")
        uploaded = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": (f"fault-{index}.csv", content.encode(), "text/csv")},
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

    def _run_upstream(self, upload_id: str) -> dict:
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
        die = self.client.post(
            "/api/v1/die-analysis/analyze",
            json={
                "upload_id": upload_id,
                "recurrence_analysis_id": recurrence.json()["execution_id"],
                "correlation_analysis_id": correlation.json()["execution_id"],
            },
        )
        self.assertEqual(die.status_code, 200, die.text)
        wafer = self.client.post(
            "/api/v1/wafer-analysis/analyze",
            json={
                "upload_id": upload_id,
                "die_analysis_id": die.json()["execution_id"],
            },
        )
        self.assertEqual(wafer.status_code, 200, wafer.text)
        return {
            "recurrence": recurrence.json(),
            "correlation": correlation.json(),
            "die": die.json(),
            "wafer": wafer.json(),
        }

    def test_full_upstream_gate_prediction_queries_and_openapi(self) -> None:
        self._prepare(1)
        current = self._prepare(2)
        upstream = self._run_upstream(current)
        predicted = self.client.post(
            "/api/v1/fault-prediction/predict",
            json={
                "upload_id": current,
                "wafer_analysis_id": upstream["wafer"]["execution_id"],
            },
        )
        self.assertEqual(predicted.status_code, 200, predicted.text)
        body = predicted.json()
        self.assertEqual(body["status"], "completed")
        self.assertIn("predictions", body)
        self.assertIn("statistics", body)
        self.assertIn("disclaimer", body)
        for endpoint, key in (
            ("/api/v1/fault-prediction", "predictions"),
            ("/api/v1/fault-prediction/history", "history"),
        ):
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertIn(key, response.json())
        self.assertEqual(
            self.client.get("/api/v1/fault-prediction/statistics").status_code, 200
        )
        if body["predictions"]:
            detail = self.client.get(
                f"/api/v1/fault-prediction/{body['predictions'][0]['prediction_id']}"
            )
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertIn("traceability", detail.json())
            feedback = self.client.post(
                "/api/v1/fault-prediction/feedback",
                json={
                    "prediction_id": body["predictions"][0]["prediction_id"],
                    "validated_fault_type": "TIMING_VIOLATION",
                    "feedback_status": "confirmed",
                },
            )
            self.assertEqual(feedback.status_code, 200, feedback.text)
        paths = self.client.get("/openapi.json").json()["paths"]
        for path in (
            "/api/v1/fault-prediction/predict",
            "/api/v1/fault-prediction",
            "/api/v1/fault-prediction/{prediction_id}",
            "/api/v1/fault-prediction/history",
            "/api/v1/fault-prediction/statistics",
            "/api/v1/fault-prediction/feedback",
            "/api/v1/root-cause/predict",
        ):
            self.assertIn(path, paths)

    def test_validation_rbac_and_upstream_gate(self) -> None:
        self.assertEqual(
            self.client.post("/api/v1/fault-prediction/predict", json={}).status_code,
            422,
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/fault-prediction", headers={"X-Role": "viewer"}
            ).status_code,
            403,
        )
        content = (FIXTURES / "csv_die_results_sample.csv").read_bytes()
        upload = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("gate-fault.csv", content, "text/csv")},
        )
        rejected = self.client.post(
            "/api/v1/fault-prediction/predict",
            json={"upload_id": upload.json()["upload"]["id"]},
        )
        self.assertEqual(rejected.status_code, 409, rejected.text)


if __name__ == "__main__":
    unittest.main()
