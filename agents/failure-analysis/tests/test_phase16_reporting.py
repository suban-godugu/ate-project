"""Phase 16 acceptance tests — FA-FR-010 failure summary & engineering reporting."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.bridge import test_records_to_die_logs
from backend.reporting.dashboard_data import build_dashboard_dataset
from backend.reporting.excel_generator import export_excel_report
from backend.reporting.json_export import export_json_report
from backend.reporting.pdf_generator import export_pdf_report
from backend.reporting.report_engine import ReportEngine
from backend.reporting.summary_generator import build_summaries
from analyzer import analyze_failures
from ingestor import DieLog, PatternResult


def _pattern(hint: str = "SETUP_TIMING") -> PatternResult:
    return PatternResult(
        pattern_id="P1",
        scan_chain_id="CH1",
        expected_signature="1",
        actual_signature="0",
        status="FAIL",
        raw_fields={"ROOT_CAUSE_HINT": hint, "FAIL_TYPE": "SCAN_SHIFT"},
    )


def _die(lot: str = "LOT1", die_id: str = "D1") -> DieLog:
    return DieLog(
        source_path=f"{lot}_{die_id}.log",
        tester_name="T1",
        device_name="SOC",
        lot_id=lot,
        wafer_id="WF01",
        die_id=die_id,
        header_fields={},
        stored_failing=[_pattern()],
        total_executions=1,
        pattern_test_counts={"P1": 1},
        declared_patterns=1,
    )


class Phase16ReportEngineTests(unittest.TestCase):
    def test_full_pipeline_outputs(self) -> None:
        dies = [_die("LOT1", f"D{i}") for i in range(5)]
        report = ReportEngine().generate(
            die_logs=dies,
            upload_meta={"upload_id": "test-upload", "original_filename": "sample.csv"},
        )
        self.assertEqual(report["requirement"], "FA-FR-010")
        self.assertIn("executive_report", report)
        self.assertIn("engineering_report", report)
        self.assertIn("failure_summary", report)
        self.assertIn("yield_report", report)
        self.assertIn("root_cause_report", report)
        self.assertIn("dashboard_dataset", report)
        self.assertIn("export_paths", report)
        self.assertTrue(report["meets_performance_target"])

    def test_summary_sections(self) -> None:
        dies = [_die("LOT1", "D1"), _die("LOT2", "D2")]
        analysis = analyze_failures(dies)
        summaries = build_summaries(
            analysis=analysis,
            module_outputs={},
            upload_meta={"upload_id": "u1", "original_filename": "t.csv"},
            config={"report": {"title": "Test"}, "sections": {}},
        )
        for key in (
            "executive_summary",
            "engineering_summary",
            "failure_trend_summary",
            "yield_summary",
            "top_failure_modes",
            "lot_summary",
            "wafer_summary",
            "die_summary",
            "root_cause_summary",
            "recommended_corrective_actions",
            "engineering_observations",
        ):
            self.assertIn(key, summaries)
        self.assertIn("generated_at", summaries["metadata"])

    def test_dashboard_charts(self) -> None:
        dies = [_die("LOT1", f"D{i}") for i in range(3)]
        analysis = analyze_failures(dies)
        summaries = build_summaries(
            analysis=analysis,
            module_outputs={},
            upload_meta={"upload_id": "u1"},
            config={"report": {}, "sections": {}},
        )
        dashboard = build_dashboard_dataset(summaries, analysis, {})
        self.assertIn("summary_cards", dashboard)
        self.assertIn("charts", dashboard)
        self.assertIn("yield_by_lot", dashboard["charts"])

    def test_json_export(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path, size_kb = export_json_report(
                report_id="r1",
                summaries={"metadata": {"generated_at": "now"}, "executive_summary": {}},
                dashboard={"summary_cards": []},
                analysis={"summary": {}},
                module_outputs={},
                export_meta={"report_id": "r1"},
                output_dir=Path(tmp),
            )
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_id"], "r1")
            self.assertGreater(size_kb, 0)

    def test_pdf_and_excel_export(self) -> None:
        dies = [_die("LOT1", f"D{i}") for i in range(3)]
        report = ReportEngine().generate(
            die_logs=dies,
            upload_meta={"upload_id": "u1", "original_filename": "t.csv"},
        )
        summaries = report["summaries"]
        report_id = report["report_id"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            pdf_path, pdf_ms = export_pdf_report(
                report_id=report_id,
                summaries=summaries,
                html_rendered=report.get("html_preview"),
                output_dir=out,
            )
            excel_path, excel_ms = export_excel_report(
                report_id=report_id,
                summaries=summaries,
                dashboard=report["dashboard_dataset"],
                output_dir=out,
            )
            self.assertTrue(pdf_path.exists())
            self.assertTrue(excel_path.exists())
            self.assertLess(pdf_ms, 5000)
            self.assertLess(excel_ms, 5000)


import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase16ReportApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_generate_after_upload(self) -> None:
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
            json={"upload_id": upload_id},
        )
        self.assertEqual(generate.status_code, 200)
        body = generate.json()
        self.assertIn("report_id", body)
        self.assertIn("executive_report", body)
        self.assertIn("dashboard_dataset", body)
        self.assertIn("meets_performance_target", body)
        self.assertLess(body["processing_ms"], 60000)
        report_id = body["report_id"]

        listing = self.client.get("/api/v1/reports")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["reports"])

        detail = self.client.get(f"/api/v1/reports/{report_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["report_id"], report_id)

        for endpoint, content_type in (
            ("/api/v1/reports/download/json", "application/json"),
            ("/api/v1/reports/download/pdf", "application/pdf"),
            ("/api/v1/reports/download/excel", None),
        ):
            resp = self.client.get(f"{endpoint}?report_id={report_id}")
            self.assertEqual(resp.status_code, 200, endpoint)
            if content_type:
                self.assertIn(content_type, resp.headers.get("content-type", ""))


if __name__ == "__main__":
    unittest.main()
