"""JSON test-record parser."""

from __future__ import annotations

import json
from pathlib import Path

from parser_engine.adapters.schema import TestRecord
from parser_engine.parsers.base import BaseParser, ParserResult


class JsonParser(BaseParser):
    parser_id = "json"

    def supported_extensions(self) -> set[str]:
        return {".json"}

    def detect(self, path: Path) -> bool:
        return path.suffix.lower() == ".json"

    def parse(self, path: Path) -> ParserResult:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return ParserResult(errors=[{"file": str(path), "error": f"JSON parse error: {exc}"}])

        records: list[TestRecord] = []
        items = payload if isinstance(payload, list) else payload.get("records", [])
        if not isinstance(items, list):
            return ParserResult(errors=[{"file": str(path), "error": "JSON schema: expected list or records[]"}])

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                records.append(
                    TestRecord(
                        lot_id="",
                        wafer_id="",
                        die_id="",
                        test_stage="",
                        tester_id="",
                        pass_fail="",
                        timestamp="",
                        source_file=str(path),
                        adapter_id=self.parser_id,
                    )
                )
                continue
            item.setdefault("source_file", str(path))
            item.setdefault("adapter_id", self.parser_id)
            records.append(TestRecord.from_dict(item))

        return ParserResult(
            records=records,
            metadata={"parser": self.parser_id, "record_count": len(records)},
        )
