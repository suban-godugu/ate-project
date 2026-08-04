"""Factory pattern for auto parser selection."""

from __future__ import annotations

from pathlib import Path

from parser_engine.parsers.ascii.ascii_parser import AsciiParser
from parser_engine.parsers.base import BaseParser, ParserResult
from parser_engine.parsers.csv.csv_parser import CsvParser
from parser_engine.parsers.custom.custom_parser import CustomParser
from parser_engine.parsers.json.json_parser import JsonParser
from parser_engine.parsers.stdf.stdf_parser import StdfParser
from parser_engine.parsers.stil.failure_stil import StilParser
from parser_engine.parsers.xml.xml_parser import XmlParser


class ParserFactory:
    """Selects the first parser whose detect() matches the uploaded file."""

    def __init__(self, parsers: list[BaseParser] | None = None) -> None:
        self._parsers = parsers or self.default_parsers()

    @staticmethod
    def default_parsers() -> list[BaseParser]:
        return [
            StilParser(),
            StdfParser(),
            CsvParser(),
            JsonParser(),
            XmlParser(),
            AsciiParser(),
            CustomParser(),
        ]

    def resolve(self, path: Path) -> BaseParser | None:
        for parser in self._parsers:
            if parser.detect(path):
                return parser
        return None

    def parse(self, path: Path) -> tuple[ParserResult, str | None]:
        parser = self.resolve(path)
        if parser is None:
            return ParserResult(errors=[{"file": str(path), "error": "Unsupported format"}]), None
        return parser.parse(path), parser.parser_id
