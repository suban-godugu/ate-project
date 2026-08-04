"""XML test-record parser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from parser_engine.adapters.schema import TestRecord
from parser_engine.parsers.base import BaseParser, ParserResult

_RECORD_TAGS = {"record", "die", "test_record", "TestRecord"}


class XmlParser(BaseParser):
    parser_id = "xml"

    def supported_extensions(self) -> set[str]:
        return {".xml"}

    def detect(self, path: Path) -> bool:
        return path.suffix.lower() == ".xml"

    def parse(self, path: Path) -> ParserResult:
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError) as exc:
            return ParserResult(errors=[{"file": str(path), "error": f"XML parse error: {exc}"}])

        root = tree.getroot()
        nodes = [
            node
            for node in root.iter()
            if node.tag.split("}")[-1] in _RECORD_TAGS
        ]
        if not nodes and root.tag.split("}")[-1] not in _RECORD_TAGS:
            nodes = list(root)

        records: list[TestRecord] = []
        for node in nodes:
            fields = {child.tag.split("}")[-1]: (child.text or "").strip() for child in node}
            fields.setdefault("source_file", str(path))
            fields.setdefault("adapter_id", self.parser_id)
            record = TestRecord.from_dict(fields)
            records.append(record)

        return ParserResult(
            records=records,
            metadata={"parser": self.parser_id, "record_count": len(records)},
        )
