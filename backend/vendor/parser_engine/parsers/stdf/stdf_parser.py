"""STDF parser — wraps adapters.stdf_v4."""

from __future__ import annotations

from pathlib import Path

from parser_engine.adapters.stdf_v4 import StdfV4Adapter
from parser_engine.parsers.base import BaseParser, ParserResult


class StdfParser(BaseParser):
    parser_id = "stdf_v4"

    def __init__(self) -> None:
        self._adapter = StdfV4Adapter()

    def supported_extensions(self) -> set[str]:
        return {".stdf", ".std"}

    def detect(self, path: Path) -> bool:
        return self._adapter.detect(path)

    def parse(self, path: Path) -> ParserResult:
        result = self._adapter.parse(path)
        return ParserResult(
            records=result.records,
            errors=result.errors,
            metadata={"parser": self.parser_id, **result.metadata},
        )
