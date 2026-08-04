"""YAML-driven CSV adapter (FA-FR-001)."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from parser_engine.adapters.base import AdapterParseResult, LogAdapter
from parser_engine.adapters.schema import TestRecord
from parser_engine.adapters.yaml_config import load_adapter_configs


class CsvAdapter(LogAdapter):
    """Parse CSV die-result files using column mapping from YAML config."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config = load_adapter_configs(config_path)
        self.adapter_id = str(self.config.get("adapter_id", config_path.stem))

    def detect(self, path: Path) -> bool:
        expected_ext = self.config.get("detect", {}).get("extension", ".csv")
        if path.suffix.lower() != expected_ext.lower():
            return False
        required = self.config.get("detect", {}).get("required_columns", [])
        if not required:
            return path.suffix.lower() == ".csv"
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                headers = {h.strip() for h in (reader.fieldnames or [])}
                return all(col in headers for col in required)
        except OSError:
            return False

    def parse(self, path: Path) -> AdapterParseResult:
        columns: dict[str, str] = self.config.get("columns", {})
        defaults: dict[str, str] = self.config.get("defaults", {})
        records: list[TestRecord] = []

        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                values = {}
                for canonical, column in columns.items():
                    values[canonical] = (row.get(column) or defaults.get(canonical, "")).strip()
                for key, val in defaults.items():
                    values.setdefault(key, val)

                pass_fail = values.get("pass_fail", "UNKNOWN").upper()
                failing_patterns = [
                    p.strip() for p in values.get("failing_patterns", "").split(";") if p.strip()
                ]
                failing_tests = [
                    t.strip() for t in values.get("failing_tests", "").split(";") if t.strip()
                ]

                record = TestRecord(
                    lot_id=values.get("lot_id", ""),
                    wafer_id=values.get("wafer_id", ""),
                    die_id=values.get("die_id", ""),
                    x=_maybe_int(values.get("x")),
                    y=_maybe_int(values.get("y")),
                    test_stage=values.get("test_stage", defaults.get("test_stage", "CP")),
                    tester_id=values.get("tester_id", defaults.get("tester_id", "UNKNOWN")),
                    product_id=values.get("product_id", ""),
                    timestamp=values.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    pass_fail=pass_fail,
                    hard_bin=values.get("hard_bin", ""),
                    soft_bin=values.get("soft_bin", ""),
                    failing_tests=failing_tests,
                    failing_patterns=failing_patterns,
                    source_file=str(path),
                    adapter_id=self.adapter_id,
                    raw_fields=values,
                )
                record.record_key = record.build_record_key()
                records.append(record)

        return AdapterParseResult(records=records)


def _maybe_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
