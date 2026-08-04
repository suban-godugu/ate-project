"""ASCII / datalog / scan-log parser — registry-backed."""

from __future__ import annotations

from pathlib import Path

from parser_engine.adapters.registry import AdapterRegistry, default_registry
from parser_engine.config.settings import ADAPTER_CONFIG_DIR
from parser_engine.parsers.base import BaseParser, ParserResult


class AsciiParser(BaseParser):
    parser_id = "ascii"

    def __init__(self, registry: AdapterRegistry | None = None) -> None:
        self._registry = registry or default_registry(ADAPTER_CONFIG_DIR)

    def supported_extensions(self) -> set[str]:
        return {".log", ".txt", ".dat"}

    def detect(self, path: Path) -> bool:
        adapter = self._registry.resolve(path)
        if adapter is None:
            return False
        return adapter.adapter_id in {"verilumen_scan_v1", "generic_datalog"}

    def parse(self, path: Path) -> ParserResult:
        adapter = self._registry.resolve(path)
        if adapter is None:
            return ParserResult(errors=[{"file": str(path), "error": "No ASCII adapter matched"}])
        result = adapter.parse(path)
        return ParserResult(
            records=result.records,
            errors=result.errors,
            metadata={"parser": adapter.adapter_id, **result.metadata},
        )
