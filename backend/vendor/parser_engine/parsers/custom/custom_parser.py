"""Customer-specific YAML template parser (strategy pattern)."""

from __future__ import annotations

from pathlib import Path

from parser_engine.adapters.csv_adapter import CsvAdapter
from parser_engine.adapters.datalog_ascii import DatalogAsciiAdapter
from parser_engine.adapters.yaml_config import load_adapter_configs
from parser_engine.config.settings import ADAPTER_CONFIG_DIR
from parser_engine.parsers.base import BaseParser, ParserResult


class CustomParser(BaseParser):
    """Loads customer templates from config/adapters/*.yaml."""

    parser_id = "custom_yaml"

    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir or ADAPTER_CONFIG_DIR
        self._adapters: list[BaseParser] = []
        self._load_templates()

    def _load_templates(self) -> None:
        for config_path in sorted(self._config_dir.glob("*.yaml")):
            cfg = load_adapter_configs(config_path)
            fmt = cfg.get("format", "")
            if fmt == "datalog_ascii":
                self._adapters.append(_YamlWrapper(DatalogAsciiAdapter(config_path)))
            elif fmt == "csv":
                self._adapters.append(_YamlWrapper(CsvAdapter(config_path)))

    def detect(self, path: Path) -> bool:
        return any(adapter.detect(path) for adapter in self._adapters)

    def parse(self, path: Path) -> ParserResult:
        for adapter in self._adapters:
            if adapter.detect(path):
                return adapter.parse(path)
        return ParserResult(errors=[{"file": str(path), "error": "No custom template matched"}])


class _YamlWrapper(BaseParser):
    def __init__(self, adapter) -> None:
        self._adapter = adapter
        self.parser_id = getattr(adapter, "adapter_id", "custom")

    def detect(self, path: Path) -> bool:
        return self._adapter.detect(path)

    def parse(self, path: Path) -> ParserResult:
        result = self._adapter.parse(path)
        return ParserResult(
            records=result.records,
            errors=result.errors,
            metadata={"parser": self.parser_id, **result.metadata},
        )
