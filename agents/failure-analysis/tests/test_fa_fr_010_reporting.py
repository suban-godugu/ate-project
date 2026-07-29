"""FA-FR-010 production reporting acceptance tests."""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.reporting.csv_exporter import export_csv_report
from backend.reporting.html_exporter import export_html_report
from backend.reporting.production_engine import (
    ReportHandoffGateError,
    ReportingConfig,
    build_benchmark_summary,
    score_completeness,
    score_consistency,
    validate_upstream_handoff,
)
from backend.reporting.report_engine import ReportEngine
from backend.reporting.templates import (
    build_module_sections,
    merge_template_sections,
)
from tests.test_phase16_reporting import _die


class FAFR010GateTests(unittest.TestCase):
    def test_validate_upstream_requires_all_modules(self) -> None:
        issues = validate_upstream_handoff({})
        self.assertEqual(len(issues), 9)
        self.assertTrue(all(item["code"] == "UPSTREAM_MISSING" for item in issues))

    def test_validate_upstream_passes_when_completed(self) -> None:
        upstream = {
            "ingestion": {"status": "completed"},
            "detection": {"execution_status": "completed"},
            "computation": {"status": "completed"},
            "classification": {"status": "completed"},
            "recurrence": {"status": "completed"},
            "correlation": {"status": "completed"},
            "die_analysis": {"status": "completed"},
            "wafer_analysis": {"status": "completed"},
            "fault_prediction": {"status": "completed"},
        }
        self.assertEqual(validate_upstream_handoff(upstream), [])

    def test_handoff_gate_error_carries_issues(self) -> None:
        issues = [{"code": "UPSTREAM_MISSING", "requirement": "FA-FR-002"}]
        with self.assertRaises(ReportHandoffGateError) as ctx:
            raise ReportHandoffGateError(issues)
        self.assertEqual(ctx.exception.issues, issues)


class FAFR010ScoringTests(unittest.TestCase):
    def test_completeness_score_weights_sections(self) -> None:
        module_sections = {
            "fa_fr_001_ingestion": {"records_accepted": 10},
            "fa_fr_002_patterns": {"pattern_count": 2},
            "fa_fr_003_failure_rates": {"metrics": [{"pattern_id": "P1"}]},
            "fa_fr_004_classification": {"total_classified": 1},
            "fa_fr_005_recurrence": {"recurring_failures": [{}]},
            "fa_fr_006_correlation": {"correlations": [{}]},
            "fa_fr_007_die_analysis": {"total_dies": 5},
            "fa_fr_008_wafer_analysis": {"total_wafers": 1},
            "fa_fr_009_fault_prediction": {"predictions": [{}]},
        }
        score = score_completeness(
            module_outputs={},
            module_sections=module_sections,
            recommendations=[{"action": "inspect"}],
        )
        self.assertGreater(score, 0.5)

    def test_consistency_score_with_lineage(self) -> None:
        upstream = {
            "detection": {"analysis_id": "det-1"},
            "computation": {
                "computation_id": "cmp-1",
                "detection_execution_id": "det-1",
            },
            "fault_prediction": {
                "upstream_execution_ids": {"detection_execution_id": "det-1"},
            },
        }
        module_outputs = {
            "die_analysis": {"total_dies": 100},
            "wafer_analysis": {"total_dies": 120},
        }
        score = score_consistency(upstream=upstream, module_outputs=module_outputs)
        self.assertGreaterEqual(score, 0.5)

    def test_benchmark_summary_performance_flags(self) -> None:
        config = ReportingConfig.load()
        summary = build_benchmark_summary(
            completeness_score=0.9,
            consistency_score=0.85,
            processing_ms=100.0,
            pdf_ms=50.0,
            excel_ms=40.0,
            config=config,
            upstream_benchmarks={},
        )
        self.assertTrue(summary["meets_performance_target"])
        self.assertTrue(summary["completeness_passed"])


