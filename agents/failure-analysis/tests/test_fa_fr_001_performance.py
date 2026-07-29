"""Performance smoke tests for FA-FR-001 ingestion throughput."""

from __future__ import annotations

import io
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tests.pg_env  # noqa: F401

from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402


class IngestionPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._client_ctx = TestClient(app)
        cls.client = cls._client_ctx.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._client_ctx.__exit__(None, None, None)

    def test_async_upload_ack_under_two_seconds(self) -> None:
        header = (
            b"Lot,Wafer,Die,Result,HardBin,SoftBin,FailingPatterns,"
            b"FailingTests,Product,Tester,Stage,Timestamp,X,Y\n"
        )
        rows = b"\n".join(
            (
                f"LOT_P,WF1,DIE_{i},PASS,1,1,,,AI_SOC,T1,CP1,"
                f"2026-07-15T00:00:00Z,1,1"
            ).encode()
            for i in range(500)
        )
        payload = header + rows + b"\n"
        started = time.perf_counter()
        response = self.client.post(
            "/api/v1/uploads?async_process=true&allow_duplicate=true",
            files={"file": ("perf_async.csv", io.BytesIO(payload), "text/csv")},
        )
        elapsed = time.perf_counter() - started
        self.assertEqual(response.status_code, 200, response.text)
        self.assertLess(elapsed, 2.0, f"async ACK took {elapsed:.3f}s")

    def test_sync_csv_validation_under_five_seconds(self) -> None:
        header = (
            b"Lot,Wafer,Die,Result,HardBin,SoftBin,FailingPatterns,"
            b"FailingTests,Product,Tester,Stage,Timestamp,X,Y\n"
        )
        rows = b"\n".join(
            (
                f"LOT_P,WF1,DIE_{i},{'PASS' if i % 2 == 0 else 'FAIL'},1,1,,,AI_SOC,T1,CP1,"
                f"2026-07-15T00:00:00Z,1,1"
            ).encode()
            for i in range(2000)
        )
        payload = header + rows + b"\n"
        started = time.perf_counter()
        response = self.client.post(
            "/api/v1/uploads?allow_duplicate=true",
            files={"file": ("perf_sync.csv", io.BytesIO(payload), "text/csv")},
        )
        elapsed = time.perf_counter() - started
        self.assertEqual(response.status_code, 200, response.text)
        self.assertLess(elapsed, 5.0, f"sync validation/parse took {elapsed:.3f}s")


if __name__ == "__main__":
    unittest.main()
