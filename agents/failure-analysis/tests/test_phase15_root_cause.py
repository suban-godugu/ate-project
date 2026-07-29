"""Phase 15 acceptance tests — FA-FR-009 AI root cause prediction engine."""

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
from backend.root_cause.rag_engine import RAGEngine
from backend.root_cause.root_cause_engine import RootCauseEngine
from ingestor import DieLog, PatternResult


def _pattern(
    *,
    pid: str = "P1",
    chain: str = "CH1",
    hint: str = "SETUP_TIMING",
    fail_type: str = "SCAN_SHIFT",
) -> PatternResult:
    return PatternResult(
        pattern_id=pid,
        scan_chain_id=chain,
        expected_signature="1",
        actual_signature="0",
        status="FAIL",
        raw_fields={
            "ROOT_CAUSE_HINT": hint,
            "FAIL_TYPE": fail_type,
            "SETUP_SLACK_PS": "-50",
        },
    )


def _die(
    lot: str = "LOT1",
    wafer: str = "WF01",
    die_id: str = "D1",
    *,
    chain: str = "CH1",
    hint: str = "SETUP_TIMING",
) -> DieLog:
    return DieLog(
        source_path=f"{lot}_{wafer}_{die_id}.log",
        tester_name="T1",
        device_name="SOC",
        lot_id=lot,
        wafer_id=wafer,
        die_id=die_id,
        header_fields={},
        stored_failing=[_pattern(chain=chain, hint=hint)],
        total_executions=1,
        pattern_test_counts={"P1": 1},
        declared_patterns=1,
    )


class Phase15RootCauseEngineTests(unittest.TestCase):
    def test_full_pipeline_outputs(self) -> None:
        dies = [
            _die("LOT1", "WF01", f"D{i}", hint="SETUP_TIMING")
            for i in range(4)
        ] + [
            _die("LOT2", "WF02", f"D{i}", hint="SETUP_TIMING")
            for i in range(3)
        ]
        report = RootCauseEngine(enable_llm=True).predict(die_logs=dies)
        self.assertEqual(report["requirement"], "FA-FR-009")
        self.assertIn("predictions", report)
        self.assertIn("root_cause_report", report)
        self.assertIn("engineering_recommendations", report)
        self.assertIn("similar_historical_cases", report)
        self.assertIn("ai_explanations", report)
        self.assertIn("engineering_dashboard", report)
        self.assertTrue(report["meets_performance_target"])
        self.assertGreater(report["total_predictions"], 0)

    def test_every_prediction_has_confidence(self) -> None:
        dies = [_die(hint="IR_DROP"), _die("LOT2", "WF02", "D2", hint="IR_DROP")]
        report = RootCauseEngine(enable_ml=False).predict(die_logs=dies)
        for pred in report["predictions"]:
            self.assertIn("confidence_score", pred)
            self.assertGreaterEqual(pred["confidence_score"], 0.0)
            self.assertLessEqual(pred["confidence_score"], 1.0)
            self.assertIn("predicted_fault_type", pred)
            self.assertIn("predicted_root_cause", pred)
            self.assertIn("ai_explanation", pred)

    def test_semantic_search_retrieves_cases(self) -> None:
        kb = ROOT / "config" / "root_cause_knowledge.yaml"
        rag = RAGEngine(knowledge_base_path=kb, use_faiss=False, top_k=3)
        results, elapsed_ms = rag.search("SETUP_TIMING scan chain negative slack")
        self.assertLess(elapsed_ms, 2000)
        self.assertTrue(results)
        self.assertIn("case_id", results[0])
        self.assertIn("similarity_score", results[0])

    def test_explainable_reasoning_steps(self) -> None:
        dies = [
            _die("LOT1", "WF01", "D1", hint="IR_DROP"),
            _die("LOT2", "WF02", "D2", hint="IR_DROP"),
        ]
        report = RootCauseEngine(enable_ml=False).predict(die_logs=dies)
        pred = report["predictions"][0]
        self.assertTrue(pred.get("reasoning_steps") or pred.get("ai_explanation"))
        self.assertIn("confidence_breakdown", pred)

    def test_recommendations_generated(self) -> None:
        dies = [
            _die("LOT1", "WF01", f"D{i}", hint="IDDQ")
            for i in range(3)
        ] + [
            _die("LOT2", "WF02", f"D{i}", hint="IDDQ")
            for i in range(2)
        ]
        report = RootCauseEngine(enable_ml=False).predict(die_logs=dies)
        self.assertTrue(report["engineering_recommendations"])
        rec = report["engineering_recommendations"][0]
        self.assertIn("action", rec)
        self.assertIn("priority", rec)


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase15RootCauseApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_predict_after_upload(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(upload.status_code, 200)
        upload_id = upload.json()["upload"]["id"]

        predict = self.client.post(
            "/api/v1/root-cause/predict",
            json={"upload_id": upload_id},
        )
        self.assertEqual(predict.status_code, 200)
        body = predict.json()
        self.assertIn("run_id", body)
        self.assertIn("predictions", body)
        self.assertIn("root_cause_report", body)
        self.assertTrue(body["meets_performance_target"])
        run_id = body["run_id"]

        listing = self.client.get("/api/v1/root-cause")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["runs"])

        history = self.client.get(f"/api/v1/root-cause/history?run_id={run_id}")
        self.assertEqual(history.status_code, 200)
        self.assertIn("predictions", history.json())

        recs = self.client.get(f"/api/v1/root-cause/recommendations?run_id={run_id}")
        self.assertEqual(recs.status_code, 200)
        self.assertIn("engineering_recommendations", recs.json())


if __name__ == "__main__":
    unittest.main()
