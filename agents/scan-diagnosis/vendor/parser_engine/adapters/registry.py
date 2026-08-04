"""Adapter registry — selects the first matching plugin for each file."""

from __future__ import annotations

from pathlib import Path

from parser_engine.adapters.base import LogAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: list[LogAdapter] = []

    def register(self, adapter: LogAdapter) -> None:
        self._adapters.append(adapter)

    def resolve(self, path: Path) -> LogAdapter | None:
        for adapter in self._adapters:
            if adapter.detect(path):
                return adapter
        return None

    @property
    def adapters(self) -> list[LogAdapter]:
        return list(self._adapters)


def default_registry(config_dir: Path | None = None) -> AdapterRegistry:
    """Build registry with all built-in adapters."""
    from parser_engine.adapters.csv_adapter import CsvAdapter
    from parser_engine.adapters.datalog_ascii import DatalogAsciiAdapter
    from parser_engine.adapters.stdf_v4 import StdfV4Adapter
    from parser_engine.adapters.verilumen_scan import VerilumenScanAdapter
    from parser_engine.adapters.yaml_config import load_adapter_configs

    registry = AdapterRegistry()
    registry.register(StdfV4Adapter())
    registry.register(VerilumenScanAdapter())

    config_root = config_dir or Path(__file__).resolve().parents[1] / "config" / "adapters"
    for config_path in sorted(config_root.glob("*.yaml")):
        cfg = load_adapter_configs(config_path)
        fmt = cfg.get("format", "")
        if fmt == "datalog_ascii":
            registry.register(DatalogAsciiAdapter(config_path))
        elif fmt == "csv":
            registry.register(CsvAdapter(config_path))

    return registry
