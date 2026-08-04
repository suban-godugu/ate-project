"""CSV parser — wraps YAML-configured csv adapter."""

from __future__ import annotations

from pathlib import Path

from parser_engine.adapters.registry import default_registry
from parser_engine.config.settings import ADAPTER_CONFIG_DIR
from parser_engine.parsers.base import BaseParser, ParserResult


class CsvParser(BaseParser):
    parser_id = "csv_die_results"

    def __init__(self) -> None:
        self._registry = default_registry(ADAPTER_CONFIG_DIR)

    def supported_extensions(self) -> set[str]:
        return {".csv"}

    def detect(self, path: Path) -> bool:
        adapter = self._registry.resolve(path)
        return adapter is not None and adapter.adapter_id == "csv_die_results"

    def parse(self, path: Path) -> ParserResult:
        adapter = self._registry.resolve(path)
        if adapter is None:
            return ParserResult(errors=[{"file": str(path), "error": "No CSV adapter matched"}])
        result = adapter.parse(path)
        return ParserResult(
            records=result.records,
            errors=result.errors,
            metadata={"parser": adapter.adapter_id, **result.metadata},
        )
