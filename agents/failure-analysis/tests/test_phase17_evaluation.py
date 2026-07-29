"""Phase 17 acceptance tests — AI Evaluation & Validation Framework."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation.ai_metrics import compute_classification_metrics, engineering_score
from evaluation.dataset_discovery import DatasetDiscoveryEngine
from evaluation.domain import ValidationStatus
from evaluation.pipeline_orchestrator import EvaluationOrchestrator
from evaluation.validation_engine import ValidationEngine


class Phase17DiscoveryTests(unittest.TestCase):
    def test_discover_finds_extensions_without_hardcoded_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stil = root / "CustomerA_SCAN_1000pat.stil"
            stil.write_text('STIL 1.0;\nTitle "demo";\n', encoding="utf-8")
            log_dir = root / "generated_logs 1000 patterns" / "LOT_1"
            log_dir.mkdir(parents=True)
            (log_dir / "fail_die_1.log").write_text(
                "DEVICE_NAME=SOC\nLOT_ID=L1\nWAFER_ID=W1\nDIE_ID=D1\n"
                "TOTAL_PATTERNS: 1000\nDIE_LABEL=FAIL\n",
                encoding="utf-8",
            )
            cfg = root / "eval.yaml"
            cfg.write_text(
                "search_roots:\n"
                f"  - \"{root.as_posix()}\"\n"
                "matching:\n"
                "  scale_tokens: [\"1000\", \"2000\", \"full\"]\n"
                "  labelled_name_patterns: [\"fail_die\", \"good_die\"]\n"
                "  ignore_name_patterns: []\n",
                encoding="utf-8",
            )
            inventory = DatasetDiscoveryEngine(config_path=cfg).discover()
            self.assertGreaterEqual(len(inventory.stil_files), 1)
            self.assertTrue(any(b.scale_token == "1000" for b in inventory.bundles))
            self.assertTrue(inventory.bundles[0].labelled_log_paths)


class Phase17MetricsTests(unittest.TestCase):
    def test_classification_metrics_and_engineering_score(self) -> None:
        metrics = compute_classification_metrics(
            ["A", "A", "B", "B"],
            ["A", "B", "B", "B"],
            confidences=[0.9, 0.4, 0.8, 0.7],
        )
        self.assertIn("accuracy", metrics)
        self.assertIn("f1_score", metrics)
        self.assertIn("confusion_matrix", metrics)
        self.assertGreater(engineering_score(metrics), 0)


class Phase17ValidationTests(unittest.TestCase):
    def test_module_validation_pass_fail_warning(self) -> None:
        engine = ValidationEngine()
        ok = engine.validate_fr001(
            {"record_count": 10, "pattern_count": 5, "stil_validation_passed": True}
        )
        self.assertEqual(ok.status, ValidationStatus.PASS)
        bad = engine.validate_fr001({"record_count": 0, "pattern_count": 0})
        self.assertEqual(bad.status, ValidationStatus.FAIL)


class Phase17OrchestratorUnitTests(unittest.TestCase):
    def test_run_on_synthetic_mini_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stil = root / "Prod_1000pat.stil"
            stil.write_text(
                'STIL 1.0;\nTitle "t";\nAnn {* pattern_begin = 1 *};\n'
                "Ann {* pattern_end = 1000 *};\n",
                encoding="utf-8",
            )
            log_dir = root / "generated_logs 1000 patterns" / "LOT_A"
            log_dir.mkdir(parents=True)
            # Legacy Verilumen-compatible log (DEVICE_NAME + [PATTERN_ID : N] blocks)
            sample = (
                "DEVICE_NAME: SOC\n"
                "TESTER_NAME: T1\n"
                "LOT_ID: LOT_A\n"
                "WAFER_ID: WF01\n"
                "DIE_ID: D1\n"
                "DIE_X: 1\n"
                "DIE_Y: 1\n"
                "DIE_LABEL: FAIL\n"
                "DEFECT_TYPE: Center\n"
                "TOTAL_PATTERNS: 1000\n"
                "[PATTERN_ID : 1]\n"
                "SCAN_CHAIN_ID: CH1\n"
                "EXPECTED_SIGNATURE: 1\n"
                "ACTUAL_SIGNATURE: 0\n"
                "STATUS: FAIL\n"
                "FAIL_TYPE: SCAN_SHIFT\n"
                "ROOT_CAUSE_HINT: SETUP_TIMING\n"
                "---\n"
            )
            (log_dir / "fail_die_1.log").write_text(sample, encoding="utf-8")
            good = (
                "DEVICE_NAME: SOC\n"
                "TESTER_NAME: T1\n"
                "LOT_ID: LOT_A\n"
                "WAFER_ID: WF01\n"
                "DIE_ID: D2\n"
                "DIE_X: 2\n"
                "DIE_Y: 2\n"
                "DIE_LABEL: PASS\n"
                "DEFECT_TYPE: Normal\n"
                "TOTAL_PATTERNS: 1000\n"
                "[PATTERN_ID : 2]\n"
                "SCAN_CHAIN_ID: CH1\n"
                "EXPECTED_SIGNATURE: 1\n"
                "ACTUAL_SIGNATURE: 1\n"
                "STATUS: PASS\n"
                "---\n"
            )
            (log_dir / "good_die_1.log").write_text(good, encoding="utf-8")

            out_dir = root / "reports"
            model_dir = root / "models"
            log_store = root / "logs"
            cfg = root / "evaluation.yaml"
            cfg.write_text(
                "search_roots:\n"
                f"  - \"{root.as_posix()}\"\n"
                "matching:\n"
                "  scale_tokens: [\"1000\"]\n"
                "  labelled_name_patterns: [\"fail_die\", \"good_die\"]\n"
                "  ignore_name_patterns: []\n"
                "execution:\n"
                "  max_logs_per_dataset: 10\n"
                "  max_stil_bytes_for_full_parse: 1000000\n"
                "  modules: [FA-FR-001, FA-FR-002, FA-FR-003, FA-FR-004, FA-FR-005, "
                "FA-FR-006, FA-FR-007, FA-FR-008, FA-FR-009, FA-FR-010]\n"
                "validation:\n"
                "  min_detection_accuracy_pct: 0\n"
                "  require_export_artifacts: false\n"
                "training:\n"
                "  enabled: true\n"
                "  min_labelled_samples: 2\n"
                f"  model_store_dir: \"{model_dir.as_posix()}\"\n"
                "reporting:\n"
                f"  output_dir: \"{out_dir.as_posix()}\"\n"
                "  formats: [json, csv]\n"
                "logging:\n"
                f"  log_dir: \"{log_store.as_posix()}\"\n",
                encoding="utf-8",
            )

            report = EvaluationOrchestrator(config_path=cfg).run(max_logs=5)
            self.assertEqual(report["requirement"], "EVAL-FRAMEWORK")
            self.assertGreaterEqual(report["datasets_evaluated"], 1)
            self.assertIn("dashboard", report)
            self.assertIn("pass_fail_summary", report)
            first = report["dataset_results"][0]
            self.assertIn("validation", first)
            self.assertIn("benchmark", first)
            self.assertTrue(any(v["module"] == "FA-FR-001" for v in first["validation"]))
            fr001 = first["module_outputs"].get("FA-FR-001", {})
            self.assertGreater(fr001.get("record_count", 0), 0)
            statuses = {v["module"]: v["status"] for v in first["validation"]}
            self.assertIn(statuses.get("FA-FR-001"), {"PASS", "WARNING"})
            self.assertEqual(statuses.get("FA-FR-002"), "PASS")
            self.assertEqual(statuses.get("FA-FR-010"), "PASS")


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


class Phase17EvaluationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_datasets_endpoint(self) -> None:
        resp = self.client.get("/api/v1/evaluation/datasets")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("stil_count", body)
        self.assertIn("bundles", body)


if __name__ == "__main__":
    unittest.main()