class FAFR010TemplateTests(unittest.TestCase):
    def test_merge_template_sections(self) -> None:
        merged = merge_template_sections(
            {"executive_summary": True, "fa_fr_009_fault_prediction": False},
            {"yield_summary": False},
        )
        self.assertTrue(merged["executive_summary"])
        self.assertFalse(merged["fa_fr_009_fault_prediction"])
        self.assertFalse(merged["yield_summary"])

    def test_build_module_sections(self) -> None:
        enabled = {f"fa_fr_00{i}_": True for i in range(1, 10)}
        enabled.update(
            {
                "fa_fr_001_ingestion": True,
                "fa_fr_002_patterns": True,
                "fa_fr_003_failure_rates": True,
                "fa_fr_004_classification": True,
                "fa_fr_005_recurrence": True,
                "fa_fr_006_correlation": True,
                "fa_fr_007_die_analysis": True,
                "fa_fr_008_wafer_analysis": True,
                "fa_fr_009_fault_prediction": True,
            }
        )
        sections = build_module_sections(
            module_outputs={
                "failure_rates": {"failure_rate_metrics": [{"pattern_id": "P1"}]},
                "classification": {"total_classified_failures": 3},
                "recurring": {"recurring_failure_list": [{"pattern_id": "P1"}]},
                "correlation": {"correlation_report": [{"pattern_id": "P1"}]},
                "die_analysis": {"total_dies": 10, "die_profiles": []},
                "wafer_analysis": {"total_wafers": 2, "wafer_statistics": []},
                "root_cause": {"predictions": [{"predicted_fault_type": "SCAN"}]},
            },
            upstream={
                "ingestion": {"status": "completed", "records_accepted": 10},
                "detection": {"analysis_id": "d1"},
                "computation": {"computation_id": "c1"},
                "classification": {"execution_id": "cl1"},
                "recurrence": {"analysis_id": "r1"},
                "correlation": {"analysis_id": "x1"},
                "die_analysis": {"analysis_id": "die1"},
                "wafer_analysis": {"analysis_id": "w1"},
                "fault_prediction": {"execution_id": "f1"},
            },
            enabled_sections=enabled,
        )
        self.assertIn("fa_fr_007_die_analysis", sections)
        self.assertEqual(sections["fa_fr_009_fault_prediction"]["requirement"], "FA-FR-009")


class FAFR010ExportTests(unittest.TestCase):
    def test_html_and_csv_exports(self) -> None:
        dies = [_die("LOT1", f"D{i}") for i in range(3)]
        report = ReportEngine().generate(
            die_logs=dies,
            upload_meta={"upload_id": "u1", "original_filename": "t.csv"},
        )
        summaries = report["summaries"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            html_path, html_ms = export_html_report(
                report_id=report["report_id"],
                summaries=summaries,
                html_rendered=report.get("html_preview"),
                output_dir=out,
            )
            csv_path, csv_ms = export_csv_report(
                report_id=report["report_id"],
                summaries=summaries,
                dashboard=report["dashboard_dataset"],
                output_dir=out,
            )
            self.assertTrue(html_path.exists())
            self.assertTrue(csv_path.exists())
            self.assertLess(html_ms, 5000)
            self.assertLess(csv_ms, 5000)
            self.assertIn("<html", html_path.read_text(encoding="utf-8").lower())


class FAFR010PerformanceTests(unittest.TestCase):
    def test_report_generation_under_target(self) -> None:
        dies = [_die("LOT1", f"D{i}") for i in range(20)]
        started = time.perf_counter()
        report = ReportEngine().generate(
            die_logs=dies,
            upload_meta={"upload_id": "perf", "original_filename": "perf.csv"},
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.assertLess(elapsed_ms, 10000)
        self.assertEqual(report["requirement"], "FA-FR-010")


import tests.pg_env  # noqa: F401

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class FAFR010ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_templates_endpoint(self) -> None:
        resp = self.client.get("/api/v1/reports/templates")
        self.assertEqual(resp.status_code, 200)
        templates = resp.json()["templates"]
        self.assertTrue(templates)
        keys = {row["template_key"] for row in templates}
        self.assertIn("enterprise_full", keys)

    def test_legacy_generate_after_upload(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(upload.status_code, 200)
        upload_id = upload.json()["upload"]["id"]

        generate = self.client.post(
            "/api/v1/reports/generate",
            json={"upload_id": upload_id, "legacy": True},
        )
        self.assertEqual(generate.status_code, 200)
        body = generate.json()
        self.assertIn("report_id", body)
        report_id = body["report_id"]

        detail = self.client.get(f"/api/v1/reports/{report_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertTrue(detail.json().get("legacy", False))

        export = self.client.post(
            "/api/v1/reports/export",
            json={"report_id": report_id, "format": "json"},
        )
        self.assertEqual(export.status_code, 200)
        self.assertEqual(export.json()["format"], "json")

    def test_production_generate_rejects_missing_upstream(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            upload = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("gate_test.csv", handle, "text/csv")},
            )
        upload_id = upload.json()["upload"]["id"]
        resp = self.client.post(
            "/api/v1/reports/generate",
            json={"upload_id": upload_id, "legacy": False},
        )
        self.assertEqual(resp.status_code, 422)
        detail = resp.json()["detail"]
        self.assertEqual(detail["code"], "REPORT_UPSTREAM_GATE_FAILED")
        self.assertTrue(detail["issues"])

    def test_history_endpoint(self) -> None:
        resp = self.client.get("/api/v1/reports/history")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("history", resp.json())

    def test_rate_limit_headers_optional(self) -> None:
        resp = self.client.get(
            "/api/v1/reports/templates",
            headers={"X-Role": "report_viewer", "X-User-Id": "tester"},
        )
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
