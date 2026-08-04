"""Central Parser Engine facade used by all Scan Chain agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from parser_engine.parsers.factory import ParserFactory
from parser_engine.parsers.stil.pattern_stil import STILParser
from parser_engine.parsers.ate.pattern_ate import ATEParser
from parser_engine.adapters.ate_log_adapter import (
    parse_ate_log_file as pattern_parse_ate_log,
    parse_ate_log_files as pattern_parse_ate_logs,
)


class ParserEngine:
    """
    Unified entry point for STIL / ATE / STDF / CSV / JSON / XML parsing.

    Profiles:
      - auto: Failure Analysis factory (format detection)
      - pattern: Pattern Analysis STIL/ATE APIs
      - diagnosis: Scan Diagnosis log/STIL helpers
    """

    def __init__(self) -> None:
        self._factory = ParserFactory()
        self._stil = STILParser()
        self._ate = ATEParser()

    def parse(self, file: str | Path, *, profile: str = "auto") -> Any:
        path = Path(file)
        profile = (profile or "auto").lower()
        if profile == "pattern":
            if path.suffix.lower() == ".stil":
                return self.parse_stil(path, profile="pattern")
            return self.parse_ate(path, profile="pattern")
        if profile == "diagnosis":
            return self.parse_ate(path, profile="diagnosis")
        result, parser_id = self._factory.parse(path)
        return {"parser_id": parser_id, "result": result}

    def parse_stil(self, file: str | Path, *, profile: str = "pattern", **kwargs: Any) -> Any:
        path = Path(file)
        profile = (profile or "pattern").lower()
        if profile == "failure":
            from parser_engine.parsers.stil.failure_stil import StilParser

            return StilParser().parse(path)
        if profile == "diagnosis":
            from parser_engine.parsers.stil.diagnosis_stil import parse_stil_scan_structures

            return parse_stil_scan_structures(path)
        # Pattern Analysis CPM path
        max_size_gb = float(kwargs.get("max_size_gb", 10.0))
        return self._stil.parse(str(path), max_size_gb=max_size_gb)

    def parse_ate(self, file: str | Path, *, profile: str = "pattern", **kwargs: Any) -> Any:
        path = Path(file)
        profile = (profile or "pattern").lower()
        if profile == "diagnosis":
            from parser_engine.parsers.ate.diagnosis_ate import parse_log_to_dataframe

            keep_status = kwargs.get("keep_status", "FAIL")
            return parse_log_to_dataframe(path, keep_status=keep_status)
        if profile == "adapter":
            return pattern_parse_ate_log(path)
        return self._ate.parse(str(path))

    def parse_stdf(self, file: str | Path) -> Any:
        from parser_engine.parsers.stdf.stdf_parser import StdfParser

        return StdfParser().parse(Path(file))

    def parse_csv(self, file: str | Path) -> Any:
        from parser_engine.parsers.csv.csv_parser import CsvParser

        return CsvParser().parse(Path(file))

    def parse_json(self, file: str | Path) -> Any:
        from parser_engine.parsers.json.json_parser import JsonParser

        return JsonParser().parse(Path(file))

    def parse_xml(self, file: str | Path) -> Any:
        from parser_engine.parsers.xml.xml_parser import XmlParser

        return XmlParser().parse(Path(file))

    def parse_ascii(self, file: str | Path) -> Any:
        from parser_engine.parsers.ascii.ascii_parser import AsciiParser

        return AsciiParser().parse(Path(file))
