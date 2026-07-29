"""Phase 7 acceptance tests — FA-FR-001 enterprise ingestion API."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tests.pg_env  # noqa: F401 — configure PostgreSQL for tests

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


class Phase7IngestionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_upload_csv_fixture(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            response = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("upload", body)
        self.assertEqual(body["upload"]["status"], "completed")
        self.assertGreater(body["upload"]["records_accepted"], 0)
        self.assertIn("validation_report", body)

    def test_upload_datalog_fixture(self) -> None:
        path = FIXTURES / "generic_datalog_sample.log"
        with path.open("rb") as handle:
            response = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("generic_datalog_sample.log", handle, "text/plain")},
            )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["upload"]["records_accepted"], 0)

    def test_list_and_get_upload(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            created = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        self.assertEqual(created.status_code, 200)
        upload_id = created.json()["upload"]["id"]
        listing = self.client.get("/api/v1/uploads")
        self.assertEqual(listing.status_code, 200)
        self.assertTrue(listing.json()["uploads"])
        detail = self.client.get(f"/api/v1/uploads/{upload_id}")
        self.assertEqual(detail.status_code, 200)
        metadata = self.client.get(f"/api/v1/uploads/{upload_id}/metadata")
        self.assertEqual(metadata.status_code, 200)
        self.assertIn("metadata", metadata.json())

    def test_duplicate_upload_rejected(self) -> None:
        import uuid

        token = uuid.uuid4().hex
        unique = (
            b"Lot,Wafer,Die,Result,HardBin,SoftBin,FailingPatterns,"
            b"FailingTests,Product,Tester,Stage,Timestamp,X,Y\n"
            + f"LOT_DUP,WF1,DIE_{token},PASS,1,1,,,AI_SOC,T1,CP1,2026-07-15T00:00:00Z,1,1\n".encode()
        )
        first = self.client.post(
            "/api/v1/uploads",
            files={"file": ("dup_probe.csv", unique, "text/csv")},
        )
        self.assertEqual(first.status_code, 200, first.text)
        second = self.client.post(
            "/api/v1/uploads",
            files={"file": ("dup_probe.csv", unique, "text/csv")},
        )
        self.assertEqual(second.status_code, 409)

    def test_delete_upload(self) -> None:
        path = FIXTURES / "csv_die_results_sample.csv"
        with path.open("rb") as handle:
            created = self.client.post(
                "/api/v1/uploads?allow_duplicate=true",
                files={"file": ("csv_die_results_sample.csv", handle, "text/csv")},
            )
        upload_id = created.json()["upload"]["id"]
        deleted = self.client.delete(f"/api/v1/uploads/{upload_id}")
        self.assertEqual(deleted.status_code, 200)
        missing = self.client.get(f"/api/v1/uploads/{upload_id}")
        self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
