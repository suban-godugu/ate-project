"""Phase 1 acceptance tests — adapter plugin architecture (FA-FR-001)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from adapters.csv_adapter import CsvAdapter
from adapters.datalog_ascii import DatalogAsciiAdapter
from adapters.registry import default_registry
from adapters.schema import TestRecord
from adapters.stdf_v4 import StdfV4Adapter, build_minimal_stdf_bytes
from adapters.validation import partition_records
from ingestion_service import ingest_directory


FIXTURES = Path(__file__).parent / "fixtures"
CONFIG = ROOT / "config" / "adapters"


class Phase1AdapterTests(unittest.TestCase):
    def test_generic_datalog_adapter_parses_fixture(self) -> None:
        adapter = DatalogAsciiAdapter(CONFIG / "generic_datalog.yaml")
        path = FIXTURES / "generic_datalog_sample.log"
        self.assertTrue(adapter.detect(path))
        result = adapter.parse(path)
        self.assertEqual(len(result.records), 1)
        record = result.records[0]
        self.assertEqual(record.lot_id, "LOT_SYN_001")
        self.assertEqual(record.die_id, "DIE_42")
        self.assertEqual(record.pass_fail, "FAIL")
        self.assertEqual(record.failing_patterns, ["P1001", "P1002"])

    def test_csv_adapter_parses_fixture(self) -> None:
        adapter = CsvAdapter(CONFIG / "csv_die_results.yaml")
        path = FIXTURES / "csv_die_results_sample.csv"
        self.assertTrue(adapter.detect(path))
        result = adapter.parse(path)
        self.assertEqual(len(result.records), 2)
        fail = [r for r in result.records if r.pass_fail == "FAIL"][0]
        self.assertEqual(fail.die_id, "DIE_8")
        self.assertEqual(fail.failing_patterns, ["P2001", "P2002"])

    def test_stdf_adapter_parses_minimal_binary(self) -> None:
        adapter = StdfV4Adapter()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.stdf"
            path.write_bytes(
                build_minimal_stdf_bytes(
                    lot_id="LOT_STDF",
                    wafer_id="WF_STDF",
                    pass_fail=1,
                    hard_bin=5,
                )
            )
            self.assertTrue(adapter.detect(path))
            result = adapter.parse(path)
            self.assertGreaterEqual(len(result.records), 1)
            record = result.records[0]
            self.assertEqual(record.lot_id, "LOT_STDF")
            self.assertEqual(record.pass_fail, "FAIL")
            self.assertEqual(record.hard_bin, "5")

    def test_mandatory_field_validation_quarantines(self) -> None:
        bad = TestRecord(
            lot_id="",
            wafer_id="W1",
            die_id="D1",
            test_stage="CP",
            tester_id="T1",
            pass_fail="FAIL",
            timestamp="2026-01-01",
            source_file="x.log",
            adapter_id="test",
        )
        accepted, quarantined = partition_records([bad])
        self.assertEqual(len(accepted), 0)
        self.assertEqual(len(quarantined), 1)

    def test_ingest_directory_multi_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "generic_datalog_sample.log").write_text(
                (FIXTURES / "generic_datalog_sample.log").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (root / "csv_die_results_sample.csv").write_text(
                (FIXTURES / "csv_die_results_sample.csv").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (root / "sample.stdf").write_bytes(
                build_minimal_stdf_bytes(lot_id="LOT_MIX", wafer_id="WF_MIX")
            )

            records, die_logs, report = ingest_directory(
                root, recursive=False, use_legacy_fallback=False
            )
            self.assertGreaterEqual(len(records), 3)
            self.assertEqual(report.files_parsed, 3)
            self.assertGreaterEqual(report.integrity_pct, 99.0)
            adapter_ids = {r.adapter_id for r in records}
            self.assertIn("generic_datalog", adapter_ids)
            self.assertIn("csv_die_results", adapter_ids)
            self.assertIn("stdf_v4", adapter_ids)

    def test_default_registry_has_adapters(self) -> None:
        registry = default_registry()
        self.assertGreaterEqual(len(registry.adapters), 4)


if __name__ == "__main__":
    unittest.main()
