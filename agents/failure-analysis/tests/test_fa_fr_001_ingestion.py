"""FA-FR-001 ingestion API & parser acceptance tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tests.pg_env  # noqa: F401

from fastapi.testclient import TestClient  # noqa: E402

from backend.ingestion.parser_factory import ParserFactory  # noqa: E402
from backend.ingestion.security import sanitize_filename, safe_relative_path  # noqa: E402
from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class SecurityAndParserUnitTests(unittest.TestCase):
    def test_sanitize_filename_strips_traversal(self) -> None:
        cleaned = sanitize_filename("../../evil.stil")
        self.assertEqual(cleaned, "evil.stil")

    def test_safe_relative_path_blocks_escape(self) -> None:
        cleaned = safe_relative_path("../outside/../../secret.txt")
        self.assertIsNotNone(cleaned)
        self.assertNotIn("..", cleaned)

    def test_stil_parser_selected(self) -> None:
        stil = FIXTURES / "minimal_scan.stil"
        parser = ParserFactory().resolve(stil)
        self.assertIsNotNone(parser)
        self.assertEqual(parser.parser_id, "stil_v1")

    def test_empty_file_rejected(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        self.assertIn(response.status_code, {400, 413, 422})


class FaFr001ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_upload_stil_fixture(self) -> None:
        path = FIXTURES / "minimal_scan.stil"
        with path.open("rb") as handle:
            response = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("minimal_scan.stil", handle, "application/octet-stream")},
            )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["upload"]["status"], "completed")
        self.assertGreater(body["upload"]["records_accepted"], 0)
        upload_id = body["upload"]["id"]
        records = self.client.get(f"/api/v1/uploads/{upload_id}/records")
        self.assertEqual(records.status_code, 200)
        self.assertGreater(records.json()["total_returned"], 0)

    def test_dataset_folder_upload(self) -> None:
        stil = FIXTURES / "minimal_scan.stil"
        log = FIXTURES / "generic_datalog_sample.log"
        with stil.open("rb") as sf, log.open("rb") as lf:
            response = self.client.post(
                "/api/v1/datasets/upload",
                data={"name": "fa_fr_001_folder", "async_process": "false"},
                files=[
                    ("files", ("minimal_scan.stil", sf.read(), "application/octet-stream")),
                    ("files", ("generic_datalog_sample.log", lf.read(), "text/plain")),
                ],
            )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertIn("dataset_id", body)
        self.assertGreaterEqual(body.get("file_count", 0), 1)
        detail = self.client.get(f"/api/v1/datasets/{body['dataset_id']}")
        self.assertEqual(detail.status_code, 200)
        self.assertGreaterEqual(len(detail.json()["uploads"]), 1)
        for item in detail.json()["uploads"]:
            self.assertEqual(item["dataset_id"], body["dataset_id"])

    def test_ingestion_statistics(self) -> None:
        response = self.client.get("/api/v1/ingestion/statistics")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("total_uploads", body)
        self.assertIn("by_parser", body)

    def test_openapi_documents_ingestion(self) -> None:
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        self.assertIn("/api/v1/uploads", paths)
        self.assertIn("/api/v1/datasets/upload", paths)
        self.assertIn("/api/v1/ingestion/statistics", paths)


if __name__ == "__main__":
    unittest.main()
