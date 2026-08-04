"""YAML-driven generic ASCII datalog adapter (FA-FR-001)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from parser_engine.adapters.base import AdapterParseResult, LogAdapter
from parser_engine.adapters.schema import TestRecord
from parser_engine.adapters.yaml_config import load_adapter_configs


class DatalogAsciiAdapter(LogAdapter):
    """Parse key-value ASCII datalog files using a per-customer YAML mapping."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.config = load_adapter_configs(config_path)
        self.adapter_id = str(self.config.get("adapter_id", config_path.stem))

    def detect(self, path: Path) -> bool:
        if path.suffix.lower() not in {".log", ".txt", ".dat"}:
            return False
        patterns = self.config.get("detect", {}).get("regex_lines", [])
        if not patterns:
            return False
        try:
            text = path.read_text(encoding="utf-8", errors="replace")[:4096]
        except OSError:
            return False
        return all(re.search(pat, text, re.MULTILINE) for pat in patterns)

    def parse(self, path: Path) -> AdapterParseResult:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()

        header_map: dict[str, str] = self.config.get("header_fields", {})
        record_map: dict[str, str] = self.config.get("record_fields", {})
        delimiter = self.config.get("record_delimiter")

        header_values = _extract_fields(lines, header_map)
        records: list[TestRecord] = []

        if delimiter:
            blocks = _split_blocks(lines, delimiter)
            for block in blocks:
                values = {**header_values, **_extract_fields(block, record_map)}
                records.append(_build_record(values, path, self.adapter_id))
        else:
            values = {**header_values, **_extract_fields(lines, record_map)}
            records.append(_build_record(values, path, self.adapter_id))

        return AdapterParseResult(records=records)


def _split_blocks(lines: list[str], delimiter: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    delim_re = re.compile(delimiter)
    for line in lines:
        if delim_re.match(line.strip()):
            if current:
                blocks.append(current)
            current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks or [lines]


def _extract_fields(lines: list[str], field_map: dict) -> dict[str, str]:
    values: dict[str, str] = {}
    for canonical, spec in field_map.items():
        if isinstance(spec, str):
            pattern = spec
            default = ""
        else:
            pattern = spec.get("regex", "")
            default = str(spec.get("default", ""))
        if not pattern:
            continue
        regex = re.compile(pattern)
        for line in lines:
            match = regex.search(line)
            if match:
                values[canonical] = match.group(1).strip() if match.groups() else match.group(0).strip()
                break
        if canonical not in values and default:
            values[canonical] = default
    return values


def _build_record(values: dict[str, str], path: Path, adapter_id: str) -> TestRecord:
    pass_fail = values.get("pass_fail", "UNKNOWN").upper()
    failing_patterns = [p.strip() for p in values.get("failing_patterns", "").split(",") if p.strip()]
    failing_tests = [t.strip() for t in values.get("failing_tests", "").split(",") if t.strip()]

    record = TestRecord(
        lot_id=values.get("lot_id", ""),
        wafer_id=values.get("wafer_id", ""),
        die_id=values.get("die_id", ""),
        x=_maybe_int(values.get("x")),
        y=_maybe_int(values.get("y")),
        test_stage=values.get("test_stage", "CP"),
        tester_id=values.get("tester_id", "UNKNOWN"),
        product_id=values.get("product_id", ""),
        timestamp=values.get("timestamp", datetime.now(timezone.utc).isoformat()),
        pass_fail=pass_fail,
        hard_bin=values.get("hard_bin", ""),
        soft_bin=values.get("soft_bin", ""),
        failing_tests=failing_tests,
        failing_patterns=failing_patterns,
        source_file=str(path),
        adapter_id=adapter_id,
        raw_fields=values,
    )
    record.record_key = record.build_record_key()
    return record


def _maybe_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None
